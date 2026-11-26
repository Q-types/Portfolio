import copy
import csv
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from .data import advance, read_series, validate_series, validate_protocol
from .evaluation import run, metrics, aligned_score, row_key
from .methods import forecast
from .adapters import recursive_scaled, tune_recursive, arima_forecast

PACKAGE = Path(__file__).resolve().parent


class ProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads((PACKAGE/'protocol.json').read_text())
        cls.series = read_series(PACKAGE/'fixtures/synthetic.csv', cls.config['experiments'])
        cls.result = run(cls.config, cls.series)

    def test_hand_metrics_and_zero_rules(self):
        m = metrics([0,2,4], [1,1,6], [(0,0),(0,1),(3,5)])
        self.assertAlmostEqual(m['mae'],4/3)
        self.assertAlmostEqual(m['rmse'],math.sqrt(2))
        self.assertAlmostEqual(m['wape_pct'],100*4/6)
        self.assertEqual(m['mape_pct'],50)
        self.assertEqual(m['mape_n'],2)
        self.assertAlmostEqual(m['coverage'],2/3)
        self.assertIsNone(metrics([0],[3])['wape_pct'])
        self.assertIsNone(metrics([0],[3])['mape_pct'])
        for a,p in [([],[]),([1],[1,2]),([float('nan')],[1])]:
            with self.assertRaises(ValueError): metrics(a,p)

    def test_calendar(self):
        self.assertEqual(advance('2020-01-31','M-END'),'2020-02-29')
        self.assertEqual(advance('2020-02-29','M-END'),'2020-03-31')
        self.assertEqual(advance('2022-12-31','W-SAT'),'2023-01-07')
        self.assertEqual(advance('2023-12-31','M-END'),'2024-01-31')
        for d,c in [('2020-02-28','M-END'),('2023-01-01','W-SAT'),('20200104','W-SAT')]:
            with self.assertRaises(ValueError): advance(d,c)

    def test_bad_series(self):
        valid = [('2020-01-04',0.),('2020-01-11',1.)]
        self.assertEqual(validate_series(valid,'W-SAT'),valid)
        for bad in [[],valid[::-1],valid+valid[-1:], [valid[0],('2020-01-18',1)],
                    [('2020-01-04',float('nan'))], [('2020-01-04',-1)]]:
            with self.assertRaises(ValueError): validate_series(bad,'W-SAT')

    def test_recursive_baselines_by_hand(self):
        self.assertEqual(forecast([1,2,3,4],5,2,'naive'),[4]*5)
        self.assertEqual(forecast([1,2,3,4],5,2,'seasonal_naive'),[3,4,3,4,3])
        self.assertEqual(forecast([1,2,3,4],5,2,'seasonal_drift'),[5,6,7,8,9])
        with self.assertRaises(ValueError): forecast([1],2,2,'naive')

    def test_partitions(self):
        for change in ('overlap','duplicate','history','horizon'):
            c=copy.deepcopy(self.config);e=c['experiments'][0]
            if change=='overlap':e['calibration'][0]=e['development'][-1]
            if change=='duplicate':e['development'].append(e['development'][-1])
            if change=='history':e['development'][0]='2015-01-03'
            if change=='horizon':e['horizon']=8
            with self.assertRaises(ValueError):validate_protocol(c,self.series)

    def test_fixed_origin_label_perturbation_and_negative_control(self):
        changed=copy.deepcopy(self.series)
        for e in self.config['experiments']:
            for title in e['titles']:
                changed[e['id'],title]=[(d,v+10000 if d>e['evaluation'][0] else v)
                                         for d,v in changed[e['id'],title]]
        result=run(self.config,changed)
        self.assertEqual(self.result['decisions'],result['decisions'])
        for e in self.config['experiments']:
            select=lambda rs:[r for r in rs if r['experiment']==e['id'] and r['origin']==e['evaluation'][0]]
            self.assertEqual(select(self.result['forecasts']),select(result['forecasts']))
            # Later origin is allowed to learn already-observed earlier evaluation history.
            select_later=lambda rs:[r for r in rs if r['experiment']==e['id'] and r['origin']==e['evaluation'][1]]
            self.assertNotEqual(select_later(self.result['forecasts']),select_later(result['forecasts']))
        self.assertNotEqual(self.result['scores'],result['scores'])
        # Deliberately leaky predictor fails the same invariant.
        bad=lambda s: s['weekly','synthetic_a'][-1][1]
        self.assertNotEqual(bad(self.series),bad(changed))

    def test_exact_alignment_and_independent_scores(self):
        rows=[r for r in self.result['forecasts'] if r['experiment']=='monthly' and r['title']=='synthetic_a' and r['method']=='naive']
        labels={row_key(r):dict(self.series['monthly','synthetic_a'])[r['target']] for r in rows}
        self.assertEqual(aligned_score(rows,labels)['n'],16)
        for bad in [rows[:-1],rows+rows[:1]]:
            with self.assertRaises(ValueError):aligned_score(bad,labels)
        shifted=copy.deepcopy(rows);shifted[0]['origin']='2020-01-31'
        with self.assertRaises(ValueError):aligned_score(shifted,labels)
        for e in self.config['experiments']:
            sets=[{row_key(r) for r in self.result['forecasts'] if r['experiment']==e['id'] and r['method']==m}
                  for m in ('naive','seasonal_naive','seasonal_drift','selected','ensemble')]
            self.assertTrue(all(s==sets[0] for s in sets))

    def test_runner_rejects_missing_comparator_row(self):
        from . import evaluation
        real_issue = evaluation.issue
        def truncated(rows, experiment, origin):
            predictions = real_issue(rows, experiment, origin)
            if origin == experiment['evaluation'][0]:
                predictions['seasonal_naive'] = predictions['seasonal_naive'][:-1]
            return predictions
        with patch.object(evaluation, 'issue', side_effect=truncated):
            with self.assertRaises(ValueError):
                run(self.config, self.series)

    def test_input_digest_binds_parsed_bytes(self):
        from .data import parse_series
        payload = (PACKAGE/'fixtures/synthetic.csv').read_bytes()
        self.assertEqual(parse_series(payload, self.config['experiments']), self.series)

    def test_calibration_radii_by_hand(self):
        from .evaluation import calibrate
        e=dict(horizon=2,season=2,cadence='W-SAT',calibration=['2020-02-01'])
        rows=[(advance('2020-01-04','W-SAT',i),float(i+1)) for i in range(7)]
        radii=calibrate(rows,e,'naive',dict(naive=1,seasonal_naive=0,seasonal_drift=0),.8)
        self.assertEqual(radii['naive'],[1,2])
        self.assertEqual(radii['ensemble'],[1,2])

    def test_advanced_fold_scaling_and_recursion(self):
        captured=[]
        def factory(x,y):
            captured.append((x,y))
            return lambda lag,date:lag[-1]+.5
        self.assertEqual(recursive_scaled([10,20,30],['a','b'],1,factory),[40,50])
        self.assertEqual(captured[0],([(0.0,),(0.5,)],[0.5,1.0]))
        e=self.config['experiments'][1]; rows=self.series['monthly','synthetic_a']
        changed=[(d,v+100000 if d>e['evaluation'][0] else v) for d,v in rows]
        factories={'last':lambda x,y:lambda lag,date:lag[-1], 'zero':lambda x,y:lambda lag,date:0}
        self.assertEqual(tune_recursive(rows,e,3,factories),tune_recursive(changed,e,3,factories))
        with self.assertRaises(ValueError):recursive_scaled([1,2],['a'],1,lambda x,y:lambda lag,date:float('nan'))

    def test_arima_alias_contract(self):
        class PM:
            def __init__(self,**options):pass
            def fit(self,history):self.last=history[-1];return self
            def predict(self,n_periods):return [self.last]*n_periods
        class SM:
            def __init__(self,history,**options):self.last=history[-1]
            def fit(self):return self
            def forecast(self,steps):return [self.last]*steps
        self.assertEqual(arima_forecast([1,2],3,'pmdarima',PM,{}),[2]*3)
        self.assertEqual(arima_forecast([1,2],3,'statsmodels',SM,{}),[2]*3)
        with self.assertRaises(ValueError):arima_forecast([1,2],3,'ambiguous',PM,{})

    def test_adapter_row_contract(self):
        from .adapters import forecast_rows
        e=self.config['experiments'][1]
        rows=forecast_rows(e,'synthetic_a',e['evaluation'][0],[1]*8,'external')
        self.assertEqual(rows[-1]['target'],advance(e['evaluation'][0],'M-END',8))
        for values in ([1]*7,[float('nan')]*8):
            with self.assertRaises(ValueError):forecast_rows(e,'synthetic_a',e['evaluation'][0],values,'external')

    def test_future_alignment(self):
        for e in self.config['experiments']:
            rows=[r for r in self.result['future'] if r['experiment']==e['id']]
            self.assertEqual({r['origin'] for r in rows},{self.series[e['id'],'synthetic_a'][-1][0]})
            self.assertTrue(all(r['target']==advance(r['origin'],e['cadence'],r['horizon']) for r in rows))

    def test_cli_replay_and_refusal(self):
        with tempfile.TemporaryDirectory() as tmp:
            outputs=[]
            for name in ('a','b'):
                dest=Path(tmp)/name
                subprocess.run([sys.executable,'-B','-m','examples.book_sales_forecasting','--output',str(dest)],check=True,capture_output=True)
                outputs.append({p.name:p.read_bytes() for p in dest.iterdir()})
            self.assertEqual(*outputs)
            private_input=Path(tmp)/'private.csv'
            private_input.write_bytes((PACKAGE/'fixtures/synthetic.csv').read_bytes())
            dest=Path(tmp)/'private_results'
            subprocess.run([sys.executable,'-B','-m','examples.book_sales_forecasting',
                            '--input',str(private_input),'--authorized-local-use',
                            '--output',str(dest)],check=True,capture_output=True)
            self.assertEqual((dest/'scores.csv').read_bytes(),outputs[0]['scores.csv'])
            self.assertEqual(json.loads((dest/'manifest.json').read_text())['evidence'],'private retrospective')
            command=[sys.executable,'-B','-m','examples.book_sales_forecasting','--output',str(Path(tmp)/'a')]
            self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0)
            command += ['--input',str(PACKAGE/'fixtures/synthetic.csv')]
            self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0)


if __name__ == '__main__':
    unittest.main()
