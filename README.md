# Crop protection NPV model

The cash-flow model behind **"Driving Innovation in Crop Protection: The 7 Percent Problem"**.

The question it answers: **what would a new active ingredient have had to earn to
justify a full originator development programme** — and what share of the crop
protection market does that represent?

The model is deliberately plain. Every input is stated, every assumption is
named, and the breakeven solves are visible in the code rather than buried in a
formula. If you disagree with an assumption, change it and see what it does to
the answer.

Everything runs on the Python standard library. No dependencies, no data files,
no workbook.

```bash
python3 crop_protection_npv.py            # base model
python3 regulation_test.py                # the regulatory counterfactuals
python3 alternative_construction.py       # an independent second construction
```

Each script writes a JSON file next to itself with the results, so the numbers
in the article can be checked without reading the code.

This is the model behind [Driving Innovation in Crop Protection: The 7 Percent
Problem](https://blog.ryanrakestraw.com/driving-innovation-in-crop-protection-the-7-percent-problem/).

---

## The headline numbers

All figures are **peak annual sales in $ millions** for a single new active
ingredient with a 15-year commercial life.

| | Peak sales needed |
|---|---:|
| NPV = 0 at a 13.5% discount rate | **$509m** |
| NPV = 0 at an 8.5% discount rate | $294m |
| 15% IRR hurdle | **$596m** |
| 15% IRR hurdle, alternative construction | $696m |

Two different numbers, and they are not interchangeable:

- The **NPV-zero hurdle** depends on the discount rate.
- The **15% IRR hurdle** does not, because the IRR of a cash-flow vector does not
  depend on the rate at which you discount it.

The 8.5% rate is **author-selected**, not a market rate. No source publishes it.
It is used as a deliberately low case: a hurdle below what any disclosed cost of
capital supports would flatter the conclusion the article argues against itself.

## The regulatory counterfactuals

`regulation_test.py` holds the $307m cost base and the revenue path fixed and
removes one regulatory channel at a time.

| Structure | NPV=0 @ 8.5% | NPV=0 @ 13.5% | 15% IRR hurdle |
|---|---:|---:|---:|
| Baseline (as published) | $294m | $509m | $596m |
| Free registration | $274m | $481m | $566m |
| 1995-speed development calendar | $262m | $422m | $484m |
| Approval wait removed, R&D programme unchanged | $264m | $429m | $493m |
| Both changes together | $243m | $396m | $455m |
| Both, plus approval wait removed | $223m | $347m | $392m |

Three things this test is careful about:

- **Free registration removes the registration phase's cost and nothing else.**
  An earlier version scaled every phase down pro rata, so roughly $31m of the
  saving came out of discovery and research rather than registration, and the
  post-launch cost lines fell as well because they scaled with the same total.
- **Removing the approval wait does not cancel the R&D programme.** The money
  spent before approval is still spent, and the cost schedule is untouched.
  Revenue starts 1.5 years earlier instead.
- **This is not deregulation.** It removes one cost category and one calendar.
  It does not remove the regulatory constraint, and the article says so.

Against the ten active ingredients launched in 2010 — $48.6m average realised
2022 revenue, and about $121.5m implied peak on the model's own revenue path —
removing both channels closes **26%** of the gap to realised revenue and **30%**
of the gap to implied peak. Across every case tested, the range is **0% to
37%** against realised revenue and **0% to 43%** against implied peak.

Note that compressing the calendar also moves spend forward, and money spent
earlier is discounted less. That effect raises the hurdle rather than lowering
it, and it is not about regulation at all. The model lets it happen rather than
assuming compression is free, which is why the compressed-calendar case is not
automatically the more favourable one.

## The alternative construction

`alternative_construction.py` is a genuinely different model, not a
re-parameterisation of the same one. Same $307m cost base; different structure:

| Assumption | Published model | Alternative |
|---|---|---|
| Operating contribution | 40% | 35% |
| Commercial life | 15 years | 10 years |
| Post-peak erosion | 15% a year | 25% a year |
| Tax | 21% | 25% |
| Separate post-launch cost lines | yes | no |

It produces a hurdle of **$696m** against **$596m** — a $101m spread from
assumption choices alone. That spread is the point. A single model construction
is not a measurement of an industry.

The alternative also differs from the published model in one respect that an
earlier version did not disclose: it spends the $307m evenly over **ten**
pre-launch years and launches at t=10, against the published model's uneven
eleven-year schedule launching at t=11. Spending the same money earlier raises
its present value. The script now states this and prices it separately, as an asserted
sequential waterfall in which one assumption group is applied at a time: an even
ten-year pre-launch calendar moves the hurdle by −$23m, dropping the post-launch
cost lines by −$45m, post-peak erosion by +$39m, the shorter commercial life by
+$18m, the lower operating contribution by +$84m and the higher tax rate by
+$28m, and removing the loss carry-forward by nothing. The deltas sum exactly to
the published spread of +$100.6m, from $595.8m to $696.4m, and the script
asserts both endpoints.

Because several assumptions change at once, the spread cannot by itself show
which assumption matters most — that is what the waterfall is for, and it is
reported rather than left to inference.

## How the cost base is built

The pre-launch cost is the **AgbioInvestor 2026** development-cost survey, used
at the level of its own functional totals rather than apportioned by phase:

| | |
|---|---:|
| Research | $133m |
| Development | $138m |
| Registration | $35m |
| **Total** | **$307m** |

The survey is of BASF Agricultural Solutions, Bayer Crop Science, Corteva, FMC
and Syngenta, on the 2020–2023 launch cohort.

## Working capital and the tax treatment

The base case carries **no working-capital funding**. That is a deliberate
omission, and it is disclosed rather than buried: working capital is not
included in the survey's development cost, and it is not in the base case
here either.

The correction is run against two ratios computed from reported balance
sheets, not assumed:

| Case | Trade working capital | 15% IRR hurdle | With group offset and R&D expensed |
|---|---:|---:|---:|
| Corteva, Inc. FY2025 Form 10-K | 35.3% | $697m | $582m |
| FMC Corporation FY2025 Form 10-K | 72.4% | $848m | $708m |
| Base case, no working capital | — | $596m | — |

Corteva is computed as accounts receivable $4,881m plus inventories $5,667m
less accounts payable $4,398m over revenue $17,401m. FMC's ratio is inflated
by a pre-divestiture inventory build. Both are whole-company ratios, and
neither is a point estimate for the industry, so the model reports the range
rather than averaging it.

The gain from expensing development spend is **not** the removal of a book
charge — the model already adds non-cash amortisation back into free cash
flow, so no cash is created by dropping it. The gain is *when* the deduction
is taken and *whether* there is profit elsewhere in the group to offset it
against. At zero tax the two treatments are identical, which is the check
that proves it; the model runs that identity as a self-check.

## Other stated assumptions

| Input | Value |
|---|---|
| Development timeline | 11 years, five phases |
| Revenue shape | 5-year ramp to full penetration, 4 years at peak, then −15% of peak per year |
| Operating margin | 40% at peak (58% gross margin less 18% SG&A) |
| Commercial life | 15 years base (18 bull, 10 bear) |
| Cost of capital | 13.5% base, 15% corporate hurdle, 8.5% low case (author-selected) |

## Two checks worth running

The model asserts two identities that a spreadsheet version of this would have
failed:

1. **The zero-tax identity.** At zero tax, a capitalised development cost and an
   expensed one must produce identical cash-flow NPVs. Amortisation is an
   accounting treatment, not a cash event. An earlier version of this model
   broke this test by $12.9m, because it took a tax shield on cash it never
   paid.

2. **The full-cash check.** The model pays the whole $307m as cash before
   launch. An earlier version amortised about $52m of development cost without
   ever paying it, which understated the hurdle by roughly $180m.

Both are enforced in code, so the script fails loudly rather than printing a
number nobody checked.

`regulation_test.py` also prints, before its results, how much cash each
counterfactual actually removes and whether any pre-launch spend is dropped by
truncation. Both are worth reading — an earlier version of that test failed
both, in the direction that flattered the conclusion.

## Corrections

An earlier version of this model produced numbers that could not be quoted. The
corrections that mattered all moved the result **against** the conclusion rather
than in its favour:

- The pre-launch cost schedule did not reproduce the survey's own functional
  split. Research and development were scaled to about $31m against the
  survey's $133m research cost.
- Development cost was capitalised and amortised without the corresponding cash
  ever being paid, and a tax shield was taken on it. The zero-tax identity above
  is what exposed this.
- Phase start times were read off year labels rather than elapsed time from
  discovery start, so phases sat a year late and the last phase was truncated at
  the horizon, dropping $24m of the pre-launch budget.
- Tax was applied to revenue rather than to EBIT, and the free-cash-flow factor
  was applied to peak EBIT rather than to NOPAT.
- A probability-of-success multiplier was applied to revenue and cost alike.
  That is not a risk-adjusted NPV: it cannot change the zero-NPV hurdle, and it
  understates losses by treating the cost of failed programmes as though it
  were never incurred. The survey cost is already attrition-inclusive, so a
  second failure haircut double-counts. Those rows have since been removed
  from the model rather than kept as diagnostics, because a diagnostic that
  cannot change a decision does not belong in the argument.
- "Effective IP protection" was a circular reference to its own cell, and the
  peak margin line subtracted dollar values of revenue from percentage values,
  producing a 74.24% margin on a 40% business.
- The regulatory calendar counterfactual was described as removing 3.1 years of
  delay. It moved first revenue by two years, from year 11 to year 9, because
  the engine ran on whole-year periods. The engine now carries continuous time,
  so the calendar compresses to exactly 8.3 years and first revenue arrives
  2.7 years earlier.
- The "free registration" counterfactual removed the wrong money. It scaled
  every phase down pro rata, so most of the saving came out of discovery
  rather than registration, and it also reduced the post-launch cost lines.
  The removal is now phase-specific, with post-launch spend held fixed.
- A third calendar variant launched commercial sales three years before the
  registration dossier was finished, which is not what removing an approval
  queue looks like. That case is gone; the approval-wait case now holds the
  R&D programme and its costs exactly fixed and moves only the launch date.
- The pre-launch schedule was scaled twice, so it summed to $308m against the
  $307m amortised cost. The double-scaling is removed and the identity is
  asserted in code.
- The IRR bisection for the 15% hurdle had its direction inverted, so every
  query returned the upper bound. The hurdle is now $596m, not the $606m
  published previously.
- The Blockbuster scenario produced **zero revenue in its last three commercial
  years**, so its IRR and NPV were wrong. The plateau is now 7 years against an
  18-year life and revenue is positive in every commercial year. NPV moves from
  +$449.4m to **+$547.7m** and IRR from **24.4% to 25.1%**. The headline hurdle
  is unchanged.
- The approval-wait counterfactual spent **$23.4m of programme cash after
  launch**, which cannot happen: a product cannot be marketed before it is
  approved. The registration dossier is now prepared concurrently with the final
  1.5 years of field trials and toxicology, with phase budgets unchanged. All
  six structures report **$0.00m** of post-launch spend, and the approval-wait
  hurdle moves from $488m to **$493m**. Every other structure is unchanged.
- The alternative construction described its rungs with labels that did not
  match what the code did, and the decomposition did not sum. It is now an
  asserted sequential waterfall with one assumption group per rung, each step
  applied to the previous one, and the deltas sum exactly to the published
  spread of **+$100.6m**, from $595.8m to $696.4m.

## What this model does not do

It is a single-product model, not a portfolio model. It does not attempt
risk-adjusted NPV in the stage-gated (rNPV) sense, because that requires
calibrating phase-by-phase probabilities, which the published survey does not
support. It uses one average development programme, not a distribution of
programmes, and it says so.

It also does not claim that most launches fail, or that regulation is the cause
of weak innovation economics. The 2010 cohort is ten products with a single
2022 revenue observation each; it is not a representative matched cohort, and
one member had its EU approval withdrawn. The model produces a hurdle under
stated assumptions. Comparing that hurdle to realised outcomes is the reader's
step, and the article is explicit about what the comparison can and cannot
support.

The working-capital correction is run across a range rather than a point,
because the two US filers whose balance sheets could be reproduced directly
give about 35% of revenue at Corteva and about 72% at FMC. At the 15% hurdle
that is $697m and $848m respectively, against $596m without it. A multinational
originator that expenses development spend as incurred and offsets it against
group profits takes the Corteva case back to $582m. At zero tax the capitalised
and expensed treatments are identical, which is the check that proves it.

## Files

| File | What it does |
|---|---|
| `crop_protection_npv.py` | Base model: cash flows, NPV, IRR, sensitivity tables |
| `regulation_test.py` | The counterfactual structures above |
| `alternative_construction.py` | The independent second construction |
| `crop_protection_npv_model_results.json` | Output of the base model |
| `crop_protection_npv_regulation_test_results.json` | Output of the counterfactual test |
| `alternative_construction_results.json` | Output of the alternative construction |

## Reproducing the published numbers

```bash
git clone https://github.com/rakestrn/crop-protection-npv.git
cd crop-protection-npv
python3 crop_protection_npv.py && python3 regulation_test.py && python3 alternative_construction.py
```

The JSON files in this repository were generated by these scripts from the
committed sources, and a clean clone reproduces all three **byte-for-byte**.
Floating-point arithmetic is not bit-reproducible across interpreter and library
builds, so the results are rounded at the point of serialisation only — no
computed value changes. If your run produces different numbers, that is a real
discrepancy and worth reporting.

## Source

AgbioInvestor for CropLife International, *Time and Cost of New Agrochemical
Product Discovery, Development and Registration*, New Agrochemical Product
Study, May 2026.

## Licence

MIT — see [LICENSE](LICENSE).
