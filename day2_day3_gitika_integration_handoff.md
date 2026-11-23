# Taeyun → Gitika | Week 2 Days 2–3 Integration Handoff

## What I verified

- GitHub `main` source definition: `finops_raw.stg_focus_billing` in MySQL `multi_cloud_finops`.
- Staging model: `stg_billing.sql` selecting the expected 26 fields and performing NULL, date, and decimal transformations.
- Week 1 input: 4,433 original and cleaned rows, 26 columns; no duplicates, date or cost errors.
- Original-vs-cleaned financial totals: BilledCost USD 332,678.83; EffectiveCost USD 213,887.47.
- Cost-allocation exceptions: 10 deliberately unattributed non-usage lines (9 Tax, 1 Credit); no usage-tag gaps.
- Independent local checks: **18 passed of 18**.

## Recommended integration steps

1. Confirm the dbt project files (`dbt_project.yml`, model and source locations) are present in a runnable project; do not add local credentials to GitHub.
2. Ensure MySQL `stg_focus_billing` has the **26 source columns**, and load the cleaned CSV **only once** (the root GitHub `Data_Integration.sql` contains multiple alternative load statements).
3. Query MySQL raw row count and cost totals to confirm the CSV actually arrived once.
4. Execute Gitika's `dbt run --select stg_billing` and verify the staging view is accessible.
5. Copy `tests/taeyun/week2/*.sql` into the dbt project's active `tests/` directory, then execute `dbt test --select stg_billing`.
6. Run `scripts/week2_days2_3_mysql_validation.sql` and compare with the expected counts/totals above.
7. If a check fails, compare the GitHub source schema, column order, timezone handling and uploaded CSV before modifying downstream dimensions.

## Files to upload to GitHub

- `docs/taeyun/week2/*.md` (three short reports/handoff)
- `scripts/taeyun_week2_days2_3_validate.py`
- `scripts/week2_days2_3_mysql_validation.sql`
- `tests/taeyun/week2/*.sql` (optional dbt tests; confirm project location)
- `outputs/taeyun/week2/*` (local audit evidence)
- `data/taeyun/week2/focus_cleaned_2026-q3.csv` (source input; optional if team already has an authoritative clean CSV at a documented location)

## Boundary of responsibility

Taeyun validated the files and prepared integration tests. Gitika owns changes to the dbt model/SQL warehouse and running tests on the configured MySQL instance. We have **not** published or overwritten Gitika's root `sources.yml` / `stg_billing.sql`.
