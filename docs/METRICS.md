# Metric definitions

The reporting date is **2020-12-31**, matching the last hiring year. Dates after it are not completed events. Eligible employees pass date-quality rules and were hired on/before this date.

Exclude missing birth/hire dates, hire before birth, exit before hire, or snapshot age outside 0–100. The supplied data has 66 exclusions, all hire-before-birth. Retain their records and flags. The additional under-16 hire-age flag is a plausibility warning, not a legal conclusion or automatic exclusion; 4,800 raw records have it, including the 66 excluded records.

| Metric | Definition |
| --- | --- |
| Active employees | Eligible; exit date missing or after reference date |
| Terminated employees | Eligible; nonblank exit date on/before reference date |
| Demographic counts | Active employees in each category |
| Age | Full years at reference date, accounting for birthday |
| Cumulative exit share | Completed exits / eligible hires to reference date; not annual turnover |
| Completed tenure | Mean days between hire and completed exit / 365.2425 |
| Active tenure | Mean days from hire to reference date / 365.2425; separate population |
| Annual hires/exits | Events occurring in that calendar year, no later than reference date |
| Opening headcount | Hired before January 1; no exit before January 1 |
| Closing headcount | Opening + hires − exits |
| Annual turnover | Annual exits / mean(opening, closing headcount); endpoint approximation |

An exit on the reporting date removes the employee from closing headcount. An exit on January 1 is included in opening headcount and subtracted as that year's event. A hire and exit in the same year contributes to both flows.

## Power BI model

`Employees` imports only eligible employee-grain rows, without names. Demographic filters apply consistently to this table. Measures recalculate ratios in the current filter context; percentage grand totals are not summed.

`Year` is a disconnected calendar-year axis. DAX trend measures explicitly filter hire/exit dates using the selected year. The annual CSV's precomputed values support reconciliation; the report trend derives from employee rows so department selections apply.

Departments reflect the extract's recorded assignment, not historical transfers. Descriptive differences do not prove causation or statistical significance. Annual turnover uses endpoint-average headcount rather than daily exposure.
