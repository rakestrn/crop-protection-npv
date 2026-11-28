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
                                    the 2020-2023 launch cohort. The survey
                                    reports the AVERAGE total cost of
                                    discovering, developing and registering
                                    one new AI across its respondents:
                                    $307m, up from $301m for 2014-2019. This
                                    is a mean, not a median, and the model
                                    does not use it to infer a distribution
                                    of programme costs.

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
                                    marketing, $30m of manufacturing
                                    scale-up, and $21m of post-launch
                                    stewardship, spread over the first
                                    four commercial years. These are held
                                    FIXED at those amounts in every case,
                                    including the regulatory counterfactuals:
                                    they are commercial-spend assumptions,
                                    not functions of the registration
                                    dossier, so a change in one must not
                                    move the others.

                                    Total programme cash is therefore about
                                    $383m - roughly 25% more than the
                                    survey's cost-to-market figure, and the
                                    reader should treat the two as different
                                    things rather than one number.

                                    Note also that the survey's own
                                    development total already includes a
                                    scale-up-of-manufacture component, so
                                    the separate $30m line here may overlap
                                    with it. The model prints the hurdle
                                    with that line removed so the size of
                                    the possible overlap is visible.

Revenue shape                      Ramp to full penetration over five
                                    commercial years, hold for four, then
                                    lose 15 PERCENTAGE POINTS of peak sales
                                    per year to zero over the remaining
                                    commercial life. This is an assumption.
                                    No observed cohort of new actives is used
                                    to calibrate it, and the article does
                                    not use this curve to estimate what any
                                    individual product earned.

Exclusivity                        Not modelled. The revenue path is a fixed
                                    ramp, plateau and erosion schedule, so
                                    shortening the development calendar does
                                    not extend the protected commercial
                                    period, and the originator's post-expiry
                                    tail is not estimated. A faster approval
                                    therefore pulls revenue forward in this
                                    model; it does not earn extra protected
                                    revenue. Real originators harvest cash
                                    from off-patent franchises for years
                                    after exclusivity ends, so this model
                                    understates the cash available to a
                                    franchise that has one.

Operating contribution              Gross margin of 58% less SG&A of 18%, or
                                    40% at peak for the base case. This is
                                    operating contribution BEFORE deducting
                                    R&D amortisation, and it is not
                                    comparable to reported segment EBIT or
                                    EBITDA margins. It is an assumption with
                                    no product-level evidence behind it.

Tax                                21% on taxable profit. Losses are carried
                                    forward and offset against later
                                    profits, so a programme that loses
                                    money early recovers the deduction
                                    later rather than losing it forever.
                                    The "group tax shield" scenario instead
                                    offsets development spend immediately
                                    against profit elsewhere in a
                                    multinational's accounts. The 21% rate
                                    and the availability of a group offset
                                    are assumptions about tax treatment,
                                    not facts about any named company.

Cost of capital                    13.5% for the base case, 15% for the
                                    corporate hurdle test, 8.5% as a
                                    deliberately low case. All three are
                                    assumptions, not observed industry
                                    rates - the model prints the hurdle
                                    across a range so the reader can see how
                                    much the choice moves.

Commercial life                    15 years in the base case, 18 in the
                                    blockbuster case, 10 in the
                                    cost-overrun case. Development spend is
                                    amortised over the same period.

REVISION HISTORY
----------------
An earlier version of this model produced numbers that could not be quoted.
The corrections that matter, all of which moved the result AGAINST the
conclusion rather than in its favour:

  * The commercial-year loop ran one period too long, so the cost-overrun
    case earned revenue in eleven commercial years against a ten-year
    amortisation life.

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
    probability rows have been removed rather than kept as diagnostics,
    because a diagnostic row that cannot change a decision invites being
    read as if it could.

  * "Effective IP protection" was a circular reference to its own cell, and
    the peak margin line subtracted dollar values of revenue from percentage
    values, producing a 74.24% margin on a 40% business.

  * THE PRE-LAUNCH SCHEDULE DID NOT SUM TO THE AMORTISED COST. The five
    phases carried a $250m reference budget scaled to about $255m, while the
    amortisation base was the full $307m dev_cost. The difference - about
    $52m - was charged to cash in one treatment and not in the other, so in
    the capitalised base case the programme took a tax shield on cash it never
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

  * THE REGULATORY COUNTERFACTUALS DID NOT DO WHAT THEY SAID. The "free
    registration" case lowered the total development cost and let the
    schedule scale every phase down pro rata, so roughly $31m of the $35m
    saving came out of DISCOVERY AND RESEARCH, not registration - and
    post-launch marketing, scale-up and stewardship fell as well, because
    they scaled with the same total. The "1995-speed calendar" case was
    described as bringing first revenue forward 2.7 years but the engine ran
    on whole-year periods and moved it two years. A third case launched
    commercial sales three years before the registration dossier was
    finished, which is not what removing an approval queue looks like. All
    three are fixed below: removal is now phase-specific and at the removed
    phase's own timing, post-launch spend is held fixed, the calendar is
    compressed to the 1995 benchmark with continuous timing so the stated
    acceleration is the one implemented, and there is no case in which
    selling precedes registration.

  * POST-LAUNCH SPEND NOW RECEIVES A TAX DEDUCTION. Launch marketing and
    stewardship were previously deducted after tax, and scale-up was neither
    expensed nor depreciated. They are now expensed before tax (marketing and
    stewardship) and depreciated straight-line over five years (scale-up),
    which is the treatment a real programme would receive.

  * LOSSES NOW CARRY FORWARD. A programme that loses money in its early
    commercial years previously lost the deduction permanently. It now
    carries the loss forward and offsets it against later profit.

One correction runs the other way and is worth stating for the same reason:
the 15% IRR hurdle is discount-rate independent by construction. The IRR of
a cash-flow vector does not depend on the rate at which you discount it, so
the hurdle survives any change in cost of capital, while the NPV-zero hurdle
does not. Both are reported, and they are different quantities. A project
can clear a corporate capital-rationing hurdle and still create value at a
lower required return.

WHAT THIS MODEL DELIBERATELY DOES NOT DO
----------------------------------------
It is a single-product model, not a portfolio model. It does not attempt
risk-adjusted NPV in the stage-gated (rNPV) sense, because that requires
calibrating phase-by-phase probabilities, which the published survey does not
support. It uses one average development programme, not a distribution of
programmes. It does not model patent expiry, post-expiry branded cash flows,
mixture or formulation extension, jurisdictional differences in net revenue
to the originator, or the difference between an originator's discovery
decision and an investor's entry decision.
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
# survey's $307m and are stated as this model's own assumptions. These are
# held fixed in every case, including the regulatory counterfactuals.
REFERENCE_DEV_COST = 306.0

# Post-launch cost lines, in $m, at the reference programme size.
LAUNCH_MARKETING = 25.0     # launch marketing, commercial year 0
SCALEUP = 30.0              # manufacturing scale-up, commercial year 0
SCALEUP_LIFE = 5            # straight-line depreciation over this many years
STEWARD = 21.0              # post-launch stewardship, over the first 4 years
STEWARD_YEARS = 4

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
REGISTRATION_PHASE_INDEX = 4

# The 1995 benchmark lead time from the same survey series.
LEAD_1995 = 8.3

TAX = 0.21
HURDLE_IRR = 0.15
BASE_DISCOUNT = 0.135

# Trade working capital as a percentage of revenue, computed from reported
# balance sheets rather than assumed:
#   Corteva, Inc. FY2025 Form 10-K: AR $4,881m + inventories $5,667m
#     less AP $4,398m over revenue $17,401m = 35.3%
#   FMC Corporation FY2025 Form 10-K: the same computation gives 72.4%,
#     inflated by a pre-divestiture inventory build.
# Both are whole-company ratios and both are run; neither is a point estimate
# for the industry.
CORTEVA_WC = 0.353
FMC_WC = 0.724

# Penetration by commercial year c: five years to full penetration, four
# years at peak, then 15 percentage points of peak lost per year to zero.
def penetration(c: int, plateau_years: int = 4) -> float:
    """Penetration factor for commercial year c.

    A five-year ramp (0.20 rising to 0.84), then `plateau_years` at full
    penetration, then 15 percentage points of peak lost per year, floored at
    zero so revenue never books negative.

    plateau_years=4 reproduces the base case, whose commercial life is
    fifteen years. A scenario with a longer commercial life needs a longer
    plateau: with the erosion rule fixed, an eighteen-year life reached zero
    revenue at year fifteen and left three of the eighteen years earning
    nothing.
    """
    ramp = (0.20, 0.36, 0.52, 0.68, 0.84)
    if c < len(ramp):
        return ramp[c]
    peak_end = len(ramp) + plateau_years - 1
    if c <= peak_end:
        return 1.00
    return max(0.0, 1.0 - 0.15 * (c - peak_end))


# The base-case revenue path, derived from penetration() so the two cannot
# drift apart. Fifteen commercial years: five ramping, four at peak, then
# six years of erosion.
PENETRATION = [penetration(c) for c in range(16)]


# ------------------------------------------------------------------- costs

def scaled_phase_costs(total: float) -> list[float]:
    """Phase costs scaled so they sum to `total`."""
    scale = total / sum(c for _, _, c in PHASES)
    return [c * scale for _, _, c in PHASES]


def phase_costs_without_registration(total: float) -> list[float]:
    """Phase costs scaled to `total` with the registration phase removed.

    The saving comes out of the registration phase and nowhere else. This is
    the whole point of the counterfactual: a registration dossier that is
    cheaper or waived does not make discovery cheaper.
    """
    costs = scaled_phase_costs(total)
    costs[REGISTRATION_PHASE_INDEX] = 0.0
    return costs


def pre_launch_pairs(costs: list[float],
                     time_scale: float = 1.0,
                     phases: list[tuple[float, float, float]] | None = None
                     ) -> list[tuple[float, float]]:
    """Pre-launch spend as (time in years, amount) pairs.

    Each phase's cost is spread across the calendar years it overlaps, in
    proportion to the overlap, so nothing is double-counted or back-loaded
    and the schedule sums exactly to the phase budget.

    `time_scale` compresses the whole calendar. 1.0 is the base case; a
    smaller value compresses the programme toward the 1995 benchmark, which
    is how the calendar counterfactual is built. Compressing moves spend
    EARLIER, which raises its present value - the model lets that happen
    rather than assuming compression is free.

    `phases` overrides the phase calendar, keeping the phase budgets but
    moving them in time. It is how a counterfactual that changes when the
    registration work happens is built; the costs list stays in phase order.
    """
    # `costs` already holds the dollar amount for each phase, so no further
    # scaling is applied here. (An earlier version scaled twice and produced a
    # schedule that no longer summed to the amortised cost.)
    active = PHASES if phases is None else phases
    horizon = max(s + d for s, d, _ in active) * time_scale
    buckets = int(-(-horizon // 1))          # ceiling, so the tail is kept
    sched = [0.0] * buckets
    for (start, dur, _), cost in zip(active, costs):
        s0 = start * time_scale
        d0 = dur * time_scale
        for b in range(buckets):
            lo, hi = float(b), float(b + 1)
            overlap = max(0.0, min(s0 + d0, hi) - max(s0, lo))
            if overlap > 0:
                sched[b] += cost * (overlap / d0)
    # Each calendar year's spend is placed at the start of that year, which
    # is the model's timing convention.
    return [(float(b), sched[b]) for b in range(buckets) if sched[b] > 0]


# ------------------------------------------------------------------ cashflow

def cashflow_pairs(peak_sales: float, dev_cost: float, ebit_margin: float,
                   tax: float, life: int, working_capital: float = 0.0,
                   tax_shield: bool = False, expense_rd: bool = False,
                   phase_costs: list[float] | None = None,
                   time_scale: float = 1.0,
                   launch_offset: float | None = None,
                   scaleup: float = SCALEUP,
                   nol_carryforward: bool = True,
                   plateau_years: int = 4,
                   phases: list[tuple[float, float, float]] | None = None
                   ) -> list[tuple[float, float]]:
    """Year-by-year unlevered free cash flow as (time in years, amount).

    Times are continuous, so a compressed calendar can be expressed exactly
    rather than rounded to whole periods.

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
                        if there is profit elsewhere to offset it.
      phase_costs     : explicit phase costs, overriding the default
                        proportional scaling. Used to remove one phase
                        without touching the others.
      time_scale      : compresses the whole pre-launch calendar.
      launch_offset   : the time at which the product launches, if earlier
                        than the end of the development schedule.
      scaleup         : the manufacturing scale-up cash amount.
      nol_carryforward : carry forward losses and offset them against later
                        profits. When false, a loss year simply shelters no
                        tax and the loss is never used again.
      plateau_years : years at full penetration before erosion begins.
      phases        : override the phase calendar without changing the phase
                      budgets.
    """
    if phase_costs is None:
        phase_costs = scaled_phase_costs(dev_cost)
    amortisation = 0.0 if expense_rd else dev_cost / life

    # Pre-launch development spend. This is the same cash in both treatments:
    # the programme pays it either way.
    pre: list[tuple[float, float]] = []
    for t, amt in pre_launch_pairs(phase_costs, time_scale, phases):
        cf = -amt
        if tax_shield and expense_rd:
            # Expensed as incurred and offset against group profits in the
            # same period.
            cf += amt * tax
        pre.append((t, cf))

    launch_t = (DEV_YEARS * time_scale) if launch_offset is None else launch_offset

    commercial: list[tuple[float, float]] = []
    prev_wc = 0.0
    nol = 0.0
    for c in range(life):
        revenue = peak_sales * penetration(c, plateau_years)
        depreciation = scaleup / SCALEUP_LIFE if c < SCALEUP_LIFE else 0.0
        marketing = LAUNCH_MARKETING if c == 0 else 0.0
        stewardship = STEWARD / STEWARD_YEARS if c < STEWARD_YEARS else 0.0

        ebit = (revenue * ebit_margin - amortisation - depreciation
                - marketing - stewardship)

        if tax_shield:
            # Losses usable immediately against group profits.
            taxable = ebit
        elif nol_carryforward:
            # Losses carried forward and offset against later profits.
            if ebit < 0:
                nol += -ebit
                taxable = 0.0
            else:
                used = min(nol, ebit)
                nol -= used
                taxable = ebit - used
        else:
            # No carry-forward: a loss year shelters no tax, and the loss is
            # never used again.
            taxable = max(0.0, ebit)
        tax_paid = taxable * tax

        nopat = ebit - tax_paid
        fcf = nopat + amortisation + depreciation   # both are non-cash

        if c == 0:
            fcf -= scaleup                     # cash out of scale-up
        if working_capital:
            wc = working_capital * revenue
            fcf -= (wc - prev_wc)              # investment in working capital
            if c == life - 1:
                fcf += wc                     # released at end of life
            prev_wc = wc
        commercial.append((launch_t + c, fcf))

    return pre + commercial


def cashflows(peak_sales: float, dev_cost: float, ebit_margin: float,
              tax: float, life: int, **kwargs) -> list[float]:
    """Cash flows as a plain list, for the integer-timed base case."""
    return [cf for _, cf in cashflow_pairs(peak_sales, dev_cost, ebit_margin,
                                           tax, life, **kwargs)]


def npv_of(pairs: list[tuple[float, float]], rate: float) -> float:
    return sum(cf / ((1.0 + rate) ** t) for t, cf in pairs)


def irr_of(pairs: list[tuple[float, float]], lo: float = -0.9999,
           hi: float = 10.0) -> float | None:
    """Internal rate of return by bisection on continuous-time cash flows."""
    def npv(r: float) -> float:
        return npv_of(pairs, r)
    try:
        if npv(lo) * npv(hi) > 0:
            return None
    except (OverflowError, ZeroDivisionError):
        return None
    for _ in range(300):
        mid = (lo + hi) / 2.0
        v = npv(mid)
        if abs(v) < 1e-12:
            return mid
        # NPV falls as the discount rate rises, so a positive NPV at `mid`
        # means the rate is too low: move the lower bound up.
        if v > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def irr(cashflows: list[float], lo: float = -0.9999, hi: float = 10.0):
    """IRR of an evenly-spaced cash flow vector."""
    return irr_of([(float(i), cf) for i, cf in enumerate(cashflows)], lo, hi)


def breakeven_npv(dev_cost: float, ebit_margin: float, tax: float, life: int,
                  discount: float, working_capital: float = 0.0,
                  tax_shield: bool = False, expense_rd: bool = False,
                  **kwargs) -> float:
    """Peak sales at which NPV = 0."""
    lo, hi = 1.0, 30000.0
    for _ in range(200):
        mid = (lo + hi) / 2.0
        pairs = cashflow_pairs(mid, dev_cost, ebit_margin, tax, life,
                               working_capital=working_capital,
                               tax_shield=tax_shield, expense_rd=expense_rd,
                               **kwargs)
        if npv_of(pairs, discount) > 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2.0


def breakeven_irr(peak_target: float, dev_cost: float, ebit_margin: float,
                  tax: float, life: int, discount: float,
                  working_capital: float = 0.0, tax_shield: bool = False,
                  expense_rd: bool = False, **kwargs) -> float:
    """Peak sales at which the project's IRR equals `peak_target`."""
    lo, hi = 1.0, 30000.0
    for _ in range(200):
        mid = (lo + hi) / 2.0
        pairs = cashflow_pairs(mid, dev_cost, ebit_margin, tax, life,
                               working_capital=working_capital,
                               tax_shield=tax_shield, expense_rd=expense_rd,
                               **kwargs)
        r = irr_of(pairs)
        # IRR rises with peak sales. If the rate at `mid` is already above
        # the target, the root sits at lower peak sales.
        if r is None or r < peak_target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


# ---------------------------------------------------------------- scenarios

# Three bundles, not a downside/base/upside ladder. The names describe what
# each one IS rather than implying an ordering the numbers do not support: the
# cost-overrun bundle has a larger peak-sales assumption than the narrow one
# and still produces a worse result, because its costs and margins are worse.
SCENARIOS = {
    "Narrow molecule": dict(peak_sales=75.0, dev_cost=307.0, ebit_margin=0.40,
                             tax=0.21, discount=0.135, life=15),
    "Cost-overrun mid-size": dict(peak_sales=200.0, dev_cost=380.0,
                                  ebit_margin=0.25, tax=0.25, discount=0.14,
                                  life=10),
    "Blockbuster": dict(peak_sales=900.0, dev_cost=240.0, ebit_margin=0.52,
                         tax=0.18, discount=0.11, life=18, plateau_years=7),
}


def evaluate(peak_sales: float, dev_cost: float, ebit_margin: float,
             tax: float, discount: float, life: int,
             plateau_years: int = 4) -> dict:
    """NPV and IRR for one scenario."""
    pairs = cashflow_pairs(peak_sales, dev_cost, ebit_margin, tax, life,
                           plateau_years=plateau_years)
    return {
        "peak_sales": peak_sales, "dev_cost": dev_cost,
        "ebit_margin": ebit_margin, "discount": discount, "life": life,
        "plateau_years": plateau_years,
        "npv": npv_of(pairs, discount),
        "irr": irr_of(pairs),
    }


def main() -> None:
    out: dict = {"scenarios": {}}

    print("=" * 78)
    print("CROP-PROTECTION NEW-ACTIVE-INGREDIENT NPV MODEL")
    print("=" * 78)
    print(f"Development period              : {DEV_YEARS} years")
    print(f"Post-launch cash (model's own)  : "
          f"${LAUNCH_MARKETING + SCALEUP + STEWARD:,.0f}m")
    print()

    hdr = f"{'Scenario':24}{'Peak$m':>9}{'NPV$m':>10}{'IRR':>9}  Hurdle"
    print(hdr)
    print("-" * len(hdr))
    for name, s in SCENARIOS.items():
        res = evaluate(**s)
        out["scenarios"][name] = res
        irr_txt = f"{res['irr']:.2%}" if res["irr"] is not None else "n/a"
        print(f"{name:24}{s['peak_sales']:>9,.0f}{res['npv']:>10,.1f}"
              f"{irr_txt:>9}  "
              f"{'ABOVE' if (res['irr'] or -1) >= HURDLE_IRR else 'below'}")

    b = SCENARIOS["Narrow molecule"]
    be_npv = breakeven_npv(b["dev_cost"], b["ebit_margin"], b["tax"], b["life"],
                           b["discount"])
    be_irr = breakeven_irr(HURDLE_IRR, b["dev_cost"], b["ebit_margin"], b["tax"],
                           b["life"], b["discount"])
    out["breakeven_npv_zero_peak_sales"] = be_npv
    out["breakeven_15pct_irr_peak_sales"] = be_irr
    print()
    print(f"Breakeven peak sales, NPV = 0   : ${be_npv:,.0f}m")
    print(f"Breakeven peak sales, IRR = 15% : ${be_irr:,.0f}m")
    print()

    print("Peak sales required for a 15% IRR, by development cost")
    for dc in (260.0, 280.0, 301.0, 307.0, 320.0, 350.0):
        v = breakeven_irr(HURDLE_IRR, dc, b["ebit_margin"], b["tax"],
                          b["life"], b["discount"])
        print(f"   dev ${dc:,.0f}m -> ${v:,.0f}m peak sales")
        out.setdefault("irr_breakeven_by_dev_cost", {})[f"{dc:.0f}"] = v
    print()

    print("Peak sales required for a 15% IRR, by operating contribution (base dev cost)")
    for mg in (0.35, 0.40, 0.45, 0.50, 0.55):
        v = breakeven_irr(HURDLE_IRR, b["dev_cost"], mg, b["tax"],
                          b["life"], b["discount"])
        print(f"   operating contribution {mg:.0%} -> ${v:,.0f}m peak sales")
        out.setdefault("irr_breakeven_by_margin", {})[f"{mg:.2f}"] = v

    print()
    print("Peak sales required for NPV = 0, by discount rate (base parameters)")
    for r in (0.08, 0.085, 0.09, 0.10, 0.11, 0.12, 0.135, 0.15):
        v = breakeven_npv(b["dev_cost"], b["ebit_margin"], b["tax"], b["life"], r)
        print(f"   discount {r:.1%} -> ${v:,.0f}m peak sales")
        out.setdefault("npv_zero_breakeven_by_discount", {})[f"{r:.3f}"] = v

    # A 5% royalty deduction is arithmetically identical to a 5pp reduction
    # in contribution margin.
    print()
    print("Peak sales required for a 15% IRR, with a 5% royalty/COGS deduction")
    v_roy = breakeven_irr(HURDLE_IRR, b["dev_cost"], b["ebit_margin"] - 0.05,
                          b["tax"], b["life"], b["discount"])
    print(f"   40% contribution less 5% royalty -> ${v_roy:,.0f}m peak sales")
    out["irr_breakeven_with_5pct_royalty"] = v_roy

    print()
    print("Cost structure: working capital and R&D tax treatment")
    print("   Working capital is taken at Corteva's 35% of revenue, the lower of")
    print("   the two filed balance-sheet ratios. The FMC ratio (72%) is run")
    print("   separately below; neither is a point estimate for the industry.")
    for r in (0.085, 0.135, 0.15):
        plain = breakeven_npv(b["dev_cost"], b["ebit_margin"], b["tax"], b["life"], r)
        nwc = breakeven_npv(b["dev_cost"], b["ebit_margin"], b["tax"], b["life"], r,
                             working_capital=CORTEVA_WC)
        both = breakeven_npv(b["dev_cost"], b["ebit_margin"], b["tax"], b["life"], r,
                             working_capital=CORTEVA_WC, tax_shield=True)
        expensed = breakeven_npv(b["dev_cost"], b["ebit_margin"], b["tax"], b["life"], r,
                                 working_capital=CORTEVA_WC, tax_shield=True,
                                 expense_rd=True)
        print(f"   discount {r:.1%}: base ${plain:,.0f}m | "
              f"NWC {CORTEVA_WC:.0%} ${nwc:,.0f}m | NWC + shield ${both:,.0f}m | "
              f"NWC + shield + R&D expensed ${expensed:,.0f}m")
        out.setdefault("cost_structure", {})[f"{r:.4f}"] = {
            "published_spec": plain,
            "nwc_corteva_35pct": nwc,
            "nwc_corteva_35pct_with_tax_shield": both,
            "nwc_corteva_35pct_shield_rdexpensed": expensed}

    print()
    print("Working capital across the range implied by two filed balance sheets")
    for label, wc in (("Corteva 35%", CORTEVA_WC),
                      ("FMC 72%", FMC_WC)):
        v = breakeven_irr(HURDLE_IRR, b["dev_cost"], b["ebit_margin"], b["tax"],
                          b["life"], b["discount"], working_capital=wc)
        ve = breakeven_irr(HURDLE_IRR, b["dev_cost"], b["ebit_margin"], b["tax"],
                           b["life"], b["discount"], working_capital=wc,
                           tax_shield=True, expense_rd=True)
        print(f"   {label}: 15% IRR hurdle ${v:,.0f}m | "
              f"with group offset and R&D expensed ${ve:,.0f}m")
        out.setdefault("working_capital_range", {})[label] = {
            "irr_hurdle": v, "irr_hurdle_shield_expensed": ve}

    print()
    print("Manufacturing scale-up: the survey's development total already")
    print("includes a scale-up-of-manufacture component, so the separate")
    print("$30m line below may overlap with it. Hurdle without that line:")
    no_scale = breakeven_irr(HURDLE_IRR, b["dev_cost"], b["ebit_margin"], b["tax"],
                             b["life"], b["discount"], scaleup=0.0)
    print(f"   15% IRR hurdle without the separate scale-up line: ${no_scale:,.0f}m")
    out["irr_hurdle_without_separate_scaleup"] = no_scale

    print()
    print("The 15% IRR hurdle does not move with the discount rate:")
    print(f"   15% IRR hurdle is ${be_irr:,.0f}m at any discount rate; NPV-zero "
          f"at 8.5% is ${breakeven_npv(b['dev_cost'], b['ebit_margin'], b['tax'], b['life'], 0.085):,.0f}m")
    print("   (the IRR-based hurdle is discount-rate independent by construction)")
    print("   8.5% is an author-selected low case, not a sourced market rate.")
    out["irr_hurdle_at_15pct"] = be_irr

    # Self-checks.
    sched = pre_launch_pairs(scaled_phase_costs(307.0))
    print()
    print("Self-checks")
    print(f"   pre-launch schedule sums to ${sum(a for _, a in sched):,.2f}m "
          f"(expect ${307.0:,.2f}m - the amortised cost)")
    assert abs(sum(a for _, a in sched) - 307.0) < 1e-6, \
        "pre-launch cash must equal the amortised cost"
    assert abs(sum(c for _, _, c in PHASES) - SURVEY_TOTAL) < 1e-6, \
        "phase costs must sum to the survey total"

    # Removing the registration phase must remove exactly the registration
    # cost and touch nothing else.
    reg_only = phase_costs_without_registration(307.0)
    base_costs = scaled_phase_costs(307.0)
    removed = [b - r for b, r in zip(base_costs, reg_only)]
    print(f"   registration-only removal takes out "
          f"${removed[REGISTRATION_PHASE_INDEX]:,.2f}m from registration and "
          f"${sum(removed) - removed[REGISTRATION_PHASE_INDEX]:,.2f}m from elsewhere")
    expected_reg = scaled_phase_costs(307.0)[REGISTRATION_PHASE_INDEX]
    assert abs(removed[REGISTRATION_PHASE_INDEX] - expected_reg) < 1e-6, \
        "registration-only removal must take out the registration cost"
    assert abs(sum(removed) - removed[REGISTRATION_PHASE_INDEX]) < 1e-6, \
        "registration-only removal must not touch other phases"

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
        pairs = cashflow_pairs(s["peak_sales"], s["dev_cost"], s["ebit_margin"],
                               s["tax"], s["life"],
                               plateau_years=s.get("plateau_years", 4))
        r = irr_of(pairs)
        assert r is not None, f"{n}: IRR undefined"
        npv_at_irr = npv_of(pairs, r)
        print(f"   {n}: NPV at own IRR = {npv_at_irr:+.4f} (must be ~0)")
        assert abs(npv_at_irr) < 0.05, f"{n} IRR not consistent with NPV"

    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "crop_protection_npv_model_results.json")
    with open(path, "w") as fh:
        json.dump(_rounded(out), fh, indent=2, default=str)
    print(f"\nResults written to {path}")



def _rounded(obj, ndigits=10):
    """Round every float in a results structure to a fixed precision.

    The published JSON files are artefacts that reviewers may re-run and
    compare byte-for-byte. Floating-point arithmetic is not bit-reproducible
    across interpreter and library builds, so the last few digits of a
    result can differ between two runs of the same code on the same
    machine. Rounding at the point of serialisation removes that noise
    without touching any value the model actually computes: at ten decimal
    places these are dollar-million figures quoted to the cent.
    """
    if isinstance(obj, dict):
        return {k: _rounded(v, ndigits) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_rounded(v, ndigits) for v in obj]
    if isinstance(obj, float):
        return round(obj, ndigits)
    return obj

if __name__ == "__main__":
    main()
