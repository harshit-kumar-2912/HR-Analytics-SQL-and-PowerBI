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
