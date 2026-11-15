# Week 1 / Day 2 — Data Understanding & Initial Analysis

**Owner:** Taeyun  
**Input:** Original `focus_exercise_2026-q3.csv`, `northwind_orders_2026-q3.csv` and publisher README.  
**Scope:** Exploratory source profiling before transformations.

## Dataset structure and observed quality

| Check | Finding |
|---|---|
| Billing rows and columns | **4,433 rows × 26 columns** |
| Orders rows and columns | **92 rows × 2 columns** |
| Billing record duplicates (exact, across all 26 fields) | **0** |
| Provider distribution | AWS: **2,675**; Microsoft: **927**; Google Cloud: **831** |
| Billing-period coverage | Q3 2026 |
| Billing currency values | USD |
| Original `BilledCost` total | **332,678.83** (source currency) |
| Original `EffectiveCost` total | **213,887.47** (source currency) |

All 26 original CSV columns were loaded **as strings for the inspection**, preventing accidental conversion of account identifiers or empty strings. The logical types below are recommendations, not transformations already applied.

## Important field groups

- **Measures:** `ListCost`, `ContractedCost`, `BilledCost`, `EffectiveCost` (fixed-precision decimal monetary values); `PricingQuantity` (decimal quantity); `x_Credits` (provider-specific credit amount).
- **Charge and date attributes:** `ChargeCategory`, `ChargeFrequency`, `ChargePeriodStart`, `ChargePeriodEnd`, `BillingPeriodStart`, `BillingPeriodEnd`, `BillingCurrency`.
- **Service candidates:** `ProviderName`, `ServiceCategory`, `ServiceName` → potential `Dim_Service` attributes.
- **Tenant candidates:** `BillingAccountId`, `SubAccountId` → potential `Dim_Tenant` attributes. Account IDs must be retained as text.
- **Region candidate:** `RegionId` → potential `Dim_Region`; codes are provider-specific and can be missing.
- **Resource / allocation:** `ResourceId`, `Tags` (JSON string), and commitment discount fields. Team/environment tags may later be parsed from `Tags`.
- **Business metric:** `northwind_orders_2026-q3.csv` has daily `date` and integer `orders`. Combine with billing after aggregation to common date granularity; avoid row-to-row joins that multiply order counts.

## Blank-value inventory (unmodified source)

| Source field | Blank cells |
|---|---:|
| `SubAccountId` | 9 |
| `RegionId` | 58 |
| `PricingQuantity` | 58 |
| `PricingUnit` | 58 |
| `CommitmentDiscountId` | 3,195 |
| `CommitmentDiscountCategory` | 3,195 |
| `CommitmentDiscountStatus` | 3,199 |
| `ResourceId` | 333 |
| `Tags` | 10 |
| `x_Credits` | 3,602 |

**Interpretation:** Blank does not always mean defective. For example, tax rows can lack `SubAccountId`, and certain commitment/adjustment entries can lack a `ResourceId` or region. `x_Credits` is intentionally absent outside Google Cloud. These need conditional rules on Days 4–6 rather than blanket imputation. Cost-allocation tags are blank in **10** rows; retain/flag unallocated charges instead of fabricating owners.

## Schema recommendations for Gitika (not final SQL design)

| Target | Source fields to consider | Note |
|---|---|---|
| `Fact_Spend` | Cost measures, quantity, periods, charge classification, resource and commitment references | Maintain source-level billing grain and monetary precision |
| `Dim_Service` | Provider, service name, service category | Service names may overlap across providers; consider provider + service key |
| `Dim_Tenant` | Billing account, subaccount | Represent missing subaccounts with an explicit unknown/unassigned member if needed |
| `Dim_Region` | Provider, region ID | Region identifiers may repeat across providers; account for missing region |

**Coordination:** Agree on handling unknown dimension keys and whether to retain column names in original FOCUS `PascalCase` (recommended for raw staging) or expose standardized aliases for downstream SQL. Maintain a source-to-target mapping instead of silently changing field names.

## Checks to carry into subsequent days

1. Import CSVs without loss of 4,433 billing rows and 92 orders.
2. Preserve original billing cost sums after cleaning, excluding explicitly documented corrections.
3. Validate date/time parsing and decimal precision; preserve source identifiers as strings.
4. Classify nulls by charge category/provider and identify invalid tag JSON before imputing anything.
5. Check downstream SQL JOIN cardinality to prevent inflated monetary totals.

**Scope boundary:** This document is Day 2 source profiling only. No rows were removed, missing values filled, or billing values modified during this analysis.

## Companion inventory
[`day2_field_inventory.csv`](day2_field_inventory.csv) lists all **26** fields, suggested logical types, meanings, missing counts, distinct nonblank counts and potential star-schema mappings.

## Source attribution
The FinOps Desk, *FOCUS analysis exercise*, https://finopscourse.com/resources/focus-analysis-exercise (CC BY 4.0). Original dataset and accompanying README.
