#!/usr/bin/env python3
"""
Regulatory cost and delay counterfactuals for the crop-protection NPV model.

Compares six pre-launch structures on the base-case parameters ($307m R&D,
40% operating contribution, 21% tax, 15-year commercial life):
  1. baseline (as published)          survey cost and 11-year timeline
  2. free registration                $35m registration phase removed at t=9.5-11.0
  3. 1995-speed calendar              pre-launch calendar compressed to 8.3 years
  4. approval wait removed            R&D budgets unchanged; dossier prepared
                                      concurrently with late field trials (t=8.0-9.5)
                                      and product launched at t=9.5
  5. both                             free registration + 1995-speed calendar
  6. both, plus approval wait removed free registration + 1995 calendar + launch at t=7.17

Usage:
    python3 regulation_test.py

Writes results to crop_protection_npv_regulation_test_results.json.
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

# 2010 launch cohort benchmark: $48.6m average 2022 revenue (year 12), which
# implies $121.5m peak sales at year-12 penetration of 0.40.
COHORT_MEAN = 48.6
IMPLIED_COHORT_PEAK = COHORT_MEAN / m.PENETRATION[12]

REGISTRATION_COST = 35.0
LEAD_1995 = m.LEAD_1995
DEV_YEARS = m.DEV_YEARS
LEAD_SCALE = LEAD_1995 / DEV_YEARS

COSTS_NO_REG = m.phase_costs_without_registration(COST)
REG_REMOVED = (m.scaled_phase_costs(COST)[m.REGISTRATION_PHASE_INDEX]
               - COSTS_NO_REG[m.REGISTRATION_PHASE_INDEX])

# Approval-wait counterfactual: dossier prepared concurrently with the final
# 1.5 years of field trials/toxicology (t=8.0 to 9.5) and product launched at
# t=9.5 so no pre-launch spend falls after launch.
APPROVAL_WAIT_LAUNCH = 9.5
PHASES_NO_APPROVAL_WAIT = list(m.PHASES)
PHASES_NO_APPROVAL_WAIT[m.REGISTRATION_PHASE_INDEX] = (8.0, 1.5, 35.0)

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
        launch_offset=APPROVAL_WAIT_LAUNCH,
        phases=PHASES_NO_APPROVAL_WAIT),
    "both": dict(
        dev_cost=COST - REG_REMOVED, phase_costs=COSTS_NO_REG,
        time_scale=LEAD_SCALE, launch_offset=None),
    "both, plus approval wait removed": dict(
        dev_cost=COST - REG_REMOVED, phase_costs=COSTS_NO_REG,
        time_scale=LEAD_SCALE,
        launch_offset=APPROVAL_WAIT_LAUNCH * LEAD_SCALE,
        phases=PHASES_NO_APPROVAL_WAIT),
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
        kw.get("time_scale", 1.0),
        kw.get("phases")))
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
        kw.get("time_scale", 1.0),
        kw.get("phases")))
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
print("SANITY: does any pre-launch spend fall after the product launches?")
print("=" * 86)
for name, kw in STRUCTURES.items():
    t_launch = first_revenue(kw["dev_cost"], **{k: v for k, v in kw.items()
                                                if k not in ("dev_cost",)})
    pre_pairs = m.pre_launch_pairs(
        kw.get("phase_costs") or m.scaled_phase_costs(kw["dev_cost"]),
        kw.get("time_scale", 1.0),
        kw.get("phases"))
    last_pre_t = max(t for t, _ in pre_pairs)
    after = sum(a for t, a in pre_pairs if t >= t_launch - 1e-9)
    assert last_pre_t <= t_launch + 1e-9, (
        f"{name}: pre-launch spend at t={last_pre_t:.2f} occurs after launch "
        f"at t={t_launch:.2f}")
    print(f"  {name:26s} last pre-launch spend at t={last_pre_t:5.2f} "
          f"(launch t={t_launch:5.2f})  ->  ${after:6.2f}m after launch")

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
                       launch_offset=kw["launch_offset"],
                       phases=kw.get("phases"))
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
                   launch_offset=kw["launch_offset"],
                   phases=kw.get("phases"))
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


def _rounded(obj, ndigits=10):
    """Round floats at serialisation so JSON outputs are byte-reproducible."""
    if isinstance(obj, dict):
        return {k: _rounded(v, ndigits) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_rounded(v, ndigits) for v in obj]
    if isinstance(obj, float):
        return round(obj, ndigits)
    return obj


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
    json.dump(_rounded(out), fh, indent=2)
print(f"\n  written: {os.path.basename(path)}")
