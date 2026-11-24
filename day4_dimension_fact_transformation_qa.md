# Week 2 · Day 4 — Dimension & Fact Transformation Quality Assurance

**Member:** Taeyun  
**Project:** Real-Time Multi-Cloud FinOps & Infrastructure Unit Economics Engine  
**Responsibility:** Source-data quality, dimensional key-mapping validation and integration handoff (supporting Gitika's SQL/dbt development).  
**Repository checked:** [`gitikagrover14/Real-Time-Multi-Cloud-FinOps-Infrastructure-Unit-Economics-Engine`](https://github.com/gitikagrover14/Real-Time-Multi-Cloud-FinOps-Infrastructure-Unit-Economics-Engine), `main` tree SHA `366636d44379bdacfc5c8ea1439e3c18ab896eb4` (24 Nov 2026).

## 1. Objective and scope

Independently verify that the **Week 1 cleaned FOCUS billing data** can be mapped into `Dim_Service`, `Dim_Tenant`, `Dim_Region` and `Fact_Spend` without loss of billing records or financial totals. Review Gitika's Day 4 dbt transformation files and supply tests she can run against her live MySQL/dbt environment.

**Important boundary:** Gitika develops the dimensional and fact dbt models. This contribution provides **local, reproducible data validation and review**; it does **not** claim to have run dbt or accessed Gitika's live MySQL instance.

## 2. Materials reviewed

- Local `focus_exercise_2026-q3.csv` and Week 1 `focus_cleaned_2026-q3.csv`, both with 26 FOCUS fields.
- Gitika's `sources.yml`, `stg_billing.sql`, `dim_service.sql`, `dim_tenant.sql`, `dim_region.sql`, and `fact_spend.sql` committed to `main`.
- Existing SQL definition/integration files for the source `Fact_Spend` and three dimensions.
- Gitika's message reporting successful execution of the four dbt models with 28 service, 10 tenant, 8 region and 4,433 fact records. These are **teammate-reported results**, not independently verified MySQL query results.

## 3. Local results (verified against the actual CSV)

| Indicator | Result |
|---|---:|
| Original billing rows | 4,433 |
| Cleaned billing rows | 4,433 |
| Source columns | 26 |
| Composite service business keys | 28 |
| Composite tenant business keys | 10 |
| Distinct region IDs including one blank value | 8 |
| Distinct *nonblank* region IDs | 7 |
| Missing/blank source `RegionId` values | 58 |
| Missing/blank source `SubAccountId` values | 9 |
| Missing/blank source `Tags` values | 10 |
| Exact duplicate cleaned rows | 0 |
| Local audit checks | **14 / 14 passed** |

**Financial reconciliation:** BilledCost **$332,678.83** and EffectiveCost **$213,887.47** in both original and cleaned files. The audit also checked ListCost and ContractedCost, source-row identity signatures, dates and populated JSON tags.

## 4. Mapping to Gitika's dimensional models

| Model | Business key or source | Local unique-key count | QA conclusion |
|---|---|---:|---|
| `dim_service.sql` | `ProviderName` + `InvoiceIssuerName` + `ServiceCategory` + `ServiceName` | 28 | Expected cardinality matches Gitika's reported 28 rows |
| `dim_tenant.sql` | `BillingAccountId` + `SubAccountId` | 10 | Expected cardinality matches; 9 tax rows have an intentionally blank subaccount |
| `dim_region.sql` | `RegionId` | 8 (including blank) | Matches reported 8 **if** the blank region is a separate dimension entry |
| `fact_spend.sql` | Existing MySQL `Fact_Spend`, joined to all three dimensions | 4,433 input rows | Preservation depends on FK mappings and `INNER JOIN` behavior |

The four committed dbt models are **views over already populated MySQL dimensions and fact tables**, rather than transforms built directly from `ref('stg_billing')`. This is appropriate for viewing the preloaded schema, but **dbt alone does not rebuild the dimensional warehouse from new raw billing data** in the current file definitions. Coordinate the loading/update workflow before claiming fully automated end-to-end ingestion.

## 5. Important finding: blank regions and `INNER JOIN`

The cleaned billing dataset contains **58 records with empty `RegionId`**. Breakdown:

| ChargeCategory | Records lacking a region |
|---|---:|
| Usage | 47 |
| Tax | 9 |
| Purchase | 1 |
| Credit | 1 |
| **Total** | **58** |

Their combined costs are **$166,315.74 BilledCost** and **$20,582.74 EffectiveCost**. Some charges legitimately have no region (for example, tax); it would be incorrect to invent a geographical assignment.

A local SQLite simulation used the actual cleaned CSV and the same business-key joins implied by the committed models:

| Scenario | Resulting fact rows | BilledCost | EffectiveCost |
|---|---:|---:|---:|
| Keep a distinct blank-region member and map all 58 rows to it | 4,433 | $332,678.83 | $213,887.47 |
| Convert blank region values to SQL `NULL` without mapping an unknown-region dimension member, then use `INNER JOIN` | **4,375** | **$166,363.09** | **$193,304.73** |

**Interpretation:** Gitika reported 4,433 fact rows and 8 region dimension rows, consistent with retaining a blank-region member, but the live MySQL mapping has not been independently inspected. The second scenario is a **sensitivity test**, not an assertion that her current run lost data.

**Recommendation:** Document and preserve an explicit policy for missing regions. Either (a) add a legitimate `Unknown / Not Applicable` region dimension member and map missing-region facts to its key, or (b) retain nullable region keys and use an appropriate `LEFT JOIN`/reporting policy. In both cases, test that all 4,433 billing rows and full costs remain represented. Do not assign a fabricated real region.

## 6. Tests prepared for Gitika

- Six **dbt singular tests**: source-to-output fact completeness, count and cost reconciliation, fact FK coverage, dimension surrogate-key uniqueness, fact primary-key uniqueness and nonblank region coverage.
- `scripts/week2_day4_mysql_dimension_fact_validation.sql`: read-only checks for staging counts, dimension keys, NULL-versus-empty-region storage, joins, costs and region exceptions.
- `scripts/taeyun_week2_day4_dim_fact_audit.py`: standard-library Python script for local CSV comparison, actual SQLite join simulation, JSON output and exception reporting.

Run the dbt tests from a correctly configured `finops_dbt` project using:

```bash
dbt test --select 'path:tests/taeyun'
```

The precise selection path depends on where Gitika places the test files. **No live test results are claimed here.**

## 7. Handoff and next steps

1. Gitika should confirm that her 8 `Dim_Region` rows include a deliberate mapping for blank source regions and inspect any `NULL`/unmatched `Region_Key` values in `Fact_Spend`.
2. After the latest `dbt run`, run the six singular tests and read-only MySQL checks. Confirm 28/10/8/4,433 dimensions/fact **in the live database** and reconcile financial measures.
3. Retain the Week 1 cleaned 26-column CSV as the canonical input; the audit does not rewrite or reassign cost-allocation tags.
4. Decide how new raw data will update the underlying MySQL dimensions/fact: currently the dbt Day 4 models read prepopulated tables.
5. For Day 5 granular unit economics, check that excluded or unmatched records are not silently omitted from provider, service and resource cost aggregates.

## 8. Completion status

**Taeyun's Week 2 Day 4 local QA and handoff: completed.** 14/14 local checks passed. Gitika's live MySQL/dbt regression checks: **provided but not executed here**. No changes have been made to Gitika's GitHub files or live database.

**Attribution:** The FinOps Desk, synthetic *FOCUS Exercise – 2026 Q3*, CC BY 4.0. The dataset is not a real-time feed or actual provider billing data.
