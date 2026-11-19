# Week 1 — Day 6: Cost-Allocation Tag Audit & Data Validation

**Owner:** Taeyun  
**Project:** Real-Time Multi-Cloud FinOps & Infrastructure Unit Economics Engine  
**Source:** FinOps Desk FOCUS exercise (synthetic Q3 2026)  
**Input:** Day 5 cleaned FOCUS CSV, cross-checked with original billing CSV  
**Scope:** Cost-allocation tag inspection and verification; does not redesign Gitika's SQL schema.

## 1. Objective and method

Check every `Tags` field for valid JSON and extract its `team` and `env` allocation attributes. Distinguish legitimate non-resource charges from missing attribution on usage charges. Reconcile original and cleaned costs and preserve all source records. No tags are guessed or manufactured.

## 2. Observed results

| Measure | Verified result |
|---|---:|
| Billing records inspected | 4,433 |
| Valid tags with `team` and `env` | 4,423 |
| Absent tags | 10 |
| Invalid JSON | 0 |
| Incomplete tag objects | 0 |
| Exact duplicate cleaned rows | 0 |
| Reconciliation checks passed | 8 / 8 |

### Missing tags by charge type

- **Adjustment:** 0 untagged records
- **Credit:** 1 untagged records
- **Purchase:** 0 untagged records
- **Tax:** 9 untagged records
- **Usage:** 0 untagged records

Missing tags occur in non-usage billing lines (taxes and credit); the usage lines have tags. Tag-free non-resource charges should not be silently attributed to a business team. These amounts may be held in an explicit `Unallocated` reporting category **derived downstream**, with original tag fields left blank; finance/business rules are needed before applying any allocation percentages.

### Tag-field interpretation

- `Tags` is JSON-formatted text containing keys such as `team` and `env`.
- `allocation_team` and `allocation_env` in the optional audit CSV are extracted reporting helpers; they do not replace original `Tags`.
- Empty helper fields mean **unattributed**, not a verified team/environment.
- Do not interpret provider/service/region as a substitute for actual team ownership.

## 3. Validation performed

- **Row count preserved:** PASS
- **Schema and order preserved:** PASS
- **No exact cleaned duplicates:** PASS
- **Cost and quantity totals reconcile:** PASS
- **All usage rows tagged:** PASS
- **All nonempty tags valid team and env:** PASS
- **Cost currency consistent:** PASS
- **All charge periods parseable:** PASS

The monetary comparison uses exact decimal arithmetic and reconciles `ListCost`, `ContractedCost`, `BilledCost`, `EffectiveCost`, and `PricingQuantity` between the original and Day 5 cleaned inputs. Totals are not interpreted as real-world cloud prices because the dataset is synthetic.

## 4. Gitika integration handoff

1. Continue using `inputs/focus_cleaned_2026-q3.csv` (the **original 26-column layout**) for `Fact_Spend` and dimensions.
2. Optionally use `outputs/focus_tag_audited_2026-q3.csv` when reporting by team/environment; it adds three columns, not schema-replacing edits.
3. The `day6_tag_exceptions.csv` lists records that cannot be attributed to a team based on source tags alone.
4. Preserve `SubAccountId`, `ResourceId`, `RegionId`, and `Tags` blanks where source semantics permit them.
5. In SQL, use explicit `Unallocated` labels only for presentation, not to rewrite the raw source; coordinate tag policy for tax and credits before allocating costs.
6. All financial validation checks have passed; verify any further transformations independently.

## 5. Deliverables

- `scripts/week1_day6_tag_audit.py` — reproducible standard-library Python audit.
- `outputs/day6_validation_results.json` — detailed machine-readable checks and distributions.
- `outputs/day6_tag_exceptions.csv` — unresolved tag exceptions and suggested disposition.
- `outputs/day6_tag_distribution.csv` — counts by team and environment.
- `outputs/focus_tag_audited_2026-q3.csv` — optional tagged view (original 26 fields plus three audited helper fields).
- `inputs/` — source and cleaned CSVs for standalone reproduction, **not necessary to commit again if the team's existing data files are available**.

## 6. Reproduce

From the project root, run:

```bash
python scripts/week1_day6_tag_audit.py inputs/focus_cleaned_2026-q3.csv inputs/focus_exercise_2026-q3.csv
```

**Source attribution:** The FinOps Desk, *FOCUS Analysis Exercise*, CC BY 4.0: https://finopscourse.com/resources/focus-analysis-exercise
