# Taeyun → Gitika: Week 2 Days 6–7 Integration Handoff

**Status:** Source validation and review materials completed; Gitika to execute live MySQL/dbt tests.

## Files to integrate

- `scripts/week2_day6_day7_mysql_readonly_checks.sql`: independent read-only MySQL model validation; run against the `multi_cloud_finops` database after building dbt models. Adjust schema names if your dbt profile uses a separate schema.
- `tests/taeyun_w2d6_*.sql`: ten optional dbt singular tests. Copy into the working `finops_dbt/tests/` folder. They do not replace or edit your existing `schema.yml` tests.
- `scripts/taeyun_week2_days6_7_final_audit.py`: exact-decimal local data QA and output generator; no packages required.
- `outputs/taeyun/week2/day6_day7_local_validation.json`: 34 local test outcomes and source hashes.
- `outputs/taeyun/week2/day7_testing_matrix.csv`: local vs live checks visibly separated.
- `docs/taeyun/week2/day6_pipeline_execution_validation_qa.md`: test methodology and issues.
- `docs/taeyun/week2/day7_final_testing_midproject_review.md`: final Week 2 review narrative.

## Commands for the shared handoff package

```bash
python3 scripts/taeyun_week2_days6_7_final_audit.py
# Expected: LOCAL VALIDATION: PASS (34/34)
```

## Commands for *your* existing MySQL/dbt installation

```bash
cd /path/to/finops_dbt     # folder containing dbt_project.yml
# Put the ten singular tests in tests/; ensure your model SQL/YAML is in models/.
dbt debug
dbt parse
dbt build
dbt test
```

Then use a MySQL client to execute `scripts/week2_day6_day7_mysql_readonly_checks.sql` and save output. All statements are read-only apart from `USE`, which selects the database.

## Live checkpoints / expected source baselines

| Check | Expected |
|---|---:|
| Source staging and dbt fact rows | 4,433 each |
| Service / tenant / region dimensions | 28 / 10 / 8 |
| Service / resource unit economics groups | 33 / 44 |
| Full BilledCost | 332,678.83 USD |
| Full EffectiveCost | 213,887.47 USD |
| Resource-identified EffectiveCost | 175,289.98 USD |
| Resource-unidentified EffectiveCost | 38,597.49 USD |
| Missing tags (tax + credit) | 10 |
| Missing region | 58 |

The resource model should **not** equal full fact cost by itself. Compare to the resource-eligible fact subset and reconcile the rest as unattributed. The six zero/missing-quantity service groups and one resource group should yield NULL rates. No cloud provider price benchmarking or real-time processing is demonstrated by these tests.

## Specific issues from the GitHub main branch

- `sources.yml` now maps Dim_Service/Dim_Tenant/Dim_Region to `dim_service__dbt_backup`, `dim_tenant__dbt_backup`, `dim_region__dbt_backup`: confirm the backup relations exist.
- `fact_spend.sql` uses INNER JOINs; ensure source blank regions survive and no total-cost loss occurs.
- `fact_spend.sql` references a prepopulated `Fact_Spend` source, rather than `ref('stg_billing')`: verify source lineage.
- `service_unit_economics.sql` uses `COUNT(DISTINCT ResourceId)`; an empty string may be counted as a real resource. Advisory in the SQL script compares to `COUNT(DISTINCT NULLIF(TRIM(ResourceId),''))`.
- `dbt_project.yml` is absent from GitHub main: keep credentials out of GitHub, but commit a sanitized project scaffold for reproducibility.

**Do not rerun both CSV loads in `Data_Integration.sql`.** That file has two alternative loads and performs insertions before the loads; use your currently validated staging data and a controlled, single-load integration workflow.

## Requested response / shared sign-off

Please share (1) the `dbt build`/`dbt test` summary, (2) MySQL checks output, (3) any failing assertions and (4) status of the source backup identifiers. Then the team can mark the live pipeline independently verified and finish the Week 2 mid-project review.
