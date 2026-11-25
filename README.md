# What a new crop-protection active ingredient is worth

A financial model of a single new active substance (AI), built to answer one
question: **what peak annual sales does a new AI have to reach before it clears
a normal corporate hurdle rate?**

The headline result: on the central case, a new AI needs **$427 million** of
peak annual sales to clear a 15% IRR, and **$372 million** to break even on
NPV at a 13.5% discount rate. A narrow active ingredient is worth roughly
nothing; only a globally scaled product clears the bar.

The model is deliberately plain. Every input is stated, every assumption is
named, and the breakeven solves are visible in the code rather than buried in a
formula. If you disagree with an assumption, change it and see what it does to
the answer.

This is the model behind [Driving Innovation in Crop Protection: The 7 Percent
Problem](https://blog.ryanrakestraw.com/driving-innovation-in-crop-protection-the-7-percent-problem/).

## Running it

```
python3 crop_protection_npv.py     # base model
python3 regulation_test.py         # regulatory counterfactuals
```

No dependencies beyond the Python standard library (tested on Python 3.9+).
Each script writes a JSON file of results alongside itself.

## What the model does

Year-by-year unlevered free cash flow for one new active substance:

| Period | Content |
|---|---|
| Years 0–10 | Development spend across five phases, spread over the calendar years each phase overlaps |
| Year 11 | Launch year — launch marketing, manufacturing scale-up, first revenue |
| Years 12+ | Commercial years: revenue ramp, tax, amortisation, working capital, stewardship |

It solves for the **peak sales** at which NPV hits zero and at which IRR hits
15%, and it prints those hurdles across a range of discount rates, development
costs, operating margins and cost-structure treatments so you can see how much
each assumption moves the answer.

## Inputs

| Input | Value | Source |
|---|---|---|
| Total cost to develop and register one new AI | $307m | AgbioInvestor for CropLife International, *Time and Cost of New Agrochemical Product Discovery, Development and Registration* (May 2026) |
| Cost split | Research $133m, Development $138m, Registration $35m | Same study, 2020–2023 cohort |
| Development timeline | 11 years, five phases | Same study, allocated to phases |
| Revenue shape | 5-year ramp to full penetration, 4 years at peak, then −15% of peak per year | Assumed |
| Operating margin | 40% at peak (58% gross margin less 18% SG&A) | Assumed |
| Commercial life | 15 years base (18 bull, 10 bear); development spend amortised over the same period | Assumed |
| Cost of capital | 13.5% base, 15% corporate hurdle | Assumed — see below |

The survey is of BASF Agricultural Solutions, Bayer Crop Science, Corteva, FMC
and Syngenta, on the 2020–2023 launch cohort.

## Two hurdles, and why they differ

The model reports two different numbers, and they are not interchangeable:

- **NPV = 0 hurdle** — depends on the discount rate. $372m at 13.5%, $230m at
  8.5%.
- **15% IRR hurdle** — $427m, and **independent of the discount rate**,
  because the IRR of a cash-flow vector does not depend on the rate at which
  you discount it.

Both are reported throughout. Conflating them is the most common way a
hurdle number gets quoted wrongly.

The 15% hurdle is an *assumed* capital-rationing rate, not an observed industry
rate. Disclosed company discount rates for context are lower (BASF Ag 6.74%,
Bayer Group 7.0%, Syngenta 8.0%, Bayer Crop Science 9.4%; CAPM asset rate
~7.75%), and the model prints the NPV-zero hurdle at each of them. A
cost-of-capital framing gives a materially lower hurdle — the strongest
counter-argument to the thesis, and it is in the output rather than suppressed.

## The regulatory counterfactuals

`regulation_test.py` asks whether the hurdle depends on the regulatory regime
or is set by the economics alone. It compares four structures:

| Structure | 15% IRR hurdle | vs $48.6m realised | vs $121.5m implied peak |
|---|---|---|---|
| Baseline, as published | $427m | 8.8× | 3.5× |
| Free registration ($35m removed) | $379m | 7.8× | 3.1× |
| Fast lead time (8.3-year calendar) | $400m | 8.2× | 3.3× |
| Full deregulation | $355m | 7.3× | 2.9× |

Full deregulation closes **19%** of the distance between the $427m hurdle and
the $48.6m that the average active ingredient launched in 2010 actually earned.
Registration is a real tax on the returns of innovation. It is not the binding
constraint.

Two columns, because the comparison needs one. The hurdle is a **peak-sales**
number; $48.6m is what those ten products earned in **2022**, a single late year
rather than their peak. Applying this model's own average revenue path to the
cohort gives implied peak sales of about **$121.5m**, and on that like-for-like
basis the baseline hurdle is 3.5× rather than 8.8×, and full deregulation
closes **24%** of the gap rather than 19%. The conclusion holds either way; the
multiple does not survive unchanged.

The script prints two sanity checks before the results: how much cash each
counterfactual actually removes, and whether any pre-launch spend is dropped by
truncation. Both are worth reading — an earlier version of this test failed
both, in the direction that flattered the conclusion.

## Corrections

An earlier version of this model produced numbers that could not be quoted.
The corrections that matter all moved the result **against** the conclusion
rather than in its favour:

- The commercial-year loop ran one period too long, so the bear case earned
  revenue in eleven commercial years against a ten-year amortisation life.
  Corrected bear NPV: −$120.5m at −1.58% IRR (was −$118.2m at −0.49%).
- Phase start times were read off year labels and used as elapsed time from
  discovery start, so every phase sat a year late and the final phase was
  truncated at the horizon, dropping $36m of the $250m pre-launch budget.
- Tax was applied to revenue rather than to EBIT, and the free-cash-flow factor
  was applied to peak EBIT rather than to NOPAT.
- A probability-of-success multiplier was applied to revenue and cost alike.
  That is not a risk-adjusted NPV: it cannot change the zero-NPV hurdle and it
  understates losses by treating the cost of failed programmes as though it
  were never incurred. The survey cost is already attrition-inclusive — the
  questionnaire asks for the total cost of synthesising and screening every
  molecule needed to yield one successful launch — so a second failure haircut
  double-counts. Those rows are retained, labelled as diagnostics.
- "Effective IP protection" was a circular reference to its own cell, and the
  peak margin line subtracted dollar values of revenue from percentage values,
  producing a 74.24% margin on a 40% business.

One further correction runs the other way and is worth stating for the same
reason: the 15% IRR hurdle is discount-rate independent by construction, so
$427m survives any change in cost of capital while the NPV-zero hurdle does
not. Both are reported, and they are different quantities.

## What this model is not

It is a single-product model, not a portfolio model. It does not attempt
risk-adjusted NPV in the stage-gated (rNPV) sense, because that requires
calibrating phase-by-phase probabilities, which the published survey does not
support. It uses one average development programme, not a distribution of
programmes, and it says so.

The $48.6m cohort figure it is compared against is what the ten active
ingredients launched in 2010 earned in 2022 — revenue in a single late year,
twelve years after launch, not peak annual sales. Their peak years were
higher, so on a strictly like-for-like basis the gap to the hurdle is smaller
than the headline multiple: on this model's own revenue path their implied peak
is about $121m, which puts the baseline hurdle at 3.5× rather than 8.8×.

## Source

AgbioInvestor for CropLife International, *Time and Cost of New Agrochemical
Product Discovery, Development and Registration*, New Agrochemical Product
Study, May 2026.

## Licence

MIT — see [LICENSE](LICENSE).
