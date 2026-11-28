#!/usr/bin/env python3
"""
Alternative DCF construction from the same $307m AgbioInvestor cost base.

Tests how much the 15% IRR peak-sales hurdle moves when rebuilt under a
different set of defensible structural assumptions ($696m vs. $596m in
crop_protection_npv.py), and decomposes the $101m spread into an exact
seven-step sequential waterfall:
  1. Even 10-year pre-launch spend (launch at t=10) vs. uneven 11-year phases
  2. No separate post-launch cost lines ($0m vs. $76m)
  3. Post-peak erosion of 25%/yr vs. 15%/yr
  4. Commercial life of 10 years vs. 15 years
  5. Operating contribution of 35% vs. 40%
  6. Tax rate of 25% vs. 21%
  7. No net operating loss carry-forward vs. loss carry-forward

Usage:
    python3 alternative_construction.py

Writes results to alternative_construction_results.json.
"""
import importlib.util
import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "crop_protection_npv", os.path.join(_HERE, "crop_protection_npv.py"))
m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m)

# --------------------------------------------------------------- assumptions

DEV_COST = 307.0          # the survey's cost, unchanged
TAX = 0.25                # higher: an originator with a less favourable mix
MARGIN = 0.35             # operating contribution before R&D amortisation
LIFE = 10                 # commercial years, and the amortisation period
HURDLE = 0.15             # the corporate hurdle
EROSION = 0.25            # post-peak decline, per year, as a fraction of peak

# Pre-launch calendar. The published model runs an uneven eleven-year
# programme; this construction spends the money evenly over ten years. The
# difference is disclosed and priced in the waterfall below.
PRE_YEARS = 10

# The published model's own assumptions, which the waterfall starts from.
PUB_MARGIN = 0.40
PUB_TAX = 0.21
PUB_LIFE = 15
PUB_EROSION = 0.15

# The revenue shape, shared by both constructions so that the published
# model's own path is reproduced exactly at 15% erosion: a five-year ramp,
# four years at peak, then the erosion rate.
RAMP = (0.20, 0.36, 0.52, 0.68, 0.84)
PLATEAU_YEARS = 4


def penetration(c: int, erosion: float) -> float:
    """Penetration for commercial year c under a given erosion rate.

    The published model's PENETRATION list is reproduced exactly at 15%
    erosion, and this construction's own path exactly at 25%.
    """
    if c < len(RAMP):
        return RAMP[c]
    peak_end = len(RAMP) + PLATEAU_YEARS - 1
    if c <= peak_end:
        return 1.00
    return max(0.0, 1.0 - erosion * (c - peak_end))


def cashflows(peak_sales: float, margin: float = MARGIN, tax: float = TAX,
              life: int = LIFE, pre_years: int = PRE_YEARS,
              post_launch_costs: bool = False) -> list[float]:
    """Pre-launch development spend, then commercial cash flow.

    The whole development cost is treated as capitalised spend amortised over
    the commercial life. With `post_launch_costs` false there are no separate
    post-launch cost lines: launch marketing, manufacturing scale-up and
    stewardship are not charged, which is itself a difference from the
    published model and one of the reasons the two constructions disagree.
    """
    amort = DEV_COST / life
    cfs = []
    # Pre-launch: the development programme is spent evenly over `pre_years`
    # years, all of it before launch.
    for _ in range(pre_years):
        cfs.append(-DEV_COST / pre_years)
    for c in range(life):
        revenue = peak_sales * penetration(c, EROSION)
        ebit = revenue * margin - amort
        if post_launch_costs:
            ebit -= (m.LAUNCH_MARKETING if c == 0 else 0.0)
            if c < m.STEWARD_YEARS:
                ebit -= m.STEWARD / m.STEWARD_YEARS
        nopat = ebit * (1.0 - tax) if ebit > 0 else ebit
        fcf = nopat + amort
        if post_launch_costs and c == 0:
            fcf -= m.SCALEUP
        cfs.append(fcf)
    return cfs


def irr(cfs):
    def npv(r):
        return sum(cf / ((1.0 + r) ** i) for i, cf in enumerate(cfs))
    lo, hi = -0.9999, 10.0
    if npv(lo) * npv(hi) > 0:
        return None
    for _ in range(400):
        mid = (lo + hi) / 2.0
        if npv(lo) * npv(mid) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2.0


def hurdle(target=HURDLE, **kw):
    lo, hi = 1.0, 30000.0
    for _ in range(300):
        mid = (lo + hi) / 2.0
        r = irr(cashflows(mid, **kw)) or -1.0
        if r < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


# --------------------------------------------------------------------------
# The waterfall's own solver.
#
# One solver serves every rung, so each rung's delta is attributable to the
# assumption that changed at that rung and to nothing else. It reproduces the
# published model exactly at the published model's assumptions, and this
# construction exactly at this construction's - both asserted in main().
# --------------------------------------------------------------------------

def bridge_cashflows(peak_sales: float, *, margin: float, tax: float,
                     life: int, erosion: float,
                     even_10yr_prelaunch: bool,
                     post_launch_costs: bool,
                     nol_carryforward: bool) -> list[tuple[float, float]]:
    """Cash flows at one point in the waterfall, as (time, amount) pairs."""
    amort = DEV_COST / life
    nol = 0.0

    if even_10yr_prelaunch:
        # This construction's calendar: the whole programme spent evenly over
        # ten years, then the commercial years.
        pre = [(float(i), -DEV_COST / PRE_YEARS) for i in range(PRE_YEARS)]
        launch_t = float(PRE_YEARS)
    else:
        # The published model's calendar: the eleven-year uneven phase
        # schedule, taken from the published script so the two cannot drift.
        pre = [(t, -amt)
               for t, amt in m.pre_launch_pairs(m.scaled_phase_costs(DEV_COST))]
        launch_t = float(m.DEV_YEARS)

    comm = []
    for c in range(life):
        rev = peak_sales * penetration(c, erosion)
        depr = (m.SCALEUP / m.SCALEUP_LIFE) if (post_launch_costs
                                                and c < m.SCALEUP_LIFE) else 0.0
        mkt = m.LAUNCH_MARKETING if (post_launch_costs and c == 0) else 0.0
        stew = (m.STEWARD / m.STEWARD_YEARS) if (post_launch_costs
                                                 and c < m.STEWARD_YEARS) else 0.0
        ebit = rev * margin - amort - depr - mkt - stew

        if nol_carryforward:
            if ebit < 0:
                nol += -ebit
                taxable = 0.0
            else:
                used = min(nol, ebit)
                nol -= used
                taxable = ebit - used
        else:
            taxable = max(0.0, ebit)

        fcf = (ebit - taxable * tax) + amort + depr
        if post_launch_costs and c == 0:
            fcf -= m.SCALEUP
        comm.append((launch_t + c, fcf))
    return pre + comm


def bridge_hurdle(*, margin: float, tax: float, life: int, erosion: float,
                  even_10yr_prelaunch: bool, post_launch_costs: bool,
                  nol_carryforward: bool) -> float:
    """Peak sales needed for a 15% IRR at one point in the waterfall."""
    def cfs_at(peak_sales: float):
        return bridge_cashflows(
            peak_sales, margin=margin, tax=tax, life=life, erosion=erosion,
            even_10yr_prelaunch=even_10yr_prelaunch,
            post_launch_costs=post_launch_costs,
            nol_carryforward=nol_carryforward)

    lo, hi = 1.0, 30000.0
    for _ in range(300):
        mid = (lo + hi) / 2.0
        r = m.irr_of(cfs_at(mid))
        if r is None or r < HURDLE:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0



def _rounded(obj, ndigits=10):
    """Round floats at serialisation so JSON outputs are byte-reproducible."""
    if isinstance(obj, dict):
        return {k: _rounded(v, ndigits) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_rounded(v, ndigits) for v in obj]
    if isinstance(obj, float):
        return round(obj, ndigits)
    return obj

if __name__ == "__main__":
    h = hurdle()
    # The published model's hurdle, for the spread.
    published = m.breakeven_irr(m.HURDLE_IRR, 307.0, PUB_MARGIN, PUB_TAX,
                                PUB_LIFE, 0.135)

    cohort_mean = 48.6
    implied_peak = cohort_mean / m.PENETRATION[12]

    print("=" * 80)
    print("ALTERNATIVE CONSTRUCTION - same $307m cost, different structure")
    print("=" * 80)
    print(f"  development cost          ${DEV_COST:,.0f}m  (survey)")
    print(f"  operating contribution     {MARGIN:.0%}  (published model: 40%)")
    print(f"  commercial life           {LIFE} years  (published model: 15)")
    print(f"  post-peak erosion         {EROSION:.0%} a year  (published model: 15%)")
    print(f"  tax                       {TAX:.0%}  (published model: 21%)")
    print(f"  separate post-launch cost lines: none  (published model: $76m)")
    print(f"  pre-launch calendar       {PRE_YEARS} years, spent evenly"
          f"  (published model: 11 years, uneven)")
    print(f"  loss carry-forward        none  (published model: yes)")
    print()
    print(f"  Peak sales for a {HURDLE:.0%} IRR")
    print(f"    this construction        ${h:,.0f}m")
    print(f"    published model          ${published:,.0f}m")
    print(f"    spread                   ${published-h:,.0f}m")
    print()
    print(f"  vs the 2010 launch cohort's 2022 revenue of ${cohort_mean}m")
    print(f"    this construction        {h/cohort_mean:.1f}x")
    print(f"    published model          {published/cohort_mean:.1f}x")
    print(f"  vs the cohort's implied peak of ${implied_peak:.1f}m")
    print(f"    this construction        {h/implied_peak:.1f}x")
    print(f"    published model          {published/implied_peak:.1f}x")

    # ------------------------------------------------------- the waterfall
    print()
    print("  Sequential waterfall: published model -> alternative construction")
    print("  (one assumption group per rung; the deltas sum to the spread)")

    s0 = bridge_hurdle(margin=PUB_MARGIN, tax=PUB_TAX, life=PUB_LIFE,
                       erosion=PUB_EROSION, even_10yr_prelaunch=False,
                       post_launch_costs=True, nol_carryforward=True)
    s1 = bridge_hurdle(margin=PUB_MARGIN, tax=PUB_TAX, life=PUB_LIFE,
                       erosion=PUB_EROSION, even_10yr_prelaunch=True,
                       post_launch_costs=True, nol_carryforward=True)
    s2 = bridge_hurdle(margin=PUB_MARGIN, tax=PUB_TAX, life=PUB_LIFE,
                       erosion=PUB_EROSION, even_10yr_prelaunch=True,
                       post_launch_costs=False, nol_carryforward=True)
    s3 = bridge_hurdle(margin=PUB_MARGIN, tax=PUB_TAX, life=PUB_LIFE,
                       erosion=EROSION, even_10yr_prelaunch=True,
                       post_launch_costs=False, nol_carryforward=True)
    s4 = bridge_hurdle(margin=PUB_MARGIN, tax=PUB_TAX, life=LIFE,
                       erosion=EROSION, even_10yr_prelaunch=True,
                       post_launch_costs=False, nol_carryforward=True)
    s5 = bridge_hurdle(margin=MARGIN, tax=PUB_TAX, life=LIFE,
                       erosion=EROSION, even_10yr_prelaunch=True,
                       post_launch_costs=False, nol_carryforward=True)
    s6 = bridge_hurdle(margin=MARGIN, tax=TAX, life=LIFE,
                       erosion=EROSION, even_10yr_prelaunch=True,
                       post_launch_costs=False, nol_carryforward=True)
    s7 = bridge_hurdle(margin=MARGIN, tax=TAX, life=LIFE,
                       erosion=EROSION, even_10yr_prelaunch=True,
                       post_launch_costs=False, nol_carryforward=False)

    assert abs(s0 - published) < 1e-4, f"Step 0 mismatch: {s0} vs {published}"
    assert abs(s7 - h) < 1e-4, f"Step 7 mismatch: {s7} vs {h}"

    waterfall = {
        "step0_published_baseline": s0,
        "step1_even_10yr_prelaunch": s1,
        "step2_drop_post_launch_costs": s2,
        "step3_erosion_15_to_25pct": s3,
        "step4_commercial_life_15_to_10_yrs": s4,
        "step5_margin_40pct_to_35pct": s5,
        "step6_tax_21pct_to_25pct": s6,
        "step7_no_loss_carryforward": s7,
        "delta_prelaunch_timing": s1 - s0,
        "delta_drop_post_launch_costs": s2 - s1,
        "delta_erosion": s3 - s2,
        "delta_commercial_life": s4 - s3,
        "delta_margin": s5 - s4,
        "delta_tax": s6 - s5,
        "delta_no_loss_carryforward": s7 - s6,
        "total_spread": s7 - s0,
    }

    print(f"  0. Published baseline                        ${s0:,.1f}m")
    print(f"  1. + Even 10-yr pre-launch calendar          ${s1:,.1f}m"
          f"  ({s1 - s0:+,.1f}m)")
    print(f"  2. + No separate post-launch cost lines       ${s2:,.1f}m"
          f"  ({s2 - s1:+,.1f}m)")
    print(f"  3. + Erosion 15% -> 25% a year               ${s3:,.1f}m"
          f"  ({s3 - s2:+,.1f}m)")
    print(f"  4. + Commercial life 15 -> 10 years          ${s4:,.1f}m"
          f"  ({s4 - s3:+,.1f}m)")
    print(f"  5. + Operating contribution 40% -> 35%       ${s5:,.1f}m"
          f"  ({s5 - s4:+,.1f}m)")
    print(f"  6. + Tax 21% -> 25%                         ${s6:,.1f}m"
          f"  ({s6 - s5:+,.1f}m)")
    print(f"  7. + No loss carry-forward                 ${s7:,.1f}m"
          f"  ({s7 - s6:+,.1f}m)")
    print(f"  Total spread                                 {s7 - s0:+,.1f}m")
    print()
    print("  Each rung changes one assumption group and the deltas sum")
    print("  exactly to the spread. Step 0 reproduces the published model")
    print("  and step 7 reproduces this construction; both are asserted.")

    print()
    print("  The spread is the point. The hurdle is a scenario, not a")
    print("  measurement, and it moves with assumptions nobody can observe")
    print("  from the outside.")

    out = {
        "alternative_15pct_irr_hurdle": h,
        "published_model_15pct_irr_hurdle": published,
        "spread": published - h,
        "assumptions": {
            "dev_cost": DEV_COST, "operating_contribution": MARGIN,
            "commercial_life": LIFE, "tax": TAX,
            "post_peak_erosion": EROSION,
            "separate_post_launch_cost_lines": False,
            "pre_launch_years": PRE_YEARS,
            "pre_launch_spend_profile": "even",
            "loss_carryforward": False,
        },
        "waterfall": waterfall,
        "cohort_mean": cohort_mean,
        "cohort_implied_peak": implied_peak,
    }
    path = os.path.join(_HERE, "alternative_construction_results.json")
    with open(path, "w") as fh:
        json.dump(_rounded(out), fh, indent=2)
    print(f"\nResults written to {path}")
