#!/usr/bin/env python3
"""Run the classifier over the harvested titles and print coverage, per-source scope rates, subgroup counts and samples."""
import collections, json, os, random, sys
sys.path.insert(0, os.path.dirname(__file__))
from classify import classify, SUBGROUPS, TOPICS, CORE
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
d = json.load(open(os.path.join(ROOT, 'data', 'analysis', 'corpus.json'), encoding='utf-8'))
res = [(it, classify(it['title'])) for it in d['items']]
why = collections.Counter(r['why'] for _, r in res)
print('in scope', sum(r['in_scope'] for _, r in res), 'of', len(res)); print(dict(why))
bys = collections.defaultdict(lambda: [0, 0])
for it, r in res: bys[it['source']][0] += 1; bys[it['source']][1] += r['in_scope']
for s, (n, k) in sorted(bys.items(), key=lambda x: -x[1][0]): print(f'  {s:38} {k:5}/{n:<5} {100*k/n:4.0f}%')
sub = collections.Counter(s for _, r in res if r['in_scope'] for s in r['subtopics'][:1])
print('primary subgroup counts'); [print(f'  {k:38} {v}') for k, v in sorted(sub.items())]
print('place', collections.Counter(r['place'] for _, r in res if r['in_scope']))
random.seed(int(sys.argv[1]) if len(sys.argv) > 1 else 1)
if '--samples' in sys.argv:
    for k in sorted(SUBGROUPS):
        pool = [it for it, r in res if r['in_scope'] and r['subtopics'][:1] == [k]]
        print('\n##', k, len(pool))
        for it in random.sample(pool, min(8, len(pool))): print('  -', it['source'][:14], '|', it['title'][:110])
if '--missed' in sys.argv:
    pool = [it for it, r in res if r['why'] in ('no-topic', 'topic-without-cost') and CORE.search(it['title'])]
    print('\n## in-health but unclassified', len(pool))
    for it in random.sample(pool, min(60, len(pool))): print('  -', it['source'][:14], '|', it['title'][:110])
