"""Week 1 Day 3: lossless staging ingestion of FOCUS billing and daily orders.
Usage: python scripts/week1_day3_ingestion.py --billing path/to/focus_exercise_2026-q3.csv --orders path/to/northwind_orders_2026-q3.csv --out outputs
No external Python dependencies required.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

EXPECTED_BILLING_COLUMNS = ['BillingAccountId','SubAccountId','ProviderName','InvoiceIssuerName','ServiceCategory','ServiceName','RegionId','ChargeCategory','ChargeFrequency','ChargePeriodStart','ChargePeriodEnd','BillingPeriodStart','BillingPeriodEnd','BillingCurrency','ListCost','ContractedCost','BilledCost','EffectiveCost','PricingQuantity','PricingUnit','CommitmentDiscountId','CommitmentDiscountCategory','CommitmentDiscountStatus','ResourceId','Tags','x_Credits']

def load_csv(path):
    with path.open('r', encoding='utf-8-sig', newline='') as f:
        r=csv.DictReader(f)
        if not r.fieldnames or len(r.fieldnames)!=len(set(r.fieldnames)):
            raise ValueError(f'Missing or duplicated headers: {path}')
        fields=list(r.fieldnames)
        rows=list(r)
    if any(None in record for record in rows):
        raise ValueError(f'Extra cells in file: {path}')
    return fields, rows

def quote(field):
    return '"'+field.replace('"','""')+'"'

def ingest(billing, orders, out):
    out.mkdir(parents=True,exist_ok=True)
    bc, br=load_csv(billing)
    oc, orows=load_csv(orders)
    if bc != EXPECTED_BILLING_COLUMNS: raise ValueError('FOCUS headers differ from expected 26-column layout')
    if oc != ['date','orders']: raise ValueError('Orders headers must be date,orders')
    db_path=out/'finops_day3_raw_staging.sqlite'
    if db_path.exists(): db_path.unlink()  # repeatable, no duplicate append
    con=sqlite3.connect(db_path)
    try:
        with con:
            con.execute('CREATE TABLE raw_focus_billing (ingestion_id INTEGER PRIMARY KEY AUTOINCREMENT, '+', '.join(quote(c)+' TEXT' for c in bc)+')')
            con.execute('CREATE TABLE raw_daily_orders (ingestion_id INTEGER PRIMARY KEY AUTOINCREMENT, '+', '.join(quote(c)+' TEXT' for c in oc)+')')
            con.execute('CREATE TABLE ingestion_metadata (dataset_name TEXT PRIMARY KEY, source_path TEXT, sha256 TEXT, row_count INTEGER, column_count INTEGER, imported_utc TEXT)')
            con.executemany('INSERT INTO raw_focus_billing ('+', '.join(quote(c) for c in bc)+') VALUES ('+', '.join('?' for _ in bc)+')',([row[c] for c in bc] for row in br))
            con.executemany('INSERT INTO raw_daily_orders ('+', '.join(quote(c) for c in oc)+') VALUES (?,?)',([row[c] for c in oc] for row in orows))
            for name,path,rows,cols in [('billing',billing,br,bc),('daily_orders',orders,orows,oc)]:
                con.execute('INSERT INTO ingestion_metadata VALUES (?,?,?,?,?,?)',(name,str(path),hashlib.sha256(path.read_bytes()).hexdigest(),len(rows),len(cols),datetime.now(timezone.utc).isoformat()))
        actual_b=con.execute('SELECT COUNT(*) FROM raw_focus_billing').fetchone()[0]
        actual_o=con.execute('SELECT COUNT(*) FROM raw_daily_orders').fetchone()[0]
        provider=dict(con.execute('SELECT ProviderName, COUNT(*) FROM raw_focus_billing GROUP BY ProviderName').fetchall())
        matches=actual_b==len(br) and actual_o==len(orows)
        if not matches: raise RuntimeError('Row counts differ after ingestion')
        result={'status':'PASS','note':'Raw import only; no cleaning, casting, imputation, or tag changes.','billing_rows':actual_b,'billing_columns':len(bc),'daily_order_rows':actual_o,'daily_order_columns':len(oc),'provider_counts':provider,'billing_sha256':hashlib.sha256(billing.read_bytes()).hexdigest(),'orders_sha256':hashlib.sha256(orders.read_bytes()).hexdigest(),'billing_columns_in_order':bc,'staging_tables':['raw_focus_billing','raw_daily_orders','ingestion_metadata'],'database_file':db_path.name}
        (out/'day3_ingestion_validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
        return result
    finally: con.close()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--billing',type=Path,required=True);p.add_argument('--orders',type=Path,required=True);p.add_argument('--out',type=Path,default=Path('outputs'));a=p.parse_args()
    print(json.dumps(ingest(a.billing,a.orders,a.out),indent=2))
