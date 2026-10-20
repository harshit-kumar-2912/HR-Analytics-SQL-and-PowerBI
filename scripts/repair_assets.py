"""Maintainer utility: prepare the repository structure and reproducible SQL."""
import json
import shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def write(path,text):
    p=ROOT/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text.strip()+'\n',encoding='utf-8')

def prepare():
    raw=ROOT/'data/raw/Human Resources.csv';raw.parent.mkdir(parents=True,exist_ok=True)
    old=ROOT/'Human Resources.csv'
    if old.exists(): shutil.move(str(old),raw)
    for name in ['HR Data Cleaning.sql','HR Final Quearies.sql']:
        old=ROOT/name
        if old.exists():
            dest=ROOT/'archive'/name;dest.parent.mkdir(exist_ok=True);shutil.move(str(old),dest)
    old=ROOT/'HRdashboardfinal.pbix'
    if old.exists():
        dest=ROOT/'archive/HRdashboardfinal.pbix';dest.parent.mkdir(exist_ok=True);shutil.move(str(old),dest)
    write('sql/01_schema.sql', '''
-- Dedicated project schema. Does not change global/session SQL validation modes.
CREATE DATABASE IF NOT EXISTS hr_analytics CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE hr_analytics;
CREATE TABLE IF NOT EXISTS hr_raw (
 emp_id VARCHAR(30) NOT NULL PRIMARY KEY,
 first_name VARCHAR(100), last_name VARCHAR(100), birthdate VARCHAR(40),
 gender VARCHAR(50), race VARCHAR(100), department VARCHAR(100), jobtitle VARCHAR(150),
 location VARCHAR(50), hire_date VARCHAR(40), termdate VARCHAR(80),
 location_city VARCHAR(100), location_state VARCHAR(100)
);
CREATE TABLE IF NOT EXISTS analysis_config (
 id TINYINT PRIMARY KEY, as_of_date DATE NOT NULL, CHECK (id=1)
);
INSERT INTO analysis_config VALUES (1,'2020-12-31')
ON DUPLICATE KEY UPDATE as_of_date='2020-12-31';
''')
    def date_expr(col,birth=False):
        # ISO is recognized first; two-digit centuries are specified, not engine-dependent.
        year=f"CAST(SUBSTRING_INDEX(REPLACE(TRIM({col}),'-','/'),'/',-1) AS UNSIGNED)"
        expanded=f"CASE WHEN {year}<100 THEN {year}+CASE WHEN {year}>20 THEN 1900 ELSE 2000 END ELSE {year} END" if birth else f"CASE WHEN {year}<100 THEN {year}+2000 ELSE {year} END"
        return f"CASE WHEN NULLIF(TRIM({col}),'') IS NULL THEN NULL WHEN TRIM({col}) REGEXP '^[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}$' THEN STR_TO_DATE(TRIM({col}),'%Y-%m-%d') ELSE STR_TO_DATE(CONCAT(SUBSTRING_INDEX(REPLACE(TRIM({col}),'-','/'),'/',2),'/',{expanded}),'%m/%d/%Y') END"
    write('sql/02_clean.sql',f'''
USE hr_analytics;
-- Parse once into typed staging rather than reparsing text on every visual/query.
-- Rebuild from immutable raw text; reruns never parse an already-cleaned date.
CREATE TABLE IF NOT EXISTS hr_dates (
 emp_id VARCHAR(30) PRIMARY KEY, birthdate DATE, hire_date DATE, termdate DATE,
 gender VARCHAR(50), race VARCHAR(100), department VARCHAR(100), jobtitle VARCHAR(150),
 location VARCHAR(50), location_city VARCHAR(100), location_state VARCHAR(100),
 INDEX idx_hr_hire (hire_date), INDEX idx_hr_exit (termdate), INDEX idx_hr_department (department)
);
START TRANSACTION;
DELETE FROM hr_dates;
INSERT INTO hr_dates
SELECT TRIM(emp_id) emp_id, {date_expr('birthdate',True)} birthdate,
 {date_expr('hire_date')} hire_date,
 CASE WHEN NULLIF(TRIM(termdate),'') IS NULL THEN NULL
 ELSE DATE(STR_TO_DATE(TRIM(termdate),'%Y-%m-%d %H:%i:%s UTC')) END termdate,
 TRIM(gender) gender, TRIM(race) race, TRIM(department) department,
 TRIM(jobtitle) jobtitle, TRIM(location) location,
 TRIM(location_city) location_city, TRIM(location_state) location_state
FROM hr_raw;
COMMIT;
CREATE OR REPLACE VIEW hr_parsed AS SELECT * FROM hr_dates;

CREATE OR REPLACE VIEW hr_quality AS
SELECT p.*, c.as_of_date, TIMESTAMPDIFF(YEAR,birthdate,c.as_of_date) age,
 CASE WHEN birthdate IS NULL OR hire_date IS NULL OR hire_date<birthdate
 OR termdate<hire_date OR TIMESTAMPDIFF(YEAR,birthdate,c.as_of_date) NOT BETWEEN 0 AND 100
 THEN 0 ELSE 1 END is_valid,
 (TIMESTAMPDIFF(YEAR,birthdate,hire_date)<16) hired_under_16
FROM hr_parsed p CROSS JOIN analysis_config c;

CREATE OR REPLACE VIEW hr_cleaned AS
SELECT q.*,
 CASE WHEN age IS NULL OR age<18 THEN 'Unknown'
 WHEN age<25 THEN '18-24' WHEN age<35 THEN '25-34' WHEN age<45 THEN '35-44'
 WHEN age<55 THEN '45-54' WHEN age<65 THEN '55-64' ELSE '65+' END age_group,
 CASE WHEN is_valid=0 THEN 'Excluded' WHEN hire_date>as_of_date THEN 'Not yet hired'
 WHEN termdate IS NOT NULL AND termdate<=as_of_date THEN 'Terminated' ELSE 'Active' END status,
 CASE WHEN is_valid=1 AND hire_date<=as_of_date THEN 1 ELSE 0 END is_eligible
FROM hr_quality q;
CREATE OR REPLACE VIEW hr_eligible AS SELECT * FROM hr_cleaned WHERE is_eligible=1;
CREATE OR REPLACE VIEW hr_active AS SELECT * FROM hr_eligible WHERE status='Active';
CREATE OR REPLACE VIEW hr_terminated AS SELECT * FROM hr_eligible WHERE status='Terminated';

CREATE OR REPLACE VIEW hr_annual AS
WITH RECURSIVE years AS (
 SELECT YEAR(MIN(hire_date)) year FROM hr_eligible
 UNION ALL SELECT year+1 FROM years WHERE year<(SELECT YEAR(as_of_date) FROM analysis_config WHERE id=1)
), counts AS (
 SELECT y.year,
 SUM(h.hire_date<MAKEDATE(y.year,1) AND (h.termdate IS NULL OR h.termdate>=MAKEDATE(y.year,1))) opening_headcount,
 SUM(YEAR(h.hire_date)=y.year AND h.hire_date<=h.as_of_date) hires,
 SUM(CASE WHEN h.termdate IS NOT NULL AND YEAR(h.termdate)=y.year AND h.termdate<=h.as_of_date THEN 1 ELSE 0 END) terminations
 FROM years y CROSS JOIN hr_cleaned h WHERE h.is_valid=1 GROUP BY y.year
), closing AS (
 SELECT *,hires-terminations net_change,opening_headcount+hires-terminations closing_headcount FROM counts
)
SELECT *,COALESCE(CAST(terminations AS DECIMAL(20,10))/NULLIF((opening_headcount+closing_headcount)/2,0),0) annual_turnover_rate FROM closing;
''')
    write('sql/03_analysis.sql', '''
USE hr_analytics;
-- Demographics describe active employees at the fixed reporting date.
-- 1. Gender
SELECT gender,COUNT(*) employee_count FROM hr_active GROUP BY gender ORDER BY employee_count DESC;
-- 2. Race/ethnicity
SELECT race,COUNT(*) employee_count FROM hr_active GROUP BY race ORDER BY employee_count DESC;
-- 3. Age and gender; unknown is never mislabeled as 65+.
SELECT age_group,gender,COUNT(*) employee_count FROM hr_active GROUP BY age_group,gender ORDER BY age_group,gender;
-- 4. Headquarters vs remote
SELECT location,COUNT(*) employee_count FROM hr_active GROUP BY location;
-- 5. Completed tenure of employees whose exit has occurred by reporting date.
SELECT ROUND(AVG(DATEDIFF(termdate,hire_date)/365.2425),4) average_completed_tenure_years FROM hr_terminated;
-- 6. Department, job title and gender
SELECT department,jobtitle,gender,COUNT(*) employee_count FROM hr_active GROUP BY department,jobtitle,gender;
-- 7. Job title distribution
SELECT jobtitle,COUNT(*) employee_count FROM hr_active GROUP BY jobtitle ORDER BY employee_count DESC;
-- 8. Cumulative exit share among eligible hires; NOT an annual turnover rate.
SELECT department,COUNT(*) total_hired,SUM(status='Terminated') terminated_count,
 SUM(status='Terminated')/COUNT(*) cumulative_exit_share
FROM hr_eligible GROUP BY department ORDER BY cumulative_exit_share DESC;
-- 9. City and state
SELECT location_state,location_city,COUNT(*) employee_count FROM hr_active GROUP BY location_state,location_city;
-- 10. Calendar-year workforce reconciliation and approximate annual turnover rate.
SELECT * FROM hr_annual ORDER BY year;
-- 11. Active tenure and completed tenure are separate populations.
SELECT department,ROUND(AVG(DATEDIFF(as_of_date,hire_date)/365.2425),4) active_tenure_years
FROM hr_active GROUP BY department;
SELECT department,ROUND(AVG(DATEDIFF(termdate,hire_date)/365.2425),4) completed_tenure_years
FROM hr_terminated GROUP BY department;
''')
    write('sql/04_validation.sql', '''
USE hr_analytics;
SELECT 'raw_rows' metric,COUNT(*) value FROM hr_raw
UNION ALL SELECT 'invalid_rows',COUNT(*) FROM hr_cleaned WHERE is_valid=0
UNION ALL SELECT 'active_employees',COUNT(*) FROM hr_active
UNION ALL SELECT 'terminated_employees',COUNT(*) FROM hr_terminated;
-- Both checks must be zero.
SELECT COUNT(*) invalid_active_rows FROM hr_active WHERE termdate<=as_of_date OR hire_date>as_of_date OR is_valid=0;
SELECT COUNT(*) reconciliation_errors FROM hr_annual
WHERE opening_headcount+hires-terminations<>closing_headcount;
''')
    write('archive/README.md', '''
# Superseded project files

These files preserve the original project for traceability. They are not the corrected workflow.
The old SQL contains known age, zero-date, and workforce-change errors. Do not run it.
The old PBIX contains cached results and legacy summary-table calculations. Do not use it for reported findings.
Use the root README, `sql/`, `data/processed/`, and `powerbi/` instead.
''')

if __name__=='__main__': prepare()
