"""Rebuild the HR portfolio outputs using only the Python standard library."""
from __future__ import annotations
import argparse
import collections
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AS_OF = dt.date(2020, 12, 31)

def parse_date(value: str, birth: bool = False) -> dt.date | None:
    value = value.strip()
    if not value:
        return None
    if ' UTC' in value:
        return dt.datetime.strptime(value, '%Y-%m-%d %H:%M:%S UTC').date()
    if len(value) == 10 and value[4] == '-':
        return dt.date.fromisoformat(value)
    month, day, year = map(int, value.replace('-', '/').split('/'))
    if year < 100:
        year += 1900 if birth and year > 20 else 2000
    return dt.date(year, month, day)

def age_on(birth: dt.date, as_of: dt.date) -> int:
    return as_of.year - birth.year - ((as_of.month, as_of.day) < (birth.month, birth.day))

def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields or list(rows[0]), lineterminator='\n')
        w.writeheader()
        w.writerows(rows)

def build(as_of: dt.date = AS_OF, output: Path | None = None) -> dict:
    output = output or ROOT / 'data' / 'processed'
    source = ROOT / 'data' / 'raw' / 'Human Resources.csv'
    with source.open(encoding='utf-8-sig', newline='') as f:
        raw = list(csv.DictReader(f))
    cleaned = []
    seen = set()
    for r in raw:
        key = r['id'].strip()
        if not key or key in seen:
            raise ValueError(f'Missing or duplicate employee ID: {key}')
        seen.add(key)
        birth, hire, term = parse_date(r['birthdate'], True), parse_date(r['hire_date']), parse_date(r['termdate'])
        if birth is None or hire is None:
            raise ValueError(f'Required date missing for {key}')
        issues = []
        if hire < birth:
            issues.append('hire_before_birth')
        if term and term < hire:
            issues.append('termination_before_hire')
        age = age_on(birth, as_of)
        if age < 0 or age > 100:
            issues.append('implausible_age')
        valid = not issues
        eligible = valid and hire <= as_of
        status = 'Excluded' if not valid else 'Not yet hired' if hire > as_of else 'Terminated' if term and term <= as_of else 'Active'
        group = 'Unknown' if age < 18 else '18-24' if age < 25 else '25-34' if age < 35 else '35-44' if age < 45 else '45-54' if age < 55 else '55-64' if age < 65 else '65+'
        cleaned.append(dict(emp_id=key, birthdate=birth.isoformat(), hire_date=hire.isoformat(), termdate=term.isoformat() if term else '',
            gender=r['gender'].strip(), race=r['race'].strip(), department=r['department'].strip(), jobtitle=r['jobtitle'].strip(),
            location=r['location'].strip(), location_city=r['location_city'].strip(), location_state=r['location_state'].strip(),
            age=age, age_group=group, status=status, is_valid=int(valid), is_eligible=int(eligible),
            quality_issue=';'.join(issues), hired_under_16=int(age_on(birth, hire)<16), as_of_date=as_of.isoformat()))
    eligible = [r for r in cleaned if r['is_eligible']]
    active = [r for r in eligible if r['status']=='Active']
    terminated = [r for r in eligible if r['status']=='Terminated']
    def breakdown(col):
        return [dict(category=k, employee_count=v) for k,v in sorted(collections.Counter(r[col] for r in active).items())]
    write_csv(output/'employees.csv', cleaned)
    for col in ['gender','race','age_group','location','location_city','location_state','jobtitle']:
        write_csv(output/f'{col}_distribution.csv', breakdown(col))
    departments=[]
    for dep in sorted({r['department'] for r in eligible}):
        population=[r for r in eligible if r['department']==dep]
        exited=sum(r['status']=='Terminated' for r in population)
        departments.append(dict(department=dep,total_hired=len(population),terminated_count=exited,
            active_count=len(population)-exited,cumulative_exit_share=exited/len(population)))
    write_csv(output/'department_exit_share.csv',departments)
    annual=[]
    valid=[r for r in cleaned if r['is_valid']]
    for year in range(min(dt.date.fromisoformat(r['hire_date']).year for r in eligible),as_of.year+1):
        start=dt.date(year,1,1); end=min(dt.date(year,12,31),as_of)
        opening=sum(dt.date.fromisoformat(r['hire_date'])<start and (not r['termdate'] or dt.date.fromisoformat(r['termdate'])>=start) for r in valid)
        hires=sum(start<=dt.date.fromisoformat(r['hire_date'])<=end for r in valid)
        exits=sum(bool(r['termdate']) and start<=dt.date.fromisoformat(r['termdate'])<=end for r in valid)
        closing=opening+hires-exits
        avg=(opening+closing)/2
        annual.append(dict(year=year,opening_headcount=opening,hires=hires,terminations=exits,net_change=hires-exits,
            closing_headcount=closing,annual_turnover_rate=exits/avg if avg else 0))
    write_csv(output/'annual_workforce.csv',annual)
    years=[(dt.date.fromisoformat(r['termdate'])-dt.date.fromisoformat(r['hire_date'])).days/365.2425 for r in terminated]
    metrics=dict(as_of_date=as_of.isoformat(),raw_records=len(raw),invalid_records=len(cleaned)-sum(r['is_valid'] for r in cleaned),
        eligible_records=len(eligible),active_employees=len(active),terminated_employees=len(terminated),
        future_termination_records=sum(bool(r['termdate']) and dt.date.fromisoformat(r['termdate'])>as_of for r in cleaned),
        hired_under_16_records=sum(r['hired_under_16'] for r in cleaned),
        cumulative_exit_share=len(terminated)/len(eligible),
        average_completed_tenure_years=sum(years)/len(years) if years else None,
        active_headquarters_share=sum(r['location']=='Headquarters' for r in active)/len(active),
        source_sha256=hashlib.sha256(source.read_bytes()).hexdigest())
    (output/'metrics.json').write_text(json.dumps(metrics,indent=2)+'\n',encoding='utf-8')
    return metrics

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--as-of',type=dt.date.fromisoformat,default=AS_OF)
    args=parser.parse_args()
    print(json.dumps(build(args.as_of),indent=2))
