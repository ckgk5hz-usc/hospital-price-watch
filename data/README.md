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

**Real bug caught and fixed before committing**: the first pass computed `is_general_acute` from raw `TYPE_CARE`/`TYPE_HOSP` fields directly and classified Kindred Hospital - San Francisco Bay Area (an LTAC) as general-acute, because HCAI's own fields mislabel LTAC/rehab/psych facilities as "Comparable" + "General Acute". Re-derived from `HCAIPanel.acute()` instead of partially reimplementing its logic, which already excludes these by name pattern (see `NONACUTE_RE` in `hcai_panel.py`, added after this project's own anti-agent review). Always prefer the existing vetted method over reimplementing its logic from the raw fields.

## Known gaps (real, not yet filled)

- No lat/long — can't plot on a map yet. Needs a city/address → coordinate geocode pass (separate task, needs a real geocoding source).
- `operating_margin_trend` only covers 2020-2024 (loaded panel years), not the panel's full 1995-2024 range.
- `county`/`is_general_acute` reflect the panel's **2024** row specifically (its newest, but preliminary/"In Process" per HCAI) — a hospital that changed classification or county between years isn't captured.
- 8 hospitals in the FYE2023 extract don't appear in the 2024 panel at all (likely closed, merged, or newly opened between years) — `county`/`is_general_acute` are `null` for these, not guessed.
- 15 hospitals have no usable page-12 gross revenue, so `payer_mix` is `null` rather than a fabricated split.

This file is the second real-data pass for the Dataset Explorer. Still not done: lat/long, insurance-provider-type grouping beyond the 5 payer categories already here, and the explorer UI itself.
