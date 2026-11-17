# Test plan v2 (16 Nov 2026)

**Device:** juice spectrophotometer. AS7343 multispectral sensor in transmission (0°), TSL2591 at 90° for scatter, white + 405 nm LEDs (+ 850 nm LED for a scattering baseline).
**Status:** v2 adds the brief's minimum requirements (juice type, concentration), liquid safety, and a requirement → test map. Targets are first estimates, to be revised after the first measurements (Fri 20 Nov). Changes go in the change log at the bottom.

---

## 1. Requirements
Source: coursework brief (Section 2) unless marked *engineering*.

| ID | Requirement | Source |
|---|---|---|
| **R1** | **Identifies the juice type** (apple, orange, pineapple…) | Brief: minimum |
| **R2** | **Measures juice concentration in water** | Brief: minimum |
| R3 | Tells fresh juice from aged juice | Brief: extension (optional) |
| R4 | Gives the same reading when the same sample is measured repeatedly (repeatable) | Engineering |
| R5 | Absorbance increases in a straight line with concentration (Beer–Lambert), over a stated range | Engineering |
| R6 | Detects small concentration changes (low limit of detection) | Engineering |
| R7 | Readings unaffected by room light and stray light | Engineering |
| R8 | Stable over a measurement session (small LED/sensor drift) | Engineering |
| R9 | Agrees with a lab-grade spectrophotometer (accurate) | Brief: "calibrate and benchmark" |
| R10 | Easy for a non-technical user: clear result on the display; data logged | Brief |
| R11 | Safe; liquid only in a removable cuvette; electronics protected from spills | Brief |

## 2. Requirement → test map
| Req. | Tested by |
|---|---|
| R1 juice type | T8, (T9) |
| R2 concentration | T7, (T9) |
| R3 freshness | T10, T11 |
| R4 repeatable | T2 |
| R5 linear | T3, T7 |
| R6 LOD | T4, T7 |
| R7 stray light | T1 |
| R8 stable | T5 |
| R9 accurate | T6 |
| R10 usable + logging | T12, T14 |
| R11 safe | T13 |

## 3. Standard method (every test unless stated)
1. Warm up the LEDs for 5 min before measuring.
2. Fix the gain and integration time for the whole series (see `as7343_channels.md`) and record them.
3. Order: **dark** (LEDs off) → **blank** (deionised water) → **samples**. Repeat the blank at the end of a series to check for drift.
4. Use the same cuvette, inserted the same way round (clear faces in the beam), wiped with a lint-free tissue.
5. Fill to a fixed volume (e.g. 3.0 mL by pipette) so the beam always passes through liquid.
6. Record the date/time, room temperature (on-board sensor), LED currents, settings and cuvette ID in the notebook.

## 4. Sample preparation
- **Dye stock (food colouring):** about 2 drops in 100 mL of deionised water; dilute by volume to the levels needed.
- **Juice dilutions:** % v/v juice in deionised water (100, 75, 50, 25, 10, 5, 0 %), made with a pipette or syringe into labelled cups. Shake cloudy juices before sampling.
- **Juices:** at least 3 types: clear apple, cloudy (orange), pineapple (optionally cloudy apple). Record the brand, batch and opening date.
- Fresh dilutions each session; discard after use.

## 5. Tests

| ID | Test | Req. | Samples | Repeats | Metric | Target (initial) | When |
|---|---|---|---|---|---|---|---|
| T1 | **Dark and stray light:** LEDs off, lid closed vs lid open in room light; opaque cuvette in the beam | R7 | Empty / water / opaque cuvette | 10 each | Mean dark counts; lid-open minus lid-closed difference; apparent absorbance with the beam blocked (sets the maximum measurable A) | Dark < 1 % of the blank; stray-light limit A_max > 2 | W2 Fri (open bench); repeat in enclosure v2 (W3) |
| T2 | **Repeatability:** remove and reinsert the cuvette each time | R4 | Water + one mid-level dye | 10 | CV of absorbance per channel | CV < 2 % | W4 |
| T3 | **Linearity (dye):** dilution series | R5 | Food colouring, 5–7 levels + blank | 3 per level | R², residuals, linear range per channel | R² > 0.99 up to A ≈ 1 | First pass W2 Fri; full W4 |
| T4 | **Limit of detection** | R6 | Blank ×10 + the lowest dilutions | 10 blanks | LOD = 3·SD(blank) ÷ slope (from T3/T7); LOQ = 10·SD ÷ slope | Report the value; compare with the lab instrument | W4 |
| T5 | **Drift:** same sample measured every 5 min for 1 h | R8 | One dye dilution | 12 points | Change in A over 1 h; LED drift (clear channel); correlation with temperature | < 1 % change over 1 h | W4 |
| T6 | **Benchmark against the lab spectrophotometer** | R9 | Dye series + 3 juices, same cuvettes on both instruments | 3 each | Lab spectrum **averaged over each channel's band (FWHM)** vs the AS7343 absorbance; R², mean difference ± uncertainty | R² > 0.95 | W3 |
| T7 | **Juice concentration calibration** (one series per juice) | **R2**, R5, R6 | Each juice: 0, 5, 10, 25, 50, 75, 100 % v/v | 3 per level | Calibration curve on the best channel(s); R², linear range, LOD; prediction error on held-out samples | Concentration within ±5 % (absolute) for clear juice; report the cloudy-juice error separately | W4 |
| T8 | **Juice-type classification** | **R1** | All juices × several dilutions (from T7) | 3 per point | PCA plot; kNN/LDA accuracy with k-fold cross-validation; confusion matrix. Train on spectra **normalised for overall intensity**, so the classifier uses spectral shape, not darkness | > 90 % accuracy across dilutions ≥ 25 % | W4 |
| T9 | **Scatter/turbidity:** TSL2591 at 90° and the 850 nm baseline | R2, R1 | Water, clear apple, cloudy apple, orange, pineapple | 3 each | 90° counts relative to water; A at 850 nm; does subtracting the 850 nm baseline improve T7 linearity for cloudy juices? | Clear vs cloudy separated; R² improves after correction | W3–W4 |
| T10 | **Freshness series**, room temperature vs fridge | R3 | Apple, orange, pineapple: one container of each at room temperature, one in the fridge | 3 per juice per day | A at F1/F2 (~405–425 nm) and scatter vs days | Monotonic trend at room temperature; slower trend in the fridge | Start Mon 23 Nov → W4 |
| T11 | **Fresh vs aged classification** | R3 | All T10 data | – | Cross-validated accuracy; days of storage needed before detection | > 80 % accuracy | W4 |
| T12 | **Usability workflow:** one button → dark → blank → sample → display + CSV | R10 | Water + one dye | 5 full runs | Runs completed without the laptop; CSV complete and correct; result understandable | 5/5 runs succeed | W3–W4 |
| T13 | **Liquid safety:** controlled spill of 1 mL of water into the cuvette well with the device unpowered; check cuvette removal | R11 | Water | 3 | Does liquid reach the electronics bay? Can the cuvette be removed without tipping? | No liquid in the bay; 3/3 clean removals | W3 (enclosure v2) |
| T14 | **Replication:** someone else builds or uses the device from the documentation alone | R10 | One dye sample | 3 | Did they get the result? Time taken; problems found | Result within the T2 spread | W5 |

## 6. Uncertainty budget (W4)
Sources, each quantified and then combined into the uncertainty on A and on concentration:
| Source | From |
|---|---|
| Dark noise | T1 |
| Repeatability / cuvette positioning | T2 |
| Drift (LED, temperature) | T5 |
| Calibration fit (slope, intercept) | T3/T7 |
| Pipetting / dilution error | Pipette spec or repeated weighing |
| Scattering (cloudy juices) | T9 |
| Finite bandwidth (wide channels) | T6, T7 (curvature at high A) |
→ Identify the **dominant** source; this ranks the improvements in the report.

## 7. Data handling
- Raw counts → `data/raw/YYYY-MM-DD_<test>.csv` (never edited by hand).
- Analysis scripts in `analysis/` produce absorbance, fits and figures → `analysis/figures/`.
- Each test gets a notebook entry: date, conditions, settings, anything unexpected.

## Change log
- v1 (16 Nov): first draft.
- v2 (16 Nov): added R1 juice type and R2 concentration (brief minimums), R11 safety; tests T7 (juice calibration), T8 (juice classification), T13 (liquid safety); bandwidth-averaged benchmark (T6); room-temperature vs fridge freshness (T10); requirement → test map; sample-preparation section; expanded uncertainty budget.
