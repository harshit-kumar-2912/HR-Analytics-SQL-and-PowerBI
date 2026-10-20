"""Static integrity checks; these are not a substitute for the Desktop engine."""
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class PowerBISourceTests(unittest.TestCase):
    def test_all_visual_fields_exist(self):
        folder=ROOT/'powerbi'
        model=json.loads((folder/'HR.SemanticModel/model.bim').read_text())['model']
        tables={t['name']:t for t in model['tables']}
        report=json.loads((folder/'HR.Report/report.json').read_text())
        self.assertEqual(len(report['sections']),2)
        visuals=0
        for page in report['sections']:
            for v in page['visualContainers']:
                sv=json.loads(v['config'])['singleVisual']
                q=sv.get('prototypeQuery')
                if not q:continue
                visuals+=1
                aliases={s['Name']:s['Entity'] for s in q['From']}
                names=set()
                for field in q['Select']:
                    kind='Measure' if 'Measure' in field else 'Column'
                    ref=field[kind];table=tables[aliases[ref['Expression']['SourceRef']['Source']]]
                    self.assertIn(ref['Property'],{f['name'] for f in table['measures' if kind=='Measure' else 'columns']})
                    names.add(field['Name'])
                for projections in sv['projections'].values():
                    for projection in projections:self.assertIn(projection['queryRef'],names)
                executable=json.loads(v['query'])['Commands'][0]['SemanticQueryDataShapeCommand']['Query']
                self.assertEqual(executable,q)
        self.assertEqual(visuals,15)
        measures={m['name']:m['expression'] for m in tables['Employees']['measures']}
        self.assertEqual(measures['Cumulative Exit Share'],'DIVIDE([Terminated Employees], [Eligible Hires])')
    def test_local_model_and_no_legacy_cloud_connection(self):
        folder=ROOT/'powerbi'
        ref=json.loads((folder/'HR.Report/definition.pbir').read_text())
        self.assertEqual(ref['datasetReference']['byPath']['path'],'../HR.SemanticModel')
        model=json.loads((folder/'HR.SemanticModel/model.bim').read_text())
        self.assertNotIn('RemoteArtifacts',str(model))

if __name__=='__main__':unittest.main()
