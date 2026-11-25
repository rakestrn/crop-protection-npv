#!/usr/bin/env python3
"""
An alternative construction of the same model, from the same cost base.

Why this exists
---------------
The published model (crop_protection_npv.py) produces a peak-sales hurdle of
about $606m for a 15% IRR at the survey's $307m development cost. That number
depends on the structure of the model, not only on the cost base and the
revenue path. A reader is entitled to know whether the result is an artefact
of the particular structure chosen.

This is that test. It is a genuinely different construction, not a parameter
change to the same one, and it is written out in full so it can be checked:

  published model                five pre-launch phases carrying the survey's
                                 function totals, $307m of pre-launch cash,
                                 post-launch launch marketing, manufacturing
                                 scale-up and stewardship charged in the
                                 commercial years, development spend
                                 amortised over the commercial life, 40%
                                 operating contribution, 15-year life.

  this construction                the whole $307m treated as capitalised
                                 development spend with NO separate
                                 post-launch cost lines, amortised over a
                                 10-year commercial life rather than 15,
                                 35% operating contribution rather than 40%,
                                 and a steeper post-peak decline - revenue
                                 erodes at 25% of peak a year rather than
                                 15%, which is closer to what happens to a
                                 product once generics arrive.

The differences are all defensible choices a reader might reasonably make.
None of them is "the right answer". The point is the spread.

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
"""
import importlib.util
import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "crop_protection_npv", os.path.join(_HERE, "crop_protection_npv.py"))
m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m)

# --------------------------------------------------------------- this model's assumptions

DEV_COST = 307.0          # the survey's cost, unchanged
TAX = 0.25                # higher: an originator with a less favourable mix
MARGIN = 0.35             # operating contribution before R&D amortisation
LIFE = 10                 # commercial years, and the amortisation period
HURDLE = 0.15             # the corporate hurdle
EROSION = 0.25            # post-peak decline, per year, as a fraction of peak

# Peak sales are found by bisection on the IRR, so the revenue path can be
# scaled without disturbing the model's own (unobserved) ramp shape.
PENETRATION = [0.20, 0.36, 0.52, 0.68, 0.84, 1.00, 1.00, 1.00, 1.00, 0.75]


def penetration(c: int) -> float:
    if c < len(PENETRATION):
        return PENETRATION[c]
    return max(0.0, 1.0 - EROSION * (c - 8))


def cashflows(peak_sales: float) -> list[float]:
    """Pre-launch development spend, then commercial cash flow.

    The whole development cost is treated as capitalised spend amortised over
    the commercial life. There are no separate post-launch cost lines: launch
    marketing, manufacturing scale-up and stewardship are not charged, which
    is itself a difference from the published model and one of the reasons
    the two constructions disagree.
    """
    amort = DEV_COST / LIFE
    cfs = []
    # Pre-launch: the development programme is spent over ten years, all of
    # it before launch.
    for yr in range(10):
        cfs.append(-DEV_COST / 10.0)
    for c in range(LIFE):
        revenue = peak_sales * penetration(c)
        ebit = revenue * MARGIN - amort
        nopat = ebit * (1.0 - TAX) if ebit > 0 else ebit
        cfs.append(nopat + amort)
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


def hurdle(target=HURDLE):
    lo, hi = 1.0, 30000.0
    for _ in range(300):
        mid = (lo + hi) / 2.0
        r = irr(cashflows(mid)) or -1.0
        if r < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


if __name__ == "__main__":
    h = hurdle()
    # The published model's hurdle, for the spread.
    published = m.solve_breakeven("irr", 307.0, 0.40, 0.21, 0.135, 15,
                                  m.HURDLE_IRR)

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
        },
        "cohort_mean": cohort_mean,
        "cohort_implied_peak": implied_peak,
    }
    path = os.path.join(_HERE, "alternative_construction_results.json")
    with open(path, "w") as fh:
        json.dump(out, fh, indent=2)
    print(f"\nResults written to {path}")
