#!/usr/bin/env python3
"""
Regulation counterfactuals for the crop-protection NPV model.

The question: does the hurdle a new active ingredient has to clear depend on
the regulatory regime, or is it determined by the economics alone?

Four structures are compared, all on the base-case parameters:

  baseline (as published)   the survey cost and timeline, unchanged
  free registration          the $35m registration dossier cost removed, at
                             the registration phase's own timing
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

HOW THE TWO CHANNELS ARE NOW IMPLEMENTED
-----------------------------------------
An earlier version of this script described interventions it did not perform,
and an external review of the published code found it. Both are fixed here.

  * "FREE REGISTRATION" REMOVED THE WRONG MONEY. It lowered the total
    development cost and let the schedule scale every phase down pro rata, so
    roughly $31m of the $35m saving came out of discovery and research rather
    than registration - and post-launch marketing, scale-up and stewardship
    fell as well, because they scaled with the same total. The removal is now
    phase-specific: the registration phase's cost goes to zero, every other
    phase keeps its budget, and the post-launch cost lines are held fixed at
    their reference amounts because they are commercial-spend assumptions,
    not functions of the registration dossier. The saving also lands at the
    registration phase's own timing, which is late in the programme and
    therefore discounted more heavily than an equivalent early saving.

  * "1995-SPEED CALENDAR" MOVED REVENUE TWO YEARS, NOT 2.7. The engine ran on
    whole-year periods, so compressing the phase calendar to 8.3 years
    actually launched the product two years earlier than the baseline while
    the text claimed 2.7 - and a third variant launched commercial sales
    three years before the registration dossier was finished, which is not
    what removing an approval queue looks like. The engine now carries
    continuous time, so the calendar compresses to exactly 8.3 years and
    first revenue arrives 2.7 years earlier, as stated. There is no longer a
    case in which the product sells before registration is finished.

COMPRESSING THE CALENDAR ALSO MOVES SPEND
------------------------------------------
Compressing the calendar pulls spending forward, and money spent earlier is
discounted less. That effect raises the hurdle rather than lowering it, and
it is not about regulation at all: the same work would cost more in present
value if it were done faster. The model lets it happen rather than assuming
compression is free, which is why the compressed-calendar case is not
automatically the more favourable one.

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

BASE = m.SCENARIOS["Narrow molecule"]
PEAK, COST = BASE["peak_sales"], BASE["dev_cost"]
MARGIN, TAX, DISC, LIFE = (BASE["ebit_margin"], BASE["tax"],
                            BASE["discount"], BASE["life"])

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
LEAD_1995 = m.LEAD_1995
DEV_YEARS = m.DEV_YEARS

# Compressing the calendar scales the phase starts and durations together.
# The engine carries continuous time, so first revenue arrives at exactly
# 8.3 years rather than at a rounded whole period.
LEAD_SCALE = LEAD_1995 / DEV_YEARS

# Phase costs with the registration phase removed. Every other phase keeps
# its budget; the saving lands at the registration phase's own timing.
COSTS_NO_REG = m.phase_costs_without_registration(COST)

# The registration phase's cost is scaled with the total, so the amount
# actually removed is the scaled figure.
REG_REMOVED = (m.scaled_phase_costs(COST)[m.REGISTRATION_PHASE_INDEX]
               - COSTS_NO_REG[m.REGISTRATION_PHASE_INDEX])

# The approval-wait case: the R&D programme is untouched - same five phases,
# same budgets, same dates - but the product launches when the dossier is
# filed at the end of the field-trials and toxicology phase, instead of
# waiting for the registration phase to run. Registration cost is still paid;
# what is removed is the queue between dossier and authorisation. This is
# the most generous version of the case, and it is an upper bound rather
# than a forecast: no source measures the split between dossier preparation
# and regulatory review inside the registration phase.
APPROVAL_WAIT_LAUNCH = 9.5

STRUCTURES = {
    "baseline (as published)": dict(
        dev_cost=COST, phase_costs=None, time_scale=1.0, launch_offset=None),
    "free registration": dict(
        dev_cost=COST - REG_REMOVED, phase_costs=COSTS_NO_REG, time_scale=1.0,
        launch_offset=None),
    "1995-speed calendar": dict(
        dev_cost=COST, phase_costs=None, time_scale=LEAD_SCALE,
        launch_offset=None),
    "approval wait removed (R&D fixed)": dict(
        dev_cost=COST, phase_costs=None, time_scale=1.0,
        launch_offset=APPROVAL_WAIT_LAUNCH),
    "both": dict(
        dev_cost=COST - REG_REMOVED, phase_costs=COSTS_NO_REG,
        time_scale=LEAD_SCALE, launch_offset=None),
    "both, plus approval wait removed": dict(
        dev_cost=COST - REG_REMOVED, phase_costs=COSTS_NO_REG,
        time_scale=LEAD_SCALE,
        launch_offset=APPROVAL_WAIT_LAUNCH * LEAD_SCALE),
}
RATES = [0.085, 0.135, 0.15]


def npv_hurdle(dev_cost, disc, **kw):
    """Peak sales at which NPV = 0 at `disc`."""
    lo, hi = 1.0, 20000.0
    for _ in range(200):
        mid = (lo + hi) / 2
        pairs = m.cashflow_pairs(mid, dev_cost, MARGIN, TAX, LIFE, **kw)
        if m.npv_of(pairs, disc) > 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def irr_hurdle(dev_cost, target=0.15, **kw):
    """Peak sales required for IRR == target."""
    lo, hi = 1.0, 20000.0
    for _ in range(200):
        mid = (lo + hi) / 2
        pairs = m.cashflow_pairs(mid, dev_cost, MARGIN, TAX, LIFE, **kw)
        r = m.irr_of(pairs)
        if r is None or r < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def cash_outflow(dev_cost, **kw):
    """All the cash the programme spends: pre-launch, launch, scale-up and
    stewardship."""
    sched = sum(a for _, a in m.pre_launch_pairs(
        kw.get("phase_costs") or m.scaled_phase_costs(dev_cost),
        kw.get("time_scale", 1.0)))
    return sched + m.LAUNCH_MARKETING + m.SCALEUP + m.STEWARD


def first_revenue(dev_cost, **kw):
    """The time at which the product first sells.

    Normally the launch is the end of the pre-launch programme. Where an
    approval-wait case pulls it forward, it is the explicit launch time.
    """
    if kw.get("launch_offset") is not None:
        return kw["launch_offset"]
    return DEV_YEARS * kw.get("time_scale", 1.0)


print("=" * 86)
print("SANITY: how much cash does each counterfactual actually remove?")
print("=" * 86)
base_out = cash_outflow(COST)
print(f"  baseline total cash outflow            ${base_out:,.2f}m")
for name, kw in list(STRUCTURES.items())[1:]:
    o = cash_outflow(kw["dev_cost"], **{k: v for k, v in kw.items() if k not in ("dev_cost", "launch_offset")})
    print(f"  {name:26s} removes ${base_out-o:6.2f}m")
print(f"  (the registration channel is ${REG_REMOVED:.2f}m)")

print()
print("=" * 86)
print("SANITY: does the removal come out of registration and nowhere else?")
print("=" * 86)
base_costs = m.scaled_phase_costs(COST)
for i, (b, r) in enumerate(zip(base_costs, COSTS_NO_REG)):
    print(f"  phase {i + 1}: ${b:7.3f}m -> ${r:7.3f}m   removed ${b-r:6.3f}m")

print()
print("=" * 86)
print("SANITY: is any pre-launch spend dropped by truncation?")
print("=" * 86)
for name, kw in STRUCTURES.items():
    alloc = sum(a for _, a in m.pre_launch_pairs(
        kw.get("phase_costs") or m.scaled_phase_costs(kw["dev_cost"]),
        kw.get("time_scale", 1.0)))
    print(f"  {name:26s} allocated ${alloc:7.2f}m of ${kw['dev_cost']:7.2f}m"
          f"  -> dropped ${kw['dev_cost']-alloc:6.2f}m")

print()
print("=" * 86)
print("SANITY: when does first revenue arrive?")
print("=" * 86)
for name, kw in STRUCTURES.items():
    t = first_revenue(kw["dev_cost"], **{k: v for k, v in kw.items()
                                        if k not in ("dev_cost",)})
    print(f"  {name:26s} first revenue at t={t:.2f}"
          f"   ({t - DEV_YEARS:+.2f} years vs baseline)")

print()
print("=" * 86)
print("NPV = 0 HURDLE (peak sales required) - depends on the discount rate")
print("=" * 86)
print(f"{'structure':<28}" + "".join(f"{d:>10.1%}" for d in RATES)
      + f"{'vs revenue':>12}")
results = {}
for name, kw in STRUCTURES.items():
    row = []
    for d in RATES:
        h = npv_hurdle(kw["dev_cost"], d, phase_costs=kw["phase_costs"],
                       time_scale=kw["time_scale"],
                       launch_offset=kw["launch_offset"])
        row.append(h)
        results.setdefault(name, {})[f"npv_zero_at_{d:.3f}"] = h
    print(f"{name:<28}" + "".join(f"${h:>9,.0f}m" for h in row) +
          f"{row[1]/COHORT_MEAN:>11.1f}x")   # vs 2022 cohort revenue

print()
print("=" * 86)
print("IRR = 15% HURDLE - discount-rate independent by construction")
print("=" * 86)
for name, kw in STRUCTURES.items():
    h = irr_hurdle(kw["dev_cost"], phase_costs=kw["phase_costs"],
                   time_scale=kw["time_scale"],
                   launch_offset=kw["launch_offset"])
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
                   ("1995-speed calendar", "1995-speed calendar"),
                   ("approval wait removed", "approval wait removed (R&D fixed)"),
                   ("both changes", "both"),
                   ("both + approval wait", "both, plus approval wait removed")):
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
# The range across every case, which is what the review asked for: the
# registration-cost channel alone closes the least, the full upper bound
# closes the most.
all_closed = [(gap_base - v["irr_15pct_hurdle"]) / (gap_base - COHORT_MEAN)
              for v in results.values()]
all_closed_peak = [(gap_base - v["irr_15pct_hurdle"])
                   / (gap_base - IMPLIED_COHORT_PEAK)
                   for v in results.values()]
print()
print(f"  Share of the distance from the ${gap_base:,.0f}m hurdle to the "
      f"${COHORT_MEAN}m cohort 2022 revenue")
print(f"  that both changes close:            {closed*100:.0f}%")
print(f"  Measured instead against the cohort's implied peak of "
      f"${IMPLIED_COHORT_PEAK:.1f}m, the like-for-like share is "
      f"{closed_peak*100:.0f}%.")
print()
print(f"  RANGE across every case tested:")
print(f"    against the cohort's 2022 revenue:   {min(all_closed)*100:.0f}% "
      f"to {max(all_closed)*100:.0f}% of the gap")
print(f"    against the cohort's implied peak:   {min(all_closed_peak)*100:.0f}% "
      f"to {max(all_closed_peak)*100:.0f}% of the gap")
print()
print("  NOTE: this share is an arithmetic distance between a scenario")
print("  threshold and a selected comparator. It is NOT the proportion of")
print("  weak industry returns caused by regulation.")

out = {"structures": results, "cohort_mean": COHORT_MEAN,
       "cohort_implied_peak": IMPLIED_COHORT_PEAK,
       "gap_closure_vs_revenue": closed, "gap_closure_vs_implied_peak": closed_peak,
       "gap_closure_range_vs_revenue": [min(all_closed), max(all_closed)],
       "gap_closure_range_vs_implied_peak": [min(all_closed_peak),
                                             max(all_closed_peak)],
       "baseline_total_cash_outflow": base_out,
       "registration_cost_removed": REG_REMOVED,
       "rates": RATES}
path = os.path.join(_HERE, "crop_protection_npv_regulation_test_results.json")
with open(path, "w") as fh:
    json.dump(out, fh, indent=2)
print(f"\n  written: {os.path.basename(path)}")
