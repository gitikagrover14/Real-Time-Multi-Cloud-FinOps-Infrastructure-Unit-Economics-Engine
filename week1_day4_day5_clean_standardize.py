#!/usr/bin/env python3
"""Taeyun's reproducible, standard-library-only Week-1 FOCUS ingestion & cleaning.

Usage: python scripts/build_taeyun_pipeline.py --input-dir /path/to/original/csvs --output-dir outputs

No guessed cloud account, region, cost, or cost-allocation tag is manufactured.
Raw data is fully retained, normalized FOCUS exports are compatible with a
subsequent star-schema loader, and all transformations are audited.
"""
import argparse
import csv
import datetime as dt
import decimal
import hashlib
import json
import collections
import pathlib
import sqlite3
from collections import Counter, defaultdict

MONEY = ['ListCost','ContractedCost','BilledCost','EffectiveCost','x_Credits']
DATES = ['ChargePeriodStart','ChargePeriodEnd','BillingPeriodStart','BillingPeriodEnd']
OPTIONAL = {'SubAccountId','RegionId','PricingQuantity','PricingUnit','CommitmentDiscountId',
            'CommitmentDiscountCategory','CommitmentDiscountStatus','ResourceId','Tags','x_Credits'}
NUMS = MONEY + ['PricingQuantity']
ENRICH = ['SourceRowNumber','ChargeDate','TagTeam','TagEnvironment','TagJob',
          'TagAllocationStatus','SubAccountStatus','RegionStatus','ResourceStatus']
SOURCE_URL = 'https://finopscourse.com/resources/focus-analysis-exercise'
EXPECTED = ['BillingAccountId','SubAccountId','ProviderName','InvoiceIssuerName','ServiceCategory',
            'ServiceName','RegionId','ChargeCategory','ChargeFrequency','ChargePeriodStart',
            'ChargePeriodEnd','BillingPeriodStart','BillingPeriodEnd','BillingCurrency','ListCost',
            'ContractedCost','BilledCost','EffectiveCost','PricingQuantity','PricingUnit',
            'CommitmentDiscountId','CommitmentDiscountCategory','CommitmentDiscountStatus','ResourceId','Tags','x_Credits']

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def read_csv(p):
    with p.open('r',encoding='utf-8-sig',newline='') as f:
        rd=csv.DictReader(f)
        fields=rd.fieldnames
        rows=list(rd)
    if not fields or any(None in row for row in rows):
        raise ValueError('Malformed CSV: '+str(p))
    return fields,rows

def canon_decimal(v,scale,where):
    try:
        d=decimal.Decimal(v)
        if not d.is_finite(): raise ValueError('non-finite amount')
        n=d.quantize(decimal.Decimal(1).scaleb(-scale))
        if d!=n: raise ValueError('precision exceeds %d decimals: %s'%(scale,v))
        return format(n, f'.{scale}f')
    except (decimal.InvalidOperation, ValueError) as ex:
        raise ValueError(f'{where}: invalid decimal {v!r} ({ex})')

def cents(v):
    return int(decimal.Decimal(v)*100) if v is not None else None

def x10000(v):
    return int(decimal.Decimal(v)*10000) if v is not None else None

def canon_utc(v,where):
    try:
        x=dt.datetime.fromisoformat(v.replace('Z','+00:00'))
        if x.tzinfo is None: raise ValueError('naive datetime')
        x=x.astimezone(dt.timezone.utc)
        return x.strftime('%Y-%m-%dT%H:%M:%SZ')
    except Exception as ex:
        raise ValueError(f'{where}: invalid UTC timestamp {v!r}: {ex}')

def write_csv(path,fields,rows):
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore')
        w.writeheader();w.writerows(rows)

def clean_record(raw,ix):
    row={}; change=[]
    for k in EXPECTED:
        src=raw[k]; v=src.strip()
        if v=='':
            if k not in OPTIONAL: raise ValueError(f'row {ix} mandatory {k} blank')
            row[k]=None
            continue
        if k in DATES: v=canon_utc(v,f'row {ix} {k}')
        if k in MONEY: v=canon_decimal(v,2,f'row {ix} {k}')
        if k=='PricingQuantity': v=canon_decimal(v,4,f'row {ix} {k}')
        if k=='Tags':
            try:
                parsed=json.loads(v)
                if not isinstance(parsed,dict): raise ValueError('must be object')
                v=json.dumps(parsed,sort_keys=True,ensure_ascii=False,separators=(',',':'))
            except (ValueError,TypeError) as ex:
                raise ValueError(f'row {ix}: invalid Tags JSON {ex}')
        row[k]=v
        if src!=v: change.append(k)
    for left,right in [('ChargePeriodStart','ChargePeriodEnd'),('BillingPeriodStart','BillingPeriodEnd')]:
        if row[left]>=row[right]: raise ValueError(f'row {ix}: {left} not before {right}')
    if not (row['BillingPeriodStart'] <= row['ChargePeriodStart'] < row['BillingPeriodEnd']):
        raise ValueError(f'row {ix}: charge start outside billing period')
    if (row['PricingQuantity'] is None)!=(row['PricingUnit'] is None):
        raise ValueError(f'row {ix}: PricingQuantity and PricingUnit missingness disagreement')
    tags=json.loads(row['Tags']) if row['Tags'] is not None else {}
    team=tags.get('team');env=tags.get('env');job=tags.get('job')
    if team and env: status='ALLOCATED'
    elif row['Tags'] is None and row['ChargeCategory']!='Usage': status='UNALLOCATED_NON_USAGE'
    elif row['Tags'] is None: status='UNALLOCATED_USAGE'
    else: status='INCOMPLETE_TAGS'
    details={
        'SourceRowNumber':ix,'ChargeDate':row['ChargePeriodStart'][:10],
        'TagTeam':team,'TagEnvironment':env,'TagJob':job,'TagAllocationStatus':status,
        'SubAccountStatus':'NOT_PROVIDED' if row['SubAccountId'] is None else 'PROVIDED',
        'RegionStatus':'NOT_PROVIDED' if row['RegionId'] is None else 'PROVIDED',
        'ResourceStatus':'NOT_PROVIDED' if row['ResourceId'] is None else 'PROVIDED'
    }
    return row,details,change

def main():
    arg=argparse.ArgumentParser()
    arg.add_argument('--input-dir',type=pathlib.Path,default=pathlib.Path('.'))
    arg.add_argument('--output-dir',type=pathlib.Path,default=pathlib.Path('outputs'))
    args=arg.parse_args();root=args.input_dir;out=args.output_dir;out.mkdir(parents=True,exist_ok=True)
    bill=root/'focus_exercise_2026-q3.csv'; orders_p=root/'northwind_orders_2026-q3.csv'
    if not bill.is_file() or not orders_p.is_file(): raise FileNotFoundError('Both publisher CSV files required')
    cols,raws=read_csv(bill); ocols,ordersraw=read_csv(orders_p)
    if cols!=EXPECTED: raise ValueError('Unexpected or reordered FOCUS columns: '+repr(cols))
    if ocols!=['date','orders']: raise ValueError('Unexpected order-file columns: '+repr(ocols))
    raw_seen=set();duplicate_rows=[];cleaned=[];enriched=[];changes=Counter();status_counts=Counter();issue=[]
    for ix,r in enumerate(raws,1):
        tup=tuple(r[k] for k in cols)
        if tup in raw_seen:
            duplicate_rows.append(ix)
            issue.append({'SourceRowNumber':ix,'Issue':'EXACT_DUPLICATE','Action':'Excluded from clean table, retained in raw','AffectedField':'all'})
            continue
        raw_seen.add(tup)
        row,details,ch=clean_record(r,ix)
        cleaned.append(row);enriched.append({**row,**details})
        status_counts[details['TagAllocationStatus']]+=1
        changes.update(ch)
        if details['TagAllocationStatus'] != 'ALLOCATED':
            issue.append({'SourceRowNumber':ix,'Issue':'MISSING_COST_ALLOCATION_TAGS',
                          'Action':details['TagAllocationStatus']+'; no tag imputed','AffectedField':'Tags'})
    clean_orders=[];seen_dates=set()
    for ix,r in enumerate(ordersraw,1):
        day=dt.date.fromisoformat(r['date'].strip()).isoformat()
        amount=int(r['orders'].strip())
        if amount<0 or day in seen_dates: raise ValueError(f'order row {ix}: invalid/duplicate date')
        seen_dates.add(day);clean_orders.append({'date':day,'orders':amount})
    write_csv(out/'focus_cleaned_2026-q3.csv',EXPECTED,cleaned)
    write_csv(out/'focus_enriched_2026-q3.csv',EXPECTED+ENRICH,enriched)
    write_csv(out/'orders_cleaned_2026-q3.csv',['date','orders'],clean_orders)
    write_csv(out/'data_quality_issues.csv',['SourceRowNumber','Issue','Action','AffectedField'],issue)
    # SQLite is an independently auditable ingestion deliverable, not Gitika's star schema.
    dbp=out/'taeyun_ingestion_cleaning.sqlite'
    if dbp.exists():dbp.unlink()
    db=sqlite3.connect(dbp)
    db.execute('PRAGMA foreign_keys=ON')
    cols_raw=', '.join('"'+x+'" TEXT' for x in EXPECTED)
    db.execute(f'CREATE TABLE raw_focus_billing (source_row_number INTEGER PRIMARY KEY,{cols_raw})')
    db.executemany('INSERT INTO raw_focus_billing VALUES ('+','.join('?' for i in range(27))+')',
                   [[i]+[r[k] for k in EXPECTED] for i,r in enumerate(raws,1)])
    typ={k:('TEXT') for k in EXPECTED}
    # Decimal values are retained exactly as canonical TEXT. Parallel integer scaled measures support exact reconciliation.
    extras= [f'"{x}" TEXT' for x in ENRICH if x!='SourceRowNumber']
    extras+=['"'+k+'Cents" INTEGER' for k in MONEY]
    extras+=['"PricingQuantityX10000" INTEGER']
    db.execute('CREATE TABLE clean_focus_billing (source_row_number INTEGER PRIMARY KEY,'+
               ', '.join('"'+k+'" '+typ[k] for k in EXPECTED)+', '+', '.join(extras)+')')
    entries=[]
    for e in enriched:
        entries.append([e['SourceRowNumber']]+[e[k] for k in EXPECTED]+[e[k] for k in ENRICH if k!='SourceRowNumber']+
                       [cents(e[k]) for k in MONEY]+[x10000(e['PricingQuantity'])])
    total_cols=1+len(EXPECTED)+(len(ENRICH)-1)+len(MONEY)+1
    db.executemany('INSERT INTO clean_focus_billing VALUES ('+','.join('?'*total_cols)+')',entries)
    db.execute('CREATE INDEX idx_clean_focus_provider ON clean_focus_billing (ProviderName)')
    db.execute('CREATE INDEX idx_clean_focus_charge ON clean_focus_billing (ChargeDate, ChargeCategory)')
    db.execute('CREATE INDEX idx_clean_focus_allocation ON clean_focus_billing (TagAllocationStatus)')
    db.execute('CREATE TABLE raw_daily_orders (source_row_number INTEGER PRIMARY KEY,date TEXT,orders TEXT)')
    db.executemany('INSERT INTO raw_daily_orders VALUES (?,?,?)',[(i,r['date'],r['orders']) for i,r in enumerate(ordersraw,1)])
    db.execute('CREATE TABLE clean_daily_orders (date TEXT PRIMARY KEY,orders INTEGER NOT NULL CHECK(orders>=0))')
    db.executemany('INSERT INTO clean_daily_orders VALUES (:date,:orders)',clean_orders)
    db.execute('CREATE TABLE ingestion_metadata (source_file TEXT PRIMARY KEY,sha256 TEXT NOT NULL,source_rows INTEGER NOT NULL,clean_rows INTEGER NOT NULL,source_url TEXT NOT NULL)')
    db.executemany('INSERT INTO ingestion_metadata VALUES (?,?,?,?,?)',[
        (bill.name,sha(bill),len(raws),len(cleaned),SOURCE_URL),
        (orders_p.name,sha(orders_p),len(ordersraw),len(clean_orders),SOURCE_URL)])
    db.execute('CREATE VIEW focus_for_star_schema AS SELECT '+', '.join('"'+k+'"' for k in EXPECTED)+' FROM clean_focus_billing')
    db.commit()
    provider=defaultdict(lambda:{'rows':0,'billed_cents':0,'effective_cents':0,'untagged_rows':0,'untagged_effective_cents':0})
    for r in enriched:
        p=provider[r['ProviderName']];p['rows']+=1
        p['billed_cents']+=cents(r['BilledCost']);p['effective_cents']+=cents(r['EffectiveCost'])
        if r['TagAllocationStatus']!='ALLOCATED':p['untagged_rows']+=1;p['untagged_effective_cents']+=cents(r['EffectiveCost'])
    p_rows=[]
    for name,p in sorted(provider.items()):
        p_rows.append({'ProviderName':name,'BillingRows':p['rows'],
                       'BilledCostUSD':f"{p['billed_cents']/100:.2f}",'EffectiveCostUSD':f"{p['effective_cents']/100:.2f}",
                       'UnallocatedTagRows':p['untagged_rows'],'UnallocatedEffectiveCostUSD':f"{p['untagged_effective_cents']/100:.2f}"})
    write_csv(out/'provider_summary.csv',list(p_rows[0]),p_rows)
    missing_counts={k:sum(r[k] is None for r in cleaned) for k in EXPECTED}
    unique_counts={k:len(set(r[k] for r in cleaned if r[k] is not None)) for k in EXPECTED}
    tags_by_charge=Counter(r['ChargeCategory'] for r in enriched if r['TagAllocationStatus']!='ALLOCATED')
    profile={'source':'The FinOps Desk (not Kaggle)','source_url':SOURCE_URL,
            'synthetic':True,'focus_naming':'FOCUS 1.2 subset + x_Credits','billing_raw_rows':len(raws),
            'billing_clean_rows':len(cleaned),'orders_raw_rows':len(ordersraw),'orders_clean_rows':len(clean_orders),
            'billing_columns':len(EXPECTED),'exact_duplicate_rows_removed':len(duplicate_rows),
            'duplicate_row_numbers':duplicate_rows,'providers':p_rows,
            'missing_by_column':missing_counts,'distinct_nonmissing_by_column':unique_counts,
            'tag_allocation_status':dict(status_counts),'missing_tags_by_charge_category':dict(tags_by_charge),
            'canonicalized_column_cells':dict(changes),
            'charge_categories':dict(Counter(r['ChargeCategory'] for r in cleaned)),
            'charge_dates':{'min':min(r['ChargePeriodStart'][:10] for r in cleaned),
                            'max':max(r['ChargePeriodStart'][:10] for r in cleaned),
                            'distinct':len(set(r['ChargePeriodStart'][:10] for r in cleaned))},
            'source_sha256':{bill.name:sha(bill),orders_p.name:sha(orders_p)},
            'notes':['Blanks in optional fields stay NULL in SQLite and empty in CSV; no inferred values.',
                     'All records are synthetic and dates represent historical daily billing, not streaming.',
                     'Tags with missing team/env are flagged, not assigned to a guessed tenant.',
                     'Amounts are USD with 2 decimals; exact money also provided in integer-cent columns.',
                     'Source FOCUS column names retained for compatibility with existing Task 3 SQL.']}
    (out/'data_quality_profile.json').write_text(json.dumps(profile,indent=2),encoding='utf-8')
    all_good=(db.execute('SELECT count(*) FROM raw_focus_billing').fetchone()[0]==len(raws) and
              db.execute('SELECT count(*) FROM clean_focus_billing').fetchone()[0]==len(cleaned) and
              db.execute('SELECT count(*) FROM clean_daily_orders').fetchone()[0]==len(clean_orders))
    for k in MONEY[:-1]:
        actual=db.execute(f'SELECT COALESCE(SUM("{k}Cents"),0) FROM clean_focus_billing').fetchone()[0]
        expected=sum(cents(r[k]) for r in cleaned)
        if actual!=expected:raise AssertionError(f'{k} reconciliation error')
    if not all_good:raise AssertionError('database row-count mismatch')
    db.close()
    txt=[
        'TAEYUN WEEK-1 INGESTION & CLEANING VALIDATION',
        'Publisher: The FinOps Desk (NOT Kaggle)',
        f'Original billing records: {len(raws)} | cleaned billing: {len(cleaned)} | exact duplicates: {len(duplicate_rows)}',
        f'Original order records: {len(ordersraw)} | cleaned orders: {len(clean_orders)}',
        'Providers: '+', '.join(f"{p['ProviderName']}={p['BillingRows']}" for p in p_rows),
        'Tag status: '+', '.join(f'{k}={v}' for k,v in status_counts.items()),
        f"Null RegionId={missing_counts['RegionId']} | Null SubAccountId={missing_counts['SubAccountId']} | Null Tags={missing_counts['Tags']}",
        'All CSVs loaded into SQLite. Row counts and exact-cent reconciliations PASSED.',
        'IMPORTANT: unallocated tag statuses are recorded, not magically repaired.',
        'IMPORTANT: dataset source is not Kaggle; obtain team/instructor approval if Kaggle-only is mandatory.',
    ]
    (out/'validation_log.txt').write_text('\n'.join(txt)+'\n',encoding='utf-8')
    print('\n'.join(txt));print('Output:',out.resolve())

if __name__=='__main__':main()
