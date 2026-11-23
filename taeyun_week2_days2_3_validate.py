#!/usr/bin/env python3
"""Read-only local source/cleaned CSV and dbt-contract QA for Taeyun Week 2 Days 2–3.

Python 3.9+; standard library only. Does not connect to MySQL or run dbt.

From repository root (or extracted package root):
    python3 scripts/taeyun_week2_days2_3_validate.py \
        --raw /path/to/focus_exercise_2026-q3.csv \
        --clean data/taeyun/week2/focus_cleaned_2026-q3.csv \
        --sources-yml sources.yml --model-sql stg_billing.sql \
        --output outputs/taeyun/week2
"""
from __future__ import annotations
import argparse
import collections
import csv
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import re
import sys

FIELD_TO_ALIAS = {
    'BillingAccountId': 'billing_account_id',
    'SubAccountId': 'sub_account_id',
    'ProviderName': 'provider_name',
    'InvoiceIssuerName': 'invoice_issuer_name',
    'ServiceCategory': 'service_category',
    'ServiceName': 'service_name',
    'RegionId': 'region_id',
    'ChargeCategory': 'charge_category',
    'ChargeFrequency': 'charge_frequency',
    'ChargePeriodStart': 'charge_period_start',
    'ChargePeriodEnd': 'charge_period_end',
    'BillingPeriodStart': 'billing_period_start',
    'BillingPeriodEnd': 'billing_period_end',
    'BillingCurrency': 'billing_currency',
    'ListCost': 'list_cost',
    'ContractedCost': 'contracted_cost',
    'BilledCost': 'billed_cost',
    'EffectiveCost': 'effective_cost',
    'PricingQuantity': 'pricing_quantity',
    'PricingUnit': 'pricing_unit',
    'CommitmentDiscountId': 'commitment_discount_id',
    'CommitmentDiscountCategory': 'commitment_discount_category',
    'CommitmentDiscountStatus': 'commitment_discount_status',
    'ResourceId': 'resource_id',
    'Tags': 'tags',
    'x_Credits': 'x_credits',
}
DATE_FIELDS = {'ChargePeriodStart', 'ChargePeriodEnd', 'BillingPeriodStart', 'BillingPeriodEnd'}
DECIMAL_FIELDS = {'ListCost', 'ContractedCost', 'BilledCost', 'EffectiveCost', 'PricingQuantity', 'x_Credits'}
COST_FIELDS = ('ListCost', 'ContractedCost', 'BilledCost', 'EffectiveCost')
REQUIRED_FIELDS = ('BillingAccountId', 'ProviderName', 'ServiceName', 'ChargeCategory')
EXPECTED_SOURCE_TABLES = {'stg_focus_billing', 'Dim_Service', 'Dim_Tenant', 'Dim_Region', 'Fact_Spend'}


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def load_csv(path):
    with open(path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        rows = list(reader)
    return headers, rows


def parse_datetime(value):
    # The Gitika MySQL staging model strips a literal trailing Z and yields
    # timezone-naive DATETIME. Audit that this is safe for these UTC-only inputs.
    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if dt.tzinfo is None or dt.utcoffset().total_seconds() != 0:
        raise ValueError('Expected a UTC ISO-8601 timestamp ending Z')
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


def coerce(name, value):
    value = (value or '').strip()
    if not value:
        return None
    if name in DECIMAL_FIELDS:
        return Decimal(value)
    if name in DATE_FIELDS:
        return parse_datetime(value)
    if name == 'Tags':
        return json.loads(value)  # semantic equality, not JSON key order
    return value


def validate(rows, kind):
    errors, normalized = [], []
    for i, row in enumerate(rows, 2):
        out = {}
        for name in FIELD_TO_ALIAS:
            try:
                out[name] = coerce(name, row.get(name))
            except (InvalidOperation, ValueError, TypeError, json.JSONDecodeError) as err:
                errors.append({'source':kind,'csv_line':i,'column':name,'error':str(err)})
                out[name] = None
        normalized.append(out)
    return normalized, errors


def money_by_provider(norm):
    sums = collections.defaultdict(lambda: [0, *[Decimal(0) for _ in COST_FIELDS]])
    for row in norm:
        p = row['ProviderName'] or '(missing)'
        sums[p][0] += 1
        for i, name in enumerate(COST_FIELDS, 1):
            sums[p][i] += row[name] or Decimal(0)
    return sums


def write_csv(path, columns, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=columns)
        w.writeheader()
        w.writerows(rows)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--raw', required=True, type=Path)
    p.add_argument('--clean', required=True, type=Path)
    p.add_argument('--sources-yml', required=True, type=Path)
    p.add_argument('--model-sql', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    src_headers, src_rows = load_csv(args.raw)
    clean_headers, clean_rows = load_csv(args.clean)
    src, src_errors = validate(src_rows, 'source')
    clean, clean_errors = validate(clean_rows, 'clean')
    errors = src_errors + clean_errors

    source_sql = args.sources_yml.read_text(encoding='utf-8')
    model_sql = args.model_sql.read_text(encoding='utf-8')
    yaml_names = re.findall(r'(?m)^\s*-\s+name:\s+([A-Za-z_][\w]*)\s*$', source_sql)
    sql_aliases = [m.group(1) for line in model_sql.splitlines()
                   if (m := re.search(r'\bAS\s+([a-z_][a-z_\d]*)\s*,?\s*$', line, flags=re.I))]
    schema_match = re.search(r'(?m)^\s*schema:\s+([A-Za-z_][\w]*)\s*$', source_sql)
    actual_schema = schema_match.group(1) if schema_match else ''

    actual_aliases = list(sql_aliases)
    expected_aliases = list(FIELD_TO_ALIAS.values())
    src_by_provider = money_by_provider(src)
    clean_by_provider = money_by_provider(clean)
    sum_costs = lambda norm: {key: str(sum((r[key] or Decimal(0) for r in norm), Decimal(0))) for key in COST_FIELDS}
    blank_counts = lambda norm: {key: sum(r[key] is None for r in norm) for key in FIELD_TO_ALIAS}

    logical_mismatches = collections.Counter()
    for a, b in zip(src, clean):
        for name in FIELD_TO_ALIAS:
            if a[name] != b[name]:
                logical_mismatches[name] += 1

    source_duplicate_count = len(src_rows) - len({tuple(r.get(name, '') for name in FIELD_TO_ALIAS) for r in src_rows})
    clean_duplicate_count = len(clean_rows) - len({tuple(r.get(name, '') for name in FIELD_TO_ALIAS) for r in clean_rows})
    tag_exceptions = []
    tag_counts = collections.Counter()
    invalid_intervals = []
    required_missing = collections.Counter()
    for i, r in enumerate(clean, 2):
        for key in REQUIRED_FIELDS:
            if r[key] is None: required_missing[key] += 1
        s, e = r['ChargePeriodStart'], r['ChargePeriodEnd']
        bs, be = r['BillingPeriodStart'], r['BillingPeriodEnd']
        if any(v is None for v in (s, e, bs, be)) or s >= e or bs >= be:
            invalid_intervals.append(i)
        tags = r['Tags']
        status = 'valid' if isinstance(tags, dict) and tags.get('team') and tags.get('env') else ('missing' if tags is None else 'incomplete')
        tag_counts[status] += 1
        if status != 'valid':
            tag_exceptions.append({
                'csv_line':i,'provider':r['ProviderName'],'charge_category':r['ChargeCategory'],
                'billing_account_id':r['BillingAccountId'],'sub_account_id':r['SubAccountId'] or '',
                'tag_status':status,'handling':'retain NULL; do not invent an allocation'
            })
    usage_bad_tags = sum(1 for r in clean if r['ChargeCategory']=='Usage' and not (
        isinstance(r['Tags'],dict) and r['Tags'].get('team') and r['Tags'].get('env')))

    checks = {
        'source_is_expected_26_fields': src_headers == list(FIELD_TO_ALIAS),
        'cleaned_is_expected_26_fields': clean_headers == list(FIELD_TO_ALIAS),
        'row_counts_match_and_are_nonzero':len(src)==len(clean) and len(src)>0,
        'no_exact_duplicates_source':source_duplicate_count == 0,
        'no_exact_duplicates_cleaned':clean_duplicate_count == 0,
        'numeric_dates_tags_parse_without_errors':not errors,
        'raw_vs_clean_semantic_content_identical':not logical_mismatches,
        'raw_vs_clean_cost_totals_identical':sum_costs(src) == sum_costs(clean),
        'raw_vs_clean_provider_counts_and_costs_identical':dict(src_by_provider) == dict(clean_by_provider),
        'required_attributes_present':not required_missing,
        'periods_present_and_ascending':not invalid_intervals,
        'usage_cost_allocation_tags_valid':usage_bad_tags == 0,
        'sources_yml_target_schema': actual_schema.lower()=='multi_cloud_finops',
        'sources_yml_has_billing_and_warehouse_tables': 'finops_raw' in yaml_names and EXPECTED_SOURCE_TABLES.issubset(set(yaml_names)),
        'dbt_model_uses_expected_source':bool(re.search(r"source\s*\(\s*['\"]finops_raw['\"]\s*,\s*['\"]stg_focus_billing['\"]\s*\)",model_sql)),
        'dbt_model_26_expected_aliases':actual_aliases==expected_aliases,
        'dbt_model_has_datetime_and_decimal_casts': all(('STR_TO_DATE' in model_sql and 'CAST' in model_sql,
            all(re.search(r'(?i)CAST\s*\(.*?AS\s+DECIMAL\(18,\s*6\)\)\s+AS\s+'+alias,model_sql,re.S) for alias in
                ('list_cost','contracted_cost','billed_cost','effective_cost','pricing_quantity','x_credits')))),
        'dbt_model_normalizes_optional_empty_values':bool(re.search(r"NULLIF\s*\(\s*TRIM\s*\(\s*Tags\s*\)\s*,\s*''\s*\)\s+AS\s+tags",model_sql,re.I)),
    }

    field_profile=[]
    for field, alias in FIELD_TO_ALIAS.items():
        typ = 'timestamp_utc_to_mysql_datetime' if field in DATE_FIELDS else ('decimal_18_6' if field in DECIMAL_FIELDS else ('json_text' if field=='Tags' else 'text'))
        field_profile.append({'source_column':field,'dbt_column':alias,'planned_staging_type':typ,
            'raw_nulls':sum(r[field] is None for r in src),'cleaned_nulls':sum(r[field] is None for r in clean),
            'distinct_cleaned_nonnull':len({json.dumps(r[field],sort_keys=True) if isinstance(r[field],dict) else str(r[field]) for r in clean if r[field] is not None})})
    write_csv(args.output/'day2_source_field_profile.csv',list(field_profile[0]),field_profile)
    write_csv(args.output/'day3_tag_exceptions.csv',['csv_line','provider','charge_category','billing_account_id','sub_account_id','tag_status','handling'],tag_exceptions)

    provider_rows=[]
    for pvd in sorted(set(src_by_provider)|set(clean_by_provider)):
        a=src_by_provider[pvd]; b=clean_by_provider[pvd]
        provider_rows.append({'provider':pvd,'raw_rows':a[0],'cleaned_rows':b[0],
            'raw_billed_cost':str(a[3]),'cleaned_billed_cost':str(b[3]),
            'raw_effective_cost':str(a[4]),'cleaned_effective_cost':str(b[4]),
            'reconciled':a==b})
    write_csv(args.output/'day3_provider_reconciliation.csv',list(provider_rows[0]),provider_rows)

    result = {
      'scope':'Local QA of Gitika committed dbt source and staging SQL vs raw/Week 1 cleaned CSV; not a dbt run or live MySQL verification',
      'source_model_snapshot_sha256':{'sources_yml':sha256(args.sources_yml),'stg_billing_sql':sha256(args.model_sql)},
      'input_sha256':{'raw':sha256(args.raw),'clean':sha256(args.clean)},
      'row_counts':{'raw':len(src),'clean':len(clean)},
      'source_columns':len(src_headers),'staging_model_aliases':len(actual_aliases),
      'source_database_schema_from_yaml':actual_schema,
      'source_tables_from_yaml':yaml_names,
      'dates':{'min_charge_period_start':min((r['ChargePeriodStart'] for r in clean if r['ChargePeriodStart']),default=None).isoformat() if clean else None,
               'max_charge_period_start':max((r['ChargePeriodStart'] for r in clean if r['ChargePeriodStart']),default=None).isoformat() if clean else None},
      'cost_totals_usd':sum_costs(clean),
      'missing_values_clean':blank_counts(clean),
      'duplicate_rows':{'raw':source_duplicate_count,'clean':clean_duplicate_count},
      'tag_counts':dict(tag_counts),'usage_rows_with_incomplete_tags':usage_bad_tags,
      'tag_exceptions_by_charge_category':dict(collections.Counter(r['charge_category'] for r in tag_exceptions)),
      'raw_clean_field_mismatch_counts':dict(logical_mismatches),
      'required_field_missing_counts':dict(required_missing),
      'invalid_period_rows':invalid_intervals[:30],
      'parsing_errors':errors[:30],
      'checks':checks,
      'checks_passed':sum(checks.values()),'checks_total':len(checks),
      'status':'PASS' if all(checks.values()) else 'FAIL',
      'limitations':['Actual MySQL database not accessible; dbt debug and dbt run not independently executed',
        'GitHub main currently contains sources.yml and stg_billing.sql at repository root, not a complete committed dbt_project.yml and models directory',
        'Datetime test only covers UTC Z timestamps in this synthetic Q3 data',
        'Original tag JSON may have different key order from cleaned JSON; semantic equality is used'],
    }
    (args.output/'day2_day3_validation.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(f"Taeyun Week 2 Days 2-3: {result['status']} ({result['checks_passed']}/{result['checks_total']} checks)")
    print('Rows:',len(src),' | BilledCost:',result['cost_totals_usd']['BilledCost'],' | EffectiveCost:',result['cost_totals_usd']['EffectiveCost'])
    print('Source tags:',dict(tag_counts),' | SQL model aliases:',len(actual_aliases))
    if not all(checks.values()):
        print('Failed checks:',[k for k,v in checks.items() if not v])
        return 1
    return 0

if __name__=='__main__':
    sys.exit(main())
