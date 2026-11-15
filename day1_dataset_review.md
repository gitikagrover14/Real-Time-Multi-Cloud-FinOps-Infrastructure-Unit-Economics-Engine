# Week 1 / Day 1 — Dataset Review & Selection

**Owner:** Taeyun  
**Project:** Real-Time Multi-Cloud FinOps & Infrastructure Unit Economics Engine  
**Status:** Dataset reviewed; suitable for the prototype subject to approval of non-Kaggle sourcing.

## Objective
Evaluate the team's proposed multi-cloud billing dataset for ingestion, analysis and the subsequent SQL dimensional model. This document concerns dataset selection, not SQL schema implementation.

## Selected dataset

| Item | Observed / documented value |
|---|---|
| Publisher | The FinOps Desk |
| Source | https://finopscourse.com/resources/focus-analysis-exercise |
| Billing file | `focus_exercise_2026-q3.csv` |
| Business metric file | `northwind_orders_2026-q3.csv` |
| Records | **4,433** billing rows; **92** daily order rows |
| Source fields | **26** billing columns |
| Period | 1 July–30 September 2026 (Q3; 92 calendar days) |
| Providers | AWS (2,675), Microsoft/Azure (927), Google Cloud (831) |
| Billing schema | Practical subset of FOCUS 1.2 field names + `x_Credits` extension |
| Provenance | Synthetic training data for the fictional Northwind Analytics company |
| License | CC BY 4.0, attribution to The FinOps Desk |

The 26 billing columns include account details, provider/service/region identifiers, charge classifications and periods, cost measurements, resource identifiers, commitments, and tags. The orders file has two fields: `date` and `orders`.

## Selection decision

**Recommended for the project prototype.** Its standardized multi-cloud column structure can be ingested and profiled, and its service, tenant and region attributes can support Gitika's proposed `Fact_Spend`, `Dim_Service`, `Dim_Tenant` and `Dim_Region` design. The separate orders data can later support cost-per-order analysis if aggregated at compatible granularity.

## Suitability and limitations

- **Strength:** Three providers represented in one billing file, with recognizable FOCUS measures such as `BilledCost` and `EffectiveCost`.
- **Strength:** Charge, account, service, region and resource fields support downstream dimensional analysis.
- **Strength:** No confidential customer data; suitable for a demonstrable prototype.
- **Limitation:** **Not from Kaggle.** Confirm with the instructor whether the original Kaggle-only requirement can be waived; otherwise source an approved Kaggle replacement before treating dataset selection as finalized.
- **Limitation:** Synthetic and daily-granularity historical records, not a real-time API or stream. A separate ingestion design will be needed for the project's eventual real-time objective.
- **Limitation:** FOCUS 1.2-style *subset*, not a complete FOCUS 1.2 compliance certification; provider-specific `x_Credits` is simplified.
- **Limitation:** These providers have different synthetic workloads; their total costs do not prove relative provider price competitiveness.

## Deliverable and handoff

Selected candidate: `focus_exercise_2026-q3.csv`. Day 2 profiling and the accompanying field inventory document its columns for Gitika's schema work. The source file remains unmodified at this stage. **Data ingestion, cleaning and normalization are scheduled for Days 3–7 and are not claimed here.**

## Source attribution
The FinOps Desk, *FOCUS analysis exercise*, https://finopscourse.com/resources/focus-analysis-exercise (CC BY 4.0). Dataset README supplied with the source files.
