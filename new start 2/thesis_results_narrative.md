# Sensor validation — thesis-style narrative

Calibration interval: ±1.96×RMSE (95% normal approximation, same as reference lux section).

## Tds (TDS (PPM))

Tds values were measured over a 7-minute window using TDS Sensor as the onboard sensor and TDS Meter as the reference meter in the NFADS node, as seen in Figure 12. The basic raw data generated showed that the MAE, RMSE and R² values were 31.67 PPM, 41.58 PPM and 0.9460 respectively. The graph has been plotted between sensor data, meter data and progressive RMSE value for a given time interval as shown in Figure 14a. On applying Ordinary Least Squares (OLS) linear regression model (Estimated TDS (PPM) = 0.8810 x (Raw Sensor Reading) + 52.8537), the calibration interval dropped from ±81.50 PPM to ±45.47 PPM.

## Water Temp (Nutrient Temperature (°C))

Nutrient temperature values were measured over a 10-minute window using Water Temperature Sensor as the onboard sensor and Temperature Meter as the reference meter in the NFADS node, as seen in Figure 13. The basic raw data generated showed that the MAE, RMSE and R² values were 0.68 °C, 0.68 °C and not applicable (low variance in reference) respectively. The graph has been plotted between sensor data, meter data and progressive RMSE value for a given time interval as shown in Figure 14b. On applying Ordinary Least Squares (OLS) linear regression model (Estimated Fluid Temperature (°C) = 0.0000 x (Raw Sensor Reading) + 30.8000), the calibration interval dropped from ±1.34 °C to ±0.00 °C.

## Ems Temp (Air Temperature (°C))

Air temperature values were measured over a 9-minute window using Environment Temperature Sensor as the onboard sensor and Temperature Meter as the reference meter in the EMS node, as seen in Figure 14. The basic raw data generated showed that the MAE, RMSE and R² values were 0.18 °C, 0.19 °C and -5.1754 respectively. The graph has been plotted between sensor data, meter data and progressive RMSE value for a given time interval as shown in Figure 16a. On applying Ordinary Least Squares (OLS) linear regression model (Estimated Air Temperature (°C) = 0.9215 x (Raw Sensor Reading) + 2.5556), the calibration interval dropped from ±0.36 °C to ±0.10 °C.

## Lux (Light Intensity (Lux))

Lux values were measured over a 12-hour daytime window using BH1750 as the lux sensor and TSL2591 as the lux meter in the LMS node, as seen in Figure 15. The basic raw data generated showed that the MAE, RMSE and R² values were 2207.98 Lux, 2660.56 Lux and 0.7842 respectively. The graph has been plotted between sensor data, meter data and progressive RMSE value for a given time interval as shown in Figure 17a. On applying Ordinary Least Squares (OLS) linear regression model (Estimated Light Intensity (Lux) = 0.7947 x (Raw Sensor Reading) - 143.7244), the calibration interval dropped from ±5214.69 Lux to ±235.18 Lux.

---

## Accuracy % and ± calibration analysis (all sensors)

**Definitions**

- **Accuracy % (vs mean)** = `100 × (1 − RMSE / mean_meter)` — primary headline metric.
- **Accuracy % (vs span)** = `100 × (1 − RMSE / meter_span)` — tracks how well the sensor follows changes over the test window.
- **± Calibration interval** = `±1.96 × RMSE` (95% normal approximation; same as lux thesis section).
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
| Water temp | Raw | 97.8%† | N/A‡ | N/A | 0.68 °C | 0.68 °C | ±1.34 °C |
| Water temp | After OLS | ~100%§ | N/A | 0.000 | ~0 °C | ~0 °C | ±0.00 °C§ |

† High vs mean because mean ≈ 29–31 °C and absolute error is small in °C; use **vs span** for EMS.  
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

Reading ± is field error after calibration; coefficient ± describes stability of the fitted line only.

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
