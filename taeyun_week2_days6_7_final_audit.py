#!/usr/bin/env python3
"""Independent local FinOps source-to-model contract QA for Week 2 Days 6–7.

Reads authentic synthetic Q3 2026 billing and cleaned CSVs and prepares
reconciliation evidence for the mid-project review. Does NOT connect to MySQL
or execute dbt. No third-party dependencies. Python >= 3.9.

Run from the root of this handoff package:
python scripts/taeyun_week2_days6_7_final_audit.py

Override inputs with --raw/--cleaned/--tag-audited/--orders and --out.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, date, timedelta
from decimal import Decimal, InvalidOperation, getcontext
from pathlib import Path

getcontext().prec = 36
MONETARY = ('ListCost','ContractedCost','BilledCost','EffectiveCost')
MEASURES = MONETARY + ('PricingQuantity',)
FIELDS = (
    'BillingAccountId','SubAccountId','ProviderName','InvoiceIssuerName',
    'ServiceCategory','ServiceName','RegionId','ChargeCategory','ChargeFrequency',
    'ChargePeriodStart','ChargePeriodEnd','BillingPeriodStart','BillingPeriodEnd',
    'BillingCurrency','ListCost','ContractedCost','BilledCost','EffectiveCost',
    'PricingQuantity','PricingUnit','CommitmentDiscountId',
    'CommitmentDiscountCategory','CommitmentDiscountStatus','ResourceId','Tags','x_Credits',
)
DIM_SERVICE = ('ProviderName','InvoiceIssuerName','ServiceCategory','ServiceName')
DIM_TENANT = ('BillingAccountId','SubAccountId')
DIM_REGION = ('RegionId',)
GRAIN_SERVICE = DIM_SERVICE + ('BillingCurrency','PricingUnit')
GRAIN_RESOURCE = DIM_SERVICE + ('ResourceId','BillingCurrency','PricingUnit')


def load(path: Path):
    with path.open('r',encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        rows=list(reader)
        columns=list(reader.fieldnames or [])
    return columns, rows


def sha256(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024),b''):
            h.update(chunk)
    return h.hexdigest()


def decimal(value):
    return Decimal((value or '').strip() or '0')


def totals(rows):
    return {col:sum((decimal(r[col]) for r in rows),Decimal(0)) for col in MEASURES}


def str_amount(v,places=2):
    return str(v.quantize(Decimal(1).scaleb(-places)))


def row_semantics_equal(raw,clean):
    for a,b in zip(raw,clean):
        for f in FIELDS:
            if f == 'Tags':
                try:
                    if (json.loads(a[f]) if a[f] else None)!=(json.loads(b[f]) if b[f] else None):return False
                except (ValueError,TypeError):return False
            elif f in MEASURES or f == 'x_Credits':
                try:
                    if decimal(a[f])!=decimal(b[f]) or bool(a[f].strip())!=bool(b[f].strip()):return False
                except InvalidOperation:return False
            elif a[f] != b[f]:
                return False
    return len(raw)==len(clean)


def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields)
        writer.writeheader(); writer.writerows(rows)


def offline_star_join_count(rows):
    """Independent in-memory mapping simulation, NOT Gitika's MySQL database."""
    cn=sqlite3.connect(':memory:')
    cn.execute('PRAGMA foreign_keys=ON')
    cn.executescript('''
    CREATE TABLE ds(id INTEGER PRIMARY KEY, code TEXT UNIQUE NOT NULL);
    CREATE TABLE dt(id INTEGER PRIMARY KEY, code TEXT UNIQUE NOT NULL);
    CREATE TABLE dr(id INTEGER PRIMARY KEY, code TEXT UNIQUE NOT NULL);
    CREATE TABLE fact(id INTEGER PRIMARY KEY, dsid INTEGER NOT NULL REFERENCES ds(id),
       dtid INTEGER NOT NULL REFERENCES dt(id), drid INTEGER NOT NULL REFERENCES dr(id));
    ''')
    keys=[DIM_SERVICE,DIM_TENANT,DIM_REGION]
    maps=[]
    for table,attrs in zip(['ds','dt','dr'],keys):
        members=sorted({tuple(row[c] for c in attrs) for row in rows})
        keys_to_id={item:i+1 for i,item in enumerate(members)}
        cn.executemany(f'INSERT INTO {table}(id,code) VALUES (?,?)',
                       [(key_id,json.dumps(key)) for key,key_id in keys_to_id.items()])
        maps.append(keys_to_id)
    cn.executemany('INSERT INTO fact(id,dsid,dtid,drid) VALUES (?,?,?,?)',
       [(i, maps[0][tuple(r[c] for c in DIM_SERVICE)],maps[1][tuple(r[c] for c in DIM_TENANT)],
         maps[2][tuple(r[c] for c in DIM_REGION)]) for i,r in enumerate(rows,1)])
    count=cn.execute('''SELECT count(*) FROM fact f JOIN ds ON f.dsid=ds.id
                JOIN dt ON f.dtid=dt.id JOIN dr ON f.drid=dr.id''').fetchone()[0]
    fk_errors=cn.execute('PRAGMA foreign_key_check').fetchall()
    cn.close()
    return count, len(fk_errors), {n:len(m) for n,m in zip(['Dim_Service','Dim_Tenant','Dim_Region'],maps)}


def audit(raw_path,clean_path,tags_path,orders_path,out):
    cols_raw,raw=load(raw_path)
    cols_clean,clean=load(clean_path)
    cols_tags,audited=load(tags_path)
    cols_orders,orders=load(orders_path)
    if not raw or not clean: raise ValueError('Missing source or cleaned billing rows')
    if cols_raw!=list(FIELDS) or cols_clean!=list(FIELDS):
        raise ValueError('FOCUS 26-column schema mismatch')
    if cols_tags!=list(FIELDS)+['allocation_team','allocation_env','tag_status']:
        raise ValueError('Tag-audit schema mismatch')
    if cols_orders!=['date','orders']:
        raise ValueError('Daily-order data schema mismatch')

    raw_totals=totals(raw); clean_totals=totals(clean)
    provider=defaultdict(list); service=defaultdict(list); resource=defaultdict(list)
    unidentified=[]; missing=Counter(); categories=Counter(); parsed_dates=[]
    tag_valid=0; invalid_tags=0; unexpected_alloc=0
    all_timestamps_ok=True; all_date_order_ok=True; all_numeric_ok=True
    google_credit_ok=True; non_google_credit_ok=True
    usage_tags_ok=True
    for row in clean:
        provider[row['ProviderName']].append(row)
        service[tuple(row[c] for c in GRAIN_SERVICE)].append(row)
        if row['ResourceId'].strip():resource[tuple(row[c] for c in GRAIN_RESOURCE)].append(row)
        else:unidentified.append(row)
        categories[row['ChargeCategory']]+=1
        for f in ['SubAccountId','RegionId','ResourceId','Tags','PricingQuantity']:
            if not row[f].strip():missing[f]+=1
        try:
            parsed=[datetime.fromisoformat(row[c].replace('Z','+00:00')) for c in
              ('ChargePeriodStart','ChargePeriodEnd','BillingPeriodStart','BillingPeriodEnd')]
            parsed_dates.append(parsed[0].date())
            if parsed[0]>=parsed[1] or parsed[2]>=parsed[3]:all_date_order_ok=False
        except (ValueError,TypeError):all_timestamps_ok=False
        for m in MEASURES:
            if row[m].strip():
                try:
                    if not decimal(row[m]).is_finite():all_numeric_ok=False
                except InvalidOperation:all_numeric_ok=False
        try:
            tag=json.loads(row['Tags']) if row['Tags'].strip() else None
            if tag is not None:
                if isinstance(tag,dict) and tag.get('team') and tag.get('env'):tag_valid+=1
                else:invalid_tags+=1
            if row['ChargeCategory']=='Usage' and not (isinstance(tag,dict) and tag.get('team') and tag.get('env')):
                usage_tags_ok=False
        except (ValueError,TypeError):
            invalid_tags+=1;usage_tags_ok=False
        if row['ProviderName']=='Google Cloud':
            if decimal(row['EffectiveCost'])!=decimal(row['BilledCost'])+decimal(row['x_Credits']):google_credit_ok=False
        elif row['x_Credits'].strip():non_google_credit_ok=False
    for r,a in zip(clean,audited):
        if any(r[c]!=a[c] for c in FIELDS):unexpected_alloc+=1
        tag=json.loads(r['Tags']) if r['Tags'].strip() else {}
        if a['allocation_team']!=(tag.get('team','') if isinstance(tag,dict) else ''):unexpected_alloc+=1
        if a['allocation_env']!=(tag.get('env','') if isinstance(tag,dict) else ''):unexpected_alloc+=1
        if a['tag_status']!=('valid' if r['Tags'].strip() else 'absent'):unexpected_alloc+=1
    order_dates=[]; orders_valid=True
    try:
        order_dates=[date.fromisoformat(r['date']) for r in orders]
        orders_valid=all(int(r['orders'])>=0 for r in orders)
    except (ValueError,TypeError):orders_valid=False
    date_sequence=[date(2026,7,1)+timedelta(days=i) for i in range(92)]
    eligible=clean[:]
    eligible=[r for r in clean if r['ResourceId'].strip()]
    total_res=totals(eligible); total_unat=totals(unidentified)
    provider_rows=[]
    for p,items in sorted(provider.items()):
        t=totals(items)
        provider_rows.append({'provider':p,'records':len(items),
          **{c:str_amount(t[c],4 if c=='PricingQuantity' else 2) for c in MEASURES}})
    cost_rows=[]
    for scope,items in [('source',clean),('resource_identified',eligible),('resource_unidentified',unidentified)]:
        t=totals(items)
        cost_rows.append({'scope':scope,'rows':len(items),
           **{c:str_amount(t[c],4 if c=='PricingQuantity' else 2) for c in MEASURES}})
    joined_rows,fk_errors,dim_counts=offline_star_join_count(clean)
    distinct_service_key_count=len({tuple(r[c] for c in DIM_SERVICE) for r in clean})
    num_total_service_groups=len(service); num_resource_groups=len(resource)
    zero_svc_groups=sum(not sum((decimal(r['PricingQuantity']) for r in items),Decimal(0)) for items in service.values())
    zero_res_groups=sum(not sum((decimal(r['PricingQuantity']) for r in items),Decimal(0)) for items in resource.values())

    checks={}
    def check(name,value):checks[name]=bool(value)
    check('raw_schema_26_columns', cols_raw==list(FIELDS))
    check('cleaned_schema_26_columns',cols_clean==list(FIELDS))
    check('raw_and_clean_4433_records',len(raw)==len(clean)==4433)
    check('cleaned_rows_semantically_match_raw',row_semantics_equal(raw,clean))
    check('no_identical_cleaned_rows',len(set(tuple(r[c] for c in FIELDS) for r in clean))==len(clean))
    check('raw_clean_four_monetary_totals_equal',all(raw_totals[c]==clean_totals[c] for c in MONETARY))
    check('raw_clean_pricing_qty_equal',raw_totals['PricingQuantity']==clean_totals['PricingQuantity'])
    check('raw_clean_source_costs_expected',clean_totals['BilledCost']==Decimal('332678.83') and clean_totals['EffectiveCost']==Decimal('213887.47'))
    check('provider_row_partition',sum(len(items) for items in provider.values())==len(clean))
    check('provider_count_and_rows_expected', {k:len(v) for k,v in provider.items()}=={'AWS':2675,'Microsoft':927,'Google Cloud':831})
    check('all_four_dates_parse',all_timestamps_ok and len(parsed_dates)==len(clean))
    check('all_periods_end_after_start',all_date_order_ok)
    check('q3_daily_coverage', min(parsed_dates)==date(2026,7,1) and max(parsed_dates)==date(2026,9,30))
    check('monetary_and_quantity_values_valid',all_numeric_ok)
    check('tag_audit_matches_clean_rows',len(audited)==len(clean) and unexpected_alloc==0)
    check('usage_tags_present_and_valid',usage_tags_ok)
    check('missing_tag_count_10',missing['Tags']==10 and tag_valid==4423 and invalid_tags==0)
    check('missing_tag_categories_only_tax_credit',all(r['ChargeCategory'] in ('Tax','Credit') for r in clean if not r['Tags'].strip()))
    check('google_synthetic_credit_consistency',google_credit_ok and non_google_credit_ok)
    check('empty_resource_id_333',len(unidentified)==333)
    check('empty_region_id_58',missing['RegionId']==58)
    check('missing_subaccount_id_9',missing['SubAccountId']==9)
    check('costs_reconcile_identified_unidentified',all(total_res[c]+total_unat[c]==clean_totals[c] for c in MEASURES))
    check('service_rollup_preserves_source_totals',all(sum((decimal(r[c]) for items in service.values() for r in items),Decimal(0))==clean_totals[c] for c in MEASURES))
    check('resource_rollup_preserves_eligible_totals',all(sum((decimal(r[c]) for items in resource.values() for r in items),Decimal(0))==total_res[c] for c in MEASURES))
    check('service_group_count_33',num_total_service_groups==33)
    check('resource_group_count_44',num_resource_groups==44)
    check('distinct_services_28',distinct_service_key_count==28)
    check('local_key_mapping_dimensions',dim_counts=={'Dim_Service':28,'Dim_Tenant':10,'Dim_Region':8})
    check('simulated_star_join_retains_rows',joined_rows==len(clean) and fk_errors==0)
    check('daily_orders_92',len(orders)==92 and orders_valid)
    check('daily_orders_unique_q3', len(set(order_dates))==92 and sorted(order_dates)==date_sequence)
    check('resource_omission_effective_cost_expected',total_unat['EffectiveCost']==Decimal('38597.49'))
    check('zero_qty_groups_handled_as_null_rate',zero_svc_groups==6 and zero_res_groups==1)

    out.mkdir(parents=True,exist_ok=True)
    write_csv(out/'day6_provider_totals.csv',provider_rows,list(provider_rows[0].keys()))
    write_csv(out/'day6_resource_cost_bridge.csv',cost_rows,list(cost_rows[0].keys()))
    write_csv(out/'day6_missing_value_summary.csv',
       [{'field':k,'blank_records':missing[k],'handling':'preserve legitimate blanks and track attribution; never fabricate dimensions or costs'}
        for k in ['SubAccountId','RegionId','ResourceId','Tags','PricingQuantity']],
       ['field','blank_records','handling'])
    test_matrix=[{'test_id':f'LOCAL_{idx:02d}','description':k.replace('_',' '),
                  'method':'independent source/cleaned CSV + Python/SQLite simulation',
                  'status':'PASS' if val else 'FAIL'}
                  for idx,(k,val) in enumerate(checks.items(),1)]
    test_matrix.extend([
       {'test_id':'LIVE_01','description':'dbt debug connection', 'method':'Gitika local dbt','status':'NOT_EXECUTED_IN_THIS_ENVIRONMENT'},
       {'test_id':'LIVE_02','description':'dbt build complete DAG', 'method':'Gitika local dbt','status':'NOT_EXECUTED_IN_THIS_ENVIRONMENT'},
       {'test_id':'LIVE_03','description':'dbt singular and schema test results', 'method':'Gitika local dbt','status':'NOT_EXECUTED_IN_THIS_ENVIRONMENT'},
       {'test_id':'LIVE_04','description':'MySQL stage/fact/service/resource parity', 'method':'MySQL read-only SQL','status':'NOT_EXECUTED_IN_THIS_ENVIRONMENT'},
       {'test_id':'LIVE_05','description':'source backup identifiers and alias resolution','method':'MySQL information_schema','status':'NOT_EXECUTED_IN_THIS_ENVIRONMENT'},
    ])
    write_csv(out/'day7_testing_matrix.csv',test_matrix,['test_id','description','method','status'])
    data={
      'task':'Taeyun Week 2 Day 6 pipeline QA / Day 7 review readiness',
      'date':'2026-11-27',
      'scope':'LOCAL independent verification only. No live MySQL, dbt test, or dbt run was performed.',
      'files':{n:{'path':str(p.name),'sha256':sha256(p)} for n,p in [('raw',raw_path),('cleaned',clean_path),('tag_audited',tags_path),('orders',orders_path)]},
      'row_counts':{'billing_raw':len(raw),'billing_cleaned':len(clean),'orders':len(orders),'resource_identified':len(eligible),'resource_unidentified':len(unidentified)},
      'model_expectations':{'Dim_Service':28,'Dim_Tenant':10,'Dim_Region_including_blank':8,'Fact_Spend':4433,
                            'service_unit_economics':num_total_service_groups,'resource_unit_economics':num_resource_groups},
      'totals_usd':{c:str_amount(clean_totals[c]) for c in MONETARY},
      'pricing_quantity':str_amount(clean_totals['PricingQuantity'],4),
      'resource_unidentified_effective_usd':str_amount(total_unat['EffectiveCost']),
      'resource_unidentified_effective_pct':str_amount(total_unat['EffectiveCost']/clean_totals['EffectiveCost']*Decimal(100)),
      'data_quality':{'blank_subaccount':missing['SubAccountId'],'blank_region':missing['RegionId'],
                      'blank_resource':missing['ResourceId'],'missing_tags':missing['Tags'],
                      'blank_pricing_quantity':missing['PricingQuantity'],'valid_tagged_rows':tag_valid,'invalid_populated_tags':invalid_tags,
                      'service_groups_zero_quantity':zero_svc_groups,'resource_groups_zero_quantity':zero_res_groups},
      'provider_totals':provider_rows,'charge_categories':dict(categories),
      'offline_star_simulation':{'all_fact_rows_joined':joined_rows,'foreign_key_errors':fk_errors,'dimensions':dim_counts,
                                'disclaimer':'This is a SQLite reconstruction, NOT the Gitika MySQL warehouse.'},
      'local_checks':checks,'local_passed':sum(checks.values()),'local_total':len(checks),
      'local_status':'PASS' if all(checks.values()) else 'FAIL',
      'live_checks_status':'NOT_EXECUTED_IN_THIS_ENVIRONMENT',
      'known_current_repo_gaps':[
        'A runnable dbt_project.yml is not present at the GitHub main root snapshot reviewed.',
        'Source definitions reference renamed dim_service__dbt_backup / dim_tenant__dbt_backup / dim_region__dbt_backup tables; verify in MySQL.',
        'Fact model uses INNER JOIN; check 58 missing-region source rows survive dimension key mapping.',
        'Resource model intentionally filters 333 records without ResourceId (EffectiveCost $38,597.49).',
      ],
    }
    (out/'day6_day7_local_validation.json').write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    return data


def main():
    root=Path(__file__).resolve().parents[1]
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--raw',type=Path,default=root/'data/raw/focus_exercise_2026-q3.csv')
    p.add_argument('--cleaned',type=Path,default=root/'data/processed/focus_cleaned_2026-q3.csv')
    p.add_argument('--tag-audited',type=Path,default=root/'data/processed/focus_tag_audited_2026-q3.csv')
    p.add_argument('--orders',type=Path,default=root/'data/raw/northwind_orders_2026-q3.csv')
    p.add_argument('--out',type=Path,default=root/'outputs/taeyun/week2')
    a=p.parse_args()
    report=audit(a.raw,a.cleaned,a.tag_audited,a.orders,a.out)
    print(f"LOCAL VALIDATION: {report['local_status']} ({report['local_passed']}/{report['local_total']})")
    print('MySQL/dbt live execution: NOT RUN (requires Gitika connection and dbt project)')
    print('Report:',a.out/'day6_day7_local_validation.json')
    if report['local_status']!='PASS':raise SystemExit(1)

if __name__=='__main__':main()
