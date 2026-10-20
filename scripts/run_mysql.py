"""Load, clean, analyze, and reconcile this project's dedicated MySQL schema."""
import argparse
import csv
import getpass
import json
import os
import subprocess
from pathlib import Path
from pipeline import ROOT, build

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--client',default='mysql')
    p.add_argument('--host',default='127.0.0.1')
    p.add_argument('--port',type=int,default=3306)
    p.add_argument('--user',default='root')
    p.add_argument('--no-password',action='store_true',help='Only for a disposable local test server')
    args=p.parse_args()
    env=os.environ.copy()
    if not args.no_password and not env.get('MYSQL_PWD'):
        env['MYSQL_PWD']=getpass.getpass('MySQL password (not saved): ')
    if args.no_password: env.pop('MYSQL_PWD',None)
    command=[args.client,'--no-defaults',f'--host={args.host}',f'--port={args.port}',f'--user={args.user}',
        '--default-character-set=utf8mb4','--local-infile=1','--batch','--raw','--skip-column-names']
    def sql(text):
        r=subprocess.run(command,input=text,encoding='utf-8',capture_output=True,env=env)
        if r.returncode: raise RuntimeError(r.stderr)
        return r.stdout.strip()
    expected=build()
    sql((ROOT/'sql/01_schema.sql').read_text(encoding='utf-8'))
    file=(ROOT/'data/raw/Human Resources.csv').as_posix().replace("'","''")
    sql("USE hr_analytics; TRUNCATE TABLE hr_raw;\n" +
        f"LOAD DATA LOCAL INFILE '{file}' INTO TABLE hr_raw CHARACTER SET utf8mb4 " +
        "FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '\"' LINES TERMINATED BY '\\n' IGNORE 1 LINES " +
        "(emp_id,first_name,last_name,birthdate,gender,race,department,jobtitle,location,hire_date,termdate,location_city,@state) " +
        "SET location_state=TRIM(TRAILING '\\r' FROM @state);")
    clean=(ROOT/'sql/02_clean.sql').read_text(encoding='utf-8')
    sql(clean)
    # Repeat cleaning: output must be identical and no schema/column operation may fail.
    before=sql('USE hr_analytics; SELECT * FROM hr_cleaned ORDER BY emp_id;')
    sql(clean)
    after=sql('USE hr_analytics; SELECT * FROM hr_cleaned ORDER BY emp_id;')
    if before!=after: raise AssertionError('Cleaning is not repeatable')
    checks={
        'raw_records':'SELECT COUNT(*) FROM hr_raw',
        'invalid_records':'SELECT COUNT(*) FROM hr_cleaned WHERE is_valid=0',
        'eligible_records':'SELECT COUNT(*) FROM hr_eligible',
        'active_employees':'SELECT COUNT(*) FROM hr_active',
        'terminated_employees':'SELECT COUNT(*) FROM hr_terminated',
        'future_termination_records':'SELECT COUNT(*) FROM hr_cleaned WHERE termdate>as_of_date',
        'hired_under_16_records':'SELECT SUM(hired_under_16) FROM hr_cleaned',
    }
    for metric,query in checks.items():
        actual=int(sql('USE hr_analytics; '+query+';'))
        if actual!=expected[metric]: raise AssertionError(f'{metric}: SQL {actual} != Python {expected[metric]}')
    with (ROOT/'data/processed/employees.csv').open(encoding='utf-8',newline='') as f:
        pyrows=list(csv.DictReader(f))
    # Every row's parsed dates, age, validity and snapshot status must agree.
    fields=['emp_id','birthdate','hire_date','termdate','gender','race','department','jobtitle','location','location_city','location_state','age','age_group','status','is_valid','is_eligible','hired_under_16']
    query="SELECT emp_id,birthdate,hire_date,COALESCE(CAST(termdate AS CHAR),''),gender,race,department,jobtitle,location,location_city,location_state,age,age_group,status,is_valid,is_eligible,hired_under_16 FROM hr_cleaned ORDER BY emp_id"
    actual=[line.split('\t') for line in sql('USE hr_analytics; '+query+';').splitlines()]
    reference=[[r[k] for k in fields] for r in sorted(pyrows,key=lambda r:r['emp_id'])]
    if actual!=reference: raise AssertionError('Employee-level SQL/Python mismatch')
    with (ROOT/'data/processed/annual_workforce.csv').open(encoding='utf-8',newline='') as f:
        annual=list(csv.DictReader(f))
    actual=sql('USE hr_analytics; SELECT year,opening_headcount,hires,terminations,net_change,closing_headcount,annual_turnover_rate FROM hr_annual ORDER BY year;').splitlines()
    for a,r in zip(actual,annual,strict=True):
        vals=a.split('\t')
        for i,k in enumerate(['year','opening_headcount','hires','terminations','net_change','closing_headcount']):
            if int(vals[i])!=int(r[k]): raise AssertionError(f'Annual mismatch {r["year"]} {k}')
        if abs(float(vals[6])-float(r['annual_turnover_rate']))>0.00001: raise AssertionError('Annual turnover mismatch')
    tenure=float(sql('USE hr_analytics; SELECT AVG(DATEDIFF(termdate,hire_date)/365.2425) FROM hr_terminated;'))
    if abs(tenure-expected['average_completed_tenure_years'])>0.00001: raise AssertionError('Tenure mismatch')
    ratios={
        'cumulative_exit_share':"SELECT CAST(SUM(status='Terminated') AS DECIMAL(20,10))/COUNT(*) FROM hr_eligible",
        'active_headquarters_share':"SELECT CAST(SUM(location='Headquarters') AS DECIMAL(20,10))/COUNT(*) FROM hr_active",
    }
    for metric,query in ratios.items():
        if abs(float(sql('USE hr_analytics; '+query+';'))-expected[metric])>0.00001:
            raise AssertionError(f'{metric} mismatch')
    analysis=sql((ROOT/'sql/03_analysis.sql').read_text(encoding='utf-8'))
    if not analysis: raise AssertionError('No analytical query output')
    sql((ROOT/'sql/04_validation.sql').read_text(encoding='utf-8'))
    report=dict(mysql_version=sql('SELECT VERSION();'),sql_mode=sql('SELECT @@sql_mode;'),
        employee_rows_reconciled=len(pyrows),annual_rows_reconciled=len(annual),
        repeated_cleaning_identical=True,analytical_queries_executed=True,metrics=expected,
        power_bi_desktop_render_and_refresh='not executed in this environment')
    output=ROOT/'docs/validation.json';output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()
