# Week 2 · Day 2 — Source Configuration & Dataset Readiness

**Owner:** Taeyun  
**Project:** Real-Time Multi-Cloud FinOps & Infrastructure Unit Economics Engine  
**Role:** Supporting data preparation, source validation, and dbt integration  
**Status:** Local dataset/source-configuration validation completed; live MySQL verification pending.

## Objective
Confirm that the prepared Q3 2026 FOCUS data can be consumed by Gitika's dbt project **without changing her database implementation**. Review the source definition, map all available attributes, and prepare repeatable data-quality evidence for downstream transformations.

## Files and current repository reviewed

- The FinOps Desk's `focus_exercise_2026-q3.csv` (original synthetic data).
- Taeyun's Week 1 `focus_cleaned_2026-q3.csv` (26 original FOCUS field names and cleaned JSON tag representation).
- Gitika's `sources.yml` and `stg_billing.sql` on the GitHub `main` branch, reviewed 23 November 2026.
- Gitika's `Week 2 Day 1 Update` (dbt 1.7.9; MySQL adapter 1.7.0; `dbt debug` reported successful).

## Source configuration review

Gitika's committed `sources.yml` declares:

| Property | Observed definition |
|---|---|
| dbt source | `finops_raw` |
| MySQL schema/database | `multi_cloud_finops` |
| Billing source table | `stg_focus_billing` |
| Other declared tables | `Dim_Service`, `Dim_Tenant`, `Dim_Region`, `Fact_Spend` |
| Staging model | `stg_billing.sql` uses `source('finops_raw','stg_focus_billing')` |

The source reference in her staging SQL matches the YAML definition. This is a **static configuration check**, not a direct query of her MySQL instance.

**Repository note:** At review time the `main` branch contains `sources.yml` and `stg_billing.sql` at the repository root, but does not contain `dbt_project.yml`. Gitika's local initialized dbt project may have these files under its `models/` directory; she should confirm that the committed repository contains the files in a runnable dbt project layout for reproducibility. Do not publish credentials or `profiles.yml` secrets.

## Dataset selection and source suitability

The previously agreed FinOps Desk FOCUS exercise contains **4,433 synthetic daily billing records**, covering AWS, Microsoft Azure, and Google Cloud in 2026 Q3. It supplies a practical **26-column subset** of FOCUS-style columns, not a complete production FOCUS export and not a live feed. It was selected by the team even though the initial brief mentioned Kaggle; instructor acceptance of non-Kaggle data may still need confirmation.

For this task, use the **26-column cleaned CSV** for any new `stg_focus_billing` load. The Week 1 tag-audited variant has 29 columns and is **not** a drop-in replacement for the 26-column staging table. Avoid appending the CSV repeatedly: load it once, verify the row count, then run dbt models.

## Data-readiness findings

| Source-readiness metric | Observed result |
|---|---:|
| Original / cleaned rows | 4,433 / 4,433 |
| Original / cleaned columns | 26 / 26 |
| Exact duplicates (both files) | 0 |
| AWS / Microsoft / Google Cloud rows | 2,675 / 927 / 831 |
| Missing sub-account IDs | 9 |
| Missing region IDs | 58 |
| Missing tags | 10 |
| Usage rows missing team/environment tags | 0 |
| BilledCost total (both) | USD 332,678.83 |
| EffectiveCost total (both) | USD 213,887.47 |

All 26 source fields have been mapped to the 26 intended `snake_case` output names of Gitika's `stg_billing` model. The accompanying `day2_source_field_profile.csv` provides the name mapping, intended type and null counts for each field.

### Validation rules for downstream dbt work

1. **Preserve identifiers as text:** e.g. `BillingAccountId` may start with zero; do not convert it to a numeric ID.
2. **Preserve source grain:** one charge/resource/day/charge type row. Do not aggregate or deduplicate non-identical rows in staging.
3. **Keep cost fields as DECIMAL:** monetary measures should not be converted to floating-point approximations.
4. **Use UTC timestamps:** this fixture uses `...Z` UTC strings. The MySQL view strips `Z` into timezone-naive DATETIME values; future non-UTC offsets need a separate conversion policy.
5. **Keep valid missing data as NULL:** tax rows can lack sub-account or region and some commitment rows lack resource information.
6. **Retain the `Tags` JSON field:** all usage records have `team` and `env` keys; don't fabricate team allocations for untagged tax/credit lines.
7. **Confirm source ingestion before model execution:** verify `stg_focus_billing` row count and cost totals to detect empty tables or accidental repeated import.

## Day 2 deliverables

- `docs/taeyun/week2/day2_dbt_source_configuration_review.md` — this review.
- `outputs/taeyun/week2/day2_source_field_profile.csv` — 26-field type/NULL/name contract.
- `scripts/taeyun_week2_days2_3_validate.py` — reproducible, read-only local audit.
- `outputs/taeyun/week2/day2_day3_validation.json` — results, test status and SHA-256 fingerprints.
- `data/taeyun/week2/focus_cleaned_2026-q3.csv` — unchanged Week 1 cleaned input (optional GitHub upload; useful to Gitika for repeatability).

**Handoff to Gitika:** The source configuration matches the planned 26-column billing contract and all local file checks pass. She should independently confirm the actual table contents inside her connected MySQL database before claiming end-to-end source readiness.
