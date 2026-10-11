# data/hospitals.json

Real extract from California's HCAI Hospital Annual Financial Disclosure Data, FYE 2023 (`49hospitaldata.csv`, the Issue Brief Project's primary dataset). 449 hospitals, generated via `Issue Brief Project/code/hcai_loader.py`.

Fields per hospital: `name`, `oshpd_id`, `city`, `licensed_beds`, `net_patient_revenue`, `operating_margin`, `total_margin`.

## Known gaps (real, not yet filled)

- No lat/long — can't plot on a map yet. Needs a city/address → coordinate geocode pass.
- No county field — only city. County is needed for district-level filtering/grouping.
- No type-of-care flag (general acute vs. psych vs. LTC vs. rehab) — this file includes all 449 facility types, not just the ~305 short-term general acute cohort the rest of this project's briefs use. Needs the `TYPE_HOSP` flag from the multi-year panel (`years_data.xlsx`) or an explicit filter before this is cohort-correct.
- No payer-mix / insurance-provider-type breakdown — exists in the source CSV (page 12 payer columns) but not pulled into this extract yet.
- Single year only (FYE 2023) — no year-on-year series yet. The multi-year panel (1995–2024) exists and can supply this.

This file is a first real-data pass for the Dataset Explorer, not the finished dataset.
