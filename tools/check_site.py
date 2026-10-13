#!/usr/bin/env python3
"""Sanity checks run on every push: data/*.json parses and has no Infinity/NaN tokens; internal links and assets in *.html resolve."""
import glob, json, os, re, sys
root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(root)
bad = []
for p in glob.glob('data/*.json'):
    raw = open(p, encoding='utf-8').read()
    if re.search(r'(?<![A-Za-z"])-?(?:Infinity|NaN)(?![A-Za-z"])', raw):
        bad.append(f'{p}: contains Infinity/NaN token')
    try:
        json.loads(raw, parse_constant=lambda c: (_ for _ in ()).throw(ValueError(c)))
    except Exception as e:
        bad.append(f'{p}: invalid JSON ({e})')
for page in glob.glob('*.html'):
    h = open(page, encoding='utf-8').read()
    for m in re.finditer(r'(?:href|src)="([^"#?:]+)(?:[?#][^"]*)?"', h):
        t = m.group(1)
        if t.startswith(('http', 'mailto', '//', 'data')) or not t:
            continue
        if not os.path.exists(t):
            bad.append(f'{page}: broken internal reference {t}')
n = json.load(open('data/news.json'))
if not n.get('items'):
    bad.append('data/news.json has no items')
print('\n'.join(bad) if bad else 'site checks passed')
sys.exit(1 if bad else 0)
