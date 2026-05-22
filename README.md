🧑‍💼 HR Workforce Analytics Dashboard
End-to-end HR analytics pipeline — SQL data cleaning & querying → Power BI visualization across 22,000+ employee records.

📌 Project Overview
This project delivers a comprehensive workforce analytics solution built on a dataset of 22,000+ employee records. It covers the full data pipeline: raw CSV ingestion, SQL-based cleaning and transformation, complex analytical queries, and a Power BI dashboard surfacing 7 key HR metrics.

Timeline: October 2025
Type: Personal Project
Tools: MySQL · Power BI · CSV

📁 Repository Structure
hr-workforce-analytics/
│
├── data/
│   └── Human_Resources.csv          # Raw HR dataset (22K+ records)
│
├── sql/
│   ├── HR_Data_Cleaning.sql         # Data cleaning & transformation pipeline
│   └── HR_Final_Queries.sql         # 11 analytical queries
│
├── dashboard/
│   └── HRdashboardfinal.pbix        # Power BI dashboard file
│
└── README.md
🛠️ Tech Stack
Layer	Tool
Database	MySQL (new_schema)
Data Cleaning	SQL (DDL + DML)
Analytics	SQL (Aggregations, CTEs, Subqueries)
Visualization	Microsoft Power BI
Source Data	CSV (22,000+ rows)
🧹 Data Cleaning Pipeline
The cleaning script (HR_Data_Cleaning.sql) handles the following transformations:

Column Rename — Fixed encoding issue on primary key column (ï»¿id → emp_id)
Date Standardization — Normalized 3 date columns (birthdate, hire_date, termdate) from mixed MM/DD/YYYY and MM-DD-YYYY formats to YYYY-MM-DD
Data Type Casting — Converted all 3 date columns from VARCHAR to DATE
Termdate Handling — Parsed UTC timestamp format and handled NULL/empty values gracefully using ALLOW_INVALID_DATES mode
Age Calculation — Added and populated a derived age column; applied ABS() to correct any negative values
📊 Analytical Queries
Eleven business questions answered via HR_Final_Queries.sql:

#	Question
1	Gender breakdown of employees
2	Race/ethnicity distribution
3	Age distribution across 5 groups (18–24, 25–34, 35–44, 45–54, 55–64, 65+) by gender
4	Headquarters vs. remote headcount
5	Average length of employment for terminated employees
6	Gender distribution across departments and job titles
7	Job title distribution across the company
8	Department-wise termination/turnover rates
9	Employee distribution by state
10	Year-over-year headcount change (hires vs. terminations, 2000–2020)
11	Average tenure per department
📈 Power BI Dashboard
The dashboard (HRdashboardfinal.pbix) visualizes 7 key HR metrics:

Gender Distribution — Company-wide breakdown by gender
Race/Ethnicity Breakdown — Diversity composition across the workforce
Age Group Distribution — Headcount across 5 age bands, segmented by gender
Work Location Split — 75% Headquarters · 25% Remote
Department Turnover Analysis — Termination rates of 0.92–0.94 across 12 departments
State-wise Employee Distribution — Geographic spread across US states
20-Year Hiring Trend (2000–2020) — Net headcount change year-over-year
🔍 Key Findings
75% of employees are headquarter-based; 25% work remotely
Termination rates are notably high (0.92–0.94) in certain departments, signalling potential retention risks
The workforce age skews toward the 25–44 band, with measurable representation across all age groups
Hiring trends from 2000 to 2020 show consistent net positive growth in most years
Average employment length for terminated employees highlights tenure patterns across the organization
🚀 How to Run
SQL (MySQL)
Import Human_Resources.csv into a MySQL database under new_schema
Run HR_Data_Cleaning.sql to clean and prepare the data
Run HR_Final_Queries.sql to generate analytical results
USE new_schema;
SOURCE sql/HR_Data_Cleaning.sql;
SOURCE sql/HR_Final_Queries.sql;
Power BI
Open HRdashboardfinal.pbix in Power BI Desktop
Update the data source connection to point to your MySQL instance
Refresh the dataset
📬 Contact
Feel free to connect or raise an issue for any questions about the project.

Built with SQL & Power BI ·
