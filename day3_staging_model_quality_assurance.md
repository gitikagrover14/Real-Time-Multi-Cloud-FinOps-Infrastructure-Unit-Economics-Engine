# Week 2 · Day 3 — dbt Staging Model Quality Assurance

**Owner:** Taeyun  
**Team dependency:** Gitika owns the MySQL/dbt staging model implementation  
**Status:** Local source-to-cleaned checks and static model review complete. End-to-end dbt execution is **not** independently tested here.

## Objective
Independently review Gitika's newly committed `stg_billing.sql` and verify that the **underlying data supports** its transformations, with a repeatable testing handoff for her live MySQL/dbt environment. Do not duplicate or overwrite the staging model itself.

## Reviewed staging transformations

| Transformation | Current dbt implementation | Our independent finding |
|---|---|---|
| Source | `source('finops_raw', 'stg_focus_billing')` | Correct match to `sources.yml` |
| Column names | 26 explicit snake_case aliases | All 26 expected aliases and order present |
| Identifiers | `NULLIF(TRIM(...),'')` | Source IDs remain nonnumeric text; blanks become NULL |
| Timestamps | `STR_TO_DATE` after replacing `T` and `Z` | All fixture timestamps are parseable UTC Z timestamps |
| Cost/quantity | `CAST(... AS DECIMAL(18,6))` | Numeric values parse cleanly, including negative credits |
| Optional fields | `NULLIF(TRIM(...),'')` | Legitimate blank fields are preserved as SQL NULL |
| Cost-allocation tags | `NULLIF(TRIM(Tags),'')` | JSON text retained; not yet split into team/env columns |

The code's date parsing is appropriate **for the provided UTC-only fixture**; a production data feed with `+HH:MM` offsets would require explicitly timezone-aware handling.

## Actual local validation results

| Check | Result |
|---|---:|
| Independent checks passed | **18 / 18** |
| Original and cleaned source rows | 4,433 each |
| Source and proposed staging fields | 26 |
| Malformed dates, decimals or JSON fields | 0 |
| Nonascending billing/charge date periods | 0 |
| Exact duplicate records | 0 |
| Logically changed values from raw to cleaned | 0 |
| Valid tagged records | 4,423 |
| Missing tag records | 10 (9 Tax, 1 Credit) |
| Usage records missing tags | 0 |
| Source/cleaned cost reconciliation | Exact match |

Costs, checked using `Decimal`, are:

| Provider | Rows | BilledCost (USD) | EffectiveCost (USD) |
|---|---:|---:|---:|
| AWS | 2,675 | 251,040.07 | 139,110.07 |
| Microsoft | 927 | 36,289.49 | 36,289.49 |
| Google Cloud | 831 | 45,349.27 | 38,487.91 |
| **Total** | **4,433** | **332,678.83** | **213,887.47** |

Original tags and cleaned tags sometimes differ in **JSON key ordering**; they are equivalent after JSON parsing. Comparing raw CSV byte-for-byte with cleaned CSV would therefore be misleading.

## Recommended dbt quality tests (new, standalone files)

Five singular tests were authored without touching Gitika's current model:

1. `test_taeyun_staging_row_counts.sql` — raw and staged record counts must match, and neither may be empty.
2. `test_taeyun_staging_cost_reconciliation.sql` — list, contracted, billed and effective cost totals must reconcile.
3. `test_taeyun_staging_required_fields_and_periods.sql` — key fields and date intervals must be valid.
4. `test_taeyun_staging_usage_tags.sql` — usage records must retain team/environment JSON tags.
5. `test_taeyun_staging_optional_null_counts.sql` — source blank counts must equal staging NULL counts for optional fields.

These queries are designed for dbt 1.7 with **MySQL 8+** (`<=>` null-safe comparison and MySQL JSON functions). dbt singular tests succeed only when their SQL returns zero rows.

### How Gitika can run them

Copy the tests to the `tests/` directory of her actual `finops_dbt` project (which must contain `dbt_project.yml`), alongside the existing source YAML and staging model under dbt's configured model paths. Then run from the dbt project directory:

```bash
dbt debug
dbt run --select stg_billing
dbt test --select stg_billing
```

If tests are not selected by `--select stg_billing` due to project configuration, run `dbt test` from the root to execute all enabled tests. Also run the standalone, read-only MySQL queries in `scripts/week2_days2_3_mysql_validation.sql` to inspect detailed expected values.

## Open integration checkpoints (not resolved by local checks)

- **Actual MySQL counts and totals:** Gitika should confirm that `stg_focus_billing` is loaded **once** and that `stg_billing` returns 4,433 rows without SQL conversion errors.
- **dbt project in GitHub:** The repository's `main` branch did not contain a `dbt_project.yml` at review time. Gitika may have it locally; committing a safe project configuration would make the pipeline reproducible. Do not commit private `profiles.yml` credentials.
- **Tag extraction for unit economics:** `stg_billing` currently retains JSON as `tags` and does not yet expose `team` and `env` fields. This is acceptable for staging, but Day 5 / downstream unit economics should decide how those allocations are exposed.
- **Future data:** The source is synthetic Q3 data, not a live feed. Source freshness and future schema changes need distinct tests before a real-time claim.

## Day 3 deliverables

- `docs/taeyun/week2/day3_staging_model_quality_assurance.md` — this report.
- `outputs/taeyun/week2/day2_day3_validation.json` — all observed local checks.
- `outputs/taeyun/week2/day3_provider_reconciliation.csv` — provider-level source/cleaned cost reconciliation.
- `outputs/taeyun/week2/day3_tag_exceptions.csv` — 10 observed, intentionally unattributed records.
- `tests/taeyun/week2/*.sql` — five suggested dbt singular tests.
- `scripts/week2_days2_3_mysql_validation.sql` — read-only live SQL verification.

**Conclusion:** The **local** data supports Gitika's staging model and all 18 source/contract checks pass. A successful execution of the dbt model against Gitika's **live** MySQL instance remains a team verification step, not an outcome claimed by this document.
