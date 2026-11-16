# Week 1 — Day 3: Data Ingestion & Preparation

**Owner:** Taeyun  
**Project:** Real-Time Multi-Cloud FinOps & Infrastructure Unit Economics Engine  
**Status:** Completed and validated against uploaded source files

## Objective
Import the team's selected dataset into a reproducible raw staging environment so that subsequent data cleaning and Gitika's dimensional SQL design can proceed without loss or unintended modification of source records.

## Sources
- `focus_exercise_2026-q3.csv`: synthetic multi-cloud FOCUS 1.2-subset billing data, 4,433 rows and 26 fields.
- `northwind_orders_2026-q3.csv`: 92 daily order-count records for downstream unit economics.
- `exercise.sql` and original publisher README are references; the publisher's worked SQL is not the ingestion pipeline.
- Original source: The FinOps Desk, https://finopscourse.com/resources/focus-analysis-exercise (CC BY 4.0).

## Ingestion approach
1. Read both CSVs as UTF-8 with BOM handling and **preserve all values as text**.
2. Check the FOCUS 26-field header layout and daily orders schema (`date`, `orders`).
3. Rebuild three SQLite tables: `raw_focus_billing`, `raw_daily_orders`, `ingestion_metadata`.
4. Insert all raw rows; assign a surrogate `ingestion_id` solely for tracking imported records.
5. Record SHA-256 source fingerprints and compare database counts with CSV counts.
6. Generate `day3_ingestion_validation.json` with the observed results.

**Important:** This is raw ingestion, not data cleaning, FOCUS normalization, MySQL production implementation, or streaming. Data casting, tag parsing, and missing-value treatment will occur in later tasks. SQLite is a portable staging tool; Gitika can use the raw CSV / cleaned exports for her planned MySQL star schema.

## Verified output
| Validation | Result |
|---|---:|
| Billing rows in CSV and staging table | 4,433 |
| Billing fields preserved | 26 |
| Daily orders rows in CSV and staging table | 92 |
| AWS rows | 2,675 |
| Microsoft rows | 927 |
| Google Cloud rows | 831 |
| Row count consistency | PASS |
| Data type coercion or imputation | None |

The exact original column names are retained, including `BilledCost`, `EffectiveCost`, `ProviderName`, `ServiceName`, `SubAccountId`, `RegionId`, and `Tags`.

## Reproduce locally
Place the two CSVs in `focus-exercise/` and run from the repository root:

```bash
python scripts/week1_day3_ingestion.py \
  --billing focus-exercise/focus_exercise_2026-q3.csv \
  --orders focus-exercise/northwind_orders_2026-q3.csv \
  --out outputs
```

Or execute `notebooks/week1_day3_data_ingestion.ipynb` from the repository root. Standard Python 3 is sufficient for the script; the notebook requires Jupyter.

**Generated local outputs:** `outputs/finops_day3_raw_staging.sqlite` and `outputs/day3_ingestion_validation.json`. The database is provided as a separate reproducible artifact, not committed by default.

## Coordination with Gitika
- Star-schema design should use `Fact_Spend` plus `Dim_Service`, `Dim_Tenant`, and `Dim_Region`.
- Raw field names and amounts are preserved for deterministic mapping; do not convert missing account/region/tag fields to invented identifiers.
- Day 4 will review missing values, duplicates, and inconsistencies; Day 5 will standardize data types and cost fields; Day 6 will assess tag allocation; Day 7 will hand off the final cleaned file.
- This source is **not from Kaggle**. Confirm that the team's agreed FinOps Desk dataset is acceptable if Kaggle is mandatory.

## Repository placement
- `docs/taeyun/week1/day3_data_ingestion.md`
- `scripts/week1_day3_ingestion.py`
- `notebooks/week1_day3_data_ingestion.ipynb`

Avoid overwriting Gitika's root-level project documents.
