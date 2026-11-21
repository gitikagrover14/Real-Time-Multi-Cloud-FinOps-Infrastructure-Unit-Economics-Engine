# Week 2 — Day 1: Source Readiness & dbt Handoff (Taeyun)

**Project:** Real-Time Multi-Cloud FinOps & Infrastructure Unit Economics Engine  
**Responsibility:** Data ingestion, data quality, and source preparation in support of Gitika's dbt warehouse setup  
**Date:** 21 November 2026  
**Status:** Local source readiness verified; live MySQL/dbt integration requires teammate verification

## 1. Scope and coordination

Gitika's Week 2 Day 1 update on the repository confirms **dbt Core 1.7.9**, **MySQL adapter 1.7.0**, initialized project `finops_dbt`, and a successful `dbt debug` connection to `multi_cloud_finops`. The existing tables listed are `stg_focus_billing`, `Dim_Service`, `Dim_Tenant`, `Dim_Region`, and `Fact_Spend`. **The current Week 2 project does not have a separately published Taeyun task distribution**; this report defines the complementary Day 1 data-owner work without claiming Gitika's environment setup or SQL design.

The source is the FinOps Desk's **synthetic** Q3 2026 multi-cloud FOCUS exercise, not a Kaggle dataset or real-time feed. Original and cleaned CSVs retain the 26 FOCUS-style fields. The tag-audited version adds `allocation_team`, `allocation_env`, and `tag_status` as **optional** analytical helpers.

## 2. Local source audit: verified

The supplied Week 1 files were re-opened and independently checked with a reproducible standard-library Python script. The audit confirmed:

| Check | Observed result |
|---|---:|
| Raw billing records | 4,433 |
| Cleaned billing records | 4,433 |
| Tag-audited billing records | 4,433 |
| Raw and cleaned fields | 26 each |
| Tag-audited fields | 29 |
| AWS / Microsoft / Google Cloud | 2,675 / 927 / 831 |
| Cleaned dataset exact duplicate rows | 0 |
| Missing subaccount / region | 9 / 58 |
| Missing cost-allocation tags | 10 |
| BilledCost in each version | USD 332,678.83 |
| EffectiveCost in each version | USD 213,887.47 |
| Local source-readiness audit | PASS |

All observed numerical values, ISO timestamps and non-empty tag objects parsed successfully. The script writes source SHA-256 identifiers, observed source metrics, and a 26-column staging field contract. Null-like empty cells remain empty for raw MySQL staging; **do not fabricate tenant or region keys**. Missing tags occur in non-usage categories, so do not silently assign costs to a team.

## 3. File selection and dbt source contract

- **Authoritative 26-column billing input:** `focus_cleaned_2026-q3.csv` from Week 1 Days 4–5. Use this file to populate Gitika's existing `stg_focus_billing` (26 `VARCHAR`/text columns); preserve original field names and order.
- **Supplementary analytical file:** `focus_tag_audited_2026-q3.csv` from Week 1 Day 6 (29 columns). Do **not** load this into the existing 26-column table unless the staging schema or loader is intentionally updated.
- **Original 26-column file:** `focus_exercise_2026-q3.csv`; retain for lineage and reconciliation, not as a second append import.
- **Daily unit-economics denominator:** `northwind_orders_2026-q3.csv` (92 dates); it must be sourced separately when unit economics are built, and should be aggregated to the correct date granularity before joining to spend.
- **dbt source location for Gitika:** database `multi_cloud_finops`, table `stg_focus_billing`; confirm schema and connection values locally. This is a **data contract**, not a claim that sources.yml has been created or a dbt transformation run has been executed.

Recommended dbt staging casts: `DECIMAL` for cost and usage fields, UTC timestamps for charge/billing periods, null handling for optional IDs, JSON extraction for `Tags`; **keep account/resource IDs as text**. Preserve `BilledCost` vs `EffectiveCost` as distinct concepts; commitments and credits differ in meaning.

## 4. Critical integration review

The `main` branch `Data_Integration.sql` currently includes dimension and fact `INSERT` statements **before** `LOAD DATA LOCAL INFILE`, and has **two alternative** `LOAD DATA` blocks (different line terminators). If run from the beginning against empty tables, inserts occur before staging rows are loaded. Running both loaders would append duplicated records.

**Safe agreed order:** (1) choose the 26-column cleaned CSV, (2) load staging exactly once into an appropriately empty staging table (with an agreed transaction/reload strategy), (3) validate row counts, tags and sums, (4) build dimensions, (5) build fact, (6) validate foreign keys and reconciliation, (7) point dbt sources at the confirmed staging table. Gitika owns implementation of the MySQL/dbt pipeline and SQL changes.

Do not treat a `dbt debug` pass as proof that the **data contents** or **dbt models** have been validated. No direct access to Gitika's private local MySQL instance was available for this report.

## 5. What to send Gitika / Day 2 dependencies

1. This report, `week2_day1_source_readiness.json`, and `week2_day1_staging_field_contract.csv`.
2. The read-only `week2_day1_mysql_staging_precheck.sql` to run in her development warehouse (not yet executed against her server).
3. Point to the previously prepared 26-column cleaned CSV (avoid re-committing large duplicates); agree on whether the existing staging table is already loaded and whether to reload.
4. Confirm the GitHub `main` branch lacks the Week 1 Taeyun files as of review; send the existing Week 1 package or commit those files separately if needed.

## 6. Reproduction

```bash
python scripts/week2_day1_source_readiness.py \
  --raw path/to/focus_exercise_2026-q3.csv \
  --clean path/to/focus_cleaned_2026-q3.csv \
  --audited path/to/focus_tag_audited_2026-q3.csv \
  --output outputs
```

Then ask Gitika to run `scripts/week2_day1_mysql_staging_precheck.sql` in her connected MySQL environment and compare results to the JSON baseline. No secret connection data is needed or committed.

**Sources:** Uploaded original/cleaned/audited CSVs; GitHub `main`: `README.md`, `Data_Integration.sql`, `Week 2 Day 1 Update` (checked 21 November 2026). Dataset attribution: The FinOps Desk, FOCUS exercise, CC BY 4.0.
