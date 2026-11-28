#!/usr/bin/env python3
"""
Discounted cash-flow model of a single new crop-protection active ingredient.

Solves for the peak annual sales a new conventional active ingredient needs to
clear a stated required return, using the functional cost structure from the
AgbioInvestor / CropLife International survey (May 2026: $307m and 11.4 years
for the 2020-2023 launch cohort across BASF, Bayer, Corteva, FMC and Syngenta).

Usage:
    python3 crop_protection_npv.py

Writes results to crop_protection_npv_model_results.json.

KEY INPUTS AND ASSUMPTIONS
--------------------------
- Pre-launch R&D ($307m over an 11-year, 5-phase schedule): carries the
  survey's functional totals — research $133m (biology $46m, chemistry $75m,
  tox/env $12m), development $138m (chemistry $32m, field trials $59m,
  toxicology $23m, environmental chemistry $24m) and registration $35m.
  Phase timing is this model's assumption; functional totals are the survey's.
- Post-launch cash ($76m, model assumption): $25m launch marketing (year 0,
  expensed), $30m manufacturing scale-up (year 0, depreciated straight-line
  over 5 years; also tested at $0m because the survey's development bucket
  includes a $23.3m scale-up item), and $21m stewardship (years 0-3, expensed).
  Total programme cash is $383m.
- Revenue trajectory: 5-year linear ramp (20% to 84% of peak), 4-year plateau
  at 100%, then 15 percentage points of peak lost per year over a 15-year
  commercial life (with alternative trajectory shapes tested in main()).
- Operating contribution & tax: 40% at peak before R&D amortisation (58% gross
  margin less 18% SG&A); 21% tax on EBIT with net operating loss carry-forward
  (plus a multinational group-tax-shield and immediate-R&D-expensing test).
- Discount rates: 7.5%-10.5% after-tax cost-of-capital range (8.5% and 9.0%
  highlighted), 13.5% legacy scenario rate, and 15.0% corporate IRR hurdle.

REVISION HISTORY
----------------
Corrections from the initial spreadsheet version (full details in README.md):
- Commercial loop fixed to `life` years (was `life + 1`); phase starts indexed
  from t=0 with ceiling horizon buckets so no pre-launch spend is truncated.
- Pre-launch phase budgets sum to the $307m amortised cost (enforced by
  self-check, along with the zero-tax capitalised-vs-expensed cash identity).
- Tax applied to EBIT after R&D amortisation, scale-up depreciation, launch
  marketing and stewardship, with loss carry-forward; probability-of-success
  scalar removed because the $307m survey cost already embeds technical
  attrition.
- Regulatory counterfactuals in regulation_test.py use phase-specific
  registration removal, fixed post-launch costs, and continuous-time calendar
  scaling.
"""
from __future__ import annotations

import json
import os

# --------------------------------------------------------------- constants

DEV_YEARS = 11          # pre-launch development period (t=0 to t=11)
SURVEY_TOTAL = 306.0    # sum of the survey's rounded function components ($m)
REFERENCE_DEV_COST = 306.0

# Post-launch cost lines ($m), held fixed across counterfactuals.
LAUNCH_MARKETING = 25.0     # commercial year 0, expensed
SCALEUP = 30.0              # commercial year 0, depreciated over SCALEUP_LIFE
SCALEUP_LIFE = 5
STEWARD = 21.0              # spread evenly over first STEWARD_YEARS years
STEWARD_YEARS = 4

# Pre-launch phases: (start_year, duration_years, cost_$m).
PHASES = [
    (0.0, 2.5, 46.0),   # Discovery & biological screening   (research: biology)
    (2.5, 2.5, 87.0),   # Lead optimisation & research chem  (research: chem + tox/env)
    (5.0, 2.0, 56.0),   # Early development & env chemistry   (development: chem + env)
    (7.0, 2.5, 82.0),   # Field trials & toxicology          (development: trials + tox)
    (9.5, 1.5, 35.0),   # Registration                      (registration)
]
REGISTRATION_PHASE_INDEX = 4
LEAD_1995 = 8.3         # 1995 survey benchmark lead time (years)

TAX = 0.21
HURDLE_IRR = 0.15
BASE_DISCOUNT = 0.135

# Trade working capital / revenue from FY2025 Form 10-K filings:
#   Corteva: (AR $4,881m + Inv $5,667m - AP $4,398m) / Rev $17,401m = 35.3%
#   FMC:     (AR $2,062m + Inv $1,220m - AP $771m)   / Rev $3,467m  = 72.4%
CORTEVA_WC = 0.353
FMC_WC = 0.724


def penetration(c: int, plateau_years: int = 4, ramp_years: int = 5,
                erosion_rate: float = 0.15) -> float:
    """Commercial-year penetration factor: linear ramp from 0.20 across
    `ramp_years`, `plateau_years` at 1.00, then `erosion_rate` lost per year."""
    if c < ramp_years:
        return 0.20 + (0.80 / ramp_years) * c
    peak_end = ramp_years + plateau_years - 1
    if c <= peak_end:
        return 1.00
    return max(0.0, 1.0 - erosion_rate * (c - peak_end))


PENETRATION = [penetration(c) for c in range(16)]


# ------------------------------------------------------------------- costs

def scaled_phase_costs(total: float) -> list[float]:
    """Phase costs scaled proportionally to sum to `total`."""
    scale = total / sum(c for _, _, c in PHASES)
    return [c * scale for _, _, c in PHASES]


def phase_costs_without_registration(total: float) -> list[float]:
    """Phase costs scaled to `total` with the registration phase zeroed out."""
    costs = scaled_phase_costs(total)
    costs[REGISTRATION_PHASE_INDEX] = 0.0
    return costs


def pre_launch_pairs(costs: list[float],
                     time_scale: float = 1.0,
                     phases: list[tuple[float, float, float]] | None = None
                     ) -> list[tuple[float, float]]:
    """Allocate phase costs into annual calendar buckets as (year, amount)
    pairs, supporting continuous-time calendar compression via `time_scale`."""
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
                   ramp_years: int = 5,
                   erosion_rate: float = 0.15,
                   phases: list[tuple[float, float, float]] | None = None
                   ) -> list[tuple[float, float]]:
    """Year-by-year unlevered free cash flow as (time_in_years, amount_$m)
    pairs. `ebit_margin` is operating contribution before R&D amortisation."""
    if phase_costs is None:
        phase_costs = scaled_phase_costs(dev_cost)
    amortisation = 0.0 if expense_rd else dev_cost / life

    pre: list[tuple[float, float]] = []
    for t, amt in pre_launch_pairs(phase_costs, time_scale, phases):
        cf = -amt
        if tax_shield and expense_rd:
            cf += amt * tax
        pre.append((t, cf))

    launch_t = (DEV_YEARS * time_scale) if launch_offset is None else launch_offset

    commercial: list[tuple[float, float]] = []
    prev_wc = 0.0
    nol = 0.0
    for c in range(life):
        revenue = peak_sales * penetration(c, plateau_years, ramp_years,
                                           erosion_rate)
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
             plateau_years: int = 4, ramp_years: int = 5,
             erosion_rate: float = 0.15) -> dict:
    """NPV and IRR for one scenario."""
    pairs = cashflow_pairs(peak_sales, dev_cost, ebit_margin, tax, life,
                           plateau_years=plateau_years,
                           ramp_years=ramp_years,
                           erosion_rate=erosion_rate)
    return {
        "peak_sales": peak_sales, "dev_cost": dev_cost,
        "ebit_margin": ebit_margin, "discount": discount, "life": life,
        "plateau_years": plateau_years,
        "npv": npv_of(pairs, discount),
        "npv_at_8_5pct": npv_of(pairs, 0.085),
        "npv_at_9_0pct": npv_of(pairs, 0.09),
        "irr": irr_of(pairs),
    }


# Three empirical peak-sales tiers from the post-2005 launch distribution
# (2010 cohort ~45m; median post-2005 $100m+ survivor ~200m; blockbuster 500m),
# evaluated on the base cost structure ($307m R&D, 40% operating contribution,
# 21% tax, 15-year commercial life).
PEAK_SALES_REFERENCE_CASES = {
    "Typical launch ($45m)": 45.0,
    "Narrow molecule ($75m)": 75.0,
    "Median successful launch ($200m)": 200.0,
    "Blockbuster threshold ($500m)": 500.0,
}

# Sales-trajectory shapes tested against the base 5y-ramp / 4y-plateau /
# 15%/yr-erosion / 15y-life curve.
TRAJECTORY_SHAPES = {
    "Base (5y ramp, 4y plateau, 15%/yr fade, 15y life)": dict(
        ramp_years=5, plateau_years=4, erosion_rate=0.15, life=15),
    "Slow ramp (8y ramp, 4y plateau, 15%/yr fade, 15y life)": dict(
        ramp_years=8, plateau_years=4, erosion_rate=0.15, life=15),
    "Diamide-like (10y ramp, no plateau, 15%/yr fade, 15y life)": dict(
        ramp_years=10, plateau_years=0, erosion_rate=0.15, life=15),
    "Fast niche SDHI (3y ramp, 8y plateau, 10%/yr fade, 15y life)": dict(
        ramp_years=3, plateau_years=8, erosion_rate=0.10, life=15),
    "Defended franchise (7y ramp, 8y plateau, 5%/yr fade, 20y life)": dict(
        ramp_years=7, plateau_years=8, erosion_rate=0.05, life=20),
    "Steep cliff (5y ramp, 4y plateau, 25%/yr fade, 15y life)": dict(
        ramp_years=5, plateau_years=4, erosion_rate=0.25, life=15),
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
    for r in (0.075, 0.08, 0.085, 0.09, 0.10, 0.105, 0.11, 0.12, 0.135, 0.15):
        v = breakeven_npv(b["dev_cost"], b["ebit_margin"], b["tax"], b["life"], r)
        print(f"   discount {r:.1%} -> ${v:,.0f}m peak sales")
        out.setdefault("npv_zero_breakeven_by_discount", {})[f"{r:.3f}"] = v

    print()
    print("Empirical peak-sales tiers on base cost structure ($307m R&D, 40% contribution)")
    for label, pk in PEAK_SALES_REFERENCE_CASES.items():
        pairs = cashflow_pairs(pk, b["dev_cost"], b["ebit_margin"], b["tax"], b["life"])
        npv_85 = npv_of(pairs, 0.085)
        npv_90 = npv_of(pairs, 0.09)
        npv_135 = npv_of(pairs, 0.135)
        r_irr = irr_of(pairs)
        irr_str = f"{r_irr:.2%}" if r_irr is not None else "n/a"
        print(f"   {label:34}: NPV@8.5% ${npv_85:+7.1f}m | NPV@9.0% ${npv_90:+7.1f}m | "
              f"NPV@13.5% ${npv_135:+7.1f}m | IRR {irr_str}")
        out.setdefault("reference_peak_cases", {})[label] = {
            "peak_sales": pk,
            "npv_at_8_5pct": npv_85,
            "npv_at_9_0pct": npv_90,
            "npv_at_13_5pct": npv_135,
            "irr": r_irr,
        }

    print()
    print("Breakeven peak sales by sales-trajectory shape ($307m R&D, 40% contribution)")
    for label, spec in TRAJECTORY_SHAPES.items():
        pk_yrs = sum(penetration(c, spec["plateau_years"], spec["ramp_years"],
                                 spec["erosion_rate"])
                     for c in range(spec["life"]))
        be_85 = breakeven_npv(b["dev_cost"], b["ebit_margin"], b["tax"],
                              spec["life"], 0.085,
                              plateau_years=spec["plateau_years"],
                              ramp_years=spec["ramp_years"],
                              erosion_rate=spec["erosion_rate"])
        be_90 = breakeven_npv(b["dev_cost"], b["ebit_margin"], b["tax"],
                              spec["life"], 0.09,
                              plateau_years=spec["plateau_years"],
                              ramp_years=spec["ramp_years"],
                              erosion_rate=spec["erosion_rate"])
        be_135 = breakeven_npv(b["dev_cost"], b["ebit_margin"], b["tax"],
                               spec["life"], 0.135,
                               plateau_years=spec["plateau_years"],
                               ramp_years=spec["ramp_years"],
                               erosion_rate=spec["erosion_rate"])
        be_15 = breakeven_irr(HURDLE_IRR, b["dev_cost"], b["ebit_margin"],
                              b["tax"], spec["life"], 0.135,
                              plateau_years=spec["plateau_years"],
                              ramp_years=spec["ramp_years"],
                              erosion_rate=spec["erosion_rate"])
        print(f"   {label:56}: {pk_yrs:4.1f} pk-yrs | "
              f"8.5% ${be_85:5.0f}m | 9.0% ${be_90:5.0f}m | 15% IRR ${be_15:5.0f}m")
        out.setdefault("trajectory_sensitivity", {})[label] = {
            **spec,
            "peak_equivalent_years": pk_yrs,
            "npv_zero_at_8_5pct": be_85,
            "npv_zero_at_9_0pct": be_90,
            "npv_zero_at_13_5pct": be_135,
            "irr_15pct_hurdle": be_15,
        }

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
    """Round floats at serialisation so JSON outputs are byte-reproducible."""
    if isinstance(obj, dict):
        return {k: _rounded(v, ndigits) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_rounded(v, ndigits) for v in obj]
    if isinstance(obj, float):
        return round(obj, ndigits)
    return obj

if __name__ == "__main__":
    main()
