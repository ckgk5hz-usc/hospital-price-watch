#!/usr/bin/env python3
"""Check data/benchmarks.json against its sources.
Each entry with a downloadable `doc` is fetched (cached in tools/data/.cache), converted with pdftotext, and every
string in `checks` must appear in it. Entries whose site blocks scripted downloads must carry `checked_by_hand`.
--age prints BENCH_STALE lines for entries published more than 18 months ago and exits 0 (used by the yearly workflow)."""
import json, re, sys, subprocess, urllib.request, datetime, hashlib
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
CACHE = Path(__file__).resolve().parent / '.cache'
CACHE.mkdir(exist_ok=True)
UA = {'User-Agent': 'Mozilla/5.0 (Macintosh) Chrome/120 Safari/537.36'}
B = {k: v for k, v in json.load(open(ROOT / 'data/benchmarks.json')).items() if not k.startswith('_')}

if '--age' in sys.argv:
    today = datetime.date.today()
    for k, v in B.items():
        y, m = (list(map(int, v['published'].split('-'))) + [1, 1])[:2]
        if (today.year - y) * 12 + today.month - m > 18:
            print(f'BENCH_STALE: {k} ({v["title"]}, published {v["published"]}) is over 18 months old; look for a newer edition and update data/benchmarks.json.')
    sys.exit(0)

bad, n = [], 0
norm = lambda s: re.sub(r'\s+', ' ', s)
for k, v in B.items():
    if not v['checks']:
        if not v.get('checked_by_hand'):
            bad.append(f'{k}: no automatic checks and no checked_by_hand date')
        else:
            print(f'{k}: checked by hand {v["checked_by_hand"]} (source blocks scripted downloads)')
        continue
    pdf = CACHE / ('bench_' + hashlib.md5(v['doc'].encode()).hexdigest()[:10] + '.pdf')
    if not pdf.exists() or pdf.stat().st_size < 10000:
        pdf.write_bytes(urllib.request.urlopen(urllib.request.Request(v['doc'], headers=UA), timeout=300).read())
    text = norm(subprocess.run(['pdftotext', '-layout', str(pdf), '-'], capture_output=True, text=True).stdout)
    for s in v['checks']:
        n += 1
        if norm(s) not in text:
            bad.append(f'{k}: "{s}" not found in {v["doc"]}')
print(f'{n} checks;', 'FAILED:\n  ' + '\n  '.join(bad) if bad else 'all passed')
sys.exit(1 if bad else 0)
