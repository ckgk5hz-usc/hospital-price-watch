"""Rule classifier for the news pipeline: scope gate, topic, subgroup, place. Rules live in taxonomy.json.

classify(title, summary='') -> {in_scope, topics, subtopics, place, state, why}
  * hard blocks (Spanish text, personnel announcements, vendor/marketing items) always drop an item
  * soft blocks (clinical/pharma pipeline, general-politics words) drop it unless a 'strong' subgroup also matched
  * an item is in scope with one strong subgroup hit, or any subgroup hit plus a cost/price/payment word
  * topics are the parent categories of the hit subgroups (strong first), at most three
The rules only choose labels. They never write or edit displayed text.
"""
import json, os, re

_DIR = os.path.dirname(os.path.abspath(__file__))
TAX = json.load(open(os.path.join(_DIR, 'taxonomy.json'), encoding='utf-8'))
_c = lambda p: re.compile(p, re.I)
CORE = _c(TAX['core'])
COST = re.compile(r'price|cost|afford|bill|premium|spend|margin|revenue|profit|payment|\bpay\b|charge|fee\b|fees\b|debt|expens|deductible|reimburs|\brates?\b|budget|\bcuts?\b|loss|clos|fund|tax|subsid|layoff|deficit|shortfall|financ|earnings|bankrupt', re.I)
HARD = {k: _c(v) for k, v in TAX['hard_block'].items()}
SOFT = _c(TAX['soft_block'])
CA = _c(TAX['place']['california'])
ES_WORDS = set('que los las el la en de con para por una pero hay del se es al sus más está dicen sin como esto lo un'.split()) - {'a', 'un', 'lo', 'se', 'es', 'al', 'como', 'sin', 'en', 'el'} | {'dicen', 'esto', 'pero', 'hay', 'están', 'más', 'sus', 'con', 'para', 'por', 'una', 'del', 'los', 'las', 'que'}
ACCENT = re.compile(r'[áéíóúñ¿¡]')
GROUPS = [(cat, sub, d['label'], bool(d.get('strong')), _c(d['any'])) for cat, c in TAX['categories'].items() for sub, d in c['subgroups'].items()]
TOPICS = {cat: c['label'] for cat, c in TAX['categories'].items()}
SUBGROUPS = {f'{cat}/{sub}': label for cat, sub, label, _, _ in GROUPS}
STATES = ['Alabama','Alaska','Arizona','Arkansas','Colorado','Connecticut','Delaware','Florida','Georgia','Hawaii','Idaho','Illinois','Indiana','Iowa','Kansas','Kentucky','Louisiana','Maine','Maryland','Massachusetts','Michigan','Minnesota','Mississippi','Missouri','Montana','Nebraska','Nevada','New Hampshire','New Jersey','New Mexico','New York','North Carolina','North Dakota','Ohio','Oklahoma','Oregon','Pennsylvania','Rhode Island','South Carolina','South Dakota','Tennessee','Texas','Utah','Vermont','Virginia','West Virginia','Wisconsin','Wyoming']
_ST = [(s, re.compile(r'\b' + s + r'\b')) for s in STATES]
_WASH = re.compile(r'\bWashington State\b|\bWashington (?:lawmakers|legislature|hospital|health)')


def place_of(title, summary=''):
    """Title signals win. A snippet can set California only if it names it twice, or a state only if it names exactly one (examples inside a national story are common)."""
    for text, need in ((title, 1), (summary, 2)):
        if not text:
            continue
        if len(CA.findall(text)) >= need:
            return 'california', None
        named = sorted({s for s, rx in _ST if rx.search(text)} | ({'Washington State'} if _WASH.search(text) else set()))
        if len(named) == 1 and (need == 1 or len(named) == 1 and len(CA.findall(text)) == 0):
            return 'state', named[0]
    return 'national', None


def classify(title, summary=''):
    """Scope is decided on the title alone (the rules were tuned on titles). The snippet can only add strong secondary topics and set the place."""
    r = _classify(title, title)
    if not r['in_scope'] or not summary:
        if r['in_scope']:
            r['place'], r['state'] = place_of(title)
        return r
    r['place'], r['state'] = place_of(title, summary)
    for cat, sub, _, strong, rx in GROUPS:
        if strong and cat not in r['topics'] and len(r['topics']) < 3 and rx.search(summary):
            r['topics'].append(cat); r['subtopics'].append(f'{cat}/{sub}')
    r['subtopics'] = r['subtopics'][:4]
    return r


def _classify(title, text):
    for name in ('personnel', 'vendor'):
        if HARD[name].search(title):
            return _out(False, why='block:' + name)
    sp = len(HARD['spanish'].findall(title)) + len([w for w in re.findall(r"[a-záéíóúñ]+", title.lower()) if w in ES_WORDS])
    if sp >= 2 or (sp and ACCENT.search(title)):
        return _out(False, why='block:spanish')
    if not CORE.search(text):
        return _out(False, why='no-health-term')
    hits = [(cat, sub, strong) for cat, sub, _, strong, rx in GROUPS if rx.search(text)]
    if not hits:
        return _out(False, why='no-topic')
    strong = [h for h in hits if h[2]]
    if SOFT.search(title) and not strong:
        return _out(False, why='block:clinical-or-offtopic')
    if not strong and not COST.search(text):
        return _out(False, why='topic-without-cost')
    order = strong + [h for h in hits if not h[2]]
    topics = []
    for cat, _, _ in order:
        if cat not in topics:
            topics.append(cat)
    place, state = place_of(title)
    return {'in_scope': True, 'topics': topics[:3], 'subtopics': [f'{c}/{s}' for c, s, _ in order][:4], 'place': place, 'state': state, 'why': 'strong' if strong else 'topic+cost'}


def _out(ok, why):
    return {'in_scope': ok, 'topics': [], 'subtopics': [], 'place': None, 'state': None, 'why': why}
