# Week 1 · Day 5 — Data Standardization & Billing Schema Normalization
**Owner:** Taeyun  
**Scope:** Make the FOCUS multi-cloud source consistent while preserving original semantics and a transparent audit trail.

## Standardization performed
- **FOCUS column names:** retain the *exact original 26 source headers* (including `x_Credits`) to avoid breaking Gitika’s `Fact_Spend` and dimension-table mapping. New derived attributes are appended only in the enriched CSV.
- **Dates:** convert charge/billing period values to canonical `YYYY-MM-DDTHH:MM:SSZ` UTC. Add derived `ChargeDate` as `YYYY-MM-DD` for analysis.
- **Costs:** `ListCost`, `ContractedCost`, `BilledCost`, `EffectiveCost` and populated `x_Credits` use fixed **2 decimal places**; `PricingQuantity` uses **4 decimal places**. No float-based currency calculations: SQLite also stores integer-cent and 1/10,000-unit measures for reconciliation.
- **Identifiers:** keep account, subscription, project and resource IDs as text, preventing dropped leading zeroes or numerical coercion.
- **Missingness:** optional empty fields map to `NULL` in staging, and blank cells in exported CSV. Never convert absent provider-specific credits to actual zero.
- **Tags:** parse JSON objects; serialize consistently with sorted keys; create explicit `TagTeam`, `TagEnvironment`, `TagJob`, `TagAllocationStatus` columns in enriched file.
- **Cross-cloud semantics:** retain provider names and charge types as recorded, rather than pretending AWS, Microsoft, and Google workloads or price units are identical. Preserve `BilledCost` separately from `EffectiveCost` (commitment amortization changes their meaning).

## Actual transformation audit
The standardization script compared each canonical value to its original input and counted modified cells. The main changes were:

| Field | Canonicalized cells |
|---|---:|
| `Tags` | 4,423 |

Where changes reflect formatting (for example canonical JSON key ordering or decimal precision), financial amounts remain unchanged. The observed validation profile is saved to `outputs/data_quality_profile.json`.

## Output formats
| File | Purpose | Schema |
|---|---|---|
| `focus_cleaned_2026-q3.csv` | **Recommended Gitika import** | Exactly 26 original FOCUS columns |
| `focus_enriched_2026-q3.csv` | Allocation/traceability analysis | 26 source columns plus 9 derived fields |
| `orders_cleaned_2026-q3.csv` | Unit economics denominator | `date`, `orders` |
| `taeyun_ingestion_cleaning.sqlite` | Auditable raw and cleaned SQL staging | `raw_focus_billing`, `clean_focus_billing`, raw/clean orders, metadata, view `focus_for_star_schema` |

## Checks and results
- Billing rows before/after: **4,433 / 4,433**.
- Daily order rows before/after: **92 / 92**.
- Cloud-provider row counts: AWS = 2675, Google Cloud = 831, Microsoft = 927.
- Monetary reconciliation: **PASSED**, using exact integer cents.
- Dates: 2026-07-01 to 2026-09-30 (92 distinct days).
- Duplicate removal: **none required**.

## Next steps for database owner (Gitika)
Use the 26-column cleaned CSV for direct existing-schema compatibility. Map `(ProviderName, ServiceCategory, ServiceName)` to `Dim_Service`; provider + billing/subaccount context to `Dim_Tenant`; `(ProviderName, RegionId)` to `Dim_Region`; preserve charge amounts and periods in `Fact_Spend`. Choose explicit unknown members for optional region/tenant blanks. Do **not** equate `PricingQuantity` with a common usage unit across services without interpreting `PricingUnit`.

**Important:** 'Standardization' here is data-format and schema consistency, **not** construction of Gitika's final dimensional star schema or equivalence of provider price models.
