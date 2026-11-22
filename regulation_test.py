#!/usr/bin/env python3
"""
Regulation-neutrality test for the crop-protection NPV model.

The question: does the hurdle a new active ingredient has to clear depend on
the regulatory regime, or is it determined by the economics alone?

Four structures are compared, all on the base-case parameters:

  baseline (as published)   the survey cost and timeline, unchanged
  free registration          the $35m registration cost removed
  fast lead time 8.3y        the development calendar compressed to the
                             1995-speed approval benchmark
  full deregulation          both of the above at once

Two hurdles are reported for each, and they are different quantities:

  NPV = 0 hurdle      depends on the discount rate
  IRR = 15% hurdle    discount-rate independent by construction

Run it:

    python3 regulation_test.py

Results are written to crop_protection_npv_regulation_test_results.json.

Three errors in an earlier version of this test are worth recording, because
all three made deregulation look more powerful than the $35m of registration
cost can justify - that is, they overstated how much of the hurdle regulation
explains.

  R1  The "free registration" case did not remove $35m. It removed the $90m
      registration phase *and* cut the development cost by $35m, taking out
      roughly $120m of cash outflow against a $35m claim. The phase covers
      launch activity as well as registration, so zeroing it double-counted.

  R2  The "fast lead time" case truncated the final phase: the calendar ran
      to t=8.30 but the schedule horizon was 8 years, so $14.6m of pre-launch
      spend was silently dropped.

  R3  "Full deregulation" combined R1 and R2 and then dropped the entire $90m
      registration phase out of the calendar entirely, plus two thirds of the
      $95m late-development phase. A further $95m of spend disappeared.

The corrections move the result against the argument that regulation is a
large tax, while strengthening the conclusion that regulation is not the
binding constraint: the corrected hurdles sit further above the $48.6m mean
realised by the 2010 launch cohort.
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

# Registration is $35m of the $307m survey total.
REGISTRATION_COST = 35.0

base_phases = list(m.PHASES)
base_years = m.DEV_YEARS


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


def npv_at(peak, dev_cost, disc):
    cfs = m.cashflows(peak, dev_cost, MARGIN, TAX, LIFE)
    return sum(cf / ((1.0 + disc) ** i) for i, cf in enumerate(cfs))


def irr_at(peak, dev_cost):
    return m.irr(m.cashflows(peak, dev_cost, MARGIN, TAX, LIFE))


def solve(fn, lo=1.0, hi=20000.0, iters=300):
    """Monotone root find: fn increasing -> find where fn crosses zero."""
    for _ in range(iters):
        mid = (lo + hi) / 2
        if fn(mid) < 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def npv_hurdle(dev_cost, years, phases, disc):
    with structure(phases, years):
        return solve(lambda p: npv_at(p, dev_cost, disc))


def irr_hurdle(dev_cost, years, phases, target=0.15):
    """Peak sales required for IRR == target. IRR rises monotonically with
    peak sales, so bisect on f(p) = IRR(p) - target."""
    with structure(phases, years):
        return solve(lambda p: (irr_at(p, dev_cost) or -1.0) - target)


def cash_outflow(dev_cost, years, phases):
    """All the cash the programme spends: pre-launch, launch, scale-up and
    stewardship."""
    with structure(phases, years):
        sched = sum(m.pre_launch_schedule(dev_cost))
    scale = dev_cost / m.REFERENCE_DEV_COST
    return (sched + m.LAUNCH_MARKETING * scale + m.SCALEUP_SHARE * dev_cost
            + m.STEWARD_SHARE * dev_cost)


# ------------------------------------------------------------------ structures
# R1: remove the $35m registration cost. The $90m registration phase is NOT
# also zeroed - it is a different cost line covering launch activity as well
# as registration.
cost_no_reg = COST - REGISTRATION_COST

# R2/R3: compressing the calendar scales the phase starts and durations
# together. The horizon must cover the whole calendar, or the final phase is
# truncated and its spend is silently dropped.
lead_scale = 8.3 / 11.0
fast_phases = [(s * lead_scale, d * lead_scale, c) for (s, d, c) in base_phases]
fast_years = 9          # calendar ends at t=8.30; horizon 9 avoids truncation

STRUCTURES = {
    "baseline (as published)": (COST, base_years, base_phases),
    "free registration": (cost_no_reg, base_years, base_phases),
    "fast lead time 8.3y": (COST, fast_years, fast_phases),
    "full deregulation": (cost_no_reg, fast_years, fast_phases),
}
RATES = [0.085, 0.135, 0.15]

print("=" * 86)
print("SANITY: how much cash does each counterfactual actually remove?")
print("=" * 86)
base_out = cash_outflow(COST, base_years, base_phases)
print(f"  baseline total cash outflow            ${base_out:,.2f}m")
for name, (dc, yrs, ph) in list(STRUCTURES.items())[1:]:
    o = cash_outflow(dc, yrs, ph)
    print(f"  {name:26s} removes ${base_out-o:6.2f}m")
print(f"  (the registration channel is ${REGISTRATION_COST:.2f}m)")

print()
print("=" * 86)
print("SANITY: is any pre-launch spend dropped by truncation?")
print("=" * 86)
for name, (dc, yrs, ph) in STRUCTURES.items():
    with structure(ph, yrs):
        alloc = sum(m.pre_launch_schedule(dc))
    nominal = dc * m.PRE_LAUNCH_BUDGET / m.REFERENCE_DEV_COST
    print(f"  {name:26s} allocated ${alloc:7.2f}m of nominal ${nominal:7.2f}m"
          f"  -> dropped ${nominal-alloc:6.2f}m")

print()
print("=" * 86)
print("NPV = 0 HURDLE (peak sales required) - depends on the discount rate")
print("=" * 86)
print(f"{'structure':<28}" + "".join(f"{d:>10.1%}" for d in RATES) + f"{'vs cohort':>12}")
results = {}
for name, (dc, yrs, ph) in STRUCTURES.items():
    row = []
    for d in RATES:
        h = npv_hurdle(dc, yrs, ph, d)
        row.append(h)
        results.setdefault(name, {})[f"npv_zero_at_{d:.3f}"] = h
    print(f"{name:<28}" + "".join(f"${h:>9,.0f}m" for h in row) +
          f"{row[1]/COHORT_MEAN:>11.1f}x")

print()
print("=" * 86)
print("IRR = 15% HURDLE - discount-rate independent by construction")
print("=" * 86)
for name, (dc, yrs, ph) in STRUCTURES.items():
    h = irr_hurdle(dc, yrs, ph)
    results.setdefault(name, {})["irr_15pct_hurdle"] = h
    print(f"  {name:28} ${h:>9,.0f}m    ({h/COHORT_MEAN:.1f}x the 2010 cohort mean of $48.6m)")

print()
print("=" * 86)
print("THE DECISIVE TEST")
print("=" * 86)
full = results["full deregulation"]
base = results["baseline (as published)"]
print(f"  Baseline NPV=0 hurdle @8.5%:      ${base['npv_zero_at_0.085']:,.0f}m")
print(f"  After FULL deregulation @8.5%:      ${full['npv_zero_at_0.085']:,.0f}m")
print(f"  Change: {(full['npv_zero_at_0.085']/base['npv_zero_at_0.085']-1)*100:+.1f}%")
print()
print(f"  2010 cohort realised mean per AI:   ${COHORT_MEAN}m")
print(f"  Full-deregulation hurdle @8.5%:     ${full['npv_zero_at_0.085']:,.0f}m "
      f"= {full['npv_zero_at_0.085']/COHORT_MEAN:.1f}x the cohort mean")
print(f"  Full-deregulation IRR=15% hurdle:   ${full['irr_15pct_hurdle']:,.0f}m "
      f"= {full['irr_15pct_hurdle']/COHORT_MEAN:.1f}x the cohort mean")
print()
gap_base = base["irr_15pct_hurdle"]
gap_full = full["irr_15pct_hurdle"]
closed = (gap_base - gap_full) / (gap_base - COHORT_MEAN)
print(f"  Share of the distance from the ${gap_base:,.0f}m hurdle to the "
      f"${COHORT_MEAN}m cohort mean")
print(f"  that full deregulation closes:       {closed*100:.0f}%")

out = {"structures": results, "cohort_mean": COHORT_MEAN, "rates": RATES}
path = os.path.join(_HERE, "crop_protection_npv_regulation_test_results.json")
with open(path, "w") as fh:
    json.dump(out, fh, indent=2)
print(f"\n  written: {os.path.basename(path)}")
