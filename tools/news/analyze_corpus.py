#!/usr/bin/env python3
"""Count words and phrases in the harvested titles (data/analysis/corpus.json) and write an Excel workbook for review.

Counts are by title (a word counted once per title) so one long headline cannot inflate a word. Plural forms are folded together.
Output: data/analysis/corpus_frequency.xlsx (sheets: Titles, Words, Phrases, By source, Sources) and data/analysis/freq.json.
Needs openpyxl, so run with the Issue Brief venv:  <venv>/bin/python tools/news/analyze_corpus.py
"""
import collections, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from classify import classify, SUBGROUPS, TOPICS
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SRC = os.path.join(ROOT, 'data', 'analysis', 'corpus.json')
XLSX = os.path.join(ROOT, 'data', 'analysis', 'corpus_frequency.xlsx')
FREQ = os.path.join(ROOT, 'data', 'analysis', 'freq.json')

STOP = set('''a about above after again against all also am an and any are aren't as at be because been before being below between both but by can can't cannot could did do does doing don't down during each few for from further had has have having he her here hers him his how i if in into is it its itself just let me more most my no nor not now of off on once only or other our out over own same she should so some such than that the their them then there these they this those through to too under until up us very was we were what when where which while who whom why will with would you your
says say said new may might will could would one two three four first last how why what who amid per via vs get gets got make makes made take takes took finds find found shows show showed set sets plans plan year years week weeks day days month months today thursday monday tuesday wednesday friday saturday sunday ago back like need needs want wants way ways look looks next many much still even ahead less well top big 2024 2025 2026 2023 us u.s s t'''.split())
WORD = re.compile(r"[a-z0-9][a-z0-9'’\-\.]*[a-z0-9]|[a-z0-9]")


def toks(title):
    t = title.lower().replace('’', "'")
    t = re.sub(r"'s\b", '', t)
    return [w.strip(".-'") for w in WORD.findall(t) if w.strip(".-'")]


def fold(w):
    if len(w) > 4 and w.endswith('ies'): return w[:-3] + 'y'
    if len(w) > 4 and w.endswith('s') and not w.endswith(('ss', 'us', 'is')): return w[:-1]
    return w


def main():
    d = json.load(open(SRC, encoding='utf-8'))
    items = d['items']
    uni, bi, tri = collections.Counter(), collections.Counter(), collections.Counter()
    uni_src, bi_src = collections.defaultdict(collections.Counter), collections.defaultdict(collections.Counter)
    srcw = collections.defaultdict(collections.Counter)
    for it in items:
        ws = [fold(w) for w in toks(it['title'])]
        keep = [w for w in ws if w not in STOP and not w.isdigit() and len(w) > 1]
        u = set(keep)
        for w in u:
            uni[w] += 1; uni_src[w][it['source']] += 1; srcw[it['source']][w] += 1
        # phrases are built from consecutive tokens with stopwords allowed only inside (of/for/to/and) to keep 'cost of care' style units
        seq = [w for w in ws if not w.isdigit()]
        b, t3 = set(), set()
        for i in range(len(seq) - 1):
            if seq[i] in STOP or seq[i + 1] in STOP: continue
            b.add(seq[i] + ' ' + seq[i + 1])
        for i in range(len(seq) - 2):
            if seq[i] in STOP or seq[i + 2] in STOP: continue
            if seq[i + 1] in STOP and seq[i + 1] not in ('of', 'for', 'to', 'and', 'in', 'on') : continue
            t3.add(' '.join(seq[i:i + 3]))
        for p in b:
            bi[p] += 1; bi_src[p][it['source']] += 1
        for p in t3:
            tri[p] += 1; bi_src[p][it['source']] += 1
    N = len(items)
    cls = {it['url']: classify(it['title']) for it in items}
    words = [(w, c, len(uni_src[w]), uni_src[w].most_common(1)[0][0], round(100 * c / N, 2)) for w, c in uni.most_common(1500)]
    phrases = [(p, c, len(bi_src[p]), bi_src[p].most_common(1)[0][0]) for p, c in (bi + tri).most_common(2500) if c >= 4]
    json.dump({'n_titles': N, 'words': words, 'phrases': phrases}, open(FREQ, 'w'), ensure_ascii=False)

    wb = Workbook()
    ws = wb.active; ws.title = 'Titles'
    H = PatternFill('solid', fgColor='1F3A5F'); HF = Font(bold=True, color='FFFFFF', name='Arial')
    def sheet(ws, head, rows, widths):
        ws.append(head)
        for c in ws[1]: c.fill, c.font = H, HF
        for r in rows: ws.append(list(r))
        for i, w in enumerate(widths, 1): ws.column_dimensions[get_column_letter(i)].width = w
        ws.freeze_panes = 'A2'; ws.auto_filter.ref = ws.dimensions
        for row in ws.iter_rows(min_row=2):
            for c in row: c.font = Font(name='Arial', size=10)
    def lab(i):
        r = cls[i['url']]
        return (i['source'], i['date'], i['title'], 'yes' if r['in_scope'] else 'no', r['why'], TOPICS.get(r['topics'][0], '') if r['topics'] else '',
                '; '.join(SUBGROUPS[x] for x in r['subtopics']), r['place'] or '', i['url'])
    sheet(ws, ['Source', 'Date', 'Title', 'In scope', 'Why', 'Topic', 'Subgroups', 'Place', 'URL'], [lab(i) for i in sorted(items, key=lambda x: (x['source'], x['date'] or ''))], [28, 11, 100, 9, 22, 24, 50, 11, 50])
    tot = collections.Counter(); ex = collections.defaultdict(list); bysrc = collections.defaultdict(collections.Counter)
    for i in items:
        r = cls[i['url']]
        if r['in_scope'] and r['subtopics']:
            k = r['subtopics'][0]; tot[k] += 1; bysrc[k][i['source']] += 1
            if len(ex[k]) < 3: ex[k].append(i['title'])
    sheet(wb.create_sheet('Taxonomy'), ['Topic', 'Subgroup', 'Titles (primary)', 'Top sources', 'Examples'],
          [(TOPICS[k.split('/')[0]], SUBGROUPS[k], c, ', '.join(f'{s} {n}' for s, n in bysrc[k].most_common(3)), ' | '.join(ex[k])) for k, c in sorted(tot.items())], [28, 40, 16, 60, 120])
    why = collections.Counter(r['why'] for r in cls.values())
    sheet(wb.create_sheet('Scope gate'), ['Outcome', 'Titles'], sorted(why.items(), key=lambda x: -x[1]), [34, 10])
    resid = collections.Counter()
    from classify import CORE
    for i in items:
        r = cls[i['url']]
        if not r['in_scope'] and r['why'] in ('no-topic', 'topic-without-cost') and CORE.search(i['title']):
            for w in {fold(x) for x in toks(i['title'])} - STOP:
                if not w.isdigit() and len(w) > 2: resid[w] += 1
    sheet(wb.create_sheet('Unclassified words'), ['Word', 'Titles'], resid.most_common(300), [24, 10])
    sheet(wb.create_sheet('Words'), ['Word', 'Titles containing', 'Sources', 'Top source', '% of titles'], words, [22, 18, 10, 34, 12])
    sheet(wb.create_sheet('Phrases'), ['Phrase', 'Titles containing', 'Sources', 'Top source'], phrases, [40, 18, 10, 34])
    rows = []
    for s, cn in sorted(srcw.items()):
        for rank, (w, c) in enumerate(cn.most_common(25), 1): rows.append((s, rank, w, c))
    sheet(wb.create_sheet('By source'), ['Source', 'Rank', 'Word', 'Titles'], rows, [34, 8, 22, 10])
    sheet(wb.create_sheet('Sources'), ['Source', 'Method', 'Titles', 'First', 'Last', 'In site pipeline', 'Error'],
          [(s['name'], s['method'], s['count'], s['first'], s['last'], 'yes' if s['in_site'] else 'candidate', s['error'] or '') for s in d['sources']], [36, 10, 10, 12, 12, 16, 50])
    wb.save(XLSX)
    print('titles', N, '| words', len(words), '| phrases', len(phrases), '->', XLSX)


if __name__ == '__main__':
    main()
