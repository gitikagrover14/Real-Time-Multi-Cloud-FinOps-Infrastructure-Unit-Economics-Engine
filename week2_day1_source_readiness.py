#!/usr/bin/env python3
"""Read-only Week 2 Day 1 source-readiness audit for Taeyun.

Run: python scripts/week2_day1_source_readiness.py --raw path/to/focus_exercise_2026-q3.csv --clean path/to/focus_cleaned_2026-q3.csv --audited path/to/focus_tag_audited_2026-q3.csv --output outputs
Dependencies: Python standard library only. No database mutation.
"""
import argparse,csv,hashlib,json,collections,decimal,datetime,pathlib,sys
EXPECTED_FIELDS=['BillingAccountId','SubAccountId','ProviderName','InvoiceIssuerName','ServiceCategory','ServiceName','RegionId','ChargeCategory','ChargeFrequency','ChargePeriodStart','ChargePeriodEnd','BillingPeriodStart','BillingPeriodEnd','BillingCurrency','ListCost','ContractedCost','BilledCost','EffectiveCost','PricingQuantity','PricingUnit','CommitmentDiscountId','CommitmentDiscountCategory','CommitmentDiscountStatus','ResourceId','Tags','x_Credits']
MONEY=['ListCost','ContractedCost','BilledCost','EffectiveCost'];DATES=['ChargePeriodStart','ChargePeriodEnd','BillingPeriodStart','BillingPeriodEnd']
NUMERIC=MONEY+['PricingQuantity','x_Credits']

def load(path):
 with open(path,encoding='utf-8-sig',newline='') as f:
  r=csv.DictReader(f);fields=r.fieldnames;rows=list(r)
 return fields,rows

def digest(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()

def money_sums(rows):
 result={}
 for key in MONEY:
  result[key]=str(sum((decimal.Decimal(row[key]) for row in rows if row[key].strip()),decimal.Decimal(0)).quantize(decimal.Decimal('0.01')))
 return result

def audit(raw,clean,audited,out):
 fp,rr=load(raw);fc,cr=load(clean);fa,ar=load(audited)
 issues=[]
 if fp!=EXPECTED_FIELDS:issues.append('Raw field list differs from expected 26-column contract')
 if fc!=EXPECTED_FIELDS:issues.append('Clean field list differs from expected 26-column contract')
 if fa!=EXPECTED_FIELDS+['allocation_team','allocation_env','tag_status']:issues.append('Tag audit field contract differs from expected 29 columns')
 if not (len(rr)==len(cr)==len(ar)==4433):issues.append('Record count inconsistency or different from 4433')
 if money_sums(rr)!=money_sums(cr) or money_sums(rr)!=money_sums(ar):issues.append('Financial totals do not reconcile')
 counts=collections.Counter(r['ProviderName'] for r in cr)
 missing={field:sum(not (r.get(field) or '').strip() for r in cr) for field in EXPECTED_FIELDS}
 malformed=[];invalid_dates=[]
 for n,row in enumerate(cr,2):
  for key in NUMERIC:
   if row[key].strip():
    try: decimal.Decimal(row[key])
    except decimal.InvalidOperation:malformed.append([n,key,row[key]])
  for key in DATES:
   try:datetime.datetime.fromisoformat(row[key].replace('Z','+00:00'))
   except ValueError:invalid_dates.append([n,key,row[key]])
  if row['Tags'].strip():
   try:
    t=json.loads(row['Tags'])
    if not isinstance(t,dict): malformed.append([n,'Tags','JSON must be object'])
   except json.JSONDecodeError:malformed.append([n,'Tags','invalid JSON'])
 if malformed or invalid_dates:issues.append('Some numeric/date/tag values are invalid')
 expected_tags=collections.Counter(r.get('tag_status','') for r in ar)
 if sum(1 for r in cr if r['ChargeCategory']=='Usage' and not r['Tags'].strip()):issues.append('Usage row without allocation Tags')
 double=collections.Counter(tuple(r.get(x,'') for x in EXPECTED_FIELDS) for r in cr)
 duplicates=sum(n-1 for n in double.values() if n>1)
 if duplicates:issues.append('Exact duplicate billing records detected')
 audit={'source':'The FinOps Desk Q3 2026 synthetic FOCUS exercise','source_files':{'raw':{'filename':pathlib.Path(raw).name,'sha256':digest(raw)},'clean':{'filename':pathlib.Path(clean).name,'sha256':digest(clean)},'audited':{'filename':pathlib.Path(audited).name,'sha256':digest(audited)}},'record_counts':{'raw':len(rr),'clean':len(cr),'audited':len(ar)},'column_counts':{'raw':len(fp),'clean':len(fc),'audited':len(fa)},'providers':dict(counts),'cost_sums_usd':{'raw':money_sums(rr),'clean':money_sums(cr),'audited':money_sums(ar)},'missing_clean_cells':{k:v for k,v in missing.items() if v},'tag_status_distribution':dict(expected_tags),'exact_duplicate_rows':duplicates,'malformed_count':len(malformed),'invalid_date_count':len(invalid_dates),'issues':issues,'readiness':'PASS' if not issues else 'FAIL','limitations':['Local file audit only; not an actual MySQL or dbt run','Source is synthetic and daily-granularity','NULL optional fields should remain NULL in staging','26-column cleaned CSV is intended for Gitika staging; 29-column audited CSV is supplemental']}
 pathlib.Path(out).mkdir(parents=True,exist_ok=True)
 with open(pathlib.Path(out)/'week2_day1_source_readiness.json','w') as f:json.dump(audit,f,indent=2)
 with open(pathlib.Path(out)/'week2_day1_staging_field_contract.csv','w',newline='') as f:
  w=csv.writer(f);w.writerow(['ordinal','source_column','suggested_staging_type','nullable','transformation_target','notes'])
  for i,k in enumerate(EXPECTED_FIELDS,1):
   kind='VARCHAR/TEXT (raw)' ;target='staging input'
   if k in MONEY:target='DECIMAL(18,6) in dbt staging'
   elif k in DATES:target='TIMESTAMP/DATETIME (UTC) in dbt staging'
   elif k in ['PricingQuantity','x_Credits']:target='DECIMAL(18,6) in dbt staging'
   if k=='Tags':target='JSON-text parse/extract in dbt staging'
   w.writerow([i,k,kind,'yes' if missing[k] else 'observed complete',target,'Preserve account/resource IDs as text' if k in ('BillingAccountId','SubAccountId','ResourceId') else ''])
 print(json.dumps({'readiness':audit['readiness'],'counts':audit['record_counts'],'billed':audit['cost_sums_usd']['clean']['BilledCost'],'effective':audit['cost_sums_usd']['clean']['EffectiveCost'],'issues':issues},indent=2))
 return 0 if not issues else 1

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--raw',required=True);p.add_argument('--clean',required=True);p.add_argument('--audited',required=True);p.add_argument('--output',default='outputs');a=p.parse_args();sys.exit(audit(a.raw,a.clean,a.audited,a.output))
