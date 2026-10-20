# Data dictionary and provenance

The raw input is the CSV originally supplied in this project. External publisher, collection method, synthetic-data status and license were not supplied and remain **unverified**. No real employer is claimed and this project grants no new license over the dataset. Verify the original source and usage rights before further redistribution or source claims.

The raw file contains names and demographic attributes. Names are omitted from the corrected analytical export and Power BI model. This unverified extract should not be used for employment decisions.

`metrics.json` records the raw input's SHA-256 checksum for reproducibility, not proof of authenticity or permission.

| Export column | Type and meaning |
| --- | --- |
| emp_id | Text; required unique original employee ID |
| birthdate, hire_date | ISO dates parsed using documented century rules |
| termdate | Nullable ISO exit date; CSV blank corresponds to SQL NULL |
| gender, race | Supplied demographic categories, trimmed without imputation |
| department, jobtitle | Recorded department and role |
| location | Headquarters or Remote |
| location_city, location_state | Recorded geographic attributes |
| age, age_group | Full years and bucket at reporting date; Unknown for unsupported ages |
| status | Active, Terminated, Not yet hired, or Excluded |
| is_valid | 0/1; passes date-quality rules |
| is_eligible | 0/1; valid and hired by reporting date |
| quality_issue | Explicit exclusion reason, otherwise blank |
| hired_under_16 | 0/1; review flag, not automatic exclusion |
| as_of_date | Reference date used to compute metrics |

Other outputs: `*_distribution.csv` contains active category counts; `department_exit_share.csv` contains eligible hires, exits, active counts and cumulative exit share; `annual_workforce.csv` contains annual flows and headcount; `metrics.json` contains validated KPIs and quality counts.

Raw names remain only in the original input and SQL staging table for traceability. `hr_cleaned` is the SQL counterpart of the employee export; it uses native DATE and NULL types.
