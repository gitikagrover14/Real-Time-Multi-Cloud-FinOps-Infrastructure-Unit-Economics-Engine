# Week 2 · Day 5 — Unit Economics Validation and Reconciliation

**Owner:** Taeyun (data quality, analysis and integration support)  
**Project:** Real-Time Multi-Cloud FinOps & Infrastructure Unit Economics Engine  
**Repository:** [gitikagrover14/Real-Time-Multi-Cloud-FinOps-Infrastructure-Unit-Economics-Engine](https://github.com/gitikagrover14/Real-Time-Multi-Cloud-FinOps-Infrastructure-Unit-Economics-Engine)  
**Models reviewed:** [`service_unit_economics.sql`](https://github.com/gitikagrover14/Real-Time-Multi-Cloud-FinOps-Infrastructure-Unit-Economics-Engine/blob/main/service_unit_economics.sql), [`resource_unit_economics.sql`](https://github.com/gitikagrover14/Real-Time-Multi-Cloud-FinOps-Infrastructure-Unit-Economics-Engine/blob/main/resource_unit_economics.sql)  
**Snapshot reviewed:** main tree `242b68b555733a6ddeed97dc6b74cc45a4e2a8d7`, 2026-11-25.

## 1. Objective and division of work

Gitika developed and ran both dbt models (as reported in her Day 5 message). My task was to independently review their transformation logic, reproduce the aggregate calculations against the source dataset, verify totals and unit rates, and provide reusable MySQL/dbt quality checks. This work does **not** modify Gitika's transformation models or assert that I executed her live MySQL pipeline.

## 2. Data and calculation methodology

- Inputs: the official synthetic FinOps Desk Q3 2026 26-column billing CSV (4,433 records) and Taeyun's Week 1 cleaned CSV.
- Numeric computations: Python `Decimal` values (not binary floats) for cost and pricing quantity.
- **Service-level grain:** provider, invoice issuer, service category and service name (the source business key for `Service_ID`), plus `BillingCurrency` and `PricingUnit`.
- **Resource-level grain:** the same service attributes plus `ResourceId`, `BillingCurrency` and `PricingUnit`; only nonblank resource IDs qualify.
- **Rates:** `SUM(EffectiveCost) / SUM(PricingQuantity)` when the denominator is non-NULL and nonzero; otherwise rate is NULL/blank. Other charges remain in the aggregates as in Gitika's code.
- Note: counts below are independent **local expected results**. Gitika's live dbt model must still be queried for final matching counts and numerical parity.

## 3. Observed independent results

| Measure | Result |
|---|---:|
| Original / cleaned billing rows | 4,433 / 4,433 |
| Distinct service business keys | 28 |
| Service-level aggregate rows (local expected) | 33 |
| Resource-level aggregate rows (local expected) | 44 |
| Records with a populated `ResourceId` | 4,100 |
| Records with no `ResourceId` | 333 |
| Service groups with missing or zero pricing quantity | 6 |
| Resource groups with missing or zero pricing quantity | 1 |
| Service groups containing at least one blank `ResourceId` | 8 |
| Local validation checks | **19/19 PASS** |

### Financial reconciliation (USD)

| Financial measure | Complete billing dataset / service model | Resource-identified subset | Unidentified-resource subset |
|---|---:|---:|---:|
| ListCost | 384,715.51 | 350,035.02 | 34,680.49 |
| ContractedCost | 384,715.51 | 350,035.02 | 34,680.49 |
| BilledCost | 332,678.83 | 297,998.34 | 34,680.49 |
| EffectiveCost | **213,887.47** | **175,289.98** | **38,597.49** |

The identified and unidentified subsets add up exactly to the overall dataset for all four financial measures and for PricingQuantity. Unidentified-resource rows represent **18.05% of total EffectiveCost**. Therefore, resource-level cost totals are expected to be lower than service-level totals, despite both models being correctly calculated on their own eligible populations.

The CSV source is entirely USD; model grouping by currency and pricing unit is still essential for reuse with other datasets. A cost per GB is not comparable with a cost per hour or per 10,000 operations.

## 4. Data quality and analytical interpretation

**Issue A — excluded resource costs (material).** `resource_unit_economics.sql` filters out blank and NULL `ResourceId` values. The 333 rows that are excluded include **323 usage records**, nine tax records, and one credit. They cannot simply be ignored in organization-wide spend reporting. Their $38,597.49 effective cost should appear as a separate "unattributed resource" category or in a clearly disclosed reconciliation bridge. The model need not change for its stated resource-only purpose.

**Issue B — distinct resource count may be inflated.** The service model currently uses `COUNT(DISTINCT f.ResourceId)`. If MySQL stores a missing resource ID as the non-NULL empty string `''`, it will count that empty string as a distinct resource. Eight local service/currency/unit groups contain at least one blank ID. Recommend changing the expression to `COUNT(DISTINCT NULLIF(TRIM(f.ResourceId), ''))` if the group agrees. Live MySQL storage semantics must be checked before classifying this as an observed model failure.

**Issue C — no valid per-unit rate in some groups.** Six service groups and one resource group lack a usable pricing quantity. Correct handling is to leave `effective_cost_per_unit` NULL, not treat missing quantity as one or divide by zero. The supplied SQL tests check this.

**Issue D — interpretation of 'unit economics'.** The models calculate cost per cloud **pricing unit** (Hours, GB, TB, etc.). They do not yet measure cost per **customer order** or business transaction. The uploaded `northwind_orders_2026-q3.csv` could support a separate business-unit metric later, if needed. Cloud provider totals do not imply cross-provider price competitiveness because workloads differ.

**Issue E — source-of-truth lineage.** The current committed fact model reads the existing `Fact_Spend` MySQL source via `source('finops_raw','Fact_Spend')` and joins dimensions; it does not currently build fact measures directly from `ref('stg_billing')`. Ensure the source fact table reflects the cleaned Week 1 dataset before interpreting results as cleaned-data transformations.

## 5. Local testing and Gitika integration

Run the independent source audit:

```bash
python scripts/taeyun_week2_day5_unit_economics_audit.py \
  --raw focus_exercise_2026-q3.csv \
  --cleaned focus_cleaned_2026-q3.csv \
  --out outputs/taeyun/week2
```

Local outputs are `day5_service_unit_economics_local.csv`, `day5_resource_unit_economics_local.csv`, `day5_resource_exclusion_bridge.csv`, and `day5_unit_economics_validation.json`. These are audit outputs, **not dbt model exports**.

Gitika can run the read-only `scripts/week2_day5_mysql_unit_economics_checks.sql` after her dbt models are built; adjust database/schema names if her profile uses a separate model schema. The five optional **dbt singular tests** in `dbt_tests/` are intended to be copied to her dbt project's `tests/` folder (do not replace the existing models). Suggested validation commands:

```bash
dbt run --select +service_unit_economics +resource_unit_economics
dbt test --select service_unit_economics resource_unit_economics
```

`dbt test --select ...` will execute tests selected by the project's dependency rules; to run the supplied custom tests, place them in the active dbt project and select by test filename (or run `dbt test`). Confirm MySQL outputs against the local expected 33 service groups, 44 resource groups, 4,433 fact rows, and the four overall financial totals above. Any disagreement must be investigated against the live table contents, not silently assumed to be correct.

## 6. Completion status

- [x] Review the two Day 5 models on GitHub main.
- [x] Reproduce service and resource aggregations independently from cleaned CSV.
- [x] Check four cost measures, quantities and effective cost per unit.
- [x] Reconcile source/service/resource cost with an explicit missing-resource bridge.
- [x] Document zero-denominator and distinct-resource caveats.
- [x] Prepare SQL and dbt regression tests for Gitika.
- [ ] Jointly execute model-validation queries on the live MySQL/dbt environment (Gitika to run or share outputs).

**Conclusion:** Day 5 independent data-side QA is complete. All 19 local checks passed. Live model parity requires Gitika's MySQL/dbt output and remains an integration action for Day 6.

**Attribution:** Synthetic dataset from The FinOps Desk, *FOCUS Analysis Exercise* (CC BY 4.0). https://finopscourse.com/resources/focus-analysis-exercise
