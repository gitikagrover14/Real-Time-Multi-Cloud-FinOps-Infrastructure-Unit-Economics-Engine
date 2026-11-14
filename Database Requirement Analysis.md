# Database Requirements – Real-Time Multi-Cloud FinOps Engine

## 1. Project Overview

The project aims to develop a Real-Time Multi-Cloud FinOps & Infrastructure Unit Economics Engine to analyze cloud infrastructure spending and understand cost distribution across different cloud providers, services, tenants, and geographical regions.

The database will follow an enterprise dimensional modeling approach using a Star Schema.

## 2. Dataset Overview

Dataset Name: FinOps Desk – Multi-Cloud FOCUS Dataset

Dataset Source: FinOps Desk

Dataset Type: Synthetic Multi-Cloud Billing Data

Cloud Providers: AWS, Azure, and GCP.

The dataset will be inspected to understand its structure, attributes, measures, and data types before designing the database schema.

## 3. Database Design Approach

The database will follow a dimensional Star Schema consisting of one central fact table and three dimension tables.

### Fact Table

**Fact_Spend**

Purpose:
To store cloud spending and usage-related numerical measures along with foreign keys connecting the dimension tables.

### Dimension Tables

**Dim_Service**

Purpose:
To store information about cloud services and service providers.

**Dim_Tenant**

Purpose:
To maintain information about cloud accounts and tenants.

**Dim_Region**

Purpose:
To store geographical and regional information associated with cloud infrastructure spending.

## 4. Measures and Attributes

Measures:
- Billed Cost
- Effective Cost
- Usage Quantity
- Other available numerical cost metrics.

Attributes:
- Cloud Provider
- Service Name
- Account/Tenant Information
- Region
- Resource Information
- Billing Period

Final columns will be selected after inspecting the actual dataset.

## 5. Keys and Relationships

The database will use:

- Primary Keys (PK) to uniquely identify records in dimension tables.
- Foreign Keys (FK) to establish relationships between Fact_Spend and dimension tables.

The fact table will reference:
- Dim_Service
- Dim_Tenant
- Dim_Region

## 6. Database Requirements

- Create Fact_Spend and three dimension tables.
- Define appropriate SQL data types.
- Establish primary and foreign key constraints.
- Maintain referential integrity.
- Support SQL JOIN operations.
- Enable structured cloud spending analysis.

## 7. Day 1 Deliverables

- Initial dataset inspection.
- Dataset column and data type analysis.
- Missing value and duplicate analysis.
- Identification of entities, measures, and attributes.
- Initial dimensional database requirements.