"""Hand-calculated contracts, fit boundaries, cohort controls and exact byte provenance."""
import copy
import csv
from decimal import Decimal
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from .features import FIELDS, money, aggregate
from .fixture import fixture_bytes
from .clustering import fit_transform, transform, kmeans, predict
from .metrics import ari, align, silhouette
from .protocol import validate, split, learn, evaluate
from .__main__ import BASE, ROOT, encoded, identity, execute, gate, decode


def config():
    return json.loads((BASE/'protocol.json').read_bytes())


def line(**kw):
    row=dict(zip(FIELDS,['C1','O1','L1','2024-12-30','2','$113.40','$56.90','($0.40)','USD']))
    row.update(kw)
    return row


def csv_data(rows):
    out=io.StringIO(newline=''); writer=csv.DictWriter(out,fieldnames=FIELDS,lineterminator='\n')
    writer.writeheader(); writer.writerows(rows)
    return out.getvalue().encode()


class FeatureTests(unittest.TestCase):
    def test_accounting_and_explicit_negative(self):
        for text in ['($0.40)','-$0.40','$-0.40','-0.4']:
            self.assertEqual(money(text),Decimal('-.40'))
        self.assertEqual(money('($1,234.50)'),Decimal('-1234.50'))
        self.assertEqual(money(' +$12.30 '),Decimal('12.30'))

    def test_zero_is_not_missing(self):
        for text in ['0','$0.00','-0','($0.00)']:
            self.assertEqual(money(text),Decimal(0))
        for text in ['', ' . ', 'NA','N/A']:
            self.assertIsNone(money(text))

    def test_ambiguous_money_rejected(self):
        for text in ['1,23','1.234,56','1e3','NaN','Infinity','--1','(-1)','($-1)',
                     '1 000','£1','1%','1.001','1.','$','00','-','1,0000','$$1']:
            with self.subTest(text=text), self.assertRaises(ValueError): money(text)

    def test_negative_reconciles_exactly(self):
        customers,ledger=aggregate(csv_data([line()]),config())
        c=customers[0]
        self.assertEqual(Decimal(c['observed_profit']),Decimal('-.40'))
        self.assertEqual(Decimal(c['reconciliation_residual']),0)
        self.assertEqual(Decimal(c['purchased_cost']),Decimal('113.80'))
        self.assertEqual(ledger['eligible_profit'],'-0.40')

    def test_multiple_lines_one_order_and_weighted_cost(self):
        rows=[line(),line(line_id='L2',quantity='1',revenue='20',unit_cost='10',profit='10')]
        c=aggregate(csv_data(rows),config())[0][0]
        self.assertEqual((c['distinct_orders'],c['line_count'],c['purchased_units']),(1,2,3))
        self.assertEqual(Decimal(c['observed_profit']),Decimal('9.60'))
        self.assertEqual(Decimal(c['unit_weighted_cost']),Decimal('123.80')/3)
        self.assertEqual(Decimal(c['line_mean_unit_cost']),Decimal('33.45'))

    def test_duplicate_replay_not_legitimate_second_line(self):
        rows=[line(),line(),line(line_id='L2')]
        c,l=aggregate(csv_data(rows),config())
        self.assertEqual((l['raw_lines'],l['retained_lines'],l['duplicate_replays']),(3,2,1))
        self.assertEqual(c[0]['line_count'],2)
        self.assertEqual(Decimal(c[0]['observed_profit']),Decimal('-.80'))

    def test_conflicting_duplicate(self):
        with self.assertRaises(ValueError):
            aggregate(csv_data([line(),line(profit='0.40')]),config())

    def test_conflicting_order_owner_or_date(self):
        for change in [{'customer_id':'C2'}, {'order_date':'2024-12-29'}]:
            with self.assertRaises(ValueError):
                aggregate(csv_data([line(),line(line_id='L2',**change)]),config())

    def test_missing_identity_or_quantity_rejected(self):
        for change in [{'line_id':''},{'customer_id':' A'},{'quantity':'0'},{'quantity':'1.5'},
                       {'quantity':'-1'},{'currency':'GBP'}]:
            with self.assertRaises(ValueError): aggregate(csv_data([line(**change)]),config())

    def test_missing_excludes_whole_customer_zero_kept(self):
        rows=[line(),line(line_id='L2',profit='.'),
              line(customer_id='C2',order_id='O2',quantity='1',revenue='0',unit_cost='0',profit='0')]
        customers,ledger=aggregate(csv_data(rows),config())
        self.assertEqual([c['customer_id'] for c in customers],['C2'])
        self.assertEqual(ledger['excluded'],[{'customer_id':'C1','reasons':['missing_money']}])

    def test_tolerance_and_flag_policy(self):
        cfg=config()
        c=aggregate(csv_data([line(profit='-0.39')]),cfg)[0][0]
        self.assertEqual(Decimal(c['reconciliation_residual']),Decimal('.01'))
        with self.assertRaises(ValueError): aggregate(csv_data([line(profit='-0.38')]),cfg)
        cfg['reconciliation_policy']='flag_exclude_customer'
        cs,l=aggregate(csv_data([line(profit='0.40')]),cfg)
        self.assertEqual(cs,[]); self.assertEqual(l['excluded'][0]['reasons'],['reconciliation'])

    def test_fixed_reference_date(self):
        c=aggregate(csv_data([line()]),config())[0][0]
        self.assertEqual(c['recency_days'],2)
        cfg=config(); cfg['reference_date']='2025-01-02'
        self.assertEqual(aggregate(csv_data([line()]),cfg)[0][0]['recency_days'],3)
        for day in ['2025-01-02','2023-12-31','2024-02-30','30DEC2024']:
            with self.assertRaises(ValueError): aggregate(csv_data([line(order_date=day)]),config())

    def test_input_row_order_does_not_change_aggregation(self):
        rows=[line(),line(line_id='L2'),line(order_id='O2',order_date='2024-12-31')]
        self.assertEqual(aggregate(csv_data(rows),config()),aggregate(csv_data(rows[::-1]),config()))

    def test_actual_original_schema_not_silently_accepted(self):
        with self.assertRaises(ValueError): aggregate(b'Customer ID,Order ID,Profit\n1,2,3\n',config())


class ScientificTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg=config()
        cls.customers,_=aggregate(fixture_bytes(),cls.cfg)
        cls.fit,cls.holdout=split(cls.customers,cls.cfg)
        cls.frozen=learn(cls.fit,cls.cfg)

    def test_signed_transform_and_zero_variance(self):
        state,x=fit_transform([[-10,7],[0,7],[10,7]],[10,1])
        self.assertAlmostEqual(x[0][0],-x[2][0]); self.assertEqual(x[1],[0,0])
        self.assertEqual(state['zero_variance'],[1])
        self.assertEqual(transform([[5,999]],state)[0][1],0)

    def test_train_only_preprocessing(self):
        state,_=fit_transform([[0],[1]],[1]); before=copy.deepcopy(state)
        self.assertGreater(transform([[1e9]],state)[0][0],10)
        self.assertEqual(state,before)
        self.assertAlmostEqual(state['means'][0],0.4406867935097715)

    def test_kmeans_hand_geometry_deterministic(self):
        x=[[0.0],[2.0],[10.0],[12.0]]
        m=kmeans(x,2,4)
        self.assertEqual(sorted(c[0] for c in m['centres']),[1,11])
        self.assertEqual(m['inertia'],4)
        self.assertTrue(m['converged'])
        self.assertEqual(m,kmeans(x,2,4))
        self.assertEqual(predict([[1],[11]],m['centres']),predict([[1],[11]],m['centres']))

    def test_degenerate_kmeans_and_budgets(self):
        with self.assertRaises(ValueError): kmeans([[0],[0],[1]],3,1)
        for key,value in [('restarts',11),('max_iterations',101),('silhouette_limit',101),('max_lines',5001)]:
            cfg=config(); cfg[key]=value
            with self.assertRaises(ValueError): validate(cfg)

    def test_ari_label_permutation_and_negative_agreement(self):
        self.assertEqual(ari([0,0,1,1],[7,7,3,3]),1)
        self.assertAlmostEqual(ari([0,0,1,1],[0,1,0,1]),-.5)
        self.assertEqual(ari([0,0,0],[9,9,9]),1)
        self.assertEqual(ari([0,1,2],[2,3,1]),1)

    def test_silhouette_hand_calculation_and_singleton(self):
        s=silhouette([[0],[2],[10],[12]],[0,0,1,1],list('abcd'),100,4)
        self.assertAlmostEqual(s['score'],((1-2/11)+(1-2/9))/2)
        s=silhouette([[0],[10],[12]],[0,1,1],list('abc'),100,4)
        self.assertAlmostEqual(s['score'],(0+.8+10/12)/3)
        self.assertIsNone(silhouette([[0],[1]],[0,0],list('ab'),100,4)['score'])

    def test_silhouette_sampling_fixed_and_bounded(self):
        x=[[float(i)] for i in range(150)]; labels=[i//50 for i in range(150)]
        a=silhouette(x,labels,list(map(str,range(150))),50,7)
        self.assertEqual(a,silhouette(x,labels,list(map(str,range(150))),50,7))
        self.assertEqual(a['n'],50); self.assertIn('sample',a['method'])

    def test_id_alignment_and_invalid_cohorts(self):
        self.assertEqual(align(['a','b'],[('b',1),('a',0)]),[0,1])
        for pairs in [[('a',0)],[('a',0),('a',1)],[('a',0),('c',1)]]:
            with self.assertRaises(ValueError): align(['a','b'],pairs)
        for ids in [self.cfg['fit_ids'][:4],self.cfg['evaluation_ids'][:-1],['UNKNOWN']*4]:
            cfg=config(); cfg['evaluation_ids']=ids
            with self.assertRaises(ValueError): split(self.customers,cfg)

    def test_holdout_perturbation_leaves_fits_unchanged(self):
        changed=copy.deepcopy(self.customers)
        for c in changed:
            if c['customer_id'] in self.cfg['evaluation_ids']:
                c['observed_profit']='999999'; c['unit_weighted_cost']='999999'
        fit,holdout=split(changed,self.cfg)
        frozen=learn(fit,self.cfg)
        self.assertEqual(frozen,self.frozen)
        before=encoded(frozen)
        evaluate(frozen,fit,holdout,self.cfg)
        self.assertEqual(encoded(frozen),before)

    def test_stability_never_fits_holdout(self):
        holdout=set(self.cfg['evaluation_ids']); train=set(self.cfg['fit_ids'])
        for c in self.frozen:
            for s in [c['baseline']]+[v['state'] for v in c['variations']]:
                self.assertFalse(holdout & set(s['fit_ids']))
                self.assertLessEqual(set(s['fit_ids']),train)
            for v in c['variations']:
                if v['kind']=='resample': self.assertLess(len(v['state']['fit_ids']),len(train))
        bad=copy.deepcopy(self.frozen)
        bad[0]['variations'][0]['state']['fit_ids'].append(self.cfg['evaluation_ids'][0])
        with self.assertRaises(ValueError): evaluate(bad,self.fit,self.holdout,self.cfg)

    def test_deterministic_full_evaluation_and_no_mutation(self):
        before=encoded(self.frozen)
        a=evaluate(self.frozen,self.fit,self.holdout,self.cfg)
        self.assertEqual(a,evaluate(learn(self.fit,self.cfg),self.fit,self.holdout,self.cfg))
        self.assertEqual(encoded(self.frozen),before)
        self.assertEqual([c['k'] for c in a],[2,3])
        for c in a:
            self.assertEqual(sum(p['n'] for p in c['evaluation_profiles']),12)
            self.assertEqual(set(c['evaluation_assignments']),set(self.cfg['evaluation_ids']))
        with self.assertRaises(ValueError): evaluate(self.frozen,self.fit,self.holdout[::-1],self.cfg)


class ArtifactTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name).resolve()
        self.ip=self.root/'input.csv'; self.cp=self.root/'config.json'; self.rp=self.root/'receipt.json'
        self.ip.write_bytes(fixture_bytes()); self.cp.write_bytes((BASE/'protocol.json').read_bytes())

    def receipt(self,output):
        r=dict(authorized_local_processing=True,redistribution_authorized=False,
               scope='private_customer_segmentation',authority_reference='TEST ONLY: invented records',
               identity_basis='TEST: generator identities',mapping_reference='TEST: canonical fixture',
               input_path=str(self.ip),config_path=str(self.cp),output_path=str(output),
               input=identity(self.ip.read_bytes()),config=identity(self.cp.read_bytes()))
        self.rp.write_bytes(encoded(r)); return r

    def test_two_fresh_replays_and_all_manifest_hashes(self):
        a,b=self.root/'a',self.root/'b'
        ma=execute(BASE/'fixtures/synthetic.csv',BASE/'protocol.json',a)
        execute(BASE/'fixtures/synthetic.csv',BASE/'protocol.json',b)
        self.assertEqual({p.name:p.read_bytes() for p in a.iterdir()},
                         {p.name:p.read_bytes() for p in b.iterdir()})
        for name,expected in ma['files'].items(): self.assertEqual(identity((a/name).read_bytes()),expected)
        for name,expected in ma['source'].items(): self.assertEqual(identity((BASE/name).read_bytes()),expected)
        self.assertEqual(ma['input'],identity(fixture_bytes()))
        self.assertEqual(ma['config'],identity((BASE/'protocol.json').read_bytes()))
        self.assertEqual(ma['frozen_before_evaluation'],identity((a/'frozen.json').read_bytes()))
        self.assertEqual(ma['run_id'],json.loads((a/'evaluation.json').read_bytes())['run_id'])
        (a/'evaluation.json').write_bytes(b'changed')
        self.assertNotEqual(ma['files']['evaluation.json'],identity((a/'evaluation.json').read_bytes()))

    def test_private_receipt_bound_to_exact_bytes_and_locations(self):
        output=self.root/'private'; receipt=self.receipt(output)
        m=execute(self.ip,self.cp,output,self.rp)
        self.assertEqual(m['scope'],'private_no_redistribution')
        self.assertEqual(m['permission_receipt'],identity(self.rp.read_bytes()))
        self.assertEqual((output/'permission_receipt.json').read_bytes(),self.rp.read_bytes())
        with self.assertRaises(ValueError): gate(self.ip,self.cp,self.root/'wrong',self.rp)
        for p in [self.ip,self.cp]:
            p.write_bytes(p.read_bytes()+b'\n')
            receipt['output_path']=str(self.root/'tamper'); self.rp.write_bytes(encoded(receipt))
            with self.assertRaises(ValueError): gate(self.ip,self.cp,self.root/'tamper',self.rp)

    def test_hashes_bind_consumed_buffers_despite_later_file_edits(self):
        output=self.root/'private'; self.receipt(output)
        original_input=self.ip.read_bytes(); original_config=self.cp.read_bytes()
        from . import __main__ as runner
        actual=runner.aggregate
        def mutate_after_read(raw,cfg):
            self.ip.write_bytes(b'changed after ingestion'); self.cp.write_bytes(b'{}')
            return actual(raw,cfg)
        with patch.object(runner,'aggregate',side_effect=mutate_after_read):
            m=execute(self.ip,self.cp,output,self.rp)
        self.assertEqual(m['input'],identity(original_input)); self.assertEqual(m['config'],identity(original_config))
        self.assertEqual((output/'input.csv').read_bytes(),original_input)
        self.assertEqual((output/'config.json').read_bytes(),original_config)

    def test_missing_false_or_unbound_authority_rejected(self):
        output=self.root/'out'
        with self.assertRaises(ValueError): gate(self.ip,self.cp,output,None)
        for key,value in [('authorized_local_processing',False),('authority_reference',''),
                          ('mapping_reference',''),('identity_basis',''),('redistribution_authorized',True),
                          ('input',{}),('config',{}),('input_path','wrong')]:
            r=self.receipt(output); r[key]=value; self.rp.write_bytes(encoded(r))
            with self.assertRaises(ValueError): gate(self.ip,self.cp,output,self.rp)

    def test_private_locations_symlinks_and_existing_output_rejected(self):
        output=self.root/'out'; self.receipt(output)
        with self.assertRaises(ValueError): gate(self.ip,self.cp,ROOT/'private-leak',self.rp)
        link=self.root/'link.csv'; link.symlink_to(self.ip)
        with self.assertRaises(ValueError): gate(link,self.cp,output,self.rp)
        output.mkdir()
        with self.assertRaises(ValueError): gate(self.ip,self.cp,output,self.rp)

    def test_nonfixture_cannot_use_public_route(self):
        from . import __main__ as runner
        real=runner.read_bounded
        def changed(path):
            return b'not invented' if path==BASE/'fixtures/synthetic.csv' else real(path)
        with patch.object(runner,'read_bounded',side_effect=changed),self.assertRaises(ValueError):
            gate(BASE/'fixtures/synthetic.csv',BASE/'protocol.json',self.root/'out',None)

    def test_duplicate_json_keys_and_nonfinite_rejected(self):
        for raw in [b'{"a":1,"a":2}',b'{"a":NaN}',b'{"a":Infinity}']:
            with self.assertRaises(ValueError): decode(raw)


if __name__=='__main__': unittest.main()
