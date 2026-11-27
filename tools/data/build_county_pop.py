"""data/county_pop.json: 2020 Census resident counts for California's 58 counties (Decennial Census DHC, P1_001N).
Needs a free Census API key (env CENSUS_API_KEY or the git-ignored tools/data/.cache/census_key). Without one the last file is kept:
these counts change only with the next census."""
import json, os, sys, urllib.request, datetime as dt
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', '..', 'data', 'county_pop.json')
KEYFILE = os.path.join(HERE, '.cache', 'census_key')
key = os.environ.get('CENSUS_API_KEY') or (open(KEYFILE).read().strip() if os.path.exists(KEYFILE) else '')
if not key:
    if os.path.exists(OUT):
        print('No Census API key: kept data/county_pop.json'); sys.exit(0)
    sys.exit('First run needs a Census API key (CENSUS_API_KEY).')
u = 'https://api.census.gov/data/2020/dec/dhc?get=NAME,P1_001N&for=county:*&in=state:06&key=' + key
try:
    rows = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'hospital-price-watch'}), timeout=60).read())[1:]
except Exception as e:
    if os.path.exists(OUT):
        print('COUNTY_POP_STALE: Census API failed (%s); kept last file' % str(e).replace(key, '[key]')[:100]); sys.exit(0)
    sys.exit('Census API failed: %s' % str(e).replace(key, '[key]')[:100])
pop = {r[0].split(',')[0].replace(' County', ''): int(r[1]) for r in rows}
if len(pop) != 58:
    sys.exit('expected 58 counties, got %d' % len(pop))
json.dump({'generated': dt.date.today().isoformat(), 'source': 'U.S. Census Bureau, 2020 Census Demographic and Housing Characteristics File (DHC), table P1, total population.',
           'url': 'https://data.census.gov/table/DECENNIALDHC2020.P1?g=040XX00US06$0500000', 'pop2020': dict(sorted(pop.items()))}, open(OUT, 'w'), indent=1)
print('counties', len(pop), 'total', sum(pop.values()))
