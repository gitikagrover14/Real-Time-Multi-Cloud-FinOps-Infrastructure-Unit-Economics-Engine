# Week 2 · Day 6 — Pipeline Execution & Data Validation (Taeyun's QA)

**Project:** Real-Time Multi-Cloud FinOps & Infrastructure Unit Economics Engine  
**Owner:** Taeyun — cleaned source data, data-quality controls, integration support  
**Date:** 27 November 2026  
**Shared GitHub:** https://github.com/gitikagrover14/Real-Time-Multi-Cloud-FinOps-Infrastructure-Unit-Economics-Engine  
**Repository snapshot inspected:** `main` tree `cd746e8a77b8d8bb6799b6441b702562293838f7`.

## Objective and division of responsibility

Gitika owns the MySQL/dbt environment and transformation models. Taeyun's Day 6 task is to verify that the cleaned Week 1 billing data is suitable for the existing dbt pipeline, independently reconcile source and expected transformed totals, assess data integrity and provide executable SQL/dbt tests for Gitika to run. No Gitika-owned model was overwritten.

**Status language matters:** **34/34 local checks PASS**. This verifies the actual downloaded source and cleaned CSVs and an independent SQLite key-mapping simulation. **Live MySQL/dbt execution remains NOT RUN by Taeyun**; Gitika reports her local dbt models were executed, but their logs were not made available for independent validation.

## Inputs reviewed

- `data/raw/focus_exercise_2026-q3.csv` — synthetic 2026-Q3 FOCUS exercise, 26 original columns.
- `data/processed/focus_cleaned_2026-q3.csv` — Taeyun's normalized, cost-preserving Week 1 file.
- `data/processed/focus_tag_audited_2026-q3.csv` — original 26 columns plus optional tag-audit helpers; use the 26-column cleaned CSV for existing MySQL staging.
- `data/raw/northwind_orders_2026-q3.csv` — 92 daily order counts, supporting later business unit economics.
- Gitika's committed `sources.yml`, `schema.yml`, `stg_billing.sql`, `dim_*`, `fact_spend.sql`, `service_unit_economics.sql` and `resource_unit_economics.sql`.

## 1. Data-quality and financial results

| Test category | Independent finding |
|---|---|
| Original / cleaned billing rows | 4,433 / 4,433 |
| Source billing fields | 26, with identical names/order |
| Original row content | Preserved by cleaned dataset; only JSON tag key ordering normalized |
| Exact cleaned duplicates | 0 |
| Billing window | 1 July – 30 September 2026, 92 days |
| Daily business order records | 92, unique Q3 calendar dates |
| ListCost / ContractedCost | $384,715.51 / $384,715.51 |
| BilledCost | $332,678.83 |
| EffectiveCost | $213,887.47 |
| Tags present, valid `team`/`env` | 4,423 |
| Missing tags | 10 (9 tax, 1 credit), intentionally unattributed |
| Missing region | 58 records, must remain in fact costs |
| Missing SubAccountId | 9 records (expected from source tax handling) |
| Missing ResourceId | 333 records |
| Independent local validation | **34/34 PASS** |

All original vs cleaned cost and pricing quantity totals match exactly using Python `Decimal` (not floating point).

### Cloud provider reconciliation

| Provider | Records | BilledCost (USD) | EffectiveCost (USD) |
|---|---:|---:|---:|
| AWS | 2,675 | 251,040.07 | 139,110.07 |
| Microsoft | 927 | 36,289.49 | 36,289.49 |
| Google Cloud | 831 | 45,349.27 | 38,487.91 |
| **Total** | **4,433** | **332,678.83** | **213,887.47** |

The providers run different workloads; spend totals must not be used as evidence that one provider offers a lower price.

## 2. Transformation, dimension and model expectations

| dbt model / business entity | Expected record count from local source |
|---|---:|
| `stg_billing` | 4,433 |
| `dim_service` | 28 |
| `dim_tenant` | 10 |
| `dim_region` | 8, including blank-region dimension member |
| `fact_spend` | 4,433 |
| `service_unit_economics` | 33 groups (service + currency + pricing unit) |
| `resource_unit_economics` | 44 groups (resource + service + currency + unit) |

A separate **SQLite in-memory reconstruction** using the cleaned CSV mapped all 4,433 fact rows through the three dimensions without foreign-key violations. This establishes that the dataset supports lossless key mapping; it is **not the live MySQL database**.

The actual `fact_spend.sql` model uses inner joins to `dim_service`, `dim_tenant`, and `dim_region`. Therefore the **58 records with blank RegionId** will be dropped if the stage converts them to NULL and no appropriate mapping is retained. The fact row-count test checks for this condition.

### Resource-level cost bridge

| Scope | Rows | BilledCost (USD) | EffectiveCost (USD) |
|---|---:|---:|---:|
| All billing rows | 4,433 | 332,678.83 | 213,887.47 |
| Rows with ResourceId | 4,100 | 297,998.34 | 175,289.98 |
| Rows without ResourceId | 333 | 34,680.49 | 38,597.49 |

The 333 unidentified-resource records comprise **18.05% of EffectiveCost** and are intentionally excluded by Gitika's `resource_unit_economics.sql`. The output is useful for resource-level analysis, but the omitted amounts must remain visible in overall spend reporting. Six service groups and one resource group have zero/missing total pricing quantity; their cost-per-unit must remain NULL.

## 3. MySQL and dbt pipeline test package

- `scripts/week2_day6_day7_mysql_readonly_checks.sql`: SQL queries for table discovery, source/stage/fact counts, dimension mapping, source totals, resource gaps, rate calculations and distinct-resource advisory.
- `tests/taeyun_w2d6_*.sql`: ten **optional dbt singular tests**, each returning zero rows on success. Designed for Gitika to copy into her working dbt project's `/tests` folder. These do not replace Gitika's `schema.yml` generic tests.
- `scripts/taeyun_week2_days6_7_final_audit.py`: standard-library-only reproducible local source QA; produces a validation JSON and three CSV reports.

**Live acceptance checklist for Gitika** (not completed in this environment):

```bash
# Run from the actual dbt project directory with its dbt_project.yml
# and a working MySQL profile; do not commit credentials.
dbt debug
dbt build
dbt test
```

Run the provided read-only SQL in MySQL, and compare the results with the observed source totals above. If using the extra singular tests, put them in the active dbt project under `tests/`, run `dbt parse`, then `dbt test --select taeyun_w2d6_*` or use `dbt test` to execute all tests. Preserve the `target/run_results.json`, command output, and a short pass/fail summary as review evidence; do not publish secrets or `profiles.yml`.

## 4. Issues to resolve before independently claiming a successful pipeline

1. **Reproducibility:** GitHub `main` contains SQL and YAML fragments but no `dbt_project.yml` or a complete runnable dbt project directory. Gitika should publish a sanitized project scaffold/model hierarchy or document how to reconstruct it.
2. **Renamed raw sources:** `sources.yml` now identifies backed-up relations `dim_service__dbt_backup`, `dim_tenant__dbt_backup`, `dim_region__dbt_backup`. Verify these exist in MySQL and reflect the intended raw source; source names differ from their identifiers.
3. **Fact lineage:** `fact_spend.sql` currently sources `Fact_Spend` from MySQL (not `ref('stg_billing')`) and uses three INNER JOINs. Confirm this source fact was populated exactly once from the cleaned input and no charges were dropped.
4. **No fabricated attribution:** Missing tags on ten tax/credit rows are preserved as unattributed, not assigned to a team.
5. **Resource coverage disclosure:** 333 charges have no ResourceId; keep them separate in reconciliations instead of counting the resource model as complete spend.
6. **Model rate semantics:** current `effective_cost_per_unit` is per cloud pricing quantity, not per customer order; units and currency cannot be mixed without grouping.
7. **Real-time claim:** dataset is synthetic historical daily data, not a streaming or continuously refreshed billing feed. Real-time ingestion remains an outstanding phase.

## Outcome

**Taeyun's Day 6 data-side validation and executable test preparation are complete; local evidence is PASS (34/34).** The final MySQL/dbt pipeline and source-alias checks require execution in Gitika's environment. Do not mark those live checks passed until outputs are saved and reviewed.

**Attribution:** The FinOps Desk, *FOCUS Analysis Exercise* (CC BY 4.0), https://finopscourse.com/resources/focus-analysis-exercise.
