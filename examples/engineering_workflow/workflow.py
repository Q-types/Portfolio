"""Small durable model; trusted callers, one local SQLite file, no external I/O."""
from contextlib import contextmanager
import hashlib
import json
import sqlite3


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


class Workflow:
    def __init__(self, path, policy):
        self.db = sqlite3.connect(path, timeout=2, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.permit = None  # Deliberately lost on restart; never reconstructed.
        self.policy = json.loads(encoded(policy))
        self.db.executescript('''
            CREATE TABLE IF NOT EXISTS settings (binding TEXT PRIMARY KEY);
            CREATE TABLE IF NOT EXISTS tasks (key TEXT PRIMARY KEY, body TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS slots (scope TEXT PRIMARY KEY, task TEXT UNIQUE NOT NULL);
            CREATE TABLE IF NOT EXISTS records (id TEXT PRIMARY KEY, body TEXT NOT NULL);
            CREATE TRIGGER IF NOT EXISTS immutable_update BEFORE UPDATE ON records
              BEGIN SELECT RAISE(ABORT, 'immutable record'); END;
            CREATE TRIGGER IF NOT EXISTS immutable_delete BEFORE DELETE ON records
              BEGIN SELECT RAISE(ABORT, 'immutable record'); END;
            CREATE TABLE IF NOT EXISTS simulated_receipts (intent TEXT PRIMARY KEY, binding TEXT NOT NULL);
        ''')
        try:
            with self.transaction():
                rows = self.db.execute('SELECT binding FROM settings').fetchall()
                if rows:
                    require(len(rows) == 1 and rows[0][0] == digest(policy), 'policy drift')
                else:
                    self.db.execute('INSERT INTO settings VALUES (?)', (digest(policy),))
        except BaseException:
            self.db.close()
            raise

    def close(self):
        self.db.close()

    @contextmanager
    def transaction(self):
        self.db.execute('BEGIN IMMEDIATE')
        try:
            yield
            self.db.commit()
        except BaseException:
            self.db.rollback()
            raise

    def task(self, key):
        row = self.db.execute('SELECT body FROM tasks WHERE key=?', (key,)).fetchone()
        require(row is not None, 'missing task')
        return json.loads(row[0])

    def save(self, task):
        self.db.execute('UPDATE tasks SET body=? WHERE key=?', (encoded(task).decode(), task['key']))

    def record(self, value):
        key = digest(value)
        self.db.execute('INSERT OR IGNORE INTO records VALUES (?,?)', (key, encoded(value).decode()))
        require(self.read(key) == value, 'record collision')
        return key

    def read(self, key):
        row = self.db.execute('SELECT body FROM records WHERE id=?', (key,)).fetchone()
        require(row is not None, 'missing evidence')
        value = json.loads(row[0])
        require(digest(value) == key, 'evidence hash mismatch')
        return value

    def owned(self, key, actor, stages):
        t = self.task(key)
        require(actor == t['request']['implementer'], 'writer mismatch')
        require(t['stage'] in stages, 'invalid transition')
        require(self.db.execute('SELECT task FROM slots WHERE scope=?',
                                (t['request']['scope'],)).fetchone()[0] == key, 'writer lost')
        return t

    def admit(self, request, owner):
        require(owner == self.policy['owner'] and digest(request) in self.policy['intake'], 'unauthorized intake')
        with self.transaction():
            old = self.db.execute('SELECT body FROM tasks WHERE key=?', (request['key'],)).fetchone()
            if old:
                require(json.loads(old[0])['request'] == request, 'conflicting request')
                return 'duplicate'
            require(request['scope'] in self.policy['scopes'], 'undeclared scope')
            require(not self.db.execute('SELECT 1 FROM slots WHERE scope=?', (request['scope'],)).fetchone(), 'writer conflict')
            self.db.execute('INSERT INTO slots VALUES (?,?)', (request['scope'], request['key']))
            task = dict(key=request['key'], request=request, stage='building', highest=0,
                        generation=0, candidate=None, evidence=None, review=None, intent=None)
            self.db.execute('INSERT INTO tasks VALUES (?,?)', (task['key'], encoded(task).decode()))
            return 'admitted'

    def candidate(self, key, actor, commit, content):
        with self.transaction():
            t = self.owned(key, actor, {'building', 'verified', 'reviewed'})
            t['generation'] += 1
            t['candidate'] = self.record(dict(kind='candidate', task=key, generation=t['generation'],
                base=t['request']['base'], base_source=t['request']['source_sha256'],
                commit=commit, source_sha256=hashlib.sha256(content.encode()).hexdigest()))
            t.update(stage='candidate', evidence=None, review=None)
            self.save(t)
            return t['candidate']

    def verify(self, key, actor, evidence):
        with self.transaction():
            t = self.owned(key, actor, {'candidate'})
            require(evidence == dict(kind='checks', candidate=t['candidate'], result='pass'), 'check binding mismatch')
            t.update(evidence=self.record(evidence), stage='verified', highest=max(t['highest'], 1))
            self.save(t)
            return t['evidence']

    def review(self, key, reviewer, candidate, evidence, verdict):
        with self.transaction():
            t = self.task(key)
            require(t['stage'] == 'verified', 'invalid transition')
            require(reviewer in self.policy['reviewers'] and reviewer != t['request']['implementer'], 'independent reviewer required')
            require((candidate, evidence) == (t['candidate'], t['evidence']), 'review binding mismatch')
            self.read(candidate); self.read(evidence)
            require(verdict in {'pass', 'reject'}, 'invalid verdict')
            t['review'] = self.record(dict(kind='review', task=key, reviewer=reviewer,
                candidate=candidate, evidence=evidence, verdict=verdict))
            t['stage'] = 'reviewed' if verdict == 'pass' else 'building'
            self.save(t)
            return t['review']

    def binding(self, key):
        t = self.task(key)
        return dict(task=key, candidate=t['candidate'], evidence=t['evidence'], review=t['review'],
                    branch=t['request']['branch'], base=t['request']['base'], epoch=self.policy['epoch'])

    def approve_publication(self, key, publisher, binding):
        with self.transaction():
            t = self.task(key)
            require(publisher in self.policy['publishers'], 'publication permission missing')
            require(t['stage'] == 'reviewed' and binding == self.binding(key), 'approval stale or mismatched')
            require(self.read(t['review'])['verdict'] == 'pass', 'review rejected')
            return self.record(dict(kind='publication_approval', publisher=publisher, binding=binding))

    def begin_publication(self, key, approval, expected_binding):
        with self.transaction():
            t = self.task(key)
            require(t['stage'] == 'reviewed', 'invalid transition')
            a = self.read(approval)
            require(a['kind'] == 'publication_approval' and a['publisher'] in self.policy['publishers']
                    and a['binding'] == expected_binding == self.binding(key), 'publication intent binding mismatch')
            t['intent'] = self.record(dict(kind='publication_intent', approval=approval, binding=expected_binding))
            t['stage'] = 'unknown'
            self.save(t)
        self.permit = t['intent']
        return t['intent']

    def simulate_once(self, key):
        """Local stand-in only. The original caller may invoke once after intent commit."""
        t = self.task(key)
        require(t['stage'] == 'unknown' and self.permit == t['intent'], 'no invocation permission; reconcile')
        self.permit = None
        with self.transaction():
            self.db.execute('INSERT INTO simulated_receipts VALUES (?,?)',
                            (t['intent'], digest(self.read(t['intent'])['binding'])))

    def reconcile(self, key):
        with self.transaction():
            t = self.task(key)
            require(t['stage'] in {'unknown', 'published'}, 'no publication intent')
            binding = self.read(t['intent'])['binding']
            receipt = self.db.execute('SELECT binding FROM simulated_receipts WHERE intent=?', (t['intent'],)).fetchone()
            if not receipt:
                return 'held_unknown'  # Absence never proves the external action did not happen.
            require(receipt[0] == digest(binding) and binding == self.binding(key), 'readback mismatch')
            t.update(stage='published', highest=max(t['highest'], 2))
            self.save(t)
            self.db.execute('DELETE FROM slots WHERE task=?', (key,))
            return 'simulated_publication_confirmed'

    def interrupt(self, key, actor):
        with self.transaction():
            t = self.owned(key, actor, {'building', 'candidate', 'verified', 'reviewed'})
            t.update(resume=t['stage'], stage='held')
            self.save(t)

    def recover(self, key, owner, source_hash):
        with self.transaction():
            t = self.task(key)
            require(owner == self.policy['owner'] and t['stage'] == 'held'
                    and source_hash == t['request']['source_sha256'], 'recovery authority mismatch')
            t['stage'] = t.pop('resume')
            self.save(t)

    def summary(self):
        return {'tasks': [json.loads(r[0]) for r in self.db.execute('SELECT body FROM tasks ORDER BY key')],
                'slots': [dict(r) for r in self.db.execute('SELECT * FROM slots ORDER BY scope')],
                'records': {r['id']: json.loads(r['body']) for r in self.db.execute('SELECT * FROM records ORDER BY id')},
                'simulated_effect_count': self.db.execute('SELECT COUNT(*) FROM simulated_receipts').fetchone()[0]}
