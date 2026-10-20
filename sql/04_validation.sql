USE hr_analytics;
SELECT 'raw_rows' metric,COUNT(*) value FROM hr_raw
UNION ALL SELECT 'invalid_rows',COUNT(*) FROM hr_cleaned WHERE is_valid=0
UNION ALL SELECT 'active_employees',COUNT(*) FROM hr_active
UNION ALL SELECT 'terminated_employees',COUNT(*) FROM hr_terminated;
-- Both checks must be zero.
SELECT COUNT(*) invalid_active_rows FROM hr_active WHERE termdate<=as_of_date OR hire_date>as_of_date OR is_valid=0;
SELECT COUNT(*) reconciliation_errors FROM hr_annual
WHERE opening_headcount+hires-terminations<>closing_headcount;
