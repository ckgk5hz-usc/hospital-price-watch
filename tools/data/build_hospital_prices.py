#!/usr/bin/env python3
"""Build data/hospital_prices.json and data/downloads/hospital_prices.csv from HCAI's Hospital Measurement Combined Dataset.

Source: OHCA/HCAI, https://hcai.ca.gov/document/hospital-measurement-combined-dataset-2022-2023/ (values come from hospitals' annual
financial reports; case mix from patient discharge data; visit intensity from the Health Care Payments Data program).
Kept: general acute care hospitals with enough volume for a per-stay or per-visit figure to mean something (thresholds below).
Every published per-unit value is recomputed from HCAI's own revenue and volume columns and must match. A figure failing the screen is
left blank, never estimated. Exits non-zero on a changed layout. Prints HCAI_STALE when the file is more than 18 months old.
"""
import csv, datetime, json, re, statistics as st, sys, urllib.request
from pathlib import Path
import openpyxl
ROOT = Path(__file__).resolve().parents[2]
CACHE = Path(__file__).resolve().parent / '.cache'
CACHE.mkdir(exist_ok=True)
URL = 'https://hcai.ca.gov/document/hospital-measurement-combined-dataset-2022-2023/'
COST_URL = 'https://hcai.ca.gov/document/ohca-hospital-cost-data-set/'  # holds OHCA's high_cost_hospital_d flag (2018-2022 data)
RENAMED = {'SALINAS VALLEY MEMORIAL HOSPITAL': 'SALINAS VALLEY HEALTH MEDICAL CENTER'}  # same HCAI facility, renamed between the two files
# CDPH's facility listing links HCAI_ID and license number to the CMS certification number (CCN), so quality joins exactly. Names are never matched.
CDPH_URL = 'https://data.chhs.ca.gov/dataset/3b5b80e8-6b8d-4715-b3c0-2699af6e72e5/resource/f0ae5731-fef8-417f-839d-54a0ed3a126e/download/health_facility_locations.csv'
CMS_META = 'https://data.cms.gov/provider-data/api/1/metastore/schemas/dataset/items/xubh-q36u'
MIN_STAYS, MIN_VISITS = 100, 1000  # per payer, per year
ODD_LOW, ODD_HIGH = .75, 5  # commercial-to-Medicare ratios outside this band are flagged, not removed


def number(x):
    return x if isinstance(x, (int, float)) and x > 0 else None


def fetch(url, name, minsize=50000):
    p = CACHE / name
    if not p.exists() or p.stat().st_size < minsize:
        p.write_bytes(urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'curl/8.7'}), timeout=180).read())
    return p


def quality():
    """Returns {hcai id or license: (ccn, cah)}, {ccn: rating}, and the CMS file's date."""
    meta = json.loads(urllib.request.urlopen(urllib.request.Request(CMS_META, headers={'User-Agent': 'curl/8.7'}), timeout=60).read())  # CMS rejects browser-like agents from scripts
    rows = list(csv.DictReader(fetch(meta['distribution'][0]['downloadURL'], 'cms_hospital.csv').open(encoding='utf-8-sig')))
    if 'Hospital overall rating' not in rows[0]:
        sys.exit('CMS layout changed')
    stars = {r['Facility ID'].strip(): (int(r['Hospital overall rating']) if r['Hospital overall rating'] in '12345' else None, r['Facility Name'], r['City/Town']) for r in rows if r['State'] == 'CA'}
    fac = list(csv.DictReader(fetch(CDPH_URL, 'cdph_facilities.csv').open(encoding='utf-8-sig', errors='replace')))
    link = {}
    for r in fac:
        if r['FAC_STATUS_TYPE_CODE'] != 'OPEN' or not r['CCN'].strip():
            continue
        v = (r['CCN'].strip(), r.get('CRITICAl_ACCESS_HOSPITAL', '').strip().upper() in ('Y', 'YES', 'D'))
        for k in (r['HCAI_ID'].strip(), r['LICENSE_NUMBER'].strip()):
            if k:
                link[k] = v
    return link, stars, meta.get('modified', '')


def main():
    p = CACHE / 'hcai_hospital_measurement.xlsx'
    if not p.exists() or p.stat().st_size < 50000:
        p.write_bytes(urllib.request.urlopen(urllib.request.Request(URL, headers={'User-Agent': 'Mozilla/5.0 Chrome/120'}), timeout=120).read())
    wb = openpyxl.load_workbook(p, data_only=True)
    updated = next(r[2] for r in wb['README'].iter_rows(values_only=True) if r[1] == 'Last updated')
    if (datetime.datetime.now() - updated).days > 548:
        print(f'HCAI_STALE: the Hospital Measurement Combined Dataset was last updated {updated:%Y-%m-%d}; look for a newer edition at https://hcai.ca.gov/affordability/ohca/office-of-health-care-affordability-data-and-reports/ and update URL in tools/data/build_hospital_prices.py.')
    ws = next(wb[n] for n in wb.sheetnames if n.startswith('hospital_dataset'))
    rows = list(ws.iter_rows(values_only=True))
    need = ['fac_no', 'fac_name', 'cy', 'end_date', 'dis_thrd', 'dis_mcar', 'cmi_thrd', 'cmi_mcar', 'est_ip_npr_thrd', 'est_ip_npr_mcar', 'ip_npr_per_cmad_thrd', 'ip_npr_per_cmad_mcar',
            'vis_thrd', 'vis_mcar', 'avi_thrd', 'avi_mcare', 'est_op_npr_thrd', 'est_op_npr_mcar', 'op_npr_per_iav_thrd', 'op_npr_per_iav_mcar']
    miss = [c for c in need if c not in rows[0]]
    if miss:
        sys.exit(f'layout changed, missing: {miss}')
    recs = [dict(zip(rows[0], r)) for r in rows[1:] if r[0]]
    year = max(r['cy'] for r in recs)
    hosp = {h['oshpd_id']: h for h in json.load(open(ROOT / 'data/hospitals.json'))['hospitals']}
    bad, out, seen, dropped = [], [], {}, {'not_general_acute': 0, 'not_matched': 0}
    q = CACHE / 'hcai_hospital_cost.csv'
    if not q.exists() or q.stat().st_size < 50000:
        q.write_bytes(urllib.request.urlopen(urllib.request.Request(COST_URL, headers={'User-Agent': 'Mozilla/5.0 Chrome/120'}), timeout=120).read())
    high = {RENAMED.get(r['hospital_name'], r['hospital_name']) for r in csv.DictReader(q.open(encoding='utf-8-sig', errors='replace')) if r['high_cost_hospital_d'] == '1'}
    link, stars, cms_date = quality()
    odd = lambda x: x is not None and not ODD_LOW <= x <= ODD_HIGH

    def per_unit(r, rev, vol, adj, pub, floor):
        """Published value if volume is enough and it reproduces from revenue / (volume x adjustment)."""
        a, b, c, v = number(r[rev]), number(r[vol]), number(r[adj]), number(r[pub])
        if not (a and b and c and v) or b < floor:
            return None
        if abs(a / (b * c) / v - 1) > .001:
            bad.append(f'{r["fac_name"]} {r["cy"]} {pub}: recomputed {a / (b * c):.0f}, published {v:.0f}')
        return v

    for r in recs:
        if r['cy'] != year:
            continue
        h = hosp.get(str(r['fac_no']))
        if h is None:
            dropped['not_matched'] += 1; continue
        if not h.get('is_general_acute'):
            dropped['not_general_acute'] += 1; continue
        ic = per_unit(r, 'est_ip_npr_thrd', 'dis_thrd', 'cmi_thrd', 'ip_npr_per_cmad_thrd', MIN_STAYS)
        im = per_unit(r, 'est_ip_npr_mcar', 'dis_mcar', 'cmi_mcar', 'ip_npr_per_cmad_mcar', MIN_STAYS)
        oc = per_unit(r, 'est_op_npr_thrd', 'vis_thrd', 'avi_thrd', 'op_npr_per_iav_thrd', MIN_VISITS)
        om = per_unit(r, 'est_op_npr_mcar', 'vis_mcar', 'avi_mcare', 'op_npr_per_iav_mcar', MIN_VISITS)
        if not (ic or oc):
            continue
        rec = {'name': r['fac_name'], 'id': str(r['fac_no']), 'city': h.get('city'), 'county': h.get('county'), 'period_end': r['end_date'],
               'ip': round(ic) if ic else None, 'ip_mcr': round(im) if im else None, 'ip_x': round(ic / im, 2) if ic and im else None, 'stays': r['dis_thrd'],
               'op': round(oc) if oc else None, 'op_mcr': round(om) if om else None, 'op_x': round(oc / om, 2) if oc and om else None, 'visits': r['vis_thrd']}
        l = link.get(str(r['fac_no'])) or link.get(str(r.get('license_num')))
        rec['ccn'], rec['cah'] = l if l else (None, False)
        rating, cname, ccity = stars.get(rec['ccn'], (None, '', ''))
        # A hospital sold or merged can carry a number that CMS now lists under another facility. Different city and no shared name word: leave the rating blank.
        words = lambda t: set(re.findall(r'[a-z]+', t.lower())) - {'hospital', 'medical', 'center', 'health', 'regional', 'community', 'of', 'the', 'and', 'mc', 'st', 'saint'}
        if ccity and ccity.lower() != (h.get('city') or '').lower() and not words(cname) & words(rec['name']):
            rating = None; dropped['rating_blanked_mismatch'] = dropped.get('rating_blanked_mismatch', 0) + 1
        rec['stars'] = rating
        rec['ip_odd'], rec['op_odd'], rec['high_cost'] = odd(rec['ip_x']), odd(rec['op_x']), rec['name'] in high
        k = rec['name']
        if k in seen:  # two filings ending in one year: keep the later one
            if rec['period_end'] <= seen[k]['period_end']:
                continue
            out.remove(seen[k])
        seen[k] = rec
        out.append(rec)
    if bad:
        print('FAILED recompute:\n  ' + '\n  '.join(bad[:30])); sys.exit(1)
    if len(out) < 150:
        sys.exit(f'only {len(out)} hospitals kept')
    out.sort(key=lambda x: x['name'])
    missing = high - {x['name'] for x in out}
    if missing or len(high) < 5:
        sys.exit(f'OHCA high-cost hospitals not matched: {missing or len(high)}')
    stat = lambda k: round(st.median(x[k] for x in out if x[k]), 2)
    summary = {k: stat(k) for k in ('ip', 'ip_mcr', 'ip_x', 'op', 'op_mcr', 'op_x')}
    by = {}
    for x in out:
        if x['ip'] and x['stars']:
            by.setdefault(x['stars'], []).append(x['ip'])
    star_tbl = [{'stars': k, 'n': len(by[k]), 'median_ip': round(st.median(by[k]))} for k in sorted(by)]
    summary.update(with_ccn=sum(1 for x in out if x['ccn']), with_stars=sum(1 for x in out if x['stars']), cah=sum(1 for x in out if x['cah']))
    if summary['with_ccn'] < len(out) * .8:
        sys.exit(f'only {summary["with_ccn"]} of {len(out)} hospitals linked to a CMS number')
    summary.update(n=len(out), n_ip=sum(1 for x in out if x['ip']), n_ip_x=sum(1 for x in out if x['ip_x']), n_op_x=sum(1 for x in out if x['op_x']), n_all=len(recs))
    (ROOT / 'data/hospital_prices.json').write_text(json.dumps({'year': year, 'updated': f'{updated:%Y-%m-%d}', 'source': URL, 'min_stays': MIN_STAYS, 'min_visits': MIN_VISITS, 'odd_low': ODD_LOW, 'odd_high': ODD_HIGH, 'cost_source': COST_URL, 'cms_date': cms_date, 'star_table': star_tbl, 'summary': summary, 'dropped': dropped, 'hospitals': out}, separators=(',', ':'), allow_nan=False))
    (ROOT / 'data/downloads').mkdir(exist_ok=True)
    with open(ROOT / 'data/downloads/hospital_prices.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['hospital', 'hcai_id', 'city', 'county', 'reporting_period_end', 'commercial_per_adjusted_stay', 'medicare_per_adjusted_stay', 'commercial_to_medicare_stay', 'commercial_stays',
                    'commercial_per_adjusted_visit', 'medicare_per_adjusted_visit', 'commercial_to_medicare_visit', 'commercial_visits', 'cms_certification_number', 'cms_overall_star_rating', 'critical_access'])
        for x in out:
            w.writerow([x['name'], x['id'], x['city'], x['county'], x['period_end'], x['ip'], x['ip_mcr'], x['ip_x'], x['stays'], x['op'], x['op_mcr'], x['op_x'], x['visits'], x['ccn'], x['stars'], x['cah']])
    print(f'{len(out)} hospitals, year {year}; medians {summary}; dropped {dropped}')


if __name__ == '__main__':
    main()
