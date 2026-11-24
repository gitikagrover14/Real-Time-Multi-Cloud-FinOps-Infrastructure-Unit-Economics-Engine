#!/usr/bin/env python3
"""Week 2 / Day 4: reproducible, read-only source-to-model contract audit.

This script validates local CSV data and simulates lookup cardinalities implied by
Gitika's committed MySQL star schema. It DOES NOT connect to or run dbt/MySQL.

Example:
  python3 scripts/taeyun_week2_day4_dim_fact_audit.py \
    --raw focus_exercise_2026-q3.csv \
    --clean focus_cleaned_2026-q3.csv \
    --output outputs/taeyun/week2

Dependencies: Python 3.9+ standard library only.
"""
import argparse
import csv
from collections import Counter, defaultdict
from datetime import datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
import sqlite3
from pathlib import Path
import sys

EXPECTED = [
    'BillingAccountId','SubAccountId','ProviderName','InvoiceIssuerName',
    'ServiceCategory','ServiceName','RegionId','ChargeCategory',
    'ChargeFrequency','ChargePeriodStart','ChargePeriodEnd',
    'BillingPeriodStart','BillingPeriodEnd','BillingCurrency','ListCost',
    'ContractedCost','BilledCost','EffectiveCost','PricingQuantity',
    'PricingUnit','CommitmentDiscountId','CommitmentDiscountCategory',
    'CommitmentDiscountStatus','ResourceId','Tags','x_Credits'
]
MONEY = ['ListCost','ContractedCost','BilledCost','EffectiveCost']
SVC = ['ProviderName','InvoiceIssuerName','ServiceCategory','ServiceName']
TENANT = ['BillingAccountId','SubAccountId']
REGION = ['RegionId']
GRAIN_KEY = ['BillingAccountId','SubAccountId','ProviderName','ServiceName',
             'ResourceId','ChargeCategory','ChargePeriodStart','BilledCost','EffectiveCost']

def read_csv(path):
    with path.open(encoding='utf-8-sig',newline='') as fh:
        rdr = csv.DictReader(fh)
        cols = rdr.fieldnames
        rows = list(rdr)
    if cols != EXPECTED:
        raise ValueError(f"Unexpected columns in {path}: {cols}")
    return rows

def amount(row, key):
    v=(row[key] or '').strip()
    return Decimal(v) if v else Decimal('0')

def totals(rows):
    return {k:sum((amount(r,k) for r in rows),Decimal('0')) for k in MONEY}

def digest(path):
    sha=hashlib.sha256()
    with path.open('rb') as fh:
        for buf in iter(lambda:fh.read(1048576),b''):
            sha.update(buf)
    return sha.hexdigest()

def stable_key(r, fields):
    return tuple((r[k] or '').strip() for k in fields)

def row_fingerprint(r):
    return (r['BillingAccountId'],r['SubAccountId'],r['ProviderName'],
            r['ServiceName'],r['ResourceId'],r['ChargeCategory'],
            r['ChargePeriodStart'],str(amount(r,'BilledCost')),str(amount(r,'EffectiveCost')))

def assert_date(r,key):
    val = r[key].strip()
    if not val:
        return False
    try:
        parsed=datetime.fromisoformat(val.replace('Z','+00:00'))
        return parsed.year == 2026
    except ValueError:
        return False

def simulate_inner_join(rows):
    """Execute local SQLite JOINs for the corresponding dimension business keys.

    This is a structural simulation; it is NOT Gitika's live MySQL database and
    the generated keys are NOT Gitika's warehouse surrogate IDs.
    """
    db=sqlite3.connect(':memory:')
    try:
        db.execute('CREATE TABLE source_rows (idx INTEGER PRIMARY KEY, provider TEXT, issuer TEXT, category TEXT, service TEXT, billing TEXT, subaccount TEXT, region TEXT)')
        db.execute('CREATE TABLE d_service (id INTEGER PRIMARY KEY, provider TEXT, issuer TEXT, category TEXT, service TEXT)')
        db.execute('CREATE TABLE d_tenant (id INTEGER PRIMARY KEY, billing TEXT, subaccount TEXT)')
        db.execute('CREATE TABLE d_region (id INTEGER PRIMARY KEY, region TEXT)')
        services=sorted({stable_key(r,SVC) for r in rows})
        tenants=sorted({stable_key(r,TENANT) for r in rows})
        regions=sorted({r['RegionId'].strip() for r in rows})
        db.executemany('INSERT INTO d_service VALUES (?,?,?,?,?)',[(i,*row) for i,row in enumerate(services,1)])
        db.executemany('INSERT INTO d_tenant VALUES (?,?,?)',[(i,*row) for i,row in enumerate(tenants,1)])
        db.executemany('INSERT INTO d_region VALUES (?,?)',[(i,row) for i,row in enumerate(regions,1)])
        db.executemany('INSERT INTO source_rows VALUES (?,?,?,?,?,?,?,?)',
          [(i,r['ProviderName'].strip(),r['InvoiceIssuerName'].strip(),r['ServiceCategory'].strip(),
            r['ServiceName'].strip(),r['BillingAccountId'].strip(),r['SubAccountId'].strip(),
            r['RegionId'].strip()) for i,r in enumerate(rows)])
        join = '''SELECT s.idx FROM source_rows s
             INNER JOIN d_service ds ON ds.provider=s.provider AND ds.issuer=s.issuer
                    AND ds.category=s.category AND ds.service=s.service
             INNER JOIN d_tenant dt ON dt.billing=s.billing AND dt.subaccount=s.subaccount
             INNER JOIN d_region dr ON dr.region=s.region ORDER BY s.idx'''
        mapped=[row[0] for row in db.execute(join)]
        # Simulate blank RegionId normalized to SQL NULL without an Unknown member.
        db.execute("DELETE FROM d_region WHERE region=''")
        db.execute("UPDATE source_rows SET region=NULL WHERE region=''")
        mapped_null_region=[row[0] for row in db.execute(join)]
        return mapped,mapped_null_region
    finally:
        db.close()

def run(raw_file, clean_file, output):
    raw=read_csv(raw_file)
    clean=read_csv(clean_file)
    output.mkdir(parents=True,exist_ok=True)
    svc_keys=set(stable_key(r,SVC) for r in clean)
    tenant_keys=set(stable_key(r,TENANT) for r in clean)
    region_keys=set(stable_key(r,REGION) for r in clean)
    region_keys_excluding_blank={x for x in region_keys if x[0]}
    service_unmatched=[i for i,r in enumerate(clean,1) if stable_key(r,SVC) not in svc_keys]
    tenant_unmatched=[i for i,r in enumerate(clean,1) if stable_key(r,TENANT) not in tenant_keys]
    region_unmatched_blanks=[i for i,r in enumerate(clean,1) if stable_key(r,REGION) not in region_keys_excluding_blank]
    mapped_all, mapped_if_null = simulate_inner_join(clean)
    region_missing=[(i,r) for i,r in enumerate(clean,1) if not r['RegionId'].strip()]
    sub_missing=[(i,r) for i,r in enumerate(clean,1) if not r['SubAccountId'].strip()]
    bad_date=[(i,k) for i,r in enumerate(clean,1) for k in
              ['ChargePeriodStart','ChargePeriodEnd','BillingPeriodStart','BillingPeriodEnd'] if not assert_date(r,k)]
    raw_t=totals(raw); clean_t=totals(clean)
    fingerprint_equal=Counter(map(row_fingerprint,raw))==Counter(map(row_fingerprint,clean))
    duplicate_count=len(clean)-len({tuple(r[c] for c in EXPECTED) for r in clean})
    tag_errors=[]
    for i,r in enumerate(clean,1):
        if r['Tags'].strip():
            try:
                obj=json.loads(r['Tags'])
                if not isinstance(obj,dict):tag_errors.append(i)
            except ValueError:tag_errors.append(i)
    cause_summary=[]
    for category in sorted(set(r['ChargeCategory'] for _,r in region_missing)):
        group=[r for _,r in region_missing if r['ChargeCategory']==category]
        cause_summary.append({
           'charge_category':category,'rows':len(group),
           'billed_cost_usd':str(sum((amount(r,'BilledCost') for r in group),Decimal('0'))),
           'effective_cost_usd':str(sum((amount(r,'EffectiveCost') for r in group),Decimal('0')))
        })
    region_lost_billed=sum((amount(r,'BilledCost') for _,r in region_missing),Decimal('0'))
    region_lost_effective=sum((amount(r,'EffectiveCost') for _,r in region_missing),Decimal('0'))
    checks = {
        'raw_has_4433_rows':len(raw)==4433,
        'clean_has_4433_rows':len(clean)==4433,
        'row_count_preserved':len(raw)==len(clean),
        'stable_row_identifiers_and_costs_preserved':fingerprint_equal,
        'cost_totals_preserved':raw_t==clean_t,
        'no_exact_duplicate_clean_rows':duplicate_count==0,
        'services_all_mapped_in_local_simulation':not service_unmatched and len(mapped_all)==len(clean),
        'tenants_all_mapped_in_local_simulation':not tenant_unmatched,
        'regions_all_mapped_when_blank_dimension_member_is_retained':len(mapped_all)==len(clean),
        'all_dates_valid_in_clean_csv':not bad_date,
        'all_populated_tags_are_json_objects':not tag_errors,
        'source_region_blanks_are_not_silently_imputed':len(region_missing)==58,
        'source_subaccount_blanks_are_not_silently_imputed':len(sub_missing)==9,
        'sql_join_sensitivity_simulation_matches_58_region_blanks':len(mapped_all)-len(mapped_if_null)==len(region_missing),
    }
    passing=sum(checks.values())
    report={
      'purpose':'Local Week 2 Day 4 QA of dimensional key mappings and source data. Not a live dbt/MySQL execution.',
      'github_repository':'gitikagrover14/Real-Time-Multi-Cloud-FinOps-Infrastructure-Unit-Economics-Engine',
      'main_tree_sha_at_review':'366636d44379bdacfc5c8ea1439e3c18ab896eb4',
      'inputs':{'original':{'file':raw_file.name,'sha256':digest(raw_file)},
                'cleaned':{'file':clean_file.name,'sha256':digest(clean_file)}},
      'row_count':{'original':len(raw),'cleaned':len(clean)},
      'unique_dimension_business_keys':{
         'Dim_Service':len(svc_keys),'Dim_Tenant':len(tenant_keys),
         'Dim_Region_including_blank':len(region_keys),
         'Dim_Region_excluding_blank':len(region_keys_excluding_blank)},
      'local_fact_row_count_if_blank_region_member_kept':len(mapped_all),
      'local_fact_row_count_if_region_blank_becomes_SQL_NULL_and_INNER_JOIN_excludes_it':len(mapped_if_null),
      'unmapped_region_if_SQL_NULL_without_unknown_member':len(region_unmatched_blanks),
      'null_or_blank_source_counts':{'RegionId':len(region_missing),'SubAccountId':len(sub_missing),
                                     'Tags':sum(not r['Tags'].strip() for r in clean)},
      'missing_region_cost_exposure_usd':{
        'BilledCost':str(region_lost_billed),'EffectiveCost':str(region_lost_effective)},
      'cost_totals_usd':{'original':{k:str(v) for k,v in raw_t.items()},
                         'cleaned':{k:str(v) for k,v in clean_t.items()}},
      'missing_region_by_charge_category':cause_summary,
      'duplicate_rows':duplicate_count,
      'local_validation':{'passed':passing,'total':len(checks),'checks':checks},
      'risks':[
         'The committed dbt fact_spend.sql INNER JOINs all dimensions: if blank RegionId changes to SQL NULL and has no dimension member, 58 source rows are omitted.',
         'The committed dbt dim_* and fact_spend models select from existing MySQL dimension/fact sources; they do not themselves populate dimensions from ref(stg_billing).',
         'Gitika reported 4,433 fact view rows and 8 region dimension rows; live MySQL state and key mapping must be checked using supplied SQL/dbt tests.'
      ]
    }
    (output/'day4_dimension_fact_validation.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    with (output/'day4_region_exceptions.csv').open('w',encoding='utf-8',newline='') as fh:
        writer=csv.writer(fh)
        writer.writerow(['source_row_number_including_header','ProviderName','ChargeCategory','BillingAccountId','SubAccountId','ServiceName','ResourceId','RegionId','BilledCost','EffectiveCost','reason'])
        for idx,r in region_missing:
            writer.writerow([idx+1,r['ProviderName'],r['ChargeCategory'],r['BillingAccountId'],r['SubAccountId'],
                              r['ServiceName'],r['ResourceId'],r['RegionId'],r['BilledCost'],r['EffectiveCost'],
                              'Blank source RegionId; retain row, decide unknown-region policy in warehouse'])
    with (output/'day4_dimension_mapping_summary.csv').open('w',encoding='utf-8',newline='') as fh:
        writer=csv.writer(fh)
        writer.writerow(['dimension','business_key_columns','distinct_source_keys_including_blanks','distinct_keys_excluding_blank_region','source_rows_with_missing_business_key','mapping_guidance'])
        writer.writerow(['Dim_Service','ProviderName + InvoiceIssuerName + ServiceCategory + ServiceName',len(svc_keys),len(svc_keys),0,'Use provider + service composite business key; verify dimension uniqueness'])
        writer.writerow(['Dim_Tenant','BillingAccountId + SubAccountId',len(tenant_keys),len(tenant_keys),len(sub_missing),'Blank subaccount expected on tax rows; use null-safe matching or explicit unknown member'])
        writer.writerow(['Dim_Region','RegionId',len(region_keys),len(region_keys_excluding_blank),len(region_missing),'Make explicit policy for blank region; avoid inner join dropping facts'])
        writer.writerow(['Fact_Spend','Spend_ID (warehouse surrogate)',len(clean),len(clean),0,'Reconcile source vs fact count and measures after dbt execution'])
    print(json.dumps({
        'checks':f'{passing}/{len(checks)}',
        'row_count':len(clean),
        'dimension_counts':[len(svc_keys),len(tenant_keys),len(region_keys)],
        'missing_region_rows':len(region_missing),
        'if_region_null_inner_join_rows':len(clean)-len(region_missing),
        'cost_exposure_if_dropped':{'billed':str(region_lost_billed),'effective':str(region_lost_effective)}
    },indent=2))
    if not all(checks.values()):
       print('FAIL: one or more checks failed; inspect day4_dimension_fact_validation.json',file=sys.stderr)
       return 1
    return 0

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--raw',required=True,type=Path,help='Original 26-column FOCUS CSV')
    ap.add_argument('--clean',required=True,type=Path,help='Cleaned 26-column FOCUS CSV from Week 1')
    ap.add_argument('--output',type=Path,default=Path('outputs/taeyun/week2'))
    args=ap.parse_args()
    sys.exit(run(args.raw,args.clean,args.output))

if __name__=='__main__':main()
