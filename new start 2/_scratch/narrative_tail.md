
---

## Accuracy % and ± calibration analysis (all sensors)

> **Note (added after reviewer response):** the tables below are the original **in-sample** results (OLS fitted and scored on the same data). Out-of-fold results, block-bootstrap intervals and the corrected water-temperature handling are in `review_response_paper_text.md` and in the "Reviewer response" sections of `main.ipynb`.

**Definitions**

- **Accuracy % (vs mean)** = `100 × (1 − RMSE / mean_meter)` — primary headline metric.
- **Accuracy % (vs span)** = `100 × (1 − RMSE / meter_span)` — tracks how well the sensor follows changes over the test window.
- **± Calibration interval** = `±1.96 × RMSE` (95% normal approximation, same as lux thesis section).
- **R²** = coefficient of determination vs reference meter.

### Table 1 — Accuracy % and ± calibration (raw vs OLS)

| Sensor | Phase | Accuracy % (vs mean) | Accuracy % (vs span) | R² | MAE | RMSE | ± Calibration (1.96×RMSE) |
|--------|-------|----------------------|----------------------|-----|-----|------|---------------------------|
| Lux | Raw | 66.1% | 86.7% | 0.784 | 2208 lux | 2661 lux | ±5214.7 lux |
| Lux | After OLS | 98.5% | 99.4% | 0.9996 | 101 lux | 120 lux | ±235.2 lux |
| TDS | Raw | 93.4% | 93.0% | 0.946 | 31.7 PPM | 41.6 PPM | ±81.5 PPM |
| TDS | After OLS | 96.3% | 96.1% | 0.983 | 20.9 PPM | 23.2 PPM | ±45.5 PPM |
| EMS air temp | Raw | 99.4%† | 7.3% | −5.18 | 0.18 °C | 0.19 °C | ±0.36 °C |
| EMS air temp | After OLS | 99.8%† | 73.2% | 0.485 | 0.044 °C | 0.054 °C | ±0.10 °C |
| Water temp | Raw | 97.8%‡ | N/A‡ | N/A | 0.68 °C | 0.68 °C | ±1.34 °C |
| Water temp | After OLS | ~100%§ | N/A | 0.000 | ~0 °C | ~0 °C | ±0.00 °C§ |

† High vs mean because mean ≈ 30–31 °C and absolute error in °C is small; use **vs span** for EMS.  
‡ Reference meter did not vary (fixed at 30.8 °C); span = 0.  
§ OLS collapses to constant 30.8 °C — not a valid calibration (logging issue).

### Table 2 — ± calibration change (before → after OLS)

| Sensor | ± interval before | ± interval after | Interval reduction | Accuracy % gain (vs mean) |
|--------|-------------------|------------------|--------------------|---------------------------|
| Lux | ±5214.7 lux | ±235.2 lux | 95.5% narrower | 66.1% → 98.5% (+32.4 pts) |
| TDS | ±81.5 PPM | ±45.5 PPM | 44.2% narrower | 93.4% → 96.3% (+2.9 pts) |
| EMS air temp | ±0.36 °C | ±0.10 °C | 71.1% narrower | 99.4% → 99.8% (+0.4 pts); span-acc. 7.3% → 73.2% |
| Water temp | ±1.34 °C | ±0.00 °C§ | misleading | invalid test |

### Table 3 — OLS model ± (95% CI on slope and intercept)

| Sensor | Calibrated equation | Slope (95% CI) | Intercept (95% CI) | Reading ± after OLS (1.96×RMSE) |
|--------|---------------------|----------------|--------------------|----------------------------------|
| Lux | 0.7947×raw − 143.72 | 0.7947 ± 0.0012 | −143.72 ± 14.75 | ±235.2 lux |
| TDS | 0.8810×raw + 52.85 | 0.8810 ± 0.0368 | +52.85 ± 25.12 | ±45.5 PPM |
| EMS air temp | 0.9215×raw + 2.56 | 0.9215 ± 0.2670 | +2.56 ± 8.09 | ±0.10 °C |
| Water temp | ~0×raw + 30.80 | ~0 ± 0 | 30.80 ± 0 | ±0.00 °C§ |

Reading ± is field error after calibration; coefficient ± describes stability of the fitted line only. (Slope/intercept intervals here are classical t-intervals; see the reviewer-response section for block-bootstrap intervals.)

### Table 4 — Ranked summary

| Criterion | Worst | Best |
|-----------|-------|------|
| Raw accuracy % (vs mean) | Lux (66.1%) | EMS air temp (99.4%†) |
| Raw ± calibration band | Lux (±5214.7 lux) | EMS air temp (±0.36 °C) |
| After OLS — lowest R² | EMS air temp (0.485) | Lux (0.9996) |
| After OLS — widest ± band | Lux (±235.2 lux) | EMS air temp (±0.10 °C) |
| After OLS — best overall | Lux / TDS | — |
| Invalid / do not use | Water temp (meter stuck at 30.8 °C) | — |

### Key insights

| Sensor | Accuracy & ± takeaway |
|--------|------------------------|
| **Lux** | Least accurate **raw** (66%); **OLS fixes it** (98.5%, ±235 lux). Deploy only with calibration. |
| **TDS** | Already strong raw (93%); OLS improves to 96% and ±46 PPM. |
| **EMS air temp** | Misleading 99% vs mean; only **73% vs span** after OLS — **weakest trustworthy fit** (R² = 0.49). |
| **Water temp** | ~0.68 °C fixed offset; meter never moved — **re-run validation** before reporting accuracy. |
