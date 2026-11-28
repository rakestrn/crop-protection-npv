#!/usr/bin/env python3
"""
An alternative construction of the same model, from the same cost base.

Why this exists
---------------
The published model (crop_protection_npv.py) produces a peak-sales hurdle of
about $596m for a 15% IRR at the survey's $307m development cost. That number
depends on the structure of the model, not only on the cost base and the
revenue path. A reader is entitled to know whether the result is an artefact
of the particular structure chosen.

This is that test. It is a genuinely different construction, not a parameter
change to the same one, and it is written out in full so it can be checked.

WHAT IS AND IS NOT DIFFERENT
-----------------------------
An earlier version of this script changed several things at once, and one of
them was not disclosed: it spent the $307m evenly over TEN pre-launch years
and launched at t=10, while the published model spends it over an uneven
ELEVEN-year schedule and launches at t=11. That undisclosed timing change
alone moves the answer materially, because spending the same money earlier
raises its present value.

This version therefore does two things the earlier one did not:

  1. It STATES the timing difference explicitly, and prints what it is worth.

  2. It separates the changes into two groups and reports each on its own,
     so a reader can see which assumption is doing the work:
       - structural:  no separate post-launch cost lines, 10-year life,
         25% erosion
       - financial:    35% operating contribution, 25% tax

The assumptions, all of which a reader might reasonably make and none of
which is "the right answer":

  published model          five pre-launch phases carrying the survey's
                           function totals on an 11-year calendar, $307m of
                           pre-launch cash, post-launch launch marketing,
                           manufacturing scale-up and stewardship charged in
                           the commercial years, development spend amortised
                           over the commercial life, 40% operating
                           contribution, 21% tax, 15-year life.

  this construction        the whole $307m treated as capitalised development
                           spend with NO separate post-launch cost lines,
                           amortised over a 10-year commercial life rather
                           than 15, 35% operating contribution rather than
                           40%, 25% tax rather than 21%, and a steeper
                           post-peak decline - revenue erodes at 25% of peak
                           a year rather than 15%, which is closer to what
                           happens to a product once generics arrive.

Run it:

    python3 alternative_construction.py

Results are written to alternative_construction_results.json.

WHAT THIS DOES NOT SHOW
-----------------------
A wide spread between two constructions is a statement about how much the
answer depends on assumptions that are not observable. It is not evidence
that either construction is the industry. A third construction would move the
answer again, and a set of matched product-level observations would be worth
more than any number of constructions.

Because several assumptions change at once, the spread between the two
constructions cannot by itself show which assumption matters most. That is why
the decomposition above is reported separately.
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
# difference is disclosed and priced below.
PRE_YEARS = 10

# Peak sales are found by bisection on the IRR, so the revenue path can be
# scaled without disturbing the model's own (unobserved) ramp shape.
PENETRATION = [0.20, 0.36, 0.52, 0.68, 0.84, 1.00, 1.00, 1.00, 1.00, 0.75]


def penetration(c: int) -> float:
    if c < len(PENETRATION):
        return PENETRATION[c]
    return max(0.0, 1.0 - EROSION * (c - 8))


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
        revenue = peak_sales * penetration(c)
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


if __name__ == "__main__":
    h = hurdle()
    # The published model's hurdle, for the spread.
    published = m.breakeven_irr(m.HURDLE_IRR, 307.0, 0.40, 0.21, 15, 0.135)

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

    # Isolate the undisclosed timing change from the rest.
    print()
    print("  Decomposition: what each group of changes is worth")
    print("  (all against this construction, holding the others fixed)")
    timing_only = hurdle(margin=0.40, tax=0.21, life=15,
                         pre_years=m.DEV_YEARS, post_launch_costs=True)
    print(f"    this construction, but with the published model's 11-year")
    print(f"    calendar and post-launch cost lines:   ${timing_only:,.0f}m")
    print(f"    -> the timing and cost-line changes alone are worth "
          f"${h - timing_only:,.0f}m of the spread")
    structural_only = hurdle(margin=0.40, tax=0.25, life=LIFE,
                             pre_years=PRE_YEARS, post_launch_costs=False)
    print(f"    this construction with only the financial changes "
          f"(35% margin, 25% tax): ${structural_only:,.0f}m")
    print(f"    -> the margin and tax changes alone are worth "
          f"${h - structural_only:,.0f}m of the spread")
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
        },
        "decomposition": {
            "timing_and_post_launch_costs_only": timing_only,
            "margin_and_tax_only": structural_only,
            "timing_and_cost_line_effect": h - timing_only,
            "margin_and_tax_effect": h - structural_only,
        },
        "cohort_mean": cohort_mean,
        "cohort_implied_peak": implied_peak,
    }
    path = os.path.join(_HERE, "alternative_construction_results.json")
    with open(path, "w") as fh:
        json.dump(out, fh, indent=2)
    print(f"\nResults written to {path}")
