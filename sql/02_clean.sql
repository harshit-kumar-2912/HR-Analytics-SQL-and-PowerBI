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
SELECT TRIM(emp_id) emp_id, CASE WHEN NULLIF(TRIM(birthdate),'') IS NULL THEN NULL WHEN TRIM(birthdate) REGEXP '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' THEN STR_TO_DATE(TRIM(birthdate),'%Y-%m-%d') ELSE STR_TO_DATE(CONCAT(SUBSTRING_INDEX(REPLACE(TRIM(birthdate),'-','/'),'/',2),'/',CASE WHEN CAST(SUBSTRING_INDEX(REPLACE(TRIM(birthdate),'-','/'),'/',-1) AS UNSIGNED)<100 THEN CAST(SUBSTRING_INDEX(REPLACE(TRIM(birthdate),'-','/'),'/',-1) AS UNSIGNED)+CASE WHEN CAST(SUBSTRING_INDEX(REPLACE(TRIM(birthdate),'-','/'),'/',-1) AS UNSIGNED)>20 THEN 1900 ELSE 2000 END ELSE CAST(SUBSTRING_INDEX(REPLACE(TRIM(birthdate),'-','/'),'/',-1) AS UNSIGNED) END),'%m/%d/%Y') END birthdate,
 CASE WHEN NULLIF(TRIM(hire_date),'') IS NULL THEN NULL WHEN TRIM(hire_date) REGEXP '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' THEN STR_TO_DATE(TRIM(hire_date),'%Y-%m-%d') ELSE STR_TO_DATE(CONCAT(SUBSTRING_INDEX(REPLACE(TRIM(hire_date),'-','/'),'/',2),'/',CASE WHEN CAST(SUBSTRING_INDEX(REPLACE(TRIM(hire_date),'-','/'),'/',-1) AS UNSIGNED)<100 THEN CAST(SUBSTRING_INDEX(REPLACE(TRIM(hire_date),'-','/'),'/',-1) AS UNSIGNED)+2000 ELSE CAST(SUBSTRING_INDEX(REPLACE(TRIM(hire_date),'-','/'),'/',-1) AS UNSIGNED) END),'%m/%d/%Y') END hire_date,
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
