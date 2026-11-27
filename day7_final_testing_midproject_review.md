# Week 2 · Day 7 — Final Testing, Documentation & Mid-Project Review

**Prepared by:** Taeyun (data ingestion, data quality, validation support)  
**Review date:** 27 November 2026  
**Project:** Real-Time Multi-Cloud FinOps & Infrastructure Unit Economics Engine

## Executive summary

Week 2 progressed from Gitika's database connection and staging model setup to dimensional dbt models and service/resource unit economics. I independently checked the cleaned data and the expected transformations, prepared reusable MySQL/dbt tests, and consolidated the evidence for the mid-project review.

**Validated locally:** **34/34 checks PASS** across 4,433 billing rows, the original 26 FOCUS columns, 92 order records, cost/quantity reconciliation, tags and key mapping. **Not independently validated:** end-to-end live MySQL/dbt execution, the renamed backup source tables and Gitika's production outputs. Her reported successful model runs are team updates, not command output supplied to this QA package.

## Week 2 delivery overview

| Day | Gitika's primary development | Taeyun's data/QA contribution | Completion basis |
|---|---|---|---|
| 1 | dbt + MySQL environment initialization | Source-readiness check and data contract | Local data verified; Gitika reports `dbt debug` succeeded |
| 2 | dbt source configuration | Source field mapping and compatibility checks | Local QA and documentation |
| 3 | `stg_billing` transformations | Data types, date, NULL, tag and cost QA | Local QA; live model must be compared |
| 4 | 3 dimension models + `fact_spend` | FK and dimension integrity, region-loss risk | Local model contract analysis |
| 5 | Service/resource unit economics | Group-level cost reconciliations; resource gap | 19/19 earlier local checks passed |
| 6 | Pipeline execution and validation | Consolidated 34-check local audit + ten dbt tests and read-only MySQL queries | **Local PASS / live PENDING** |
| 7 | End-to-end testing and documents | Final status report, testing matrix, Gitika runbook and review notes | **Documentation ready / live sign-off PENDING** |

## Mid-project review scorecard

| Area | Evidence | Review status |
|---|---|---|
| Input quality | 4,433 cleaned billing rows, 0 exact duplicates, 26 source columns | Verified locally |
| Cost integrity | $332,678.83 BilledCost, $213,887.47 EffectiveCost unchanged | Verified locally |
| Tag completeness | 4,423 valid tagged rows; 10 tax/credit rows with no team attribution | Verified locally |
| Database shape | 28 service, 10 tenant, 8 region dimensions; expected 4,433 fact rows | Verified in local reconstruction; Gitika reported live counts earlier |
| Service unit economics | 33 distinct service/currency/unit groups expected | Independently calculated |
| Resource unit economics | 44 groups; excludes 333 records / $38,597.49 EffectiveCost | Independently calculated |
| MySQL/dbt run | Gitika reported successful runs; local logs not provided | Joint verification pending |
| dbt tests | `schema.yml` exists; ten further tests prepared | Requires execution in Gitika's project |
| Reproducible repository | Main branch lacks complete dbt project scaffold | Requires Gitika to publish sanitized scaffold |
| Streaming real-time input | Synthetic 2026 Q3 batch data only | Future work |

## Key technical findings to explain during the review

**1. Original monetary amounts are preserved.** Source, cleaned and tag-audited data were checked using exact decimal arithmetic. The difference between BilledCost and EffectiveCost is expected because the synthetic dataset models AWS/Azure commitment amortization and Google synthetic credits.

**2. Missing values are not automatically errors.** Tax rows omit some subaccounts, and other legitimate non-resource charges omit ResourceId or RegionId. Keep the corresponding billing costs in Fact_Spend; report their missing attribution explicitly.

**3. Service vs resource cost totals answer different questions.** The resource model is intentionally limited to identifiable resources, so $38,597.49 in EffectiveCost must be reconciled separately. A total-cloud-spend dashboard should use the complete fact or service rollup, not the resource-only rollup.

**4. Existing models depend on previously loaded MySQL tables.** The current fact model selects from `source('finops_raw','Fact_Spend')`; it is not rebuilt directly from `ref('stg_billing')`. Confirm that cleaned input was used and no duplicates were introduced by repeated loading.

**5. Real-time functionality remains out of scope of the existing prototype.** Current data are synthetic daily Q3 2026 billing; the team should distinguish a successful dbt batch pipeline from continuous ingestion. This is a recommended next-stage development task, not a Week 2 accomplishment.

## Five-minute presentation outline

1. **Project and Week 2 goal (30 sec):** Build repeatable multi-cloud billing transformations and unit economics models.
2. **Data readiness (1 min):** FOCUS Q3 2026 source, three providers, 4,433 records, preserved costs; describe tag exceptions.
3. **Architecture (1 min):** MySQL billing source → staging → fact/dimensions → service and resource cost views. Mention that the fact model currently reads the existing source fact table.
4. **Unit economics (1 min):** per-pricing-unit ratios; totals, 333 missing resource IDs, and missing-resource reconciliation.
5. **Validation and next steps (1.5 min):** local 34/34 passed, pending live dbt/MySQL execution evidence, backup identifier check, repository scaffold, later true real-time ingestion.

## Evidence Gitika should provide for final live sign-off

- The commands and output for `dbt debug`, `dbt build` and `dbt test` from the active `finops_dbt` directory (omit credentials).
- A summary of actual MySQL `stg_billing` / `dbt_fact_spend` counts, dimensions, and service/resource group counts.
- Query results showing BilledCost and EffectiveCost match the local expected values.
- `information_schema` confirmation of `dim_*__dbt_backup` source tables.
- Any failed or skipped singular tests, with explanations and fixes.
- A sanitized committed `dbt_project.yml` and organized `models/` and `tests/` directories (Gitika's ownership).

## Completion and ownership boundary

Taeyun has completed Day 7 **documentation, offline validation and handoff**. Gitika must still execute the pipeline and test suite in the real environment for joint Week 2 sign-off. The package deliberately does not claim successful live model execution or silently alter her SQL models.

**Data source/license:** The FinOps Desk, synthetic FOCUS Exercise, CC BY 4.0. https://finopscourse.com/resources/focus-analysis-exercise
