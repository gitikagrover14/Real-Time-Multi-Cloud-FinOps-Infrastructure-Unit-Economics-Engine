# Week 1 · Day 4 — Data Cleaning and Missing Values
**Owner:** Taeyun  
**Project:** Real-Time Multi-Cloud FinOps & Infrastructure Unit Economics Engine  
**Source:** The FinOps Desk, synthetic Q3 2026 FOCUS 1.2 subset (not Kaggle)

## Objective
Inspect and handle missing values, exact duplicates and inconsistent billing entries without changing financial meaning. The cleaned output is intended for Gitika’s star schema integration.

## Method and observed findings
The raw billing CSV contains **4,433 rows** and **26 fields**; the daily orders CSV contains **92 records**. Files were imported with all billing identifiers held as strings. Every source row was checked for exact duplication, required-field completeness, valid dates and decimal precision, and valid JSON in `Tags`.

| Check | Observed result | Treatment |
|---|---:|---|
| Exact duplicate billing rows | 0 | None removed; code excludes only exact repeats if encountered |
| Missing `SubAccountId` | 9 | Leave missing; tax transactions can lack a subaccount |
| Missing `RegionId` | 58 | Leave missing; not every charge belongs to a resource region |
| Missing `ResourceId` | 333 | Preserve; tax, purchase, and unused commitments may lack a resource |
| Missing `Tags` | 10 | Mark **UNALLOCATED_NON_USAGE**, not fabricated |
| Missing commitment ID | 3195 | Optional for non-commitment charges |
| Missing `x_Credits` | 3602 | Provider-specific Google field; do not fill zeros for other providers |

**Tag audit:** 4,423 rows have both team and env tags; 10 non-usage rows have no cost-allocation tags. Their category distribution is **{'Tax': 9, 'Credit': 1}**. There are **0 untagged Usage rows**.

## Cleaning rules
1. Strip leading/trailing whitespace from raw values. A blank optional value becomes SQL `NULL` (and an empty CSV cell); required blanks cause a failure rather than silent correction.
2. Detect duplicates using every one of the original 26 fields, retaining raw source rows for audit. No duplicates were found.
3. Validate all four charge/billing timestamps, ordering, and whether the charge start lies within the billing period.
4. Validate financial amounts as finite, precise decimals; reject unexpected precision rather than rounding.
5. Parse `Tags` as JSON objects; preserve values and flag missing team/environment keys.
6. Retain original `BillingAccountId`, `SubAccountId`, service and region identifiers as text. No inferred tenant, tag, region, resource, or cost is generated.
7. Preserve original source records separately from normalized output in SQLite staging tables.

## Deliverables and validation
- `outputs/data_quality_issues.csv`: **10** unresolved untagged rows and their source-row locations.
- `outputs/data_quality_profile.json`: actual missingness, duplicates, provider counts, charge mix, and source SHA-256 hashes.
- `outputs/focus_cleaned_2026-q3.csv`: source-compatible 26-column cleaned file.
- `outputs/focus_enriched_2026-q3.csv`: cleaned 26 fields plus traceability/allocation flags.
- `outputs/taeyun_ingestion_cleaning.sqlite`: both original and cleaned tables.

**Validation:** raw count = clean count = **4,433**; orders = **92**; integer-cent sums of `ListCost`, `ContractedCost`, `BilledCost` and `EffectiveCost` reconcile with the cleaned data. The script fails on invalid values rather than guessing corrections.

## Coordination
Gitika should use `focus_cleaned_2026-q3.csv` for column-for-column FOCUS ingestion, and `focus_enriched_2026-q3.csv` if she wants `TagTeam`, `TagEnvironment`, `TagAllocationStatus` and source row identifiers. Unallocated tags require an explicit downstream unknown/unallocated classification; they should not be assigned to tenants arbitrarily.

## Limits
The dataset is synthetic, historical and published by The FinOps Desk, not Kaggle. Missing values are not necessarily errors; blank cost-allocation fields are documented, not magically repaired.
