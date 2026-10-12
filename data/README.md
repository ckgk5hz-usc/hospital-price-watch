# data/hospitals.json

Real extract from California's HCAI Hospital Annual Financial Disclosure Data: the single-year FYE2023 CSV (`49hospitaldata.csv`) plus the multi-year panel (`years_data.xlsx`, 2020-2024), both via the Issue Brief Project's existing loaders (`hcai_loader.py`, `hcai_panel.py`). 449 hospitals.

## Fields

| Field | Source | Coverage |
|---|---|---|
| `name`, `oshpd_id`, `city`, `licensed_beds` | FYE2023 CSV, page 0-1 | 449/449 (beds 447/449) |
| `net_patient_revenue`, `operating_margin`, `total_margin` | FYE2023 CSV, page 8 col 1 | ~448/449 |
| `county` | Panel, joined by OSHPD ID = panel `fac_no`, panel's 2024 (latest) row | 439/449 |
| `is_general_acute` | Panel's own `HCAIPanel.acute()` cohort definition (`comparable_only=True, drop_specialty=True`) — `TYPE_CARE` General/General Acute + `TYPE_HOSP`=Comparable, **with LTAC/rehab/psych facilities HCAI miscodes as comparable-acute (Kindred, Vibra, Aurora, etc.) excluded by name pattern**, matching this project's existing anti-agent-reviewed cohort definition — not reimplemented from scratch | 435/449 resolved (275 true / 160 false), 8 unmatched to panel → `null` |
| `payer_mix` | FYE2023 CSV, page 12 gross revenue (inpatient+outpatient, summed across every revenue-center line), share of each hospital's own total across Medicare/MediCal/County/Private/Other | 434/449 (15 hospitals have zero/unusable gross revenue on page 12) |
| `operating_margin_trend` | Panel, `op_margin` per year, 2020-2024 (the panel's full range is 1995-2024, but only 2017-2024 sheets were loaded for this pass) | 449/449 have ≥1 year, 392/449 have all 5 years |
| `gross_patient_revenue`, `total_operating_expenses` | FYE2023 CSV, `income_statement()` | 449/449 |
| `other_operating_revenue` | FYE2023 CSV, `income_statement()` | 417/449 |
| `total_operating_revenue` | FYE2023 CSV, `income_statement()` | 448/449 |
| `operating_income` | FYE2023 CSV, `income_statement()` | 445/449 |
| `net_income` | FYE2023 CSV, `income_statement()` | 441/449 |
| `nonoperating_revenue`, `bad_debt` | FYE2023 CSV, `income_statement()` | 397/449 |
| `charity_discounts` | FYE2023 CSV, `income_statement()` | 353/449 |
| `uncompensated_care_rate` | FYE2023 CSV, `income_statement()` — (bad_debt + charity_discounts) / gross_patient_revenue | 348/449 |

**Real bug caught and fixed before committing**: the first pass computed `is_general_acute` from raw `TYPE_CARE`/`TYPE_HOSP` fields directly and classified Kindred Hospital - San Francisco Bay Area (an LTAC) as general-acute, because HCAI's own fields mislabel LTAC/rehab/psych facilities as "Comparable" + "General Acute". Re-derived from `HCAIPanel.acute()` instead of partially reimplementing its logic, which already excludes these by name pattern (see `NONACUTE_RE` in `hcai_panel.py`, added after this project's own anti-agent review). Always prefer the existing vetted method over reimplementing its logic from the raw fields.

**Second real bug, caught while building the explorer page, not before committing**: Department of State Hospitals Coalinga (a zero-revenue state psychiatric facility, correctly `null` on every other financial field) had `operating_margin_trend` values of literal `-Infinity` — a divide-by-zero in the trend calc that the single-year `income_statement()` path already guards against but the panel trend calc didn't. Python's `json.dump` silently writes non-standard `-Infinity`/`NaN` tokens that are **not valid JSON** and that no browser's `JSON.parse` accepts — the explorer page failed to load any data at all until this was found. Fixed by setting those 5 values to `null`, consistent with the hospital's other zero-revenue fields. **Standing lesson: when deriving a ratio/margin field programmatically, always guard the zero-denominator case explicitly (`None` if revenue==0 else ratio) rather than let it silently produce `inf`/`nan` — and validate any hand-written or generated JSON by loading it in the actual consumer (a browser's `JSON.parse`), not just Python's `json.load`, since Python accepts tokens JavaScript rejects.**

## Known gaps (real, not yet filled)

- 27 hospital records (26 distinct city/name pairs) have no coordinates — see the Geocoding section below. They are `null`, not guessed.
- `operating_margin_trend` only covers 2020-2024 (loaded panel years), not the panel's full 1995-2024 range.
- `county`/`is_general_acute` reflect the panel's **2024** row specifically (its newest, but preliminary/"In Process" per HCAI) — a hospital that changed classification or county between years isn't captured.
- 8 hospitals in the FYE2023 extract don't appear in the 2024 panel at all (likely closed, merged, or newly opened between years) — `county`/`is_general_acute` are `null` for these, not guessed.
- 15 hospitals have no usable page-12 gross revenue, so `payer_mix` is `null` rather than a fabricated split.

This file is the third real-data pass for the Dataset Explorer (adds the full real income-statement variable set — gross/other/total operating revenue, operating expenses, operating income, nonoperating revenue, net income, bad debt, charity discounts, uncompensated care rate — all from `HCAIDataset.income_statement()`, none recomputed by hand). Validated both ways before committing: `json.load()` parses clean, and a raw-text grep for `Infinity`/`NaN` returns zero matches (not just the first check — `json.load` would happily re-parse an invalid `-Infinity` token back in, which is exactly how the last bug slipped through undetected). Still not done: lat/long, insurance-provider-type grouping beyond the 5 payer categories already here.

## Geocoding (`lat`, `lon`, `geo_source`) and `ca_counties.geojson`

**Positions are city centroids, not street addresses.** Every hospital in the same city shares one point, and a big city's centroid can be miles from a given hospital. Good for a county/city-level map, not for locating a building.

- **Source:** U.S. Census Bureau 2024 Gazetteer, Places file (`https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2024_Gazetteer/2024_Gaz_place_national.zip`), California rows only, using each place's `INTPTLAT`/`INTPTLONG`. Each hospital's `city` was matched to a CA place name after stripping " city"/" CDP"/" town" and normalizing SAINT/ST and MOUNT/MT. One explicit alias: `VENTURA` → "San Buenaventura (Ventura)" (Census lists it under its legal name).
- **Where a city name matched both an incorporated city and a CDP** (Burbank, Mountain View), the candidate was kept only if it fell inside the hospital's own county polygon.
- **`geo_source`:** `census_place_centroid` (410 hospitals), `county_polygon_centroid` (12 — see next point), or `null` (27).
- **San Francisco:** Census's "San Francisco city" centroid includes the Farallon Islands and lands in the Pacific (lon -123.03). Those 12 hospitals instead use the centroid of the real county polygon's main landmass (37.7553, -122.4412), labeled `county_polygon_centroid`.
- **Validated:** all non-null points fall inside California's bounding box (lat 32.5–42.0, lon -124.5 to -114.0); every other point sits inside its own county polygon except 5 coastal/island edge cases (Alameda, Avalon, Santa Monica ×2, La Palma) where the point is correct but the simplified 20m county outline cuts the coast slightly. 94.0% of hospitals are geocoded (422/449).
- **Deliberately nulled — wrong matches caught by the county check:** `MISSION HILLS` (a Los Angeles neighborhood) collided with Mission Hills CDP in Santa Barbara County, and a hospital whose source `city` reads `CHICO` but whose county is San Bernardino (Canyon Ridge Hospital — the source city field looks mistyped; we did not silently correct it).
- **Not matched (no Census place exists for the name, or ambiguous):** mostly Los Angeles neighborhoods that are not Census places. Assigning the whole city's centroid would put them miles off, so they stay `null`:

  - BIG BEAR — BEAR VALLEY COMMUNITY HOSPITAL
  - CHICO — CANYON RIDGE HOSPITAL INC
  - ENCINO — PRIME HEALTHCARE SERVICES-ENCINO, LLC
  - GREENBRAE — MARINHEALTH MEDICAL CENTER
  - HARBOR — KAISER FOUNDATION HOSPITALS - SOUTH BAY
  - HOLLYWOOD — SOUTHERN CA HEALTHCARE SYSTEM, INC.
  - LA JOLLA — SCRIPPS GREEN HOSPITAL
  - LA JOLLA — SCRIPPS MEMORIAL HOSPITAL - LA JOLLA
  - MISSION HILLS — PROVIDENCE HOLY CROSS MEDICAL CENTER
  - NORTHRIDGE — NORTHRIDGE HOSPITAL MEDICAL CENTER
  - PANORAMA CITY — KAISER FOUNDATION HOSPITALS - PANORAMA
  - PANORAMA CITY — MISSION COMMUNITY HOSPITAL
  - PATTON — DEPT OF STATE HOSPITALS-PATTON
  - RESEDA — JOYCE EISENBERG KEEFER MEDICAL CENTER
  - SAN PEDRO — PROVIDENCE LITTLE COMPANY OF MARY MC - SAN PEDRO
  - SHERMAN OAKS — PRIME HEALTHCARE SERVICES - SHERMAN OAKS, LLC
  - SUN VALLEY — PACIFICA OF THE VALLEY CORPORATION
  - SYLMAR — LOS ANGELES COUNTY OLIVE VIEW-UCLA MEDICAL CENTER
  - TARZANA — PROVIDENCE CEDARS-SINAI TARZANA MEDICAL CENTER
  - TARZANA — TARZANA TREATMENT CENTERS, INC.
  - VALENCIA — HENRY MAYO NEWHALL MEMORIAL HOSPITAL
  - VAN NUYS — VALLEY PRESBYTERIAN HOSPITAL
  - WEST HILLS — WEST HILLS HOSPITAL
  - WEST LOS ANGELES — KAISER PERMANENTE HOSPITALS - WEST LA
  - WOODLAND HILLS — KAISER FOUNDATION HOSPITALS - WOODLAND HILLS
  - WOODLAND HILLS — MOTION PICTURE AND TELEVISION FUND

**`data/ca_counties.geojson`** — 58 California county outlines from the plotly `geojson-counties-fips.json` dataset (Census 20m cartographic boundaries), California rows only (state FIPS 06), simplified with Douglas–Peucker to ~49 KB, coordinates rounded to 3 decimals. Properties: `name` (matches the `county` field in `hospitals.json`) and `fips`. The simplification is for display, not measurement.

## Yearly series (`annual`)

Each hospital has `annual["2022"|"2023"|"2024"]` with net/gross patient revenue, total operating revenue and expenses, operating income, net income, operating and total margin, and uncompensated care rate. Built from `48hospitaldata` (FY2022), `49hospitaldata` (FY2023) and `50hospitaldata` (FY2024) through the same `income_statement()` method as the single-year fields. Fiscal year = year the reporting period ends (a mix of June and December year-ends). Reports covering fewer than 350 days (48 hospital-years) are left out rather than annualized. 6 hospital IDs present in the 2022/2024 files are not in the 449-hospital set and were not added. FY2023 net patient revenue matches the top-level field for every hospital. The explorer's operating-margin trend still uses the panel series (2020-2024); the 2024 filing is preliminary per HCAI.
