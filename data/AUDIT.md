# Numbers audit, October 12, 2026

Scope: every number and attributed claim on the live site, `tools/content.py`, the static text in `tools/build.py`, and the integrity of `data/hospitals.json`. Sources were fetched directly where the site allowed it. Where a publisher blocked the fetch (HTTP 403), the claim was checked against search-result text from the publisher or a named secondary report, and the status says so.

Totals: 22 items checked. 11 verified, 9 corrected, 0 removed, 1 unverified (Axios), 1 open (geocoded count after de-duplication).

## Published claims

| Claim | Where | Source checked | Status | Notes |
|---|---|---|---|---|
| Sutter prices "30% more after imposing all-or-nothing contracts" | Exhibit, home | USC Schaeffer page (Melnick & Fonkych, J Hosp Mgmt Health Policy, July 1, 2024) | CORRECTED | The 30% is the gap to control hospitals ("remained substantially above ... a +30% difference"), not Sutter's own before/after change. Wording, chart label and source line fixed. |
| Trauma centers "4.4% more for ordinary non-trauma care" | Exhibit | Kessler, Sweeney & Melnick, Health Affairs 43(3), March 2024 (DOI 10.1377/hlthaff.2023.00249); figures via TechTarget summary because Health Affairs returned 403 | CORRECTED | 4.4% is for non-trauma inpatient admissions; non-trauma ED visits were 5.2%. Data are national commercial claims 2012 to 2018, so the exhibit is now tagged United States. Schaeffer and Stanford abstracts give no percentage. Link now goes to the DOI. |
| ED visits -18% (2020), -10% (2021), -12% (early 2022) | Exhibit | AJEM, Nov 1, 2022, Melnick, O'Leary, Zaniello & Abrishamian (Providence digital commons abstract) | CORRECTED | Numbers match the abstract exactly. The sample is "a large sample of US hospitals", not California, so the exhibit is tagged United States. "Early 2022" is the first quarter. Added the paper to the research list. |
| KFF 2025: family premium $26,993, +6%, +26% over five years, worker pays $6,850 | Exhibit | KFF 2025 Employer Health Benefits Survey, October 22, 2025 | VERIFIED | All four figures confirmed on the page. |
| Employer share $20,143 | Exhibit chart | Arithmetic: 26,993 - 6,850 | VERIFIED | Labeled as derived. |
| Private insurance hospital prices +30% vs Medicare +21%, April 2019 to April 2026; "47% faster" | Exhibit, brief | KFF, Godwin & Levinson, May 18, 2026 | VERIFIED | BLS PPI data; Jan to Apr 2026 preliminary. |
| 91% of premium growth from higher spending; premiums +78.4% (2011 to 2024) | Exhibit, brief | Healthcare Dive (Sept 11, 2026), Becker's, Healthcare Finance News, Axios. Fierce returned 403 | VERIFIED (secondary) | Study is Cooper (Yale) & Craig (Wisconsin), JAMA Health Forum, early September 2026. Spending +84.2%. It is an accounting decomposition and does not show cause; the source line now says so. The JAMA paper itself was not fetched. |
| RAND: private plans paid 253% of Medicare (2022), 254% (2018), 246% (2020), state-level median | Exhibit, research | RAND report RRA1144-2-v2 (Whaley et al., Dec 10, 2024, Round 5.1). RAND returned 403 | VERIFIED (search text) | Numbers and date confirmed from RAND page text in search results, not by direct fetch. |
| HCCI brief "emergency visit prices 20% to 30% higher at system-affiliated hospitals" | Brief | HCCI July 8, 2025 brief; HCCI June 25, 2025 companion report | CORRECTED | The 20% to 30% figure is for emergency-room evaluation-and-management outpatient prices and appears in the June 25 companion report, not the July brief. Brief summary now states only what the brief reports (system-affiliated hospitals higher; inpatient highest at nonprofits, outpatient at for-profits). Home page wording softened the same way. Authors and date confirmed. |
| Outpatient shift: 248 hospitals, 36% to 44% (2014 to 2024), about 45% in 2025 | Brief | Center brief, July 2026, Melnick & Subramanian | CORRECTED | Exact values: 35.8% (2014), 43.7% (2024), 45.2% as filed for 2025 (about 44.6% adjusted). Rural 68.5%, smallest hospitals 76.4% in 2025. Date was wrong ("2026"); now July 2026. Authors added. |
| CalMatters commentary, Glenn Melnick, April 10, 2026 | News | calmatters.org page | VERIFIED | Byline and date confirmed (updated April 16). |
| CHCF items (Oct 8, 2026) | News | HTTP 200 on both URLs | VERIFIED (exists) | Content not read in full. News list belongs to the news pipeline. |
| Axios, Sept 9, 2026 (insurer markups) | News | Appears in search results; site returns 403 to bots | UNVERIFIED | Title and date came from search results. Treat as unconfirmed until opened in a browser. |
| "Hospital Prices Post-COVID-19: Troubling Trends From California", Melnick, Jan 2026 | Research | Health Affairs Forefront (search result: Glenn Melnick, January 8, 2026) | VERIFIED | Previously flagged for byline. Not listed on the Center's publications page, so the link now goes to Health Affairs. |
| Titles and authors of trauma, MCRR, Healthcare (Basel) and HealthAffairs Blog items | Research | Center publications page | CORRECTED | Full titles restored ("... in the US commercially insured population", "... in the United States", "... of the US Healthcare Delivery System"). Authors added: Andreyeva, Yamamoto, Akintola & Melnick (MCRR); Melnick & Maerki (2023 blog). |
| About: Center founded 1996, USC Price; Melnick Blue Cross of California Chair; Schaeffer Senior Scholar | About page | improvinghealth About and Researchers pages | VERIFIED | |

## Computed exhibits and site stats

The state file has 449 records but 441 distinct hospitals. Eight hospitals filed a second, short report in the FY2023 file (a change of operator or fiscal year), so they appear twice. The default cohort (general acute, or unclassified) is 283 records but 276 hospitals. The yearly stats below use one record per hospital.

| Claim | Where | Recomputed | Status | Notes |
|---|---|---|---|---|
| Share with negative operating margin, FY20 to FY24: 42/41/54/56/50 | Exhibit | 42.8 / 40.7 / 53.6 / 56.2 / 49.3 (n = 271, 273, 274, 276, 270) | CORRECTED | Only FY2024 changed when rounded (50% became 49%); FY20 shows 43%. "283 hospitals" in the source line replaced. |
| Median operating margin: -1.6% (FY23), +0.2% (FY24), etc. | Exhibit | +1.81, +2.39, -0.81, -1.78, +0.32 for FY20 to FY24 | CORRECTED | Duplicate records had pulled the medians slightly. |
| Median uncompensated care rate 1.8 / 1.7 / 1.9% (FY22 to FY24) | Exhibit | 1.80, 1.69, 1.88 | VERIFIED | Definition note added: bad debt plus charity "Other" (line 355) over gross revenue; Hill-Burton (line 350) and restricted donations (line 360) are excluded. |
| "449 hospitals" | Home, about | 441 distinct hospital IDs | CORRECTED | Text now says 441. The explorer still shows 449 until `data/hospitals.json` is de-duplicated. |
| "422 geocoded" | Map caption | 422 records, 415 distinct hospitals | OPEN | Correct as records; becomes 415 after de-duplication. |
| 19 measures, 11 chart types, 3 fiscal years | Home | Counted in explorer.html: 19 VARS, 11 chart buttons; annual series FY2022 to FY2024 | VERIFIED | |

## Data integrity (`data/hospitals.json`)

- Duplicate IDs: 8 (Lakewood, West Hills, Fountain Valley, Los Alamitos, Placentia-Linda, Loma Linda Behavioral, Langley Porter, SLO/Crestwood). Raw CSV confirms two rows each. For five, one row is a full year (01/01/2023 to 12/31/2023) and the other a short post-sale stub (01/01/2024 to late March 2024); for Loma Linda BMC and Langley Porter, a full year to 6/30/2023 plus a short stub; for SLO PHF, the county's full year plus a Crestwood stub from July to December 2023. These are the "8 mismatching margins": the stub row carries its own small-period dollars and margin, while the panel trend (joined by ID) is identical on both rows. The full-year row is the right one for FY2023; the stub rows should be dropped (or merged) so each hospital counts once.
- Margins recomputed from income-statement fields match `operating_margin` and `total_margin` for every row except those 8 stub or full-year mismatches.
- `payer_mix` sums to 1 (within 1%) for all 434 rows that have it; 15 rows have none, as documented.
- 9 hospitals have operating margins below -100% (psychiatric, rehab and tiny facilities, e.g. SLO PHF -251%, Langley Porter -106%). Not errors, but they are why medians are used.
- 5 records have net revenue above gross revenue (psychiatric facilities with tiny charges). Not errors in the extract.
- County names: all 56 counties in the data match the GeoJSON; 2 GeoJSON counties have no hospitals; 10 hospitals have no county.
- General-acute flag: 275 true, 166 false, 8 unclassified (None).
- `charity_discounts` is HCAI line 355 ("Charity Discounts - Other"), so "charity care" is narrower than the label suggests.

## WordPress (improvinghealth), public view, October 12, 2026

- Root returns 200, tagline set, Home 2798 published. Test Page and TBD no longer public.
- Old Home (page 21) is still published at `/improvinghealth/home/` with its own canonical (`/home/`) and is still in `wp-sitemap-posts-page-1.xml`. This duplicates the new front page. Recommend drafting it or redirecting it.
- Excerpts are set on Issue Briefs, Projects, Our Team, Researchers and Collaborators. Still unset: Bibliography series (2200), Student Research Projects (2337), Summer Research Associates (2225).
- No `<meta name="description">` or Open Graph tags on the front page.
- Publications page: 21 external links, 12 return 403 to a bot (journals and publishers, expected). News archive: 36 external links; two look genuinely broken for a bot: `advisory.com/daily-briefing/2018/10/04/ed-costs` (404) and a News & Observer article (no response); the rest are 403/401/406 bot blocks (NYT, WSJ, Modern Healthcare, Health Affairs).

## Verified candidates for a "Behind the numbers" strip

Prefer the newest editions. All checked against the source page.

1. $26,993: average annual premium for employer family coverage, 2025, up 6% from 2024 (KFF 2025 Employer Health Benefits Survey, October 22, 2025). https://www.kff.org/health-costs/2025-employer-health-benefits-survey/
2. 6% vs 4%: family premiums versus workers' wages, 2025 (same survey). Over five years premiums rose 26% against 28.6% for wages, so the five-year comparison does not show premiums outpacing wages; use the one-year comparison and say so.
3. $6,850: what covered workers paid toward family coverage, 2025 (same survey).
4. 59%: Californians who skipped or delayed care because of cost in the past 12 months; 70% of low-income and 55% of higher-income residents; 40% have medical debt (55% of low-income) (CHCF 2026 California Health Policy Survey, fielded late 2025, published February 25, 2026). https://www.chcf.org/resource/2026/02/25/2026-california-health-policy-survey/
5. 30% vs 21%: private insurance vs Medicare hospital price growth, April 2019 to April 2026 (KFF, May 18, 2026).

Not used from the reference site: "$25,572" and "7% vs 4.5%" are the 2024 survey (premium $25,572, +7%; wages +4.5%, inflation 3.2%; worker share $6,296) and are verified but superseded by 2025. "53% skipped care (CHCF 2024)" was not verified and is superseded by the 59% from the 2026 survey.


## Direct source check, October 15, 2026

Every external link on the site (28 URLs) was opened and read. Seven sites block scripted requests (Axios, Fierce, Health Affairs, DOI, three CHCF pages); those were read in a real browser. Results:

| Source | Result |
|---|---|
| Axios, Sept 9 2026, Caitlin Owens, "Insurer markups only a small part of premium increases" | VERIFIED. Title, date, 78% premium growth 2011 to 2024 confirmed. Previously unverified. |
| Fierce Healthcare, Sept 9 2026, Yale study | VERIFIED. 91%, 78.4%, 84.2%, JAMA Health Forum Sept 4. Fierce says the study covers the large-group market; other outlets say large-group, small-group and individual. The site does not state a market scope. Study authors Cooper and Craig confirmed by Healthcare Finance News and Becker's snippets only. |
| Health Affairs Forefront, Jan 8 2026, Melnick (sole author) | VERIFIED. Byline and date. |
| Kessler, Sweeney & Melnick, Health Affairs, Mar 4 2024 | VERIFIED. 4.4% inpatient, 5.2% ED (baseline model), 2.7% ED in the sensitivity model (now noted on the site). National claims, 2012 to 2018. |
| CHCF 2026 California Health Policy Survey, Feb 25 2026 | VERIFIED. 59%, 70% low income, 83% priority. Survey fielded late 2025. |
| CHCF Policy Options brief | CORRECTED. Published Aug 20, 2026, not September. The hospital-prices spotlight PDF is not machine-readable, so its title and authors were not confirmed; the entry now cites the CHCF landing page and Bailit Health. |
| CHCF blog, Oct 8 2026, AI bills | VERIFIED. Title, date, authors. |
| HCAI brief, April 2026 | VERIFIED from the PDF. Four authors now spelled out; "more than twice" Medicare confirmed. |
| KFF 2025 EHBS, KFF May 18 2026 hospital prices, RAND RRA1144-2-v2, USC outpatient brief, Schaeffer Sutter page, Providence ED abstract, CalMatters commentary, Healthcare Dive (two), KFF Health News, Marketplace (Melnick quoted), Assembly hearing page (Oct 27 2020) | VERIFIED against the page text. |
| HCCI July 8 2025 brief (Burke and Chang) | VERIFIED. The odd URL slug (placeholder-hospital) is the real one and loads. |
| CalMatters, Sept 2024: 56 hospitals stopped delivering babies since 2012 | VERIFIED. Wording in the maternity notes now says "since 2012, September 2024 analysis". |

Not directly verifiable: Anaheim Global and Lancaster maternity unit closures (no news source found); the maternity list is inferred from HCAI filings and is labeled that way.
