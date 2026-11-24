# Day 4 → Gitika: Integration handoff

## What is ready

- `outputs/taeyun/week2/day4_dimension_fact_validation.json` — repeatable local audit and 14 checks.
- `outputs/taeyun/week2/day4_dimension_mapping_summary.csv` — dimension key counts and mapping guidance.
- `outputs/taeyun/week2/day4_region_exceptions.csv` — all 58 blank-region billing records; no region has been invented.
- `scripts/taeyun_week2_day4_dim_fact_audit.py` — independent CSV audit and SQLite inner-join simulations.
- `scripts/week2_day4_mysql_dimension_fact_validation.sql` — read-only source/fact/dimension checks in MySQL.
- `tests/taeyun/*.sql` — six optional dbt singular regression tests.

## Differences that matter

The source has **8 region values only if the empty-string region counts as a member** (7 nonblank regions). The fact dbt model currently uses `INNER JOIN` on `Region_Key`; if 58 blank regions become SQL `NULL` without a mapped member, records may disappear. Local simulation: 4,433 vs 4,375 facts; missing rows have $166,315.74 billed and $20,582.74 effective cost. This is a risk scenario, **not a finding of failure in Gitika's actual dbt run**.

Also, `fact_spend.sql` and `dim_*.sql` are views selecting from existing MySQL dimension/fact tables. They do not, on their own, refresh those source tables from the new staging view.

## Integration steps

1. In Gitika's actual `finops_dbt` project, place the six supplied singular tests under its configured `tests/taeyun/` directory. Do not replace her existing models or `sources.yml`.
2. Verify that `dbt_project.yml` includes the usual test path (`tests`); this file is not currently committed to the public repository.
3. Run `dbt run` and `dbt test --select 'path:tests/taeyun'`. Record execution results in GitHub separately.
4. Execute the MySQL checks to confirm that `Fact_Spend` and the `dbt_fact_spend` view preserve the full 4,433 rows and both cost totals.
5. Agree on the missing-region policy with Taeyun and rerun all tests if the mapping logic changes.

## Suggested GitHub commit message

`test: add Taeyun Week 2 Day 4 dimension and fact integrity checks`
