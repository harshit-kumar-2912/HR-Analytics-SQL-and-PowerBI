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
