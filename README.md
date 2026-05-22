# 🧑‍💼 HR Workforce Analytics Dashboard

An end-to-end HR analytics project built using **MySQL** and **Power BI**, focused on transforming raw workforce data into actionable business insights through data cleaning, SQL analysis, and interactive visualizations.

The project analyzes **22,000+ employee records** to uncover trends in workforce demographics, employee turnover, hiring patterns, departmental retention, and remote work distribution.

---

# 📌 Project Overview

This project demonstrates a complete analytics workflow:

* Raw HR dataset ingestion from CSV
* SQL-based data cleaning and transformation
* Advanced analytical querying in MySQL
* Interactive dashboard development in Power BI
* Business insight generation from workforce metrics

### 🔧 Tools & Technologies

* **MySQL**
* **SQL**
* **Power BI**
* **CSV Dataset**

### 📅 Timeline

October 2025

### 📂 Project Type

Personal Data Analytics Project

---

# 📁 Repository Structure

```text id="wqj4b8"
HR-Workforce-Analytics/
│
├── data/
│   └── Human_Resources.csv
│
├── sql/
│   ├── HR_Data_Cleaning.sql
│   └── HR_Final_Queries.sql
│
├── dashboard/
│   └── HRdashboardfinal.pbix
│
└── README.md
```

---

# 🛠️ Tech Stack

| Layer         | Technology |
| ------------- | ---------- |
| Database      | MySQL      |
| Data Cleaning | SQL        |
| Data Analysis | SQL        |
| Visualization | Power BI   |
| Data Source   | CSV        |

---

# 🧹 Data Cleaning & Transformation

The dataset underwent a complete preprocessing pipeline using SQL to ensure consistency, accuracy, and analytical readiness.

### Key Cleaning Operations

* Renamed malformed primary key column (`ï»¿id` → `emp_id`)
* Standardized inconsistent date formats
* Converted date columns from `VARCHAR` to `DATE`
* Parsed UTC timestamp values in `termdate`
* Handled missing and invalid date values
* Added derived employee age column
* Corrected negative age values using `ABS()`

### Cleaned Columns

* `birthdate`
* `hire_date`
* `termdate`

---

# 📊 SQL Analysis

The project answers 11 major HR business questions using SQL aggregations, grouping, conditional logic, and analytical queries.

### Business Questions Solved

1. Gender distribution of employees
2. Race and ethnicity breakdown
3. Employee age distribution by gender
4. Headquarters vs remote employee ratio
5. Average employment length for terminated employees
6. Gender distribution across departments and job roles
7. Company-wide job title distribution
8. Department-wise turnover analysis
9. Employee distribution by state
10. Year-over-year workforce growth trends
11. Average employee tenure by department

---

# 📈 Power BI Dashboard

The Power BI dashboard visualizes workforce trends and HR KPIs through interactive charts and reports.

### Dashboard Highlights

* Gender diversity analysis
* Race and ethnicity composition
* Age group segmentation
* Remote vs headquarters workforce split
* Department turnover rates
* Geographic employee distribution
* 20-year hiring trend analysis

---

# 🔍 Key Insights

* Approximately **75%** of employees work from headquarters while **25%** work remotely
* Certain departments show significantly higher termination rates, indicating potential retention concerns
* The workforce is primarily concentrated in the **25–44 age group**
* Hiring trends from **2000–2020** indicate sustained workforce growth
* Employee tenure analysis reveals varying retention patterns across departments

---

# 🚀 How to Run the Project

## 1️⃣ MySQL Setup

Import the dataset into a MySQL database.

Run the SQL scripts in the following order:

```sql id="a95x0m"
USE new_schema;

SOURCE sql/HR_Data_Cleaning.sql;
SOURCE sql/HR_Final_Queries.sql;
```

---

## 2️⃣ Power BI Setup

1. Open `HRdashboardfinal.pbix`
2. Connect Power BI to your MySQL database
3. Refresh the dataset
4. Explore the dashboard visuals

---

# 📌 Project Features

✅ End-to-end analytics workflow
✅ SQL data cleaning pipeline
✅ Workforce trend analysis
✅ HR KPI dashboarding
✅ Business insight generation
✅ Real-world HR dataset analysis

---

# 📬 Contact

If you have questions, suggestions, or feedback, feel free to connect or open an issue in the repository.

---

# ⭐ Acknowledgements

Built using **SQL**, **MySQL**, and **Power BI** for workforce analytics and business intelligence learning.
