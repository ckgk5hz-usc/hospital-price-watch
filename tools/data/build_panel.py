"""Builds per-hospital yearly series (FY2012-FY2024) and segment fields from the HCAI multi-year panel
(years_data.xlsx, one harmonized sheet per year) and merges them into data/hospitals.json.
Run from the repo root with the Issue Brief Project venv:  <venv>/bin/python tools/data/build_panel.py
Needs local files (OneDrive), so it is NOT run in GitHub Actions; the output JSON is committed."""
import sys, json, math
sys.path.insert(0, '/Users/ckgk5hz/Documents/Claude/Projects/Melnick/Melnick/Issue Brief Project/code')
import numpy as np
from hcai_panel import HCAIPanel

YEARS = list(range(2012, 2025))
SUMMARY = {}

def nid(x):
    s = str(x).strip()
    return s[:-2] if s.endswith('.0') else s

def clean(v, nd=None):
    if v is None: return None
    try: f = float(v)
    except (TypeError, ValueError): return None
    if not math.isfinite(f): return None
    return round(f, nd) if nd is not None else int(round(f))

p = HCAIPanel()
frames = {}
for y in YEARS:
    d = p.year(y).copy()
    d['fac_no'] = d['fac_no'].map(nid)
    d = d[d['fac_no'].str.match(r'^\d{9}$')].drop_duplicates('fac_no').set_index('fac_no')
    frames[y] = d

data = json.load(open('data/hospitals.json'))
H = data['hospitals']
old_annual = {h['oshpd_id']: h.get('annual', {}) for h in H}

def metrics(r):
    days = r.get('period_days')
    full = days is not None and not (isinstance(days, float) and math.isnan(days)) and days >= 350
    out = {}
    if not full: return None
    g = lambda k: r.get(k) if k in r.index else np.nan
    gross, net, oprev, opexp = g('gross_rev'), g('net_pt_rev'), g('op_rev'), g('op_exp')
    opinc, nonop, ni = g('op_income'), g('nonop_rev'), g('net_income')
    out['net_patient_revenue'] = clean(net); out['gross_patient_revenue'] = clean(gross)
    out['total_operating_revenue'] = clean(oprev); out['total_operating_expenses'] = clean(opexp)
    out['operating_income'] = clean(opinc); out['net_income'] = clean(ni)
    out['operating_margin'] = clean(opinc / oprev, 5) if oprev and oprev > 0 else None
    tot = (oprev if oprev == oprev else 0) + (nonop if nonop == nonop else 0)
    out['total_margin'] = clean(ni / tot, 5) if tot and tot > 0 else None
    uc = (g('bad_debt') if g('bad_debt') == g('bad_debt') else 0) + (g('charity_oth') if g('charity_oth') == g('charity_oth') else 0) + (g('charity_hb') if g('charity_hb') == g('charity_hb') else 0)
    out['uncompensated_care_rate'] = clean(uc / gross, 5) if gross and gross > 0 else None
    gop, gip = g('gr_op_tot'), g('gr_ip_tot')
    out['outpatient_share'] = clean(gop / (gop + gip), 5) if gop == gop and gip == gip and (gop + gip) > 0 else None
    out['charge_ratio'] = clean(gross / net, 3) if gross == gross and net == net and net > 0 else None
    dis, dday = g('dis_tot'), g('day_tot')
    out['discharges'] = clean(dis) if dis == dis and dis > 0 else None
    out['avg_stay_days'] = clean(dday / dis, 2) if dis == dis and dis > 0 and dday == dday else None
    mc = (g('dis_mcal_tr') if g('dis_mcal_tr') == g('dis_mcal_tr') else 0) + (g('dis_mcal_mc') if g('dis_mcal_mc') == g('dis_mcal_mc') else 0)
    pv = (g('dis_thrd_tr') if g('dis_thrd_tr') == g('dis_thrd_tr') else 0) + (g('dis_thrd_mc') if g('dis_thrd_mc') == g('dis_thrd_mc') else 0)
    out['medical_discharge_share'] = clean(mc / dis, 4) if dis == dis and dis > 0 else None
    out['private_discharge_share'] = clean(pv / dis, 4) if dis == dis and dis > 0 else None
    return out

# ---- yearly series ----
covered = 0; partial = 0
for h in H:
    oid = h['oshpd_id']; ann = {}
    for y in YEARS:
        fr = frames[y]
        if oid not in fr.index: continue
        m = metrics(fr.loc[oid])
        if m is None: partial += 1; continue
        ann[str(y)] = m
    if ann: covered += 1
    else: ann = old_annual.get(oid, {})
    # FY2024: the standalone FY2024 disclosure file is newer than the panel's 'In Process' 2024 rows, so its values win for the base measures
    o24 = old_annual.get(oid, {}).get('2024')
    if o24:
        base = ann.setdefault('2024', {})
        for k, v in o24.items():
            if v is not None: base[k] = v
    h['annual'] = ann
    h['operating_margin_trend'] = {y: v.get('operating_margin') for y, v in ann.items()}
SUMMARY['hospitals_with_panel_series'] = covered; SUMMARY['partial_year_reports_dropped'] = partial

# ---- segments from the latest year each hospital filed ----
SYS_TOP = None
def latest_row(oid):
    for y in reversed(YEARS):
        if oid in frames[y].index: return frames[y].loc[oid], y
    return None, None
CTRL = {'Non-Profit': 'Nonprofit', 'Investor': 'Investor-owned', 'District': 'Health care district', 'City/County': 'City or county', 'State': 'State'}
for h in H:
    r, y = latest_row(h['oshpd_id'])
    if r is None: h['segments'] = None; continue
    sysn = str(r.get('system')).strip() if r.get('system') is not None else ''
    h['segments'] = {
        'ownership': CTRL.get(str(r.get('control')).strip(), None),
        'system': None if sysn in ('', 'N/A', 'nan', 'None') else sysn.title().replace('Of ', 'of '),
        'safety_net': True if str(r.get('dsh_hosp')).strip() == 'DSH' else (False if str(r.get('dsh_hosp')).strip() == 'Non-DSH' else None),
        'setting': 'Rural' if bool(r.get('rural')) else ('Teaching' if bool(r.get('teaching')) else 'Urban, non-teaching'),
        'segment_year': y,
    }
# patient-income proxy: share of gross charges billed to Medi-Cal + county indigent programs (HCAI has no patient income field)
for h in H:
    pm = h.get('payer_mix')
    if pm and pm.get('medical') is not None:
        pub = (pm.get('medical') or 0) + (pm.get('county') or 0)
        h['low_income_share'] = round(pub, 4)

# ---- validation of the adaptation: panel vs the FY2022/23/24 disclosure files (old_annual) ----
chk = {}
for y in ('2022', '2023'):
    for k in ('net_patient_revenue', 'operating_income', 'net_income', 'total_operating_expenses', 'uncompensated_care_rate'):
        tot = ok = 0; maxrel = 0
        for h in H:
            a = h['annual'].get(y, {}).get(k); b = old_annual.get(h['oshpd_id'], {}).get(y, {}).get(k)
            if a is None or b is None: continue
            tot += 1
            tol = 0.02 * max(abs(b), 1e-9) if k != 'uncompensated_care_rate' else 0.002
            if k == 'uncompensated_care_rate': tol = 0.002
            if abs(a - b) <= max(tol, 1): ok += 1
        chk['%s/%s' % (y, k)] = (ok, tot)
SUMMARY['panel_vs_disclosure_files(match, compared)'] = chk
data['years_note'] = 'annual: per-hospital yearly series FY2012-FY2024 from the HCAI multi-year panel (harmonized annual disclosure); FY2024 base measures are overridden by the newer standalone FY2024 disclosure file. Fiscal year = year the reporting period ends. Reports shorter than 350 days are left out. FY2024 is preliminary.'
s = json.dumps(data, allow_nan=False, separators=(',', ':'))
open('data/hospitals.json', 'w').write(s)
print(json.dumps(SUMMARY, indent=1)); print(len(s) // 1024, 'KB')
