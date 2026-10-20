# Validation and setup

## Executed evidence

Tested on an isolated **MySQL 8.0.44** instance with normal strict settings:

`ONLY_FULL_GROUP_BY, STRICT_TRANS_TABLES, NO_ZERO_IN_DATE, NO_ZERO_DATE, ERROR_FOR_DIVISION_BY_ZERO, NO_ENGINE_SUBSTITUTION`.

- Loaded all 22,214 records.
- Rebuilt cleaning views twice with identical complete results.
- Reconciled every employee's dates, age, age group, status, eligibility and quality flags against Python.
- Reconciled all 21 annual workforce rows and compared snapshot KPIs/completed tenure.
- Executed every analytical SQL statement.
- Passed regression and report-reference tests.

See [validation.json](validation.json). Static reference tests do not prove DAX execution or Desktop rendering.

## MySQL setup

Use a trusted local development MySQL 8.0 instance with `local_infile` enabled for CSV loading. An administrator can configure `local_infile=ON` or run `SET GLOBAL local_infile=1;` on that dedicated development instance. Do not alter a shared production server for this portfolio project.

Run `python scripts/run_mysql.py --user root`. The password is prompted without saving. The loader replaces only this project's staging rows in `hr_analytics`, then rebuilds views. It does not disable strict validation or require zero dates. Use `--client`, `--host` and `--port` as needed. `--no-password` is only for a disposable local/CI test service.

GitHub Actions repeats the reconciliation in its own MySQL service; check the actual workflow result rather than assuming a future CI run passed.

## Power BI Desktop checklist — pending application-level validation

The replacement uses documented [PBIP report](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report) and [TMSL semantic-model](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-dataset) formats. It has no old remote dataset reference. Static tests check projected fields/measures against the model.

Power BI Desktop is unavailable in the repair environment. These checks remain pending:

- [ ] Set your export path with `python scripts/build_powerbi.py --data-folder "C:/actual/path/data/processed"`.
- [ ] Open `powerbi/HR.pbip` without report/model errors.
- [ ] Refresh both imported tables without Power Query errors.
- [ ] Confirm active 20,259; eligible 22,148; completed exits 1,889.
- [ ] Confirm cumulative exit share 8.53%; mean completed tenure 6.61 years.
- [ ] Confirm 2020 closing headcount is 20,259.
- [ ] Confirm the department exit-share grand total recalculates to 8.53% rather than summing percentages.
- [ ] Test the department slicer, demographic cross-filtering and both pages; clear filters before checking totals.
- [ ] Save a validated PBIX and add actual Desktop screenshots.

The PNG/PDF previews are generated with Matplotlib from validated exports and are explicitly not Desktop screenshots.
