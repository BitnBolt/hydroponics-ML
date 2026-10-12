E = DEC['ems_temp']; T_ = DEC['tds']; L_ = DEC['lux']
pe = PROT['ems_temp']
mse_e = E['MSE']
sd_ill = 2.0                                           # illustrative reference SD (deg C) for a wider temperature sweep
r2_ill = 1 - mse_e / sd_ill ** 2
sd_break = float(np.sqrt(mse_e))                       # reference SD at which the same absolute error gives R2 = 0

T5 = md_table(
    ['Quantity', 'Reference SD', 'Sensor bias', '|bias| / ref. SD', 'SSE / SST', 'r² (+)', 'scale (−)', 'bias (−)', 'Raw R²'],
    [[NAME[k], f"{DEC[k]['ref_sd']:.4g} {U[k]}", f"{DEC[k]['bias']:+.4g} {U[k]}", f"{DEC[k]['bias_over_sd']:.2f}", f"{DEC[k]['SSE']/DEC[k]['SST']:.3f}",
      f"{DEC[k]['corr_term']:.3f}", f"{DEC[k]['scale_term']:.3f}", f"{DEC[k]['bias_term']:.3f}", f"{DEC[k]['R2']:.3f}"] for k in ['tds', 'lux', 'ems_temp']])

Q2_TEXT = f"""# Reviewer Comment 2 - Why the pre-calibration air-temperature R² is negative

## 2.1 Explanation (paper-ready)
The negative value (raw R² = {E['R2']:.2f}, EMS air temperature) is a property of the metric, not a computational error. R² = 1 - SSE/SST compares the sensor with a trivial baseline that always outputs the mean of the reference; it is negative whenever the sensor's squared error SSE exceeds the squared spread SST of the reference around its own mean. In the EMS test the reference stayed within {ed['Ref. min']:g}-{ed['Ref. max']:g} °C (SD = {E['ref_sd']:.3f} °C, SST = {E['SST']:.3f} °C²), whereas the uncalibrated sensor read a nearly constant {abs(E['bias']):.3f} °C *below* the reference (SSE = {E['SSE']:.3f} °C²). Hence SSE/SST = {E['SSE']/E['SST']:.2f} and R² = 1 - {E['SSE']/E['SST']:.2f} = {E['R2']:.2f}.

The result follows exactly from the identity

R² = r² - (r - s_sensor/s_ref)² - (bias/s_ref)²,

where r is the Pearson correlation, s the standard deviations and bias = mean(sensor) - mean(reference). For the EMS data: r² = {E['corr_term']:.3f} (correlation is positive), scale-mismatch term = {E['scale_term']:.3f} (negligible, s_sensor/s_ref = {E['sensor_sd']/E['ref_sd']:.2f}), bias term = ({E['bias']:.3f}/{E['ref_sd']:.3f})² = {E['bias_term']:.2f}, which accounts for {100*E['bias_share_of_MSE']:.0f} % of the mean-square error. Because r² ≤ 1, R² ≤ 1 - (bias/s_ref)²: **any offset larger than the spread of the reference makes R² negative, however small the offset is in absolute terms** (Figure R3c). TDS and light do not show this because their reference spread (SD {T_['ref_sd']:.0f} PPM, {L_['ref_sd']:.0f} lux) is large relative to their bias (|bias|/SD = {T_['bias_over_sd']:.2f} and {L_['bias_over_sd']:.2f} versus {E['bias_over_sd']:.2f} for air temperature), so their raw R² stays positive ({T_['R2']:.3f}, {L_['R2']:.3f}) (Table 5).

**Table 5. Decomposition of raw R² (R² = r² − scale − bias).**

{T5}

## 2.2 What this does and does not say about the sensor
* **The offset is physically small.** The raw RMSE is {E['MSE']**0.5:.2f} °C and the bias {E['bias']:.2f} °C ({100*abs(E['bias'])/E['ref_mean']:.2f} % of the reading). The Bland-Altman 95 % limits of agreement for the raw sensor are [{LOA['lo']:.2f}, {LOA['hi']:.2f}] °C. The sensor is *consistently low*, not noisy: the SD of the difference is only {LOA['sd']:.3f} °C.
* **The "improvement" after calibration is almost entirely offset removal.** OLS forces the mean error to zero, so the in-sample R² becomes r² = {pe['insample']['R2']:.3f} (from {E['R2']:.2f}) while the correlation itself is unchanged (r = {E['r']:.3f}). The in-sample value is optimistic: out-of-fold R² is {pe['blocked']['R2']:.2f}.
* **The modest correlation is largely a resolution effect.** Both devices log in {QUANT['q_ref']:.1f} °C steps (only {QUANT['distinct_ref']} distinct reference values over a {ed['Ref. span']:.1f} °C span). Rounding noise (SD ≈ {QUANT['sd_q']:.3f} °C, q/√12) equals about {100*QUANT['share_ref']:.0f} % of the reference variance and {100*QUANT['share_sen']:.0f} % of the sensor variance, which caps the attainable correlation at about r ≈ {QUANT['r_max']:.2f} (R² ≈ {QUANT['r2_max']:.2f}) even for a perfect sensor.
* **R² is therefore the wrong headline metric for this test.** With the same absolute error (MSE = {mse_e:.4f} °C²) R² would exceed {r2_ill:.2f} if the reference SD were {sd_ill:.0f} °C (a wider temperature sweep), and would be 0 at an SD of only {sd_break:.2f} °C.

## 2.3 Recommended wording for the manuscript
> Prior to calibration, the EMS air-temperature sensor showed a negative coefficient of determination (R² = {E['R2']:.2f}). This is a consequence of the narrow reference range during the test ({ed['Ref. min']:g}-{ed['Ref. max']:g} °C, SD = {E['ref_sd']:.3f} °C) combined with a systematic offset of {E['bias']:.2f} °C: R² benchmarks the sensor against the reference mean, and the squared offset ({E['bias']**2:.4f} °C²) was {E['bias']**2/E['ref_sd']**2:.1f} times the reference variance ({E['ref_sd']**2:.4f} °C²). The sensor tracked the reference direction (r = {E['r']:.2f}) with low scatter (SD of differences {LOA['sd']:.3f} °C), and OLS calibration removed the offset (bias {E['bias']:.2f} → 0 °C; RMSE {E['MSE']**0.5:.3f} → {pe['insample']['RMSE']:.3f} °C in-sample, {pe['blocked']['RMSE']:.3f} °C out-of-fold). For near-constant temperature we therefore report bias, MAE, RMSE and Bland-Altman limits of agreement rather than R², and we note that the R² of {pe['insample']['R2']:.2f} after calibration (out-of-fold {pe['blocked']['R2']:.2f}) is limited by the 0.1 °C resolution and 0.2 °C span of the test; validation over a wider temperature range is left for future work.
"""
display(Markdown(Q2_TEXT))

full = ('# Reviewer response - paper-ready text (auto-generated by main.ipynb)\n\n'
        'Figures: figures/review_q1_blocked_cv.png, figures/review_q1_ci_autocorrelation.png, figures/review_q2_negative_r2.png\n\n'
        + Q1_TEXT + '\n\n---\n\n' + Q2_TEXT)
Path('review_response_paper_text.md').write_text(full, encoding='utf-8')
print('Saved:', Path('review_response_paper_text.md').resolve())
