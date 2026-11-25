#!/usr/bin/env python3
"""
Regulation counterfactuals for the crop-protection NPV model.

The question: does the hurdle a new active ingredient has to clear depend on
the regulatory regime, or is it determined by the economics alone?

Four structures are compared, all on the base-case parameters:

  baseline (as published)   the survey cost and timeline, unchanged
  free registration          the $35m registration cost removed
  1995-speed calendar        the pre-launch calendar compressed to the
                             1995 lead time of 8.3 years
  both of those at once

Two hurdles are reported for each, and they are different quantities:

  NPV = 0 hurdle      depends on the discount rate
  IRR = 15% hurdle    discount-rate independent by construction

Run it:

    python3 regulation_test.py

Results are written to crop_protection_npv_regulation_test_results.json.

WHAT THIS TEST DOES AND DOES NOT SHOW
-------------------------------------
It removes ONE cost category - the registration dossier - and compresses ONE
calendar. It does not remove regulation. The AgbioInvestor study places
regulatory activity inside the development phase as well as inside
registration: registration field trials alone ran at $30.4m in 2020-23, and
the study's own definition of "Product Launch & Development" covers
"all regulatory costs linked to product launch, label expansions and product
defence". A shorter approval queue also has effects this model does not
estimate: a denied application, a lost indication, a delayed cash receipt,
an abandoned programme, or geographic exclusion from a market.

So the honest reading of the result is narrow: removing the registration
dossier and compressing the calendar does not rescue the assumed small-product
case. It is not a finding that regulation is unimportant, and the scenario
below is not a free-registration regime.

CALENDAR COMPRESSION, AND WHY IT IS DONE WITH FRACTIONAL TIMING
----------------------------------------------------------------
The 1995 lead time was 8.3 years and the model's development programme is 11
years, so compression removes 2.7 years. An earlier version of this script
compressed the phase calendar to 8.3 years but ran the cash-flow engine on
whole-year periods, so the product actually launched two years earlier than
the baseline rather than 2.7 - and the chart footnote claimed 3.1. That
mismatch overstated the benefit of fast approval.

Two counterfactuals are therefore reported separately:

  compressed calendar      the development work is genuinely done faster.
                           The R&D programme is compressed to 8.3 years, so
                           the same $307m is spent sooner and first revenue
                           arrives 2.7 years earlier. This is the strongest
                           reading of "fast approval".

  approval wait removed    the R&D programme is NOT compressed. The same
                           11-year spend pattern is unchanged and the
                           product launches while it is still being spent, so
                           the delay saved is waiting for approval rather
                           than working faster. This is the narrower and more
                           defensible reading.

Compressing the calendar also pulls spending forward, which lowers the hurdle
for reasons that are not about regulation at all - money spent earlier is
discounted less. The two variants separate that effect from the timing of
first revenue.

THE $700m QUESTION
-------------------
An earlier version of this piece also published a second, independently
written construction of the same model from the same $307m cost base, which
produced a breakeven of about $700m for the same 15% hurdle. The comparison
was worth making - it showed the result is not structure-invariant - but it
was presented without publishing that construction, so a reader could not
check it. The alternative model is therefore published here as
alternative_construction.py, with its assumptions stated, and the article
points to it directly rather than asserting internal consistency.
"""
import importlib.util
import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "crop_protection_npv", os.path.join(_HERE, "crop_protection_npv.py"))
m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m)

BASE = m.SCENARIOS["Base"]
PEAK, COST = BASE["peak_sales"], BASE["dev_cost"]
MARGIN, TAX, DISC, LIFE = BASE["ebit_margin"], BASE["tax"], BASE["discount"], BASE["life"]

# Mean realised revenue per active ingredient for the ten new actives
# launched in 2010, measured on their 2022 revenue.
COHORT_MEAN = 48.6

# The cohort figure above is revenue in a single late year (2022), twelve
# years after launch, not peak annual sales. Applying this model's own
# average revenue path to the cohort - year-12 penetration of 0.40 - gives
# implied peak sales per active ingredient of about $121m. Both comparisons
# are printed below: the headline multiple uses realised revenue, the
# like-for-like multiple uses implied peak.
IMPLIED_COHORT_PEAK = COHORT_MEAN / m.PENETRATION[12]

# Registration is $35m of the $307m survey total.
REGISTRATION_COST = 35.0

# The 1995 lead time, and the model's own development period.
LEAD_1995 = 8.3
DEV_YEARS = m.DEV_YEARS

base_phases = list(m.PHASES)


class structure:
    """Temporarily swap the model's pre-launch structure."""

    def __init__(self, phases, years):
        self.phases, self.years = phases, years

    def __enter__(self):
        self.old = (m.PHASES, m.DEV_YEARS)
        m.PHASES, m.DEV_YEARS = self.phases, self.years
        return self

    def __exit__(self, *a):
        m.PHASES, m.DEV_YEARS = self.old


def npv_at(peak, dev_cost, disc, **kw):
    cfs = m.cashflows(peak, dev_cost, MARGIN, TAX, LIFE, **kw)
    return sum(cf / ((1.0 + disc) ** i) for i, cf in enumerate(cfs))


def irr_at(peak, dev_cost, **kw):
    return m.irr(m.cashflows(peak, dev_cost, MARGIN, TAX, LIFE, **kw))


def solve(fn, lo=1.0, hi=20000.0, iters=300):
    """Monotone root find: fn increasing -> find where fn crosses zero."""
    for _ in range(iters):
        mid = (lo + hi) / 2
        if fn(mid) < 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def npv_hurdle(dev_cost, years, phases, disc, **kw):
    with structure(phases, years):
        return solve(lambda p: npv_at(p, dev_cost, disc, **kw))


def irr_hurdle(dev_cost, years, phases, target=0.15, **kw):
    """Peak sales required for IRR == target. IRR rises monotonically with
    peak sales, so bisect on f(p) = IRR(p) - target."""
    with structure(phases, years):
        return solve(lambda p: (irr_at(p, dev_cost, **kw) or -1.0) - target)


def cash_outflow(dev_cost, years, phases):
    """All the cash the programme spends: pre-launch, launch, scale-up and
    stewardship."""
    with structure(phases, years):
        sched = sum(m.pre_launch_schedule(dev_cost))
    scale = dev_cost / m.REFERENCE_DEV_COST
    return (sched + m.LAUNCH_MARKETING * scale + m.SCALEUP_SHARE * dev_cost
            + m.STEWARD_SHARE * dev_cost)


# ------------------------------------------------------------------ structures
# Removing the registration dossier removes $35m of cash. It does NOT zero
# the registration phase: that phase also carries work that would still have
# to be done, and zeroing it would remove more cash than the $35m claim.
cost_no_reg = COST - REGISTRATION_COST

# Compressing the calendar scales the phase starts and durations together.
# The horizon must cover the whole calendar, or the final phase is truncated
# and its spend is silently dropped.
lead_scale = LEAD_1995 / DEV_YEARS
fast_phases = [(s * lead_scale, d * lead_scale, c) for (s, d, c) in base_phases]
fast_years = 9          # calendar ends at t=8.30; horizon 9 avoids truncation

# The approval-wait variant: the R&D programme is untouched, but the product
# launches while development is still being spent. 2.7 years earlier, which
# on whole-year periods is three periods earlier (the calendar is measured
# from the first synthesis, and revenue in the launch year is not a full
# year of selling).
wait_saved = round(DEV_YEARS - (DEV_YEARS * lead_scale))
launch_offset = DEV_YEARS - wait_saved

STRUCTURES = {
    "baseline (as published)": (COST, base_years_placeholder := DEV_YEARS, base_phases, {}),
    "free registration": (cost_no_reg, DEV_YEARS, base_phases, {}),
    "approval wait removed": (COST, DEV_YEARS, base_phases,
                              {"launch_offset": launch_offset}),
    "1995-speed calendar": (COST, fast_years, fast_phases, {}),
    "both": (cost_no_reg, fast_years, fast_phases, {}),
}
RATES = [0.085, 0.135, 0.15]

print("=" * 86)
print("SANITY: how much cash does each counterfactual actually remove?")
print("=" * 86)
base_out = cash_outflow(COST, DEV_YEARS, base_phases)
print(f"  baseline total cash outflow            ${base_out:,.2f}m")
for name, (dc, yrs, ph, kw) in list(STRUCTURES.items())[1:]:
    o = cash_outflow(dc, yrs, ph)
    print(f"  {name:26s} removes ${base_out-o:6.2f}m")
print(f"  (the registration channel is ${REGISTRATION_COST:.2f}m)")

print()
print("=" * 86)
print("SANITY: is any pre-launch spend dropped by truncation?")
print("=" * 86)
for name, (dc, yrs, ph, kw) in STRUCTURES.items():
    with structure(ph, yrs):
        alloc = sum(m.pre_launch_schedule(dc))
    print(f"  {name:26s} allocated ${alloc:7.2f}m of ${dc:7.2f}m"
          f"  -> dropped ${dc-alloc:6.2f}m")

print()
print("=" * 86)
print("SANITY: how much earlier does first revenue arrive?")
print("=" * 86)
print(f"  baseline            first revenue at t={DEV_YEARS}")
print(f"  1995-speed calendar first revenue at t={fast_years} "
      f"(calendar compressed {DEV_YEARS-LEAD_1995:.1f} years)")
print(f"  approval wait removed first revenue at t={launch_offset} "
      f"with the R&D programme unchanged")

print()
print("=" * 86)
print("NPV = 0 HURDLE (peak sales required) - depends on the discount rate")
print("=" * 86)
print(f"{'structure':<28}" + "".join(f"{d:>10.1%}" for d in RATES) + f"{'vs revenue':>12}")
results = {}
for name, (dc, yrs, ph, kw) in STRUCTURES.items():
    row = []
    for d in RATES:
        h = npv_hurdle(dc, yrs, ph, d, **kw)
        row.append(h)
        results.setdefault(name, {})[f"npv_zero_at_{d:.3f}"] = h
    print(f"{name:<28}" + "".join(f"${h:>9,.0f}m" for h in row) +
          f"{row[1]/COHORT_MEAN:>11.1f}x")   # vs 2022 cohort revenue

print()
print("=" * 86)
print("IRR = 15% HURDLE - discount-rate independent by construction")
print("=" * 86)
for name, (dc, yrs, ph, kw) in STRUCTURES.items():
    h = irr_hurdle(dc, yrs, ph, **kw)
    results.setdefault(name, {})["irr_15pct_hurdle"] = h
    print(f"  {name:28} ${h:>9,.0f}m    ({h/COHORT_MEAN:.1f}x the 2010 cohort 2022 revenue of $48.6m; "
          f"{h/IMPLIED_COHORT_PEAK:.1f}x its implied peak of ${IMPLIED_COHORT_PEAK:.1f}m)")

print()
print("=" * 86)
print("THE DECISIVE TEST")
print("=" * 86)
full = results["both"]
base = results["baseline (as published)"]
print(f"  Baseline NPV=0 hurdle @8.5%:      ${base['npv_zero_at_0.085']:,.0f}m")
print(f"  After BOTH changes @8.5%:         ${full['npv_zero_at_0.085']:,.0f}m")
print(f"  Change: {(full['npv_zero_at_0.085']/base['npv_zero_at_0.085']-1)*100:+.1f}%")
print()
print(f"  2010 cohort realised mean per AI:   ${COHORT_MEAN}m (2022 revenue)")
print(f"  Cohort implied peak per AI:          ${IMPLIED_COHORT_PEAK:.1f}m "
      f"(this model's revenue path, year-12 penetration {m.PENETRATION[12]:.2f})")
print(f"  Both-changes hurdle @8.5%:         ${full['npv_zero_at_0.085']:,.0f}m "
      f"= {full['npv_zero_at_0.085']/COHORT_MEAN:.1f}x the cohort 2022 revenue")
print(f"  Both-changes IRR=15% hurdle:       ${full['irr_15pct_hurdle']:,.0f}m "
      f"= {full['irr_15pct_hurdle']/COHORT_MEAN:.1f}x the cohort 2022 revenue, "
      f"{full['irr_15pct_hurdle']/IMPLIED_COHORT_PEAK:.1f}x its implied peak")
print()

for label, key in (("registration cost removed", "free registration"),
                   ("approval wait removed", "approval wait removed"),
                   ("1995-speed calendar", "1995-speed calendar"),
                   ("both changes", "both")):
    g_base = base["irr_15pct_hurdle"]
    g_new = results[key]["irr_15pct_hurdle"]
    closed = (g_base - g_new) / (g_base - COHORT_MEAN)
    closed_peak = (g_base - g_new) / (g_base - IMPLIED_COHORT_PEAK)
    print(f"  {label:28} hurdle ${g_new:,.0f}m | closes "
          f"{closed*100:4.0f}% of the gap to the cohort's 2022 revenue, "
          f"{closed_peak*100:4.0f}% of the gap to its implied peak")

gap_base = base["irr_15pct_hurdle"]
gap_full = full["irr_15pct_hurdle"]
closed = (gap_base - gap_full) / (gap_base - COHORT_MEAN)
closed_peak = (gap_base - gap_full) / (gap_base - IMPLIED_COHORT_PEAK)
print()
print(f"  Share of the distance from the ${gap_base:,.0f}m hurdle to the "
      f"${COHORT_MEAN}m cohort 2022 revenue")
print(f"  that both changes close:            {closed*100:.0f}%")
print(f"  Measured instead against the cohort's implied peak of "
      f"${IMPLIED_COHORT_PEAK:.1f}m, the like-for-like share is "
      f"{closed_peak*100:.0f}%.")

out = {"structures": results, "cohort_mean": COHORT_MEAN,
       "cohort_implied_peak": IMPLIED_COHORT_PEAK,
       "gap_closure_vs_revenue": closed, "gap_closure_vs_implied_peak": closed_peak,
       "baseline_total_cash_outflow": base_out,
       "rates": RATES}
path = os.path.join(_HERE, "crop_protection_npv_regulation_test_results.json")
with open(path, "w") as fh:
    json.dump(out, fh, indent=2)
print(f"\n  written: {os.path.basename(path)}")
