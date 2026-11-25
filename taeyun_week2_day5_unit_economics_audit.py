#!/usr/bin/env python3
"""Taeyun Week 2 Day 5 — independent local QA for dbt unit economics models.

This is an offline parity/reconciliation check using the source and Week 1 cleaned
CSV files. It does NOT query or execute Gitika's live MySQL/dbt warehouse.

Requires Python >=3.9, standard library only.
Example:
 python scripts/taeyun_week2_day5_unit_economics_audit.py \\
   --raw focus_exercise_2026-q3.csv --cleaned focus_cleaned_2026-q3.csv \\
   --out outputs/taeyun/week2
"""
import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from decimal import Decimal, getcontext
from pathlib import Path

getcontext().prec = 32
MONEY = ("ListCost", "ContractedCost", "BilledCost", "EffectiveCost")
SERVICE_ATTR = ("ProviderName", "InvoiceIssuerName", "ServiceCategory", "ServiceName")
SERVICE_GRAIN = SERVICE_ATTR + ("BillingCurrency", "PricingUnit")
RESOURCE_GRAIN = SERVICE_ATTR + ("ResourceId", "BillingCurrency", "PricingUnit")
EXPECTED_SOURCE_COLUMNS = ("BillingAccountId", "SubAccountId", "ProviderName", "InvoiceIssuerName", "ServiceCategory", "ServiceName", "RegionId", "ChargeCategory", "ChargeFrequency", "ChargePeriodStart", "ChargePeriodEnd", "BillingPeriodStart", "BillingPeriodEnd", "BillingCurrency", "ListCost", "ContractedCost", "BilledCost", "EffectiveCost", "PricingQuantity", "PricingUnit", "CommitmentDiscountId", "CommitmentDiscountCategory", "CommitmentDiscountStatus", "ResourceId", "Tags", "x_Credits")


def read_data(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader=csv.DictReader(f)
        fields=tuple(reader.fieldnames or [])
        rows=list(reader)
    if fields != EXPECTED_SOURCE_COLUMNS:
        raise ValueError(f"Expected 26 FOCUS fields in original order; observed {fields}")
    return rows


def hash_file(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for part in iter(lambda:f.read(1<<20),b""):
            h.update(part)
    return h.hexdigest()


def d(x):
    return Decimal((x or "").strip() or "0")


def fstr(v, places=2):
    return str(v.quantize(Decimal("1").scaleb(-places)))


def empty_bucket():
    return dict(rows=0,cost={c:Decimal('0') for c in MONEY},qty=Decimal('0'),n_qty=0,resources=set(),blank_resource_rows=0)


def add(bucket,row):
    bucket['rows']+=1
    for c in MONEY: bucket['cost'][c]+=d(row[c])
    q=row['PricingQuantity'].strip()
    if q:
        bucket['qty']+=d(q)
        bucket['n_qty']+=1
    rid=row['ResourceId'].strip()
    if rid: bucket['resources'].add(rid)
    else: bucket['blank_resource_rows']+=1


def to_flat(key,bucket,grain,service=False):
    out=dict(zip(grain,key))
    out['billing_rows']=bucket['rows']
    for c in MONEY:out['total_'+c.lower().replace('cost','_cost')]=fstr(bucket['cost'][c])
    out['total_pricing_quantity']=fstr(bucket['qty'],4) if bucket['n_qty'] else ''
    # SQL 'SUM(...) IS NULL OR SUM(...) = 0 THEN NULL'
    out['effective_cost_per_unit']=(fstr(bucket['cost']['EffectiveCost']/bucket['qty'],8) if bucket['n_qty'] and bucket['qty']!=0 else '')
    if service:
        out['distinct_nonblank_resource_ids']=len(bucket['resources'])
        out['has_blank_resource_id']=int(bucket['blank_resource_rows']>0)
        # MySQL COUNT(DISTINCT ResourceId) counts '' if blank IDs persist as strings.
        out['possible_sql_total_resources_if_blank_is_empty_string']=len(bucket['resources'])+int(bucket['blank_resource_rows']>0)
    return out


def write_csv(path, rows, headers):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=headers,extrasaction='ignore')
        w.writeheader()
        w.writerows(rows)


def audit(raw_path,clean_path,out):
    raw=read_data(raw_path)
    cleaned=read_data(clean_path)
    if not cleaned:raise ValueError('No cleaned rows')
    service=defaultdict(empty_bucket)
    resource=defaultdict(empty_bucket)
    excluded=defaultdict(empty_bucket)
    by_provider=defaultdict(empty_bucket)
    resource_rows=0
    quantity_missing=0
    for row in cleaned:
        srv=tuple(row[c].strip() for c in SERVICE_GRAIN)
        res=tuple(row[c].strip() for c in RESOURCE_GRAIN)
        add(service[srv],row)
        add(by_provider[row['ProviderName'].strip()],row)
        if row['ResourceId'].strip():
            add(resource[res],row)
            resource_rows+=1
        else: add(excluded[(row['ProviderName'].strip(),row['ChargeCategory'].strip())],row)
        quantity_missing+=not bool(row['PricingQuantity'].strip())
    cost_total=lambda rows: {c:sum((d(r[c]) for r in rows),Decimal('0')) for c in MONEY}
    raw_sums,clean_sums=cost_total(raw),cost_total(cleaned)
    resource_sums={c:sum((v['cost'][c] for v in resource.values()),Decimal('0')) for c in MONEY}
    excl_sums={c:sum((v['cost'][c] for v in excluded.values()),Decimal('0')) for c in MONEY}
    service_sums={c:sum((v['cost'][c] for v in service.values()),Decimal('0')) for c in MONEY}
    raw_q=sum((d(r['PricingQuantity']) for r in raw),Decimal('0'))
    clean_q=sum((d(r['PricingQuantity']) for r in cleaned),Decimal('0'))
    resource_q=sum((v['qty'] for v in resource.values()),Decimal('0'))
    excluded_q=sum((v['qty'] for v in excluded.values()),Decimal('0'))
    service_q=sum((v['qty'] for v in service.values()),Decimal('0'))
    missing_count=len(cleaned)-resource_rows
    svc_flat=[to_flat(k,v,SERVICE_GRAIN,True) for k,v in sorted(service.items())]
    res_flat=[to_flat(k,v,RESOURCE_GRAIN) for k,v in sorted(resource.items())]
    excluded_flat=[]
    for k,b in sorted(excluded.items()):
        line={'ProviderName':k[0],'ChargeCategory':k[1]}
        line.update(to_flat((),b,()))
        excluded_flat.append(line)
    service_headers=list(svc_flat[0]);resource_headers=list(res_flat[0]);excluded_headers=list(excluded_flat[0])
    write_csv(out/'day5_service_unit_economics_local.csv',svc_flat,service_headers)
    write_csv(out/'day5_resource_unit_economics_local.csv',res_flat,resource_headers)
    write_csv(out/'day5_resource_exclusion_bridge.csv',excluded_flat,excluded_headers)

    checks={
      'source_has_26_expected_fields':len(cleaned[0])==26 and len(raw[0])==26,
      'raw_clean_row_count_equal':len(raw)==len(cleaned),
      'expected_4433_rows':len(cleaned)==4433,
      'no_duplicate_cleaned_records':len({tuple(r[c] for c in EXPECTED_SOURCE_COLUMNS) for r in cleaned})==len(cleaned),
      'monetary_totals_raw_clean_equal':raw_sums==clean_sums,
      'pricing_quantity_raw_clean_equal':raw_q==clean_q,
      'service_groups_partition_all_rows':sum(v['rows'] for v in service.values())==len(cleaned),
      'service_cost_totals_match_clean_source':service_sums==clean_sums,
      'service_pricing_quantity_matches_clean_source':service_q==clean_q,
      'resource_groups_include_only_identified_rows':sum(v['rows'] for v in resource.values())==resource_rows,
      'excluded_plus_resource_row_counts_equal_all':resource_rows+missing_count==len(cleaned),
      'resource_plus_excluded_costs_equal_source':all(resource_sums[c]+excl_sums[c]==clean_sums[c] for c in MONEY),
      'resource_plus_excluded_quantity_equal_source':resource_q+excluded_q==clean_q,
      'expected_28_distinct_service_entities':len({tuple(r[c] for c in SERVICE_ATTR) for r in cleaned})==28,
      'cost_per_unit_equals_grouped_effective_divided_by_quantity':all((x['effective_cost_per_unit']=='' if not b['n_qty'] or b['qty']==0 else abs(d(x['effective_cost_per_unit'])-b['cost']['EffectiveCost']/b['qty'])<Decimal('0.00000001')) for x,b in list(zip(svc_flat,[service[k] for k in sorted(service)]))+list(zip(res_flat,[resource[k] for k in sorted(resource)]))),
      'zero_denominator_rates_are_blank':all(x['effective_cost_per_unit']=='' for x in svc_flat+res_flat if x['total_pricing_quantity'] in ('','0.0000')),
      'grouped_by_currency_and_pricing_unit':all('BillingCurrency' in x and 'PricingUnit' in x for x in svc_flat+res_flat),
      'no_duplicate_service_group_keys':len(svc_flat)==len({tuple(x[c] for c in SERVICE_GRAIN) for x in svc_flat}),
      'no_duplicate_resource_group_keys':len(res_flat)==len({tuple(x[c] for c in RESOURCE_GRAIN) for x in res_flat}),
    }
    # Provider-level reconciliation and flags for model documentation
    provider_rows=[]
    for name,b in sorted(by_provider.items()):
        provider_rows.append({'provider':name,'rows':b['rows'],**{c:fstr(b['cost'][c]) for c in MONEY}})
    model_limits={
      'excluded_resource_rows':missing_count,
      'excluded_resource_cost_usd':{c:fstr(excl_sums[c]) for c in MONEY},
      'excluded_resource_quantity':fstr(excluded_q,4),
      'excluded_pct_effective_cost':fstr((excl_sums['EffectiveCost']/clean_sums['EffectiveCost']*100),2),
      'blank_resource_service_groups':sum(b['blank_resource_rows']>0 for b in service.values()),
      'service_groups_with_no_or_zero_qty':sum(b['n_qty']==0 or b['qty']==0 for b in service.values()),
      'resource_groups_with_no_or_zero_qty':sum(b['n_qty']==0 or b['qty']==0 for b in resource.values()),
      'quantity_missing_rows':quantity_missing,
      'currencies':sorted({r['BillingCurrency'].strip() for r in cleaned}),
      'pricing_units':sorted({r['PricingUnit'].strip() for r in cleaned}),
      'service_resource_count_may_include_blank_string':'COUNT(DISTINCT f.ResourceId) includes empty string if persisted as non-NULL; propose NULLIF(TRIM(ResourceId), \'\')',
      'resource_model_excludes_unidentified_costs':'Resource model filters ResourceId NULL/blank. Reconcile to resource-eligible fact only; explain omitted costs explicitly.',
      'aggregate_unit_rate_not_order_unit_economics':'EffectiveCost / PricingQuantity is per source pricing unit, not per business order. Do not compare pricing units directly.',
    }
    report={
       'scope':'Local Week 2 Day 5 QA against FOCUS CSV and Gitika main-branch service_unit_economics.sql/resource_unit_economics.sql logic; NOT a live MySQL or dbt run',
       'source_files':{'raw':{'name':raw_path.name,'sha256':hash_file(raw_path)},'cleaned':{'name':clean_path.name,'sha256':hash_file(clean_path)}},
       'row_counts':{'raw':len(raw),'cleaned':len(cleaned),'resource_identified':resource_rows,'resource_unidentified':missing_count},
       'expected_local_model_group_counts':{'service_unit_economics':len(service),'resource_unit_economics':len(resource)},
       'distinct_service_entities':len({tuple(r[c] for c in SERVICE_ATTR) for r in cleaned}),
       'totals_usd':{'source':{c:fstr(clean_sums[c]) for c in MONEY},'resource_identified':{c:fstr(resource_sums[c]) for c in MONEY},'resource_unidentified':{c:fstr(excl_sums[c]) for c in MONEY}},
       'pricing_quantity_totals':{'source':fstr(clean_q,4),'resource_identified':fstr(resource_q,4),'resource_unidentified':fstr(excluded_q,4)},
       'providers':provider_rows,'observations':model_limits,
       'checks':checks,'checks_passed':sum(checks.values()),'checks_total':len(checks),
       'status':'PASS' if all(checks.values()) else 'FAIL',
       'limitations':['Assumes Gitika fact_spend contains all 4,433 source rows as stated in her Day 4 message. Must verify via live query.', 'No live connection, dbt debug or dbt run was made; SQL scripts supplied for Gitika to execute.', 'Local grouping uses observed cleaned CSV and mirrors group-by columns; MySQL precision and NULL/string behaviors must be checked separately.', 'Synthetic daily Q3 2026 data; no real time ingestion or provider price benchmarking.']
    }
    p=out/'day5_unit_economics_validation.json'
    p.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    if not all(checks.values()):raise AssertionError({k:v for k,v in checks.items() if not v})
    return report


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--raw',type=Path,required=True)
    ap.add_argument('--cleaned',type=Path,required=True)
    ap.add_argument('--out',type=Path,default=Path('outputs/taeyun/week2'))
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    result=audit(a.raw,a.cleaned,a.out)
    print('Validation:',result['status'],result['checks_passed'],'/',result['checks_total'])
    print('Service groups:',result['expected_local_model_group_counts']['service_unit_economics'])
    print('Resource groups:',result['expected_local_model_group_counts']['resource_unit_economics'])
    print('Unidentified resource spend: $',result['totals_usd']['resource_unidentified']['EffectiveCost'])


if __name__=='__main__': main()
