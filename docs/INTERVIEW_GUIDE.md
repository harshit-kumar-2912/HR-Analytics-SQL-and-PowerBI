# Interview preparation — Harshit Kumar

Run the workflow yourself and complete the Power BI Desktop checklist before demonstrating the report.

## Project introduction

“This is a workforce analytics portfolio using a supplied HR extract. I made the analysis reproducible with a fixed reporting date, explicit date-quality checks, and consistent employee-status definitions. The SQL calculations are reconciled against an independent Python implementation. The Power BI source uses employee-level data and reusable DAX measures instead of disconnected summary percentages.”

## Questions and explanations

**What business questions does it answer?** Workforce demographics, location mix, department exit shares, completed tenure and historical headcount. It does not prove why employees left.

**Why December 31, 2020?** It matches the final hiring year and prevents results changing with `CURDATE()`. Future exit dates are retained but do not count as completed exits at this snapshot.

**What quality issues did you find?** Mixed formats and two-digit years, 66 hire dates before birthdates, and many implausibly young hire ages. Explicit century rules avoid engine-dependent interpretation. Impossible sequences are excluded, and other warnings remain visible rather than being silently rewritten.

**Why not use ABS(age)?** It hides a bad birthdate or parsing error. Age should be calculated from validated dates using full elapsed years.

**What are the main results?** 22,214 raw records; 66 exclusions; 22,148 eligible hires; 20,259 active employees; 1,889 completed exits; 8.53% cumulative exit share and 6.61 years mean completed tenure. These are exploratory dataset results, not verified employer statistics.

**Is 8.53% annual turnover?** No. It is exits to date / eligible hires to date. Annual turnover uses that year's exits / average opening and closing headcount. The denominators answer different questions.

**How do you calculate annual headcount?** Count hires in hire year and exits in exit year; opening + hires − exits must equal closing. Grouping eventual exits by hire year would describe a cohort, not annual workforce movement.

**How did you validate it?** Reconcile every employee's parsed dates, age, status and eligibility independently in MySQL and Python. Reconcile all 21 annual rows, compare KPIs/tenure, execute every query, and verify the cleaning can run twice unchanged. Tests also cover birthdays, century rules and report references.

**Why use a percentage measure?** Total exits / total eligible hires recalculates correctly under filters and at totals. Adding department percentages produces a misleading total.

**How does the model work?** One employee-grain fact table supports demographic filtering. A disconnected Year axis lets DAX explicitly evaluate both event dates. The import path is parameterized and the model uses local CSVs rather than another account's cloud dataset.

**What are its limitations?** Unverified source/license, implausible date patterns, no historical department-transfer data, endpoint-average rather than daily turnover exposure, and descriptive rather than causal findings. Power BI rendering and refresh must be checked on the demonstration machine.

**What would you do next with business access?** Verify permissions and provenance, resolve anomalies with HR, obtain effective-dated department history, agree definitions with stakeholders, and add governed scheduled refresh. These are future improvements, not completed features.

## Five-minute demonstration

1. Explain the reporting date and dataset limitations.
2. Run `python scripts/pipeline.py`; show `data/processed/metrics.json`.
3. Explain active/terminated logic and annual reconciliation in `sql/02_clean.sql`.
4. Run tests; show `docs/validation.json`.
5. Demonstrate Power BI only after its local checks pass; explain one comparison without claiming causation.

## Resume wording

After Desktop verification: “Developed an HR workforce analytics portfolio using MySQL and Power BI; analyzed 22,214 records, implemented date-quality checks and reproducible snapshot metrics, and reconciled SQL outputs against an independent Python pipeline.”

Do not invent a business impact percentage, production deployment, data ownership, or tests you have not performed.
