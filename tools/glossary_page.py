"""glossary.html: plain definitions of the terms this site uses, grouped by subject, each with a link to where it appears."""
import re

GROUPS = [
 ('Hospital finances', [
  ('Operating margin', 'Operating income (operating revenue minus operating expenses) as a share of operating revenue. It leaves out income from investments, donations and other nonoperating sources.', 'hospital.html'),
  ('Total margin', 'Net income, including investment income, donations and other nonoperating revenue, as a share of total revenue.', 'hospital.html'),
  ('Gross charges', 'A hospital\'s list prices for everything it provided, before any discount. Few payers pay them; they are the starting point for negotiated and government rates.', 'explorer.html'),
  ('Net patient revenue', 'What a hospital expects to collect for patient care after discounts to insurers and government programs, charity care and bad debt are taken off its gross charges.', 'explorer.html'),
  ('Charges per dollar of net revenue', 'Gross charges divided by net patient revenue. A value of 4.0 means the hospital listed $4 in charges for every $1 it expects to collect.', 'hospital.html'),
  ('Payer mix', 'The share of a hospital\'s gross charges billed to each payer: Medicare, Medi-Cal, private insurance, county programs and others. It is based on charges, not on what each payer actually pays.', 'hospital.html'),
  ('Bad debt', 'Bills a hospital expected patients to pay that went unpaid.', 'theme-access.html'),
  ('Charity care', 'Care a hospital provided free or at a discount under its financial assistance policy, to patients it judged unable to pay.', 'theme-access.html'),
  ('Uncompensated care', 'On this site, bad debt plus charity care, as a share of gross charges.', 'theme-access.html'),
  ('Outpatient share', 'The share of a hospital\'s gross patient revenue that comes from outpatient care (visits, procedures and tests without an overnight admission).', 'theme-finances.html'),
  ('Fiscal year (FY)', 'On this site, the year a hospital\'s reporting period ends. A hospital whose year runs July 2023 to June 2024 reports FY2024.', 'explorer.html'),
 ]),
 ('Hospitals', [
  ('General acute care hospital', 'A hospital that provides round-the-clock inpatient medical and surgical care. The comparisons on this site leave out psychiatric, rehabilitation and long-term acute care hospitals.', 'explorer.html'),
  ('Safety-net hospital (DSH)', 'On this site, a hospital that qualifies for Medicare disproportionate share hospital (DSH) payments, which go to hospitals treating a large share of low-income patients.', 'theme-finances.html'),
  ('Critical access hospital', 'A small rural hospital with no more than 25 inpatient beds, usually far from another hospital, that Medicare pays based on its costs.', 'hospital-prices.html'),
  ('Health system', 'A group of hospitals, and often physician groups and clinics, under common ownership or management.', 'hospital.html'),
  ('CMS star rating', 'The Centers for Medicare & Medicaid Services\' Overall Hospital Quality Star Rating: one to five stars summarizing measures of mortality, safety, readmissions, patient experience and timely care. Hospitals that report too few measures get no rating.', 'hospital-prices.html'),
 ]),
 ('Prices', [
  ('Commercial insurance', 'Coverage from private insurers, through an employer or bought individually, including Covered California plans.', 'hospital-prices.html'),
  ('Case-mix adjusted stay', 'An inpatient stay weighted by how resource-intensive the patient\'s condition is, so a hospital treating sicker patients can be compared with one treating healthier ones.', 'hospital-prices.html'),
  ('Price compared with Medicare', 'What commercial insurers paid divided by what Medicare paid for comparable care at the same hospital. 2.0 means commercial insurers paid twice Medicare\'s rate.', 'hospital-prices.html'),
  ('Medicare', 'The federal health insurance program for people 65 and older and some younger people with disabilities. Traditional Medicare sets hospital payment rates rather than negotiating them; Medicare Advantage plans are run by private insurers.', 'theme-prices.html'),
  ('Medi-Cal', 'California\'s Medicaid program, which covers people with low incomes. Most members are enrolled in managed care plans.', 'theme-finances.html'),
 ]),
 ('Coverage and premiums', [
  ('Premium', 'The amount paid for health coverage, usually monthly. For employer plans, the total premium is split between the employer and the worker.', 'theme-affordability.html'),
  ('Worker contribution', 'The part of an employer plan\'s premium that the employee pays, usually through payroll deduction.', 'affordability.html'),
  ('Deductible', 'What a person pays for covered care each year before the plan starts paying, apart from services the plan covers in full.', 'affordability.html'),
  ('High-deductible health plan', 'A plan whose deductible is at least the minimum the IRS sets for pairing it with a health savings account.', 'affordability-data.html'),
  ('Covered California', 'California\'s health insurance marketplace under the Affordable Care Act, where people without job-based coverage buy plans, often with federal and state help.', 'districts.html'),
  ('Benchmark Silver plan', 'The second-lowest-cost Silver plan available in an area. Federal premium tax credits are calculated from its price.', 'districts.html'),
  ('Premium tax credit', 'A federal subsidy that lowers Marketplace premiums for eligible people based on income. California adds its own help for some enrollees.', 'districts.html'),
 ]),
 ('Spending and affordability', [
  ('Office of Health Care Affordability (OHCA)', 'An office within HCAI, created by state law in 2022, that measures health spending in California and sets and enforces limits on how fast it may grow.', 'theme-spending.html'),
  ('Spending growth target', 'OHCA\'s limit on yearly growth in health spending per person, starting at 3.5% for 2025 and stepping down to 3.0% by 2029.', 'theme-spending.html'),
  ('Per member per year (PMPY)', 'Spending divided by the number of people covered, for a year, so markets and regions of different sizes can be compared.', 'theme-spending.html'),
  ('Rating region', 'One of the 19 geographic areas Covered California uses to set premiums. OHCA reports spending using the same regions.', 'theme-spending.html'),
  ('True cost of economic security', 'The Urban Institute\'s measure of what a family needs to cover essentials without hardship and to save for emergencies and the future. It is set higher than the federal poverty line.', 'districts.html'),
  ('Delinquency', 'A debt payment that is past due. The district page reports the share of people whose credit card or auto loan payments are 60 or more days late.', 'districts.html'),
 ]),
 ('Data and sources', [
  ('HCAI', 'The California Department of Health Care Access and Information, which collects hospitals\' annual financial disclosures and publishes the Hospital Measurement dataset used for prices on this site.', 'sources.html'),
  ('MEPS-IC', 'The Insurance Component of the federal Medical Expenditure Panel Survey: a yearly survey of private employers on premiums, contributions and deductibles, with estimates for every state.', 'sources.html'),
  ('Median', 'The middle value when hospitals or places are ranked. Half are above and half below, so a few extreme values do not move it.', 'about.html#method'),
  ('Preliminary', 'Data the source may still revise. On this site FY2024 hospital figures are preliminary.', 'explorer.html'),
  ('Congressional district', 'One of California\'s 52 areas that each elect a member of the U.S. House. This site uses the boundaries in effect for the 119th Congress.', 'districts.html'),
 ]),
]


def slug(t):
    return re.sub(r'[^a-z0-9]+', '-', t.lower()).strip('-')


def terms():
    return [(slug(t), t, d, g) for g, rows in GROUPS for t, d, _ in rows]


def build(root, H, head, header, tail, write):
    toc = ''.join('<a href="#g-%s">%s</a>' % (slug(g), H(g)) for g, _ in GROUPS)
    body = ''.join('<section id="g-%s"><h2>%s</h2><dl class="gl">%s</dl></section>' % (slug(g), H(g), ''.join(
        '<div id="%s"><dt>%s</dt><dd>%s <a href="%s">Where it appears</a></dd></div>' % (slug(t), H(t), H(d), H(u)) for t, d, u in rows)) for g, rows in GROUPS)
    out = head('Glossary of hospital finance and health cost terms | Hospital Price Watch', 'Plain definitions of the terms used on Hospital Price Watch: margins, charges, case-mix adjusted stays, benchmark plans, OHCA and more.', 'glossary.html') + header('glossary.html')
    out += '''<main id="main"><div class="page-head"><div class="wrap"><h1>Glossary</h1><p class="lede">What the terms on this site mean, in plain words, and where to see each one used.</p></div></div>
<div class="wrap aside-grid"><nav class="toc" aria-label="Glossary sections">%s</nav><div class="prose gl-body">%s
<p class="sub">Definitions describe how this site uses each term. For the full methods behind a figure, see the source named under each chart and <a href="sources.html">Sources and how we check them</a>.</p></div></div></main>
''' % (toc, body)
    write('glossary.html', out + tail())
    return sum(len(r) for _, r in GROUPS)
