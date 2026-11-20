# Day 7 — Final Dataset Preparation, Validation & Gitika Handoff

**Owner:** Taeyun  
**Project:** Real-Time Multi-Cloud FinOps & Infrastructure Unit Economics Engine  
**Week 1 activity:** Final data preparation, integration handoff and documentation

## 1. Final dataset selection

Use `outputs/focus_cleaned_2026-q3.csv` from the **Day 4–5 package** as the authoritative **26-column** input to Gitika's MySQL `stg_focus_billing` staging table. The separate `focus_tag_audited_2026-q3.csv` from Day 6 contains **three extra columns** (`allocation_team`, `allocation_env`, `tag_status`) and must **not** be loaded directly into Gitika's existing 26-column staging table. Use it for QA or extend the schema first.

Dataset source: The FinOps Desk's *FOCUS Exercise – 2026 Q3* (synthetic dataset), not Kaggle. Confirm instructor accepts the non-Kaggle source. Q3 2026 billing is batch data, not a live feed. CC BY 4.0 attribution to The FinOps Desk must be retained.

## 2. Final checks from the real files

| Validation item | Result |
|---|---:|
| Original billing rows | 4,433 |
| Cleaned billing rows | 4,433 |
| Audited billing rows | 4,433 |
| FOCUS source columns | 26 |
| Supplemental order rows | 92 |
| Exact duplicates in raw input | 0 |
| Missing Tags | 10 |
| Missing RegionId | 58 |
| Missing SubAccountId | 9 |
| BilledCost, original = cleaned | 332678.83 USD |
| EffectiveCost, original = cleaned | 213887.47 USD |

Provider counts: AWS 2,675, Microsoft 927, Google Cloud 831. Original and cleaned totals match for ListCost, ContractedCost, BilledCost, EffectiveCost and PricingQuantity. The Day 6 tag audit finds 4,423 valid tagged records and 10 missing (9 Tax and 1 Credit); usage records all have tags. Missing subaccounts, regions and non-usage tags were not fabricated.

See `outputs/day7_final_validation.json` for checksums, full column missingness and exact measure totals.

## 3. Repository alignment — current main branch (checked 20 Nov 2026)

Gitika's root-level MySQL scripts are `Dimension_Tables_Creation.sql`, `Fact_Table_Creation.sql`, `Data_Integration.sql` and `Validation_Testing.sql`. **Do not overwrite these files**: the SQL/database implementation is Gitika's work. MySQL staging declares the original 26 FOCUS source columns in their current order, so the Day 4–5 cleaned CSV is the correct exchange artifact.

**Critical execution-order issue to resolve with Gitika:** `Data_Integration.sql` currently contains dimension/fact INSERT statements **before** its `LOAD DATA LOCAL INFILE` blocks. It also includes **two** LOAD DATA statements for the same CSV (one with `\r\n` and one with `\n`). Running it end-to-end in the existing order could leave dimensions/fact empty initially and could append billing rows twice. Load the cleaned CSV **once** into an **empty** staging table first, verify 4,433 rows, and only then run the dimension/fact inserts. Avoid repeating inserts without a safe reset or idempotency safeguards. The SQL currently uses a hard-coded Windows CSV path, which Gitika will need to replace with her local path.

A separate optional check script is provided in `scripts/day7_gitika_mysql_checks.sql`; it is **not** a modification of Gitika's code.

## 4. Recommended MySQL integration sequence

1. Gitika runs her dimension and fact table creation scripts and creates an empty `stg_focus_billing` using her Data Integration file's CREATE TABLE section.
2. Check that staging is empty (`SELECT COUNT(*) FROM stg_focus_billing;`). Use a single CSV import for `focus_cleaned_2026-q3.csv`, with the path and newline choice suited to her system.
3. Check staged count = 4,433; confirm all 26 columns map correctly, and inspect representative rows/timestamps/JSON tags.
4. Execute dimension and fact INSERT portions **only after** staging import. Do not rerun INSERTs on already populated targets without explicit reset rules.
5. Expect **nullable** `Region_Key` for rows missing `RegionId`; this is intentional. Use `LEFT JOIN`s so regional reporting does not silently discard unattributed spend.
6. Run Gitika's validation SQL and compare staged vs fact counts and the exact source totals below.
7. Review key mapping and team cost allocation. Tax and credit charges without tags must remain unattributed until an explicit cost-allocation policy is agreed.

## 5. Expected reconciliation figures

| Measure | Expected source total |
|---|---:|
| ListCost | 384715.51 |
| ContractedCost | 384715.51 |
| BilledCost | 332678.83 |
| EffectiveCost | 213887.47 |
| PricingQuantity | 174853167.4731 |

These are sums of all charge categories and must not be mistaken for usage-only costs.

## 6. Completion and outstanding integration status

**Taeyun Day 7 data handoff: completed.** Final CSV selection, row-level QA, source-to-clean reconciliation, schema-format review and repository-aware instructions have been prepared.

**Not claimed as completed:** Running Gitika's *MySQL* implementation on her machine, importing the CSV to her current MySQL database, or verifying that its resulting Fact_Spend count/totals match. Those remain joint integration checks, and MySQL credentials/runtime were not supplied.

## Source attribution

The FinOps Desk, *FOCUS Exercise – Northwind Analytics 2026 Q3*; synthetic and CC BY 4.0. https://finopscourse.com/resources/focus-analysis-exercise
