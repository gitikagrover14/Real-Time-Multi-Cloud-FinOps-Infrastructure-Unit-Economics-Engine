# Real-Time Multi-Cloud FinOps & Infrastructure Unit Economics Engine

## 1. Project Overview

The **Real-Time Multi-Cloud FinOps & Infrastructure Unit Economics Engine** is designed to analyze and monitor cloud infrastructure spending across multiple cloud environments.

The project focuses on organizing cloud billing data, identifying spending patterns, tracking resource utilization, and enabling better cost allocation and financial management.

It aims to provide structured insights into cloud expenditure across services, tenants, and geographical regions.

## 2. Project Objectives

- Analyze multi-cloud billing and infrastructure cost data.
- Integrate and organize cloud spending information.
- Design an enterprise-level dimensional database.
- Track cloud expenditure across services, tenants, and regions.
- Enable efficient data analysis through SQL queries.
- Support cloud cost optimization and financial decision-making.

## 3. Technology Stack

| Technology | Purpose |
|---|---|
| Python | Data inspection and processing |
| Pandas | Data analysis and manipulation |
| MySQL | Relational database management |
| SQL | Database design and querying |
| Jupyter Notebook | Dataset exploration |
| GitHub | Version control and collaboration |

## 4. Dataset Information

**Dataset Name:** FOCUS Exercise – 2026 Q3

**Dataset File:** `focus_exercise_2026-q3.csv`

**Dataset Format:** CSV

**Dataset Source:** FinOps Desk – FOCUS Analysis Exercise

The dataset is used to understand multi-cloud billing information and support the development of the project's database architecture.

Dataset exploration and profiling include:

- Understanding dataset structure and dimensions.
- Identifying column names and data types.
- Analyzing missing values.
- Checking duplicate records.
- Identifying relevant measures and attributes.

## 5. Database Architecture

The project follows an **Enterprise Dimensional Star Schema** approach.

The database consists of one central fact table and three dimension tables.

### Fact Table

**Fact_Spend**

Stores cloud spending and usage-related numerical information along with foreign keys connecting the dimension tables.

### Dimension Tables

**Dim_Service**
- Stores cloud service information.
- Maintains service-related attributes.

**Dim_Tenant**
- Stores tenant and cloud account information.
- Maintains account-related attributes.

**Dim_Region**
- Stores geographical and regional information.
- Maintains region-related attributes.

### Database Relationships

The Fact_Spend table will be connected to:

- Dim_Service
- Dim_Tenant
- Dim_Region

Primary keys and foreign keys will establish relationships and maintain referential integrity.

## 6. Team Responsibilities

### Gitika – SQL Database Design & Implementation

- Dataset structure and requirement analysis.
- Enterprise dimensional star schema design.
- Fact and dimension table creation.
- Primary key and foreign key definition.
- SQL data integration and validation.
- Database testing using JOIN queries.

### Taeyun – Dataset Selection, Ingestion & Data Cleaning

- Dataset selection and exploration.
- Dataset ingestion and preparation.
- Missing value and duplicate handling.
- Data normalization and standardization.
- Identification and handling of missing cost-allocation tags.

## 7. Project Folder Structure

```text
Real-Time-Multi-Cloud-FinOps-Engine/
│
├── focus-exercise/
│   ├── focus_exercise_2026-q3.csv
│   ├── exercise.sql
│   └── README.md
│
├── notebooks/
│   └── day1_dataset_inspection.ipynb
│
├── docs/
│   ├── database_requirements.md
│   └── dataset_column_summary.csv
│
├── sql/
│
└── README.md
```

## 8. Project Progress

### Week 1 – Database Design & Data Preparation

- Dataset inspection and requirement analysis.
- Dataset selection and ingestion.
- Data cleaning and normalization.
- Dimensional star schema design.
- Fact and dimension table creation.
- Database relationships and validation.

Further development will include additional project phases and analytical capabilities.

## 9. Expected Outcomes

- A structured multi-cloud billing database.
- An enterprise dimensional star schema.
- Reliable and organized cloud spending information.
- SQL-based cost analysis capabilities.
- A foundation for real-time cloud FinOps monitoring and infrastructure unit economics.

---

**Project:** Real-Time Multi-Cloud FinOps & Infrastructure Unit Economics Engine

**Internship Organization:** Infyntrek Systems

**Domain:** Data Analytics | Cloud FinOps | SQL Database Design