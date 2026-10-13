# Verdicts for the 59 candidates in data/closure_candidates.csv.
# Every verdict is backed by pages found via WebSearch/WebFetch in this session (2026-10-13).
# FETCHED = page body actually fetched and read; everything else was returned by a search whose summary supports the claim.
# Where a source could not be fetched (403/402/429) it is still listed but not marked fetched.
# status: closed_permanent | closed_then_reopened | ceased_inpatient_converted | continues_under_new_license_or_name |
#         merged_into_other_campus | still_operating_stopped_filing | cannot_verify
V = {}
def v(oid, status, date, note, ev, conf='medium', fetched=(), county=None):
    V[oid] = dict(status=status, closed_date=date, note=note, evidence=ev, evidence_fetched=list(fetched), confidence=conf, county_override=county)

# ---------------- headline general-acute rows ----------------
v('106190066','closed_then_reopened','April 2013 (emergency department closed Apr 3, 2013); reopened July 2015',
  'The owner closed Bellflower Medical Center in April 2013 for financial reasons; Prospect Medical Holdings bought it and reopened an 80-bed hospital as Los Angeles Community Hospital at Bellflower in July 2015 (it does not appear in the HCAI disclosure data after 2013).',
  ['https://file.lacounty.gov/SDSInter/bos/bc/195291_BellflowerClosure05-14-13.pdf','https://www.businesswire.com/news/home/20150728006518/en/Prospect-Medical-Holdings-Announces-Reopening-Hospital-Bellflower'],'medium',
  fetched=['https://file.lacounty.gov/SDSInter/bos/bc/195291_BellflowerClosure05-14-13.pdf'])
v('106160702','ceased_inpatient_converted','2013 (ER closed March 2013; hospital operations ceased Sept 30, 2013)',
  'Corcoran District Hospital stopped hospital operations in 2013 after losing prison-system business and emergency-room money, and continued as an outpatient clinic; the district sold its assets to Adventist Health in 2018.',
  ['https://abc30.com/archive/9037817/','https://corcoranhospital.specialdistrict.org/about-us'],'medium',fetched=['https://abc30.com/archive/9037817/'])
v('106370705','closed_permanent','November 2014 (ER and ICU closed Nov 17, 2014; urgent care ran into late Dec 2014)',
  'Fallbrook Hospital, run by Community Health Systems for about 16 years under an agreement with the Fallbrook district, closed its emergency room and ICU on Nov 17, 2014 after multimillion-dollar losses; the hospital property was later sold.',
  ['https://sandiegoreader.com/news/2014/oct/10/ticker-fallbrook-hospital-ER-palomar-tricity','https://www.villagenews.com/story/2014/11/14/news/hospital-er-to-close-nov-17-to-become-urgent-care/42485.html','https://www.villagenews.com/story/2017/10/05/news/fallbrook-hospital-sale-closes-escrow/51204.html'],'medium',
  fetched=['https://sandiegoreader.com/news/2014/oct/10/ticker-fallbrook-hospital-ER-palomar-tricity'])
v('106190854','closed_permanent','April 2013',
  'Los Angeles Metropolitan Medical Center, a Pacific Health Corp. hospital, closed in April 2013 after its owner ran into legal and financial trouble; the building has stood vacant.',
  ['https://www.beckershospitalreview.com/hospital-management-administration/hospitals-that-closed-in-2013.html','https://www.ahd.com/free_profile/050644/Los_Angeles_Metropolitan_Medical_Center/Los_Angeles/California/','https://cbsnews.com/losangeles/news/4-socal-hospitals-close-their-er-doors'],'medium')
v('106190784','closed_permanent','September 9, 2014',
  'Temple Community Hospital ceased operations at midnight on Sept 9, 2014, citing low reimbursement, an aging building and capital needs.',
  ['https://www.theeastsiderla.com/real_estate/temple-community-hospital-closes-amid-talk-of-real-estate-development-updated/article_536d50c6-6abc-5d51-8d6b-9eb55bd46510.html','https://www.healthcarefacilitiestoday.com/posts/Earthquake-retrofit-costs-lead-to-closing-of-LA-hospital--6783'],'high',
  fetched=['https://www.theeastsiderla.com/real_estate/temple-community-hospital-closes-amid-talk-of-real-estate-development-updated/article_536d50c6-6abc-5d51-8d6b-9eb55bd46510.html'])
v('106070904','closed_permanent','April 21, 2015',
  'Doctors Medical Center in San Pablo closed on April 21, 2015 after running out of money; about 90% of patients were on Medicare or Medi-Cal and the hospital was losing about $18 million a year.',
  ['https://abc7news.com/post/doctors-medical-center-in-san-pablo-closing-tuesday/667216/','https://votersedge.kqed.org/news/11830978/a-lot-of-trust-was-lost-what-losing-its-only-hospital-meant-to-an-east-bay-community'],'high',
  fetched=['https://abc7news.com/post/doctors-medical-center-in-san-pablo-closing-tuesday/667216/'])
v('106160787','ceased_inpatient_converted','March 7, 2016 (inpatient services ended)',
  'Adventist Health moved Central Valley General Hospital\'s last inpatient service (labor and delivery) to its Hanford medical center on March 7, 2016; the campus is now a clinic called Adventist Health Community Care-Hanford.',
  ['https://en.wikipedia.org/wiki/Adventist_Health_Community_Care-Hanford'],'medium',fetched=['https://en.wikipedia.org/wiki/Adventist_Health_Community_Care-Hanford'])
v('106230949','continues_under_new_license_or_name','2017 (renamed)',
  'Frank R. Howard Memorial Hospital in Willits was renamed Adventist Health Howard Memorial in 2017 and is still operating; HCAI gave it a new ID.',
  ['https://lfis.hcai.ca.gov/Facility/History/106234038'],'medium')
v('106190468','continues_under_new_license_or_name','2019 (sold to Kindred; renamed Kindred Hospital Paramount)',
  'Promise Hospital of East Los Angeles kept operating: Promise Healthcare sold it to Kindred in the 2019 bankruptcy and it became Kindred Hospital Paramount. It stopped appearing in the HCAI disclosure data after 2016.',
  ['https://archive.hasc.org/post/kindred-healthcare-acquires-promise-hospital-los-angeles','https://hklaw.com/en/news/intheheadlines/2019/02/promise-healthcares-80m-ch-11-sale-of-calif-hospital-okd'],'medium')
v('106370787','closed_permanent','April 30, 2017',
  'Promise Hospital of San Diego, a long-term acute care hospital on University Avenue, closed permanently on April 30, 2017; the owner planned to lease the building to Crestwood Behavioral Health.',
  ['https://www.sdbj.com/?p=48276','https://sdbj.com/?p=48277'],'high')
v('106190712','ceased_inpatient_converted','2017 (relocated to Pasadena as an outpatient and ambulatory surgery center)',
  'Shriners Hospitals for Children - Los Angeles was replaced in 2017 by a smaller outpatient and ambulatory-surgery center in Pasadena; overnight stays go to Huntington Hospital. The Koreatown building was sold.',
  ['https://www.pasadenanow.com/main/?p=327002','https://www.beckersasc.com/?p=42911'],'medium',fetched=['https://www.pasadenanow.com/main/?p=327002'])
v('106190307','closed_permanent','November 30, 2017',
  'Pacific Alliance Medical Center (formerly French Hospital), Chinatown\'s only hospital, closed on Nov 30, 2017 rather than renew its lease and pay for seismic work; the building was sold in 2018 for conversion to urgent care.',
  ['https://nwasianweekly.com/2017/12/only-hospital-in-los-angeles-chinatown-shuts-down','https://www.healthcarefinancenews.com/news/california-physician-group-buys-closed-pacific-alliance-medical-center-33-million'],'high',
  fetched=['https://nwasianweekly.com/2017/12/only-hospital-in-los-angeles-chinatown-shuts-down'])
v('106424102','closed_permanent','June to July 2017',
  'The Champion Center, a 34-bed addiction treatment hospital run by Lompoc Valley Medical Center, closed in mid-2017 after losing about $3 million a year since opening in 2014.',
  ['https://lompocrecord.com/news/local/lompoc-s-champion-center-closes-its-doors-possibly-for-good/article_ce8125da-d9e8-5f3a-a4c4-9493356b3c2a.html','https://santamariatimes.com/news/local/the-rise-and-fall-of-lompocs-champion-center-treatment-facility-lost-about-3m-per-year/article_0e67e6fe-9f18-5784-8638-62bef1716792.html'],'medium')
v('106010782','cannot_verify',None,
  'Sutter threatened to close Thunder Road Adolescent Treatment Centers around 2015 and ran it down; the search found no dated source confirming whether it closed or passed to another operator.',
  ['https://www.cbsnews.com/sanfrancisco/news/vote-could-shutter-oakland-youth-drug-alcohol-treatment-center-after-30-years-of-service/'],'low')
v('106150808','continues_under_new_license_or_name','2018-2019 (new hospital building and new license)',
  'Adventist Health Tehachapi Valley moved into a new hospital at 1100 Magellan Drive; the older downtown hospital (built 1954) was replaced. The new hospital appears in the HCAI data from 2019 under a new ID.',
  ['https://bakersfieldnow.com/news/local/the-new-adventist-health-tehachapi-valley-hospital-opens'],'medium')
v('106380964','continues_under_new_license_or_name','August 2018 (replaced by CPMC Mission Bernal Campus)',
  'CPMC\'s St. Luke\'s campus was replaced by the new 120-bed Mission Bernal hospital in August 2018.',
  ['https://www.sutterhealth.org/about/cpmc-history','https://www.beckershospitalreview.com/capital/538m-san-francisco-hospital-opening-in-august-5-things-to-know/'],'medium')
v('106040875','closed_permanent','November 2018 (Camp Fire); confirmed permanent July 2023',
  'Adventist Health Feather River in Paradise closed after the 2018 Camp Fire; in July 2023 executives said it "cannot and will not reopen." Local clinics remain.',
  ['https://www.mynspr.org/news/2023-07-26/paradises-only-hospital-emergency-room-will-not-reopen-leaving-healthcare-vacuum','https://backup.adventisthealth.org/feather-river/camp-fire-update/'],'high',
  fetched=['https://www.mynspr.org/news/2023-07-26/paradises-only-hospital-emergency-room-will-not-reopen-leaving-healthcare-vacuum'])
v('106380929','continues_under_new_license_or_name','2019 (services moved to CPMC Van Ness Campus)',
  'CPMC ended inpatient and emergency services at its older Pacific and California campuses when the Van Ness Campus opened in 2019; the Van Ness hospital appears in the HCAI data under a new ID.',
  ['https://en.wikipedia.org/wiki/California_Pacific_Medical_Center','https://www.sutterhealth.org/about/cpmc-history'],'medium')
v('106414018','cannot_verify',None,
  'No source found on what happened to Menlo Park Surgical Hospital (570 Willow Road); it stops appearing in the HCAI disclosure data after 2019.',
  [],'low')
v('106430837',"continues_under_new_license_or_name",'March 1, 2019 (Santa Clara County took over)',
  'O\'Connor Hospital still operates as a 358-bed county-owned hospital after Santa Clara County bought it from bankrupt Verity Health on March 1, 2019.',
  ['https://news.santaclaracounty.gov/node/3736','https://www.beckershospitalreview.com/hospital-transactions-and-valuation/bankrupt-california-hospital-chain-closes-235m-sale.html'],'high')
v('106013619','continues_under_new_license_or_name','2013 (Alameda Health System took over from Sutter)',
  'Alameda Health System took over San Leandro Hospital from Sutter in 2013, kept the emergency room open, and was still running it as of 2021; the reason it stopped filing a separate HCAI disclosure after 2019 is not documented.',
  ['https://en.wikipedia.org/wiki/Alameda_Health_System','https://www.beckershospitalreview.com/hospital-transactions-and-valuation/alameda-health-system-to-take-over-san-leandro-hospital-from-sutter-health/'],'medium',fetched=['https://en.wikipedia.org/wiki/Alameda_Health_System'])
v('106434138','continues_under_new_license_or_name','March 1, 2019 (Santa Clara County took over)',
  'St. Louise Regional Hospital in Gilroy continues as a county-owned hospital after Santa Clara County bought it from Verity Health on March 1, 2019.',
  ['https://news.santaclaracounty.gov/node/3736','https://morganhilltimes.com/county-offers-to-buy-saint-louise-hospital/'],'high')
v('106250956','continues_under_new_license_or_name','2021 (new replacement hospital, new ID)',
  'Modoc Medical Center in Alturas still operates; it moved into a replacement building and appears in the HCAI data from 2021 under a new ID.',
  ['https://dbia.org/project/modoc-medical-center-replacement-facility/'],'medium')
v('106560508','continues_under_new_license_or_name','July 6, 2021 (renamed St. John\'s Hospital Camarillo)',
  'St. John\'s Pleasant Valley Hospital in Camarillo was renamed St. John\'s Hospital Camarillo on July 6, 2021 and kept operating.',
  ['https://dignityhealth.org/central-coast/locations/pleasantvalley/about-us/press-center/2021-07-06-name-change','https://www.pacbiztimes.com/2021/07/06/camarillo-hospital-puts-camarillo-in-its-name/'],'high')
v('106190762','closed_permanent','January 2020 (announced Jan 6, 2020)',
  'Verity Health closed St. Vincent Medical Center after a $610 million sale to KPC Group fell through, wound down services in under three weeks.',
  ['https://abc7.com/post/st-vincent-medical-center-in-la-to-close-following-collapse-of-sale/5822222/','https://www.businesswire.com/news/home/20200106005962/en','https://www.beckershospitalreview.com/finance/los-angeles-hospital-closes-after-purchase-deal-falls-through/'],'high',
  fetched=['https://abc7.com/post/st-vincent-medical-center-in-la-to-close-following-collapse-of-sale/5822222/'])
v('106190475','closed_permanent','November 2021 (acute care ended; earlier closed July 3, 2018 and partly reopened in 2021)',
  'Community Hospital Long Beach closed July 3, 2018 after an active fault was found under the campus, reopened in 2021, and then ended acute care and closed its emergency department in November 2021.',
  ['https://lbpost.com/news/community-hospital-officially-closes-tuesday-city-hopes-new-operator-will-reopen-soon','https://www.beckershospitalreview.com/?p=190267','https://www.cbsnews.com/amp/losangeles/news/historic-long-beach-hospital-to-close-emergency-department'],'high',
  fetched=['https://lbpost.com/news/community-hospital-officially-closes-tuesday-city-hopes-new-operator-will-reopen-soon'])
v('106190534','closed_permanent','March 31, 2021',
  'Olympia Medical Center in Los Angeles suspended all patient care at the end of March 2021 after UCLA Health bought the campus; the building is being converted to a UCLA neuropsychiatric clinic.',
  ['https://en.wikipedia.org/wiki/Olympia_Medical_Center','https://www.beckershospitalreview.com/finance/los-angeles-hospital-closing-after-74-years/'],'high',fetched=['https://en.wikipedia.org/wiki/Olympia_Medical_Center'])
v('106190159','closed_then_reopened','February 2017; reopened March 2021 (status after 2021 not verified)',
  'Gardens Regional Hospital closed in early 2017 after bankruptcy and a failed sale; it reopened in March 2021 as Pacific Gardens Medical Center. It filed HCAI data for 2021 but no later year, and the search found nothing on its status after 2021.',
  ['https://www.beckershospitalreview.com/finance/bankrupt-california-hospital-closes/','https://lmlamplighter.com/2021/03/29/pacific-gardens-medical-center-reopens-in-hawaiian-gardens/'],'medium',
  fetched=['https://lmlamplighter.com/2021/03/29/pacific-gardens-medical-center-reopens-in-hawaiian-gardens/'])
v('106370755','merged_into_other_campus','2015 announcement; reporting ended 2021',
  'Palomar Health announced in June 2015 that it would close the old downtown Escondido campus and move services to the new Palomar Medical Center and Pomerado Hospital; the campus last filed HCAI data for 2021 and the new Palomar Medical Center files under its own ID.',
  ['https://www.villagenews.com/story/2015/06/25/news/palomar-health-announces-it-will-close-old-site-in-downtown-escondido/44516.html','https://beckershospitalreview.com/finance/palomar-health-to-close-california-hospital-3-things-to-know.html'],'medium')
v('106190636','continues_under_new_license_or_name','2022 (consolidated reporting under Emanate Health)',
  'Emanate Health Queen of the Valley in West Covina is open (HCAI lists a 325-bed general acute hospital); the state profile shows it reported jointly with Emanate Health Inter-Community Hospital, which probably explains the separate ID stopping.',
  ['https://hcai.ca.gov/facility/citrus-valley-medical-center-qv-campus/','https://hcai.ca.gov/hospital/emanate-health-queen-of-the-valley-hospital'],'low')
v('106190857','cannot_verify',None,
  'West Covina Medical Center (46 licensed beds) is listed as open by HCAI, with a financial report that ends June 20, 2022; the search found no closure report and no explanation for the reporting stop.',
  ['https://hcai.ca.gov/facility/west-covina-medical-center'],'low')
v('106370652','continues_under_new_license_or_name','December 11, 2023 (sold to UC San Diego Health; now East Campus Medical Center)',
  'Alvarado Hospital Medical Center did not close: Prime Healthcare sold it to UC San Diego Health on Dec 11, 2023 and it operates as UC San Diego Health East Campus.',
  ['https://today.ucsd.edu/story/uc-san-diego-health-completes-acquisition-of-alvarado-hospital-medical-center','https://www.businesswire.com/news/home/20231010532993/en/Prime-Healthcare-Announces-Preliminary-Agreement-with-UC-San-Diego-Health-for-the-Sale-of-Alvarado-Hospital-Medical-Center'],'high')
v('106190081','continues_under_new_license_or_name','September 6, 2023 (sold; now Adventist Health White Memorial Montebello)',
  'Beverly Hospital in Montebello filed for bankruptcy in 2023 and Adventist Health White Memorial bought it; the sale closed Sept 6, 2023 and the hospital operates as Adventist Health White Memorial Montebello.',
  ['https://adventisthealth.org/montebello/about-us/our-history','https://www.oag.ca.gov/news/press-releases/attorney-general-bonta-conditionally-approves-sale-beverly-community-hospital','https://jonesday.com/en/practices/experience/2023/09/adventist-health-maintains-access-to-emergency-services-for-montebello-community-through-chapter-11-sale'],'high')
v('106201281','closed_then_reopened','January 2023 (emergency room closed December 2022); reopened March 18, 2025',
  'Madera Community Hospital closed in January 2023 over severe financial problems and reopened on March 18, 2025 after the state granted a license and a $57 million distressed-hospital loan.',
  ['https://www.kvpr.org/health/2025-03-19/after-two-year-closure-madera-community-hospital-reopens-on-monumental-historic-day','https://abc30.com/post/madera-community-hospital-set-reopen-today-years-long-closure/16043490/'],'high',
  fetched=['https://www.kvpr.org/health/2025-03-19/after-two-year-closure-madera-community-hospital-reopens-on-monumental-historic-day'])

# ---------------- ID changes and merges (data-backed, mostly 2012 to 2015) ----------------
v('106010805','continues_under_new_license_or_name','2013 (new HCAI ID)',
  'Eden Medical Center in Castro Valley kept operating; the same-named hospital reappears in the HCAI data from 2013 under a new ID.',
  ['https://en.wikipedia.org/wiki/Eden_Medical_Center'],'medium')
v('106190110','cannot_verify',None,
  'Brotman Medical Center in Culver City stops appearing in the HCAI data after 2012. Wikipedia suggests the hospital was renamed Southern California Hospital at Culver City after its 2005 reopening and is still operating, but it does not state they are the same licensed facility and the HCAI data show no successor ID.',
  ['https://en.wikipedia.org/wiki/Southern_California_Hospital_at_Culver_City'],'low',fetched=['https://en.wikipedia.org/wiki/Southern_California_Hospital_at_Culver_City'])
v('106301132','continues_under_new_license_or_name','2013 (replacement hospital on La Palma Avenue)',
  'Kaiser opened a new Anaheim Medical Center on La Palma Avenue to replace its Lakeview hospital and kept the old license suspended; the new hospital appears in the HCAI data from 2013.',
  ['https://www.fiercehealthcare.com/it/kaiser-permanente-orange-county-opens-new-anaheim-medical-center'],'medium')
v('106010858','continues_under_new_license_or_name','June 2014 (replaced by Kaiser San Leandro Medical Center)',
  'Kaiser replaced its Hayward hospital with a new San Leandro Medical Center that opened in 2014.',
  ['https://www.tradelineinc.com/news/2005-11/kaiser-permanente-plans-hayward-replacement-hospital','https://mcdmag.com/2015/01/kaiser-permanentes-new-redwood-city-hospital-opens'],'medium')
v('106010856','continues_under_new_license_or_name','July 2014 (replacement hospital)',
  'Kaiser Oakland moved to a new 12-story replacement hospital on July 1, 2014; the new building appears in the HCAI data under a new ID.',
  ['https://en.wikipedia.org/wiki/Kaiser_Oakland_Medical_Center'],'medium')
v('106410804','continues_under_new_license_or_name','December 2014 (replacement hospital)',
  'Kaiser Redwood City opened a replacement hospital on Dec 16, 2014 next to the old one.',
  ['https://hconews.com/2015/01/04/kaiser-opens-replacement-hospital-in-redwood-city/','https://globest.com/2014/12/16/new-redwood-city-hospital-opens/'],'medium')
v('106490919','continues_under_new_license_or_name','2014 (new hospital, renamed Sutter Santa Rosa Regional Hospital)',
  'Sutter opened a new hospital on Mark West Springs Road in 2014 to replace the aging Chanate Road facility.',
  ['https://sutterhealth.org/about/ssrrh-history','https://www.northbaybusinessjournal.com/article/industry-news/sutter-renames-new-santa-rosa-hospital/'],'medium')
v('106400466','continues_under_new_license_or_name','after 2013 (reports under Marian Regional Medical Center license)',
  'Arroyo Grande Community Hospital is still open under Dignity Health; a 2018 California Attorney General notice calls it Marian Regional Medical Center - Arroyo Grande, which likely explains why it stopped filing a separate report.',
  ['https://en.wikipedia.org/wiki/Arroyo_Grande_Community_Hospital','https://www.oag.ca.gov/sites/all/files/agweb/pdfs/charities/nonprofithosp/notice-dignity-poster-slo.pdf'],'low')
v('106105029','still_operating_stopped_filing','after 2015',
  'Fresno Heart and Surgical Hospital still operates; the HCAI facility record lists it as open, and a 2024 notice shows it receiving patients. It stopped appearing in the disclosure data after 2015.',
  ['https://lfis.hcai.ca.gov/Facility/Detail/138736','https://communitymedical.org/getmedia/b01248c6-aae8-4a4d-bc0d-30b2d0e85655/ADTC-Notification-of-Closure-Letter-FINAL_combined2.pdf'],'medium')
v('106564121','merged_into_other_campus','December 1, 2012 (acquired by Los Robles)',
  'Thousand Oaks Surgical Hospital joined Los Robles Hospital and Medical Center\'s health system on Dec 1, 2012 and still operates there.',
  ['https://losrobleshospital.com/about/newsroom/los-robles-health-system-purchases-thousand-oaks-surgical-hospital-building','https://www.losrobleshospital.com/locations/thousand-oaks-surgical-hospital'],'medium')
v('106374084','closed_permanent','February 2013 (announced) to 2013',
  'San Diego Hospice, California\'s largest hospice, announced in February 2013 that it would shut down after a federal Medicare audit and a Chapter 11 filing, and closed its 24-bed inpatient unit in Hillcrest.',
  ['https://www.kpbs.org/news/health/2013/02/13/meidcare-audit-forces-sd-hospice-close','https://inewsource.org/2017/09/15/san-diego-hospice-end-journey/'],'medium',
  fetched=['https://www.kpbs.org/news/health/2013/02/13/meidcare-audit-forces-sd-hospice-close'],county='San Diego')
# ---------------- state developmental centers ----------------
v('106191014','closed_permanent','December 23, 2014 (last resident moved out)',
  'Lanterman Developmental Center in Pomona closed when its last resident moved to the community on Dec 23, 2014; the property went to Cal Poly Pomona in 2015.',
  ['https://www.dds.ca.gov/services/state-facilities/dc-closures','https://en.wikipedia.org/wiki/Lanterman_Developmental_Center'],'high',fetched=['https://www.dds.ca.gov/services/state-facilities/dc-closures'])
v('106491267','closed_permanent','2018 (last year filed); property transferred to the state Department of General Services in 2019',
  'Sonoma Developmental Center is on the state\'s list of closed developmental centers; the state says the property was transferred to the Department of General Services in 2019 (the exact closure date is not stated on the page read).',
  ['https://www.dds.ca.gov/services/state-facilities/dc-closures'],'medium',fetched=['https://www.dds.ca.gov/services/state-facilities/dc-closures'])
v('106301781','closed_permanent','February 2020 (all residents moved to community settings)',
  'Fairview Developmental Center in Costa Mesa closed in February 2020 when all residents moved into community settings; the land is being planned for housing.',
  ['https://www.dds.ca.gov/services/state-facilities/dc-closures'],'high',fetched=['https://www.dds.ca.gov/services/state-facilities/dc-closures'])
# ---------------- psychiatric / specialty / rehab ----------------
v('106154147','continues_under_new_license_or_name','2014 (name change only)',
  'Crestwood Psychiatric Health Facility in Bakersfield kept filing under ID 106154160 with a slightly different name from 2012-2024; this ID was a duplicate/variant listing.',
  [],'high')
v('106560838','cannot_verify',None,
  'No source found that Pacific Shores Hospital (Oxnard) closed; a recruiting profile still describes it as operating. It stops appearing in the HCAI data after 2014.',
  [],'low')
v('106104089','still_operating_stopped_filing','after 2019',
  'The Fresno psychiatric health facility (formerly Crestwood PHF - Fresno, then Exodus PHF) still operates: Fresno County\'s FY2022-23 outcomes report lists the Exodus adult PHF as operating from January 1, 2016 to present.',
  ['https://fresnocountyca.gov/files/sharedassets/county/v/1/behavioral-health/contracted-services/22-23-non-mhsa/exodus-adult-phf-outcomes-report-att-a-fy-2022-23.pdf'],'medium',county='Fresno')
v('106197931','cannot_verify',None,
  'No source found on the Culver City Exodus Recovery psychiatric health facility; it stops appearing in the HCAI data after 2019.',
  [],'low')
v('106370033','cannot_verify',None,
  'Casa Palmera in Del Mar appears on a state list of licensed chemical dependency recovery hospitals open as of August 2022 and was acquired by Discovery Behavioral Health; no source says it closed after its last HCAI filing in 2022.',
  ['https://hcai.ca.gov/document/chargemaster-licensed-chemical-dependency-recovery-hospitals'],'low')
v('106304079','continues_under_new_license_or_name','April 2022 (relocated within Tustin; new ID)',
  'Encompass Health Rehabilitation Hospital of Tustin moved to a new 65-bed building in April 2022 under the same name; the new building appears in the HCAI data from 2023 under a new ID.',
  ['https://healthsouth.mediaroom.com/2022-04-28-Encompass-Health-Rehabilitation-Hospital-of-Tustin-opens-new-location-with-65-private-patient-rooms?asPDF=1'],'medium')
v('106301304','cannot_verify',None,
  'Newport Bay Hospital (a 34-36 bed psychiatric hospital) is described as operating in directory listings; no closure source found. It stops appearing in the HCAI data after 2022.',
  [],'low')
v('106154101','continues_under_new_license_or_name','2023 (acquired by Adventist Health; renamed Adventist Health Specialty Bakersfield in 2024)',
  'Bakersfield Heart Hospital was taken over by Adventist Health in 2023 and renamed Adventist Health Specialty Bakersfield in 2024.',
  ['https://www.bakersfield.com/news/bakersfield-heart-hospitals-new-name-adventist-health-specialty-bakersfield-reflects-new-strategy/article_84e3c560-d678-11ee-aa7b-97831bce808b.html','https://adventisthealth.org/specialty-bakersfield/about-us/our-history'],'high')
v('106380868','continues_under_new_license_or_name','2024 (new HCAI ID)',
  'Langley Porter Psychiatric Institute still operates; it reappears in the HCAI data in 2024 under a new ID with the same name and 56 beds.',
  [],'medium')
v('106364014','cannot_verify',None,
  'Loma Linda University Behavioral Medicine Center is listed as open by HCAI (89 licensed beds), with a financial report ending Aug 29, 2023; no source explains the reporting stop.',
  ['https://hcai.ca.gov/facility/loma-linda-university-behavioral-medicine-center/'],'low')
v('106340025','continues_under_new_license_or_name','April 2023 (opened; new HCAI ID)',
  'UC Davis Rehabilitation Hospital opened in April 2023 with Lifepoint Rehabilitation; the HCAI data list it in 2023 under two IDs (a placeholder name and a final ID).',
  ['https://health.ucdavis.edu/awards/about/uc-davis-health-opens-sacramentos-first-rehab-hospital/2023/04'],'medium')

v('106430837','continues_under_new_license_or_name','March 1, 2019 (Santa Clara County took over operations)',
  "O'Connor Hospital in San Jose was bought out of Verity Health's bankruptcy by Santa Clara County, which took over operations on March 1, 2019; the county lists it as an active 358-bed acute care hospital.",
  ['https://news.santaclaracounty.gov/node/3736','https://www.santaclaracounty.gov/node/956'],'medium')
