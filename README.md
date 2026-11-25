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
python3 regulation_test.py                # five regulatory counterfactuals
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
| NPV = 0 at a 13.5% discount rate | **$518m** |
| NPV = 0 at an 8.5% discount rate | $301m |
| 15% IRR hurdle | **$606m** |
| 15% IRR hurdle, alternative construction | $696m |

Two different numbers, and they are not interchangeable:

- The **NPV-zero hurdle** depends on the discount rate.
- The **15% IRR hurdle** does not, because the IRR of a cash-flow vector does not
  depend on the rate at which you discount it.

The 8.5% rate is **author-selected**, not a market rate. No source publishes it.
It is used as a deliberately low case: a hurdle below what any disclosed cost of
capital supports would flatter the conclusion the article argues against itself.

## The five counterfactuals

`regulation_test.py` holds the $307m cost base and the revenue path fixed and
removes one regulatory channel at a time.

| Structure | NPV=0 @ 8.5% | NPV=0 @ 13.5% | 15% IRR hurdle |
|---|---:|---:|---:|
| Baseline (as published) | $301m | $518m | $606m |
| Free registration | $267m | $459m | $537m |
| Approval wait removed, R&D programme unchanged | $240m | $364m | $410m |
| 1995-speed development calendar | $285m | $469m | $541m |
| Both changes together | $252m | $416m | $480m |

Two things this test is careful about:

- **Removing the approval wait does not cancel the R&D programme.** The money
  spent before approval is still spent. The counterfactual starts revenue
  earlier and leaves the cost schedule alone.
- **This is not deregulation.** It removes one cost category and one calendar.
  It does not remove the regulatory constraint, and the article says so.

Against the ten active ingredients launched in 2010 — $48.6m average realised
2022 revenue, and about $121.5m implied peak on the model's own revenue path —
removing both channels closes **23%** of the gap to realised revenue and **26%**
of the gap to implied peak.

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

It produces a hurdle of **$696m** against **$606m** — a $90m spread from
assumption choices alone. That spread is the point. A single model construction
is not a measurement of an industry.

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
  second failure haircut double-counts. Those rows are retained, labelled as
  diagnostics.
- "Effective IP protection" was a circular reference to its own cell, and the
  peak margin line subtracted dollar values of revenue from percentage values,
  producing a 74.24% margin on a 40% business.
- The regulatory calendar counterfactual was described as removing 3.1 years of
  delay. It moved first revenue by two years, from year 11 to year 9.

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

## Files

| File | What it does |
|---|---|
| `crop_protection_npv.py` | Base model: cash flows, NPV, IRR, sensitivity tables |
| `regulation_test.py` | The five counterfactual structures above |
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
committed sources. If your run produces different numbers, that is a real
discrepancy and worth reporting.

## Source

AgbioInvestor for CropLife International, *Time and Cost of New Agrochemical
Product Discovery, Development and Registration*, New Agrochemical Product
Study, May 2026.

## Licence

MIT — see [LICENSE](LICENSE).
