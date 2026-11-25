# Taeyun → Gitika — Week 2 Day 5 unit economics handoff

**Status:** Data-side independent audit completed (19/19 local PASS); live MySQL/dbt test pending.

## What I validated

1. Reproduced the group-by logic from your committed `service_unit_economics.sql` and `resource_unit_economics.sql` on the Week 1 cleaned FOCUS data.
2. Verified 4,433 billing rows, 28 service entities, 33 expected service group rows, and 44 expected resource group rows.
3. Verified ListCost, ContractedCost, BilledCost and EffectiveCost totals to exact cents.
4. Verified the definition `SUM(EffectiveCost)/SUM(PricingQuantity)` for each eligible group and NULL on missing or zero denominators.
5. Prepared a bridge showing the 333 billing rows **not included** in resource analysis: 323 usage, 9 tax, 1 credit. Their EffectiveCost totals $38,597.49. Resource-only EffectiveCost is $175,289.98; whole-dataset EffectiveCost is $213,887.47.

## Please check in your MySQL/dbt environment

- Run `scripts/week2_day5_mysql_unit_economics_checks.sql` against the existing model views; this script is read-only.
- If helpful, add five optional files from `dbt_tests/` to your actual dbt project's `tests/` folder, then run `dbt test`.
- Confirm how missing `ResourceId` values are represented (`NULL` or `''`). Your service-level `COUNT(DISTINCT f.ResourceId)` could include empty strings; suggest `COUNT(DISTINCT NULLIF(TRIM(f.ResourceId), ''))` for semantic clarity.
- Validate that both models are built from the correct populated `Fact_Spend` source, and that no costs disappear in upstream fact/dimension JOINs.
- Consider showing resource-unattributed spend separately in dashboard/reporting totals instead of forcing resource rows to equal all-cloud totals.

## Expected local outputs for comparison

| View | Expected rows |
|---|---:|
| `fact_spend` | 4,433 |
| `service_unit_economics` | 33 |
| `resource_unit_economics` | 44 |

| Scope | BilledCost (USD) | EffectiveCost (USD) |
|---|---:|---:|
| Complete source / service aggregation | 332,678.83 | 213,887.47 |
| Identifiable-resource subset | 297,998.34 | 175,289.98 |
| Missing-resource bridge | 34,680.49 | 38,597.49 |

**Important:** All counts and financial figures above were independently computed against the local CSV source, not observed by executing your live MySQL dbt models. No modifications are needed to the GitHub root files to add my QA documents.
