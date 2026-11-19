#!/usr/bin/env python3
"""Day 6: auditable tag review and financial validation; no invented allocations."""
import csv, json, hashlib, pathlib, collections, decimal, sys
from datetime import datetime
D=decimal.Decimal
BASE=pathlib.Path(__file__).resolve().parent.parent
OUT=BASE/'outputs';OUT.mkdir(exist_ok=True)
source=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else BASE/'inputs'/'focus_cleaned_2026-q3.csv'
original=pathlib.Path(sys.argv[2]) if len(sys.argv)>2 else BASE/'inputs'/'focus_exercise_2026-q3.csv'
def load(path):
    with path.open(newline='',encoding='utf-8-sig') as f:
        rd=csv.DictReader(f);return rd.fieldnames,list(rd)
cols, rows=load(source);orig_cols,raw=load(original)
assert cols==orig_cols,'Original/cleaned column schema differs'
assert len(rows)==len(raw)==4433,'Unexpected source/cleaned record count'
assert set(cols)==set(rows[0]),'Schema mismatch'
counts=collections.Counter(); statuses=collections.Counter();by_charge=collections.Counter(); by_provider=collections.Counter();bad=[];exceptions=[];team_counts=collections.Counter();env_counts=collections.Counter(); tags_parsed=[]
for i,row in enumerate(rows,2):
    tag=row['Tags'].strip(); status='valid';team='';env='';issues=[]
    if not tag: status='absent'; issues=['missing_tag']
    else:
        try:
            obj=json.loads(tag)
            if not isinstance(obj,dict): status='invalid';issues.append('tags_not_object')
            else:
                team=obj.get('team',''); env=obj.get('env','')
                if not isinstance(team,str) or not team.strip(): issues.append('missing_or_invalid_team')
                if not isinstance(env,str) or not env.strip(): issues.append('missing_or_invalid_env')
                if issues: status='incomplete'
        except json.JSONDecodeError:status='invalid';issues=['invalid_json']
    if status!='valid':
        exceptions.append({'csv_line':i,'ProviderName':row['ProviderName'],'ChargeCategory':row['ChargeCategory'],'SubAccountId':row['SubAccountId'],'ResourceId':row['ResourceId'],'TagStatus':status,'Issues':';'.join(issues),'Action':'retain blank/invalid tags; do not infer owner'})
    statuses[status]+=1;by_charge[(row['ChargeCategory'],status)]+=1;by_provider[(row['ProviderName'],status)]+=1
    if status=='valid':team_counts[team]+=1;env_counts[env]+=1
    tags_parsed.append((team,env,status))
for filename,rowsout,header in [
 ('day6_tag_exceptions.csv',exceptions,['csv_line','ProviderName','ChargeCategory','SubAccountId','ResourceId','TagStatus','Issues','Action']),
 ('day6_tag_distribution.csv',[{'Dimension':'team','Value':k,'Rows':v} for k,v in sorted(team_counts.items())]+[{'Dimension':'env','Value':k,'Rows':v} for k,v in sorted(env_counts.items())],['Dimension','Value','Rows'])]:
 with (OUT/filename).open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=header);w.writeheader();w.writerows(rowsout)
# Optional enriched file adds status, leaves original 26 columns unchanged
with (OUT/'focus_tag_audited_2026-q3.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.writer(f);w.writerow(cols+['allocation_team','allocation_env','tag_status']);
 for row,(team,env,status) in zip(rows,tags_parsed):w.writerow([row[c] for c in cols]+[team,env,status])
def summ(data):return {c:str(sum(D(r[c] or '0') for r in data)) for c in ('ListCost','ContractedCost','BilledCost','EffectiveCost','PricingQuantity')}
original_totals=summ(raw);cleaned_totals=summ(rows)
checks={
 'row_count_preserved':len(rows)==len(raw),
 'schema_and_order_preserved':cols==orig_cols,
 'no_exact_cleaned_duplicates':len({tuple(r[c] for c in cols) for r in rows})==len(rows),
 'cost_and_quantity_totals_reconcile':original_totals==cleaned_totals,
 'all_usage_rows_tagged':all(r['Tags'].strip() for r in rows if r['ChargeCategory']=='Usage'),
 'all_nonempty_tags_valid_team_and_env':all(s=='valid' for r,(_,_,s) in zip(rows,tags_parsed) if r['Tags'].strip()),
 'cost_currency_consistent':len({r['BillingCurrency'] for r in rows})==1,
 'all_charge_periods_parseable':all(_parse(r['ChargePeriodStart']) and _parse(r['ChargePeriodEnd']) for r in rows)
} if False else {}
def parse_date(s):
 try:datetime.fromisoformat(s.replace('Z','+00:00'));return True
 except (TypeError,ValueError):return False
checks={'row_count_preserved':len(rows)==len(raw),'schema_and_order_preserved':cols==orig_cols,
'no_exact_cleaned_duplicates':len({tuple(r[c] for c in cols) for r in rows})==len(rows),
'cost_and_quantity_totals_reconcile':original_totals==cleaned_totals,
'all_usage_rows_tagged':all(r['Tags'].strip() for r in rows if r['ChargeCategory']=='Usage'),
'all_nonempty_tags_valid_team_and_env':all(s=='valid' for r,(_,_,s) in zip(rows,tags_parsed) if r['Tags'].strip()),
'cost_currency_consistent':len({r['BillingCurrency'] for r in rows})==1,
'all_charge_periods_parseable':all(parse_date(r['ChargePeriodStart']) and parse_date(r['ChargePeriodEnd']) for r in rows)}
profile={'input_cleaned_file':source.name,'input_original_file':original.name,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
'rows':len(rows),'columns':len(cols),'status_counts':dict(statuses),'missing_by_charge':{c:sum(v for (cc,s),v in by_charge.items() if cc==c and s!='valid') for c in sorted(set(x[0] for x in by_charge))},
'provider_status':{p:{s:by_provider[(p,s)] for s in ('valid','absent','invalid','incomplete')} for p in sorted(set(x[0] for x in by_provider))},
'charge_status':{c:{s:by_charge[(c,s)] for s in ('valid','absent','invalid','incomplete')} for c in sorted(set(x[0] for x in by_charge))},
'original_totals':original_totals,'cleaned_totals':cleaned_totals,'checks':checks,'all_checks_pass':all(checks.values()),'team_distribution':dict(sorted(team_counts.items())),'environment_distribution':dict(sorted(env_counts.items()))}
(OUT/'day6_validation_results.json').write_text(json.dumps(profile,indent=2)+'\n')
print(json.dumps(profile,indent=2));
if not all(checks.values()):sys.exit(1)
