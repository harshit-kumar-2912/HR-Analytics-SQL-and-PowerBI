import datetime as dt
import importlib.util
import unittest
import tempfile
import csv
from pathlib import Path

spec=importlib.util.spec_from_file_location('pipeline',Path(__file__).resolve().parents[1]/'scripts'/'pipeline.py')
p=importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)

class DateTests(unittest.TestCase):
    def test_century_is_explicit(self):
        self.assertEqual(p.parse_date('05-09-68',True),dt.date(1968,5,9))
        self.assertEqual(p.parse_date('05-09-02',True),dt.date(2002,5,9))
        self.assertEqual(p.parse_date('07-06-09'),dt.date(2009,7,6))
    def test_iso_rerun_and_null(self):
        self.assertEqual(p.parse_date('2020-12-31'),p.AS_OF)
        self.assertIsNone(p.parse_date(''))
        self.assertEqual(p.parse_date('2029-10-29 06:09:38 UTC'),dt.date(2029,10,29))
    def test_age_uses_birthday(self):
        self.assertEqual(p.age_on(dt.date(2000,12,31),dt.date(2020,12,30)),19)
        self.assertEqual(p.age_on(dt.date(2000,12,31),dt.date(2020,12,31)),20)
    def test_invalid_dates_fail(self):
        with self.assertRaises(ValueError): p.parse_date('02-30-20')

class FullDatasetTests(unittest.TestCase):
    def test_snapshot_and_repeatability(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)
            metrics=p.build(output=out)
            self.assertEqual(metrics['raw_records'],22214)
            self.assertEqual(metrics['invalid_records'],66)
            self.assertEqual(metrics['active_employees'],20259)
            self.assertEqual(metrics['terminated_employees'],1889)
            self.assertEqual(metrics['eligible_records'],metrics['active_employees']+metrics['terminated_employees'])
            before={f.name:f.read_bytes() for f in out.iterdir()}
            p.build(output=out)
            self.assertEqual(before,{f.name:f.read_bytes() for f in out.iterdir()})
            with (out/'annual_workforce.csv').open(newline='',encoding='utf-8') as f:
                years=list(csv.DictReader(f))
            self.assertEqual(len(years),21)
            previous=0
            for y in years:
                self.assertEqual(int(y['opening_headcount']),previous)
                self.assertEqual(int(y['closing_headcount']),int(y['opening_headcount'])+int(y['hires'])-int(y['terminations']))
                previous=int(y['closing_headcount'])
            self.assertEqual(previous,metrics['active_employees'])
            with (out/'employees.csv').open(newline='',encoding='utf-8') as f:
                employees=list(csv.DictReader(f))
            for e in employees:
                if e['status']=='Active':
                    self.assertEqual(e['is_valid'],'1')
                    self.assertTrue(not e['termdate'] or e['termdate']>metrics['as_of_date'])
                if e['is_valid']=='0':self.assertEqual(e['status'],'Excluded')

if __name__=='__main__': unittest.main()
