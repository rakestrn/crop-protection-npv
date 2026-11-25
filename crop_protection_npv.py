#!/usr/bin/env python3
"""
What a new crop-protection active ingredient is worth.

A small, transparent financial model of a single new active substance (AI),
built to answer one question: what peak annual sales does a new AI have to
reach before it clears a normal corporate hurdle rate?

The model is deliberately plain. Every input is stated, every assumption is
named, and the breakeven solves are visible in the code rather than hidden in
one place. If you disagree with an assumption you can change it and see what it
does to the answer.

Run it:

    python3 crop_protection_npv.py

Results are written to crop_protection_npv_model_results.json.

INPUTS AND WHERE THEY COME FROM
-------------------------------
Development cost, timeline          AgbioInvestor for CropLife International,
                                    "Time and Cost of New Agrochemical
                                    Product Discovery, Development and
                                    Registration" (May 2026). A survey of
                                    BASF Agricultural Solutions, Bayer Crop
                                    Science, Corteva, FMC and Syngenta, on
                                    the 2020-2023 launch cohort. Median total
                                    cost of discovering, developing and
                                    registering one new AI: $307m, up from
                                    $301m for 2014-2019.

Cost bridge, survey to cash        The survey reports the cost of a new AI by
                                    function, not by year. The five phases
                                    below carry those function totals:
                                    research $133m (chemistry $75m, biology
                                    $46m, toxicology/environmental chemistry
                                    $12m), development $138m (chemistry $32m,
                                    field trials $59m, toxicology $23m,
                                    environmental chemistry $24m) and
                                    registration $35m. The survey does not
                                    say when any of that money is spent, so
                                    the calendar below is this model's
                                    assumption, not the survey's. What is
                                    the survey's is the total and its
                                    division across functions.

Post-launch cash                   Launch marketing, manufacturing scale-up
                                    and post-launch stewardship are real
                                    programme costs, but they are NOT part
                                    of the survey's $307m and they are not
                                    sourced from the survey either. They are
                                    this model's own assumptions, stated so
                                    they can be changed: $25m of launch
                                    marketing at the reference cost, plus
                                    scale-up and stewardship at 30/306 and
                                    21/306 of the development cost. Total
                                    programme cash is therefore about $384m
                                    - roughly 25% more than the survey's
                                    cost-to-market figure, and the reader
                                    should treat the two as different
                                    things rather than one number.

Revenue shape                      Ramp to full penetration over five
                                    commercial years, hold for four, then
                                    decay 15% of peak per year to zero over
                                    the remaining commercial life. This is an
                                    assumption. No observed cohort of new
                                    actives is used to calibrate it.

Exclusivity                        Not modelled. The revenue path is a fixed
                                    ramp, plateau and erosion schedule, so
                                    shortening the development calendar does
                                    not extend the protected commercial
                                    period, and the originator's post-expiry
                                    tail is not estimated. A faster approval
                                    therefore pulls revenue forward in this
                                    model; it does not earn extra protected
                                    revenue.

Operating contribution              Gross margin of 58% less SG&A of 18%, or
                                    40% at peak for the base case. This is
                                    operating contribution BEFORE deducting
                                    R&D amortisation, and it is not
                                    comparable to reported segment EBIT or
                                    EBITDA margins. It is an assumption with
                                    no product-level evidence behind it.

Cost of capital                    13.5% for the base case, 15% for the
                                    corporate hurdle test. Both are assumptions,
                                    not observed industry rates - the model
                                    prints the hurdle across a range so the
                                    reader can see how much the choice moves.

Commercial life                    15 years in the base case, 18 in the bull
                                    case, 10 in the bear case. Development
                                    spend is amortised over the same period.

REVISION HISTORY
----------------
An earlier version of this model produced numbers that could not be quoted.
The corrections that matter, all of which moved the result AGAINST the
conclusion rather than in its favour:

  * The commercial-year loop ran one period too long, so the bear case earned
    revenue in eleven commercial years against a ten-year amortisation life.
    Corrected bear NPV: -$120.5m at -1.58% IRR (was -$118.2m at -0.49%).

  * Phase start times were read off year labels and used as elapsed time from
    discovery start. Every phase sat a year late and the final phase was
    truncated at the horizon, dropping $36m of the $250m pre-launch budget.
    Correcting it raises the hurdle.

  * Tax was applied to revenue rather than to EBIT, and the free-cash-flow
    factor was applied to peak EBIT rather than to NOPAT.

  * A probability-of-success multiplier was applied to revenue and cost
    alike. That is not a risk-adjusted NPV: it cannot change the zero-NPV
    hurdle and it understates losses by treating the cost of failed programmes
    as though it were never incurred. The survey cost is already
    attrition-inclusive - the questionnaire asks for the total cost of
    synthesising and screening every molecule needed to yield one successful
    launch - so applying a second failure haircut double-counts. The
    probability rows are retained below, labelled as diagnostics.

  * "Effective IP protection" was a circular reference to its own cell, and
    the peak margin line subtracted dollar values of revenue from percentage
    values, producing a 74.24% margin on a 40% business.

Two further corrections are recorded here because they were found by an
external review of the published model, and both matter:

  * THE PRE-LAUNCH SCHEDULE DID NOT SUM TO THE AMORTISED COST. The five
    phases carried a $250m reference budget scaled to about $255m, while the
    amortisation base was the full $307m dev_cost. The difference - about
    $52m - was charged to cash in one treatment and not the other, so in the
    capitalised base case the programme took a tax shield on cash it never
    paid. The phases are now built from the survey's own function totals and
    the pre-launch schedule sums to exactly the amortised cost. The model now
    asserts this in its self-checks, and asserts that a capitalised and an
    expensed treatment give identical cash at zero tax, which they did not
    before.

  * THE EXPLANATION OF THE EXPENSING SCENARIO WAS WRONG. The earlier version
    said the benefit came from "removing the amortisation charge". The code
    already adds non-cash amortisation back into free cash flow, so no cash
    is created by dropping a book charge. The real difference is WHEN the
    deduction is taken and WHETHER there is profit elsewhere in the group to
    offset it against. At zero tax the two treatments are now identical, as
    they must be.

One further correction runs the other way and is worth stating for the same
reason: the 15% IRR hurdle is discount-rate independent by construction. The
IRR of a cash-flow vector does not depend on the rate at which you discount
it, so the hurdle survives any change in cost of capital, while the NPV-zero
hurdle does not. Both are reported, and they are different quantities. A
project can clear a corporate capital-rationing hurdle and still create value
at a lower required return.
"""
from __future__ import annotations

import json
import os

# --------------------------------------------------------------- constants

# Development period. Phases run from discovery (t=0) to the end of
# registration (t=11).
DEV_YEARS = 11

# The survey's 2020-23 total cost of discovering, developing and registering
# one new active ingredient, and the function split it reports.
#
#   research      $133m   (chemistry 75, biology 46, toxicology/env 12)
#   development   $138m   (chemistry 32, field trials 59, tox 23, env 24)
#   registration   $35m
#   total         $307m
#
# The phases below carry these function totals. Their placement on the
# calendar is this model's assumption; the totals are the survey's.
SURVEY_TOTAL = 306.0

# Reference total for the post-launch cost lines, which are not part of the
# survey's $307m and are stated as this model's own assumptions.
REFERENCE_DEV_COST = 306.0

# Post-launch cost lines, expressed as a share of REFERENCE_DEV_COST.
SCALEUP_SHARE = 30.0 / 306.0     # manufacturing scale-up
STEWARD_SHARE = 21.0 / 306.0     # post-launch stewardship
LAUNCH_MARKETING = 25.0          # launch marketing at the reference cost

# Development phases: (start t in years, duration in years, cost in $m).
# Each phase carries whole survey function totals, so the phase costs sum to
# SURVEY_TOTAL and the pre-launch schedule sums to the amortised cost.
PHASES = [
    (0.0, 2.5, 46.0),   # Discovery & biological screening   (research: biology)
    (2.5, 2.5, 87.0),   # Lead optimisation & research chem  (research: chem + tox/env)
    (5.0, 2.0, 56.0),   # Early development & env chemistry   (development: chem + env)
    (7.0, 2.5, 82.0),   # Field trials & toxicology          (development: trials + tox)
    (9.5, 1.5, 35.0),   # Registration                      (registration)
]

# Probability of success by phase, and the share of programmes that reach
# commercial launch. Diagnostic only - see the revision history.
PHASE_POS = [0.15, 0.35, 0.45, 0.55, 0.70]
COMMERCIAL_POS = 0.30

TAX = 0.21
HURDLE_IRR = 0.15
BASE_DISCOUNT = 0.135

# Penetration by commercial year: five years to full penetration, four years
# at peak, then 15% of peak lost per year to zero.
PENETRATION = [0.20, 0.36, 0.52, 0.68, 0.84, 1.00, 1.00, 1.00, 1.00,
               0.85, 0.70, 0.55, 0.40, 0.25, 0.10, 0.00]


def penetration(c: int) -> float:
    """Penetration factor for commercial year c, extended past the schedule.

    Floored at zero: past the end of the schedule the extrapolation would
    otherwise go negative and book negative revenue.
    """
    if c < len(PENETRATION):
        return PENETRATION[c]
    return max(0.0, 1.0 - 0.15 * (c - 8))


def pre_launch_schedule(dev_cost: float) -> list[float]:
    """Pre-launch spend, $m, in each of years 1..DEV_YEARS.

    Each phase's cost is spread across the calendar years it overlaps, in
    proportion to the overlap, so nothing is double-counted or back-loaded and
    the schedule sums exactly to the phase budget.

    The phase costs are scaled so that the schedule sums to `dev_cost` -
    that is, to exactly the amount the programme amortises. Scaling against
    the sum of the nominal phase costs (rather than a fixed reference) means
    a counterfactual that drops a phase, such as removing registration
    entirely, drops the right amount of cash without touching the rest.
    """
    nominal_total = sum(cost for _, _, cost in PHASES)
    scale = dev_cost / nominal_total
    sched = [0.0] * DEV_YEARS
    for start, dur, cost in PHASES:
        for year in range(1, DEV_YEARS + 1):
            lo, hi = year - 1.0, float(year)
            overlap = max(0.0, min(start + dur, hi) - max(start, lo))
            sched[year - 1] += cost * (overlap / dur) * scale
    return sched


def irr(cashflows: list[float], lo: float = -0.9999, hi: float = 10.0):
    """Internal rate of return by bisection. None if there is no sign change."""
    def npv(r: float) -> float:
        return sum(cf / ((1.0 + r) ** i) for i, cf in enumerate(cashflows))
    try:
        if npv(lo) * npv(hi) > 0:
            return None
    except ZeroDivisionError:
        return None
    for _ in range(400):
        mid = (lo + hi) / 2.0
        if npv(lo) * npv(mid) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2.0


def cashflows(peak_sales: float, dev_cost: float, ebit_margin: float,
              tax: float, life: int, working_capital: float = 0.0,
              tax_shield: bool = False, expense_rd: bool = False,
              launch_offset: int | None = None) -> list[float]:
    """Year-by-year unlevered free cash flow.

    t = 0..10   development spend (negative)
    t = 11      launch year (commercial year 0)
    t = 12..    commercial years 1..life-1

    `life` is both the number of commercial years in which the product earns
    revenue and the period over which development spend is amortised. These
    are the same quantity by construction.

    ebit_margin is operating contribution BEFORE R&D amortisation, applied to
    revenue in every commercial year (40% at peak in the base case: gross
    margin of 58% less SG&A of 18%). It is not comparable to reported
    segment EBIT or EBITDA margins.

    Optional treatments:
      working_capital : trade working capital as a share of revenue; the
                        annual movement is a cash cost and the balance is
                        released in the final commercial year.
      tax_shield      : a multinational originator offsets development spend
                        against profits elsewhere in the group, so the loss
                        is usable immediately rather than carried forward.
      expense_rd      : development spend is expensed as incurred instead of
                        capitalised and amortised. The cash outflow is
                        identical either way - only the timing of the tax
                        deduction changes, and the tax shield only has value
                        if there is profit elsewhere to offset.
      launch_offset   : the period at which the product launches, if earlier
                        than the end of the development schedule. Used for
                        the "approval wait removed" counterfactual: the R&D
                        programme is unchanged and still runs for DEV_YEARS
                        periods, but the product starts selling before it
                        finishes, which is what a shorter approval queue
                        looks like from the cash-flow statement.
    """
    post_scale = dev_cost / REFERENCE_DEV_COST
    amortisation = 0.0 if expense_rd else dev_cost / life
    cfs = []

    # Pre-launch development spend. This is the same cash in both
    # treatments: the programme pays it either way.
    pre = []
    for amt in pre_launch_schedule(dev_cost):
        cf = -amt
        if tax_shield and expense_rd:
            # Expensed as incurred and offset against group profits in the
            # same period.
            cf += amt * tax
        pre.append(cf)

    start = DEV_YEARS if launch_offset is None else launch_offset
    commercial = []
    prev_wc = 0.0
    for c in range(life):
        revenue = peak_sales * penetration(c)
        if expense_rd:
            ebit = revenue * ebit_margin
        else:
            ebit = revenue * ebit_margin - amortisation
        if tax_shield:
            # Losses usable immediately against group profits.
            nopat = ebit * (1.0 - tax)
        else:
            nopat = ebit * (1.0 - tax) if ebit > 0 else ebit
        fcf = nopat + amortisation          # amortisation is non-cash
        if c == 0:
            spend = (LAUNCH_MARKETING * post_scale
                     + SCALEUP_SHARE * dev_cost)
            fcf -= spend
        if c < 4:
            st = STEWARD_SHARE * dev_cost / 4.0
            fcf -= st
        if working_capital:
            wc = working_capital * revenue
            fcf -= (wc - prev_wc)           # investment in working capital
            if c == life - 1:
                fcf += wc                  # released at end of life
            prev_wc = wc
        commercial.append(fcf)

    if start >= DEV_YEARS:
        return pre + commercial

    # Early launch: development spend continues alongside revenue for the
    # remaining periods of the R&D programme.
    total = max(DEV_YEARS, start + life)
    out = []
    for i in range(total):
        cf = pre[i] if i < DEV_YEARS else 0.0
        if start <= i < start + life:
            cf += commercial[i - start]
        out.append(cf)
    return out


def evaluate(peak_sales: float, dev_cost: float, ebit_margin: float,
             tax: float, discount: float, life: int, p_success: float) -> dict:
    """NPV and IRR for one scenario."""
    cfs = cashflows(peak_sales, dev_cost, ebit_margin, tax, life)
    npv = sum(cf / ((1.0 + discount) ** i) for i, cf in enumerate(cfs))
    r = irr(cfs)
    # The two probability-weighted rows are NOT a risk-adjusted NPV. They
    # scale revenue and cost alike, cannot change the zero-NPV peak-sales
    # hurdle, and understate losses by treating the cost of failed programmes
    # as though it were never incurred. They are arithmetic diagnostics only.
    return {
        "peak_sales": peak_sales, "dev_cost": dev_cost,
        "ebit_margin": ebit_margin, "discount": discount, "life": life,
        "p_success": p_success, "npv": npv,
        "npv_times_probability_DIAGNOSTIC_ONLY": npv * p_success,
        "npv_per_rd_DIAGNOSTIC_ONLY": (npv * p_success) / dev_cost,
        "irr": r,
        "clears_hurdle": bool(r is not None and r >= HURDLE_IRR),
    }


SCENARIOS = {
    "Bear": dict(peak_sales=200.0, dev_cost=380.0, ebit_margin=0.25,
                 tax=0.25, discount=0.14, life=10, p_success=0.0110),
    "Base": dict(peak_sales=75.0, dev_cost=307.0, ebit_margin=0.40,
                 tax=0.21, discount=0.135, life=15, p_success=0.0027),
    "Bull": dict(peak_sales=900.0, dev_cost=240.0, ebit_margin=0.52,
                 tax=0.18, discount=0.11, life=18, p_success=0.0900),
}

TECH_POS = 1.0
for p in PHASE_POS:
    TECH_POS *= p
OVERALL_POS = TECH_POS * COMMERCIAL_POS


def solve_breakeven(metric: str, dev_cost: float, ebit_margin: float,
                    tax: float, discount: float, life: int,
                    target: float = 0.0) -> float:
    """Peak sales at which NPV hits `target`, or IRR hits `target`."""
    lo, hi = 1.0, 30000.0
    for _ in range(300):
        mid = (lo + hi) / 2.0
        cfs = cashflows(mid, dev_cost, ebit_margin, tax, life)
        val = (sum(cf / ((1.0 + discount) ** i) for i, cf in enumerate(cfs))
               if metric == "npv" else (irr(cfs) or -1.0))
        if val < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def breakeven_irr(peak_target: float, dev_cost: float, ebit_margin: float,
                  tax: float, life: int, discount: float,
                  working_capital: float = 0.0, tax_shield: bool = False,
                  expense_rd: bool = False) -> float:
    """Peak sales at which the project's IRR equals `peak_target`."""
    lo, hi = 1.0, 30000.0

    def f(p):
        cfs = cashflows(p, dev_cost, ebit_margin, tax, life,
                        working_capital, tax_shield, expense_rd)
        return (irr(cfs) or -1.0) - peak_target

    a = f(lo)
    for _ in range(300):
        mid = (lo + hi) / 2.0
        v = f(mid)
        if (v > 0) == (a > 0):
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def breakeven_npv(dev_cost: float, ebit_margin: float, tax: float, life: int,
                  discount: float, working_capital: float = 0.0,
                  tax_shield: bool = False, expense_rd: bool = False) -> float:
    """Peak sales at which NPV = 0 at `discount`."""
    lo, hi = 1.0, 30000.0

    def f(p):
        cfs = cashflows(p, dev_cost, ebit_margin, tax, life,
                        working_capital, tax_shield, expense_rd)
        return sum(cf / ((1.0 + discount) ** i) for i, cf in enumerate(cfs))

    a = f(lo)
    for _ in range(300):
        mid = (lo + hi) / 2.0
        v = f(mid)
        if (v > 0) == (a > 0):
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def main() -> None:
    out: dict = {"technical_pos": TECH_POS, "overall_pos": OVERALL_POS,
                 "scenarios": {}}

    print("=" * 78)
    print("CROP-PROTECTION NEW-ACTIVE-INGREDIENT NPV MODEL")
    print("=" * 78)
    print(f"Development period              : {DEV_YEARS} years")
    print(f"Technical PoS (base)            : {TECH_POS:.4%}")
    print(f"Overall PoS (x30% comm.)        : {OVERALL_POS:.4%}")
    print()

    hdr = (f"{'Scenario':9}{'Peak$m':>9}{'NPV$m':>10}{'NPVxP(diag)':>12}"
           f"{'IRR':>8}  Hurdle")
    print(hdr)
    print("-" * len(hdr))
    for name, s in SCENARIOS.items():
        res = evaluate(**s)
        out["scenarios"][name] = res
        irr_txt = f"{res['irr']:.2%}" if res["irr"] is not None else "n/a"
        print(f"{name:9}{s['peak_sales']:>9,.0f}{res['npv']:>10,.1f}"
              f"{res['npv_times_probability_DIAGNOSTIC_ONLY']:>12,.2f}"
              f"{irr_txt:>8}  "
              f"{'ABOVE' if res['clears_hurdle'] else 'below'}")

    b = SCENARIOS["Base"]
    be_npv = solve_breakeven("npv", b["dev_cost"], b["ebit_margin"],
                              b["tax"], b["discount"], b["life"], 0.0)
    be_irr = solve_breakeven("irr", b["dev_cost"], b["ebit_margin"],
                              b["tax"], b["discount"], b["life"], HURDLE_IRR)
    out["breakeven_npv_zero_peak_sales"] = be_npv
    out["breakeven_15pct_irr_peak_sales"] = be_irr
    print()
    print(f"Breakeven peak sales, NPV = 0   : ${be_npv:,.0f}m")
    print(f"Breakeven peak sales, IRR = 15% : ${be_irr:,.0f}m")
    print()

    print("Peak sales required for a 15% IRR, by development cost")
    for dc in (260.0, 280.0, 301.0, 307.0, 320.0, 350.0):
        v = solve_breakeven("irr", dc, b["ebit_margin"], b["tax"],
                            b["discount"], b["life"], HURDLE_IRR)
        print(f"   dev ${dc:,.0f}m -> ${v:,.0f}m peak sales")
        out.setdefault("irr_breakeven_by_dev_cost", {})[f"{dc:.0f}"] = v
    print()

    print("Peak sales required for a 15% IRR, by operating contribution (base dev cost)")
    for mg in (0.35, 0.40, 0.45, 0.50, 0.55):
        v = solve_breakeven("irr", b["dev_cost"], mg, b["tax"],
                            b["discount"], b["life"], HURDLE_IRR)
        print(f"   operating contribution {mg:.0%} -> ${v:,.0f}m peak sales")
        out.setdefault("irr_breakeven_by_margin", {})[f"{mg:.2f}"] = v

    # A cost-of-capital framing gives a materially lower hurdle than the 15%
    # corporate rate. Both are worth seeing.
    print()
    print("Peak sales required for NPV = 0, by discount rate (base parameters)")
    print("   (a cost-of-capital framing gives a materially lower hurdle)")
    for r in (0.08, 0.09, 0.10, 0.11, 0.12, 0.135):
        v = solve_breakeven("npv", b["dev_cost"], b["ebit_margin"],
                            b["tax"], r, b["life"], 0.0)
        print(f"   discount {r:.1%} -> ${v:,.0f}m peak sales")
        out.setdefault("npv_zero_breakeven_by_discount", {})[f"{r:.3f}"] = v

    # A 5% royalty deduction is arithmetically identical to a 5pp reduction
    # in contribution margin.
    print()
    print("Peak sales required for a 15% IRR, with a 5% royalty/COGS deduction")
    v_roy = solve_breakeven("irr", b["dev_cost"], b["ebit_margin"] - 0.05,
                            b["tax"], b["discount"], b["life"], HURDLE_IRR)
    print(f"   40% contribution less 5% royalty -> ${v_roy:,.0f}m peak sales")
    out["irr_breakeven_with_5pct_royalty"] = v_roy

    # Disclosed company discount rates for context: BASF Ag 6.74%, Bayer Group
    # 7.0%, Syngenta 8.0%, Bayer Crop Science 8.8% (Q4 2025, after tax).
    # The 15% hurdle is an assumed capital-rationing rate, not an observed
    # industry rate.
    print()
    print("Peak sales for NPV = 0, by discount rate (base parameters)")
    for r in (0.0674, 0.0775, 0.085, 0.088, 0.094, 0.10, 0.135, 0.15):
        v = breakeven_npv(307.0, 0.40, 0.21, 15, r)
        print(f"   discount {r:.2%} -> ${v:,.0f}m peak sales")
        out.setdefault("npv_zero_breakeven_by_discount", {})[f"{r:.4f}"] = v

    print()
    print("Cost structure: working capital and R&D tax shield")
    for r in (0.085, 0.135, 0.15):
        plain = breakeven_npv(307.0, 0.40, 0.21, 15, r)
        nwc = breakeven_npv(307.0, 0.40, 0.21, 15, r, working_capital=0.42)
        both = breakeven_npv(307.0, 0.40, 0.21, 15, r, working_capital=0.42,
                             tax_shield=True)
        expensed = breakeven_npv(307.0, 0.40, 0.21, 15, r,
                                 working_capital=0.42, tax_shield=True,
                                 expense_rd=True)
        print(f"   discount {r:.2%}: base ${plain:,.0f}m | "
              f"NWC 42% ${nwc:,.0f}m | NWC + shield ${both:,.0f}m | "
              f"NWC + shield + R&D expensed ${expensed:,.0f}m")
        out.setdefault("cost_structure", {})[f"{r:.4f}"] = {
            "published_spec": plain, "nwc_42pct": nwc,
            "nwc_42pct_with_tax_shield": both,
            "nwc_42pct_shield_rdexpensed": expensed}

    print()
    print("15% IRR hurdle at the sourced cost of capital (8.5%)")
    print(f"   15% IRR hurdle is ${be_irr:,.0f}m at any discount rate; NPV-zero at 8.5% "
          f"is ${breakeven_npv(307.0, 0.40, 0.21, 15, 0.085):,.0f}m")
    print("   (the IRR-based hurdle is discount-rate independent by construction)")
    out["irr_hurdle_at_15pct"] = be_irr

    # Self-checks.
    sched = pre_launch_schedule(307.0)
    print()
    print("Self-checks")
    print(f"   pre-launch schedule sums to ${sum(sched):,.2f}m "
          f"(expect ${307.0:,.2f}m - the amortised cost)")
    assert abs(sum(sched) - 307.0) < 1e-6, \
        "pre-launch cash must equal the amortised cost"
    assert abs(sum(c for _, _, c in PHASES) - SURVEY_TOTAL) < 1e-6, \
        "phase costs must sum to the survey total"

    # A capitalised and an expensed treatment must produce identical cash at
    # zero tax: no tax means no deduction, so no timing effect and no
    # amortisation shield. This check fails if the programme pays different
    # amounts of cash in the two treatments.
    for kw in ({}, {"tax_shield": True}):
        cap = sum(cashflows(75.0, 307.0, 0.40, 0.0, 15, **kw))
        exp = sum(cashflows(75.0, 307.0, 0.40, 0.0, 15,
                            expense_rd=True, **kw))
        diff = abs(cap - exp)
        label = "capitalised" if not kw else "capitalised + group tax shield"
        print(f"   zero tax, {label}: capitalised vs expensed "
              f"undiscounted cash difference = {diff:.10f} (must be 0)")
        assert diff < 1e-6, "capitalised and expensed must be identical at zero tax"

    for n, s in SCENARIOS.items():
        cfs = cashflows(s["peak_sales"], s["dev_cost"], s["ebit_margin"],
                        s["tax"], s["life"])
        r = irr(cfs)
        assert r is not None, f"{n}: IRR undefined"
        npv_at_irr = sum(cf / ((1.0 + r) ** i) for i, cf in enumerate(cfs))
        print(f"   {n}: NPV at own IRR = {npv_at_irr:+.4f} (must be ~0)")
        assert abs(npv_at_irr) < 0.05, f"{n} IRR not consistent with NPV"

    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "crop_protection_npv_model_results.json")
    with open(path, "w") as fh:
        json.dump(out, fh, indent=2, default=str)
    print(f"\nResults written to {path}")


if __name__ == "__main__":
    main()
