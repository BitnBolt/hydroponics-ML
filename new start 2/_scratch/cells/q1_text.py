def md_table(headers, rows):
    out = ['| ' + ' | '.join(headers) + ' |', '|' + '|'.join(['---'] * len(headers)) + '|']
    return '\n'.join(out + ['| ' + ' | '.join(str(c) for c in r) + ' |' for r in rows])


def g3(v):  # compact significant-figure formatting
    return f'{v:.3g}' if abs(v) < 1000 else f'{v:,.0f}'


CT = {r['Quantity']: r for r in collection_table.to_dict('records')}
CI = {r['k']: r for r in ci_rows}
U = {k: CFG[k]['rmse_unit'] for k in CFG}
t, e, l = 'tds', 'ems_temp', 'lux'

# ---- Table 1: data collection ----
T1 = md_table(
    ['Quantity (node)', 'Onboard sensor vs. reference', 'Clock window', 'Duration', 'Paired samples n', 'Sampling', 'Reference range (SD)'],
    [[f"{r['Quantity']} ({r['Node']})", f"{r['Onboard sensor']} vs. {r['Reference']}", f"{r['Start']}-{r['End']}",
      f"{r['Duration (min)']:.1f} min" if r['Duration (min)'] < 60 else f"{r['Duration (min)']/60:.1f} h", r['n pairs'],
      f"{r['Sampling (s)']:.0f} s", (f"{r['Ref. min']:g}-{r['Ref. max']:g} (SD {r['Ref. SD']:.4g})" if r['Ref. span'] > 0 else f"constant {r['Ref. min']:g}")]
     for r in collection_table.to_dict('records')])

# ---- Table 2: evaluation protocols ----
def cell(k, proto):
    m = PROT[k][proto]; y = PROT[k]['y'] if proto != 'chrono' else PROT[k]['y'][PROT[k]['n_train']:]
    return f"{g3(m['RMSE'])} ({accuracy_pct(m['RMSE'], y):.1f} %)"

T2 = md_table(
    ['Quantity', 'In-sample (fit = test)', 'Blocked 5-fold CV (out-of-fold)', 'Chronological 70/30 hold-out', 'Leave-one-out (leaky)', 'R² in-sample', 'R² out-of-fold'],
    [[f"{NAME[k]} [{U[k]}]", cell(k, 'insample'), cell(k, 'blocked'), cell(k, 'chrono'), cell(k, 'loo'),
      f"{PROT[k]['insample']['R2']:.3f}", f"{PROT[k]['blocked']['R2']:.3f}"] for k in VALID_KEYS])

# ---- Table 3: parameter intervals ----
T3 = md_table(
    ['Quantity', 'Residual lag-1 autocorr.', 'n / n_eff', 'Slope 95% CI: classical', 'Slope 95% CI: block bootstrap', 'Intercept 95% CI: classical', 'Intercept 95% CI: block bootstrap'],
    [[NAME[k], f"{CI[k]['lag-1 autocorr. of residuals']:.2f}", f"{CI[k]['n']} / {CI[k]['n_eff (AR1)']:.0f}", CI[k]['Slope 95% CI classical'],
      CI[k]['Slope 95% CI block-bootstrap'], CI[k]['Intercept 95% CI classical'], CI[k]['Intercept 95% CI block-bootstrap']] for k in VALID_KEYS])

# ---- Table 4: accuracy ----
AC = {r['Quantity']: r for r in accuracy_table.to_dict('records')}
T4 = md_table(
    ['Quantity', 'Raw accuracy %', 'In-sample accuracy % (original)', 'Out-of-fold accuracy % (95% CI)', 'Out-of-fold span-accuracy %', 'Out-of-fold RMSE', 'Reading band ±1.96·RMSE'],
    [[NAME[k], f"{AC[NAME[k]]['Raw accuracy %']:.1f}", f"{AC[NAME[k]]['In-sample accuracy %']:.1f}",
      f"{AC[NAME[k]]['Out-of-fold accuracy % (vs mean)']:.1f} {AC[NAME[k]]['Out-of-fold accuracy 95% CI'].replace(', ', '–')}",
      f"{AC[NAME[k]]['Out-of-fold accuracy % (vs span)']:.1f}",
      f"{g3(AC[NAME[k]]['Out-of-fold RMSE'])} {U[k]}", f"±{g3(AC[NAME[k]]['Reading uncertainty +-1.96*RMSE (OOF)'])} {U[k]}"] for k in VALID_KEYS])

rho_lo = min(CI[k]['lag-1 autocorr. of residuals'] for k in VALID_KEYS); rho_hi = max(CI[k]['lag-1 autocorr. of residuals'] for k in VALID_KEYS)
w_lo = min(CI[k]['Slope CI width ratio (boot/classical)'] for k in VALID_KEYS); w_hi = max(CI[k]['Slope CI width ratio (boot/classical)'] for k in VALID_KEYS)
cov_lo = min(CI[k]['Empirical coverage of band (OOF) %'] for k in VALID_KEYS); cov_hi = max(CI[k]['Empirical coverage of band (OOF) %'] for k in VALID_KEYS)
ld = CT['Light']; td = CT['TDS']; ed = CT['Air temp.']; nd = CT['Nutrient temp.']

Q1_TEXT = f"""# Reviewer Comment 1 - Data collection, train/test procedure, confidence intervals and accuracy percentages

## 1.1 Data collection
Each onboard sensor was operated side-by-side with a reference instrument, and both were logged simultaneously at a fixed interval ({td['Sampling (s)']:.0f} s for the NFADS and EMS nodes, {ld['Sampling (s)']:.0f} s for the LMS node), giving time-stamped paired readings (sensor_i, reference_i). Four independent single-session experiments were performed (Table 1): TDS ({td['n pairs']} pairs, {td['Duration (min)']:.1f} min, reference ranging from {td['Ref. min']:g} to {td['Ref. max']:g} PPM), air temperature in the EMS node ({ed['n pairs']} pairs, {ed['Duration (min)']:.1f} min), nutrient temperature in the NFADS node ({nd['n pairs']} pairs, {nd['Duration (min)']:.1f} min) and light intensity in the LMS node ({ld['n pairs']} pairs over {ld['Duration (min)']/60:.1f} h, {ld['Start']}-{ld['End']}, reference range {ld['Ref. min']:g}-{ld['Ref. max']:g} lux). [Insert: reference-instrument models and manufacturer accuracy, probe/sensor placement, warm-up time, calendar date(s), and how paired timestamps were aligned.]

**Table 1. Data-collection summary.**

{T1}

## 1.2 Train/test (validation) procedure
The OLS calibration `reference = a * sensor + b` was originally fitted and scored on the same pairs (resubstitution). Such in-sample figures are optimistic, so all accuracy figures were re-computed with time-ordered validation, which is appropriate because consecutive samples are strongly autocorrelated (residual lag-1 autocorrelation {rho_lo:.2f}-{rho_hi:.2f}):

1. **Blocked 5-fold cross-validation (primary).** Each record was cut into five contiguous time blocks without shuffling; every block was predicted by a calibration line fitted only on the other four blocks, and RMSE, MAE, bias and R² were computed on the pooled out-of-fold predictions. Fold sizes were {int(np.ceil(td['n pairs']/K_FOLDS))}/{int(np.ceil(ed['n pairs']/K_FOLDS))}/{int(np.ceil(ld['n pairs']/K_FOLDS))} samples (TDS/EMS/Lux).
2. **Chronological 70/30 hold-out (secondary).** The first 70 % of the record trained the line and the last 30 % tested it (TDS {PROT[t]['n_train']}/{PROT[t]['n_test']}, EMS {PROT[e]['n_train']}/{PROT[e]['n_test']}, Lux {PROT[l]['n_train']}/{PROT[l]['n_test']}).
3. **Leave-one-out** is reported only as a contrast: it leaks information between neighbouring samples and under-estimates the error (TDS RMSE {PROT[t]['loo']['RMSE']:.1f} vs. {PROT[t]['blocked']['RMSE']:.1f} PPM with blocked CV).

**Table 2. Out-of-sample error of the same OLS model under different protocols** (RMSE in sensor units; accuracy % in brackets; chronological hold-out is scored on its own test segment).

{T2}

Out-of-sample error was higher than the in-sample error for every sensor (TDS {PROT[t]['insample']['RMSE']:.1f} -> {PROT[t]['blocked']['RMSE']:.1f} PPM, EMS {PROT[e]['insample']['RMSE']:.3f} -> {PROT[e]['blocked']['RMSE']:.3f} °C, Lux {PROT[l]['insample']['RMSE']:.0f} -> {PROT[l]['blocked']['RMSE']:.0f} lux), so the in-sample values are reported only for reference. For the EMS 30 % hold-out segment the reference was constant, so R² is undefined there (n/a).

## 1.3 Confidence intervals
* **Slope and intercept.** The original intervals were classical Student-t intervals, estimate ± t(0.975, n-2) * SE, with SE(intercept) = SE(slope) * sqrt(sum(x²)/n). They assume independent residuals, which does not hold here (Durbin-Watson {min(CI[k]['Durbin-Watson'] for k in VALID_KEYS):.2f}-{max(CI[k]['Durbin-Watson'] for k in VALID_KEYS):.2f}; effective sample size n_eff = n(1-ρ)/(1+ρ) is only {', '.join(f"{CI[k]['n_eff (AR1)']:.0f} of {CI[k]['n']}" for k in VALID_KEYS)} for TDS, EMS, Lux). We therefore also report **moving-block bootstrap** 95 % intervals (B = {N_BOOT}, paired blocks of length b = ceil(2n/n_eff) = {', '.join(str(CI[k]['Block length b']) for k in VALID_KEYS)} samples, 2.5th-97.5th percentiles). The classical slope intervals were too narrow by a factor of {w_lo:.1f}-{w_hi:.1f}; the block-bootstrap intervals are the ones that should be quoted (Table 3, Figure R2).
* **"Calibration interval" ±1.96·RMSE.** This is *not* a confidence interval for a parameter. It is a 95 % reading-uncertainty band for a single calibrated reading, assuming approximately normal, zero-mean errors. We now compute it from the out-of-fold RMSE; its empirical out-of-fold coverage was {cov_lo:.0f}-{cov_hi:.0f} %, confirming that it is adequate (slightly conservative).
* **Uncertainty of RMSE / accuracy %.** The 95 % CI of the out-of-fold RMSE was obtained by block-bootstrapping the out-of-fold squared errors (same b, B = {N_BOOT}) and transformed to accuracy % through the accuracy formula below.

**Table 3. Calibration parameters with classical vs. autocorrelation-aware 95 % intervals.**

{T3}

## 1.4 Accuracy percentages
Accuracy (%) = 100 * (1 - RMSE / mean(reference)), where the RMSE is the out-of-fold RMSE and the mean is that of the reference meter over the test. Because this ratio is dominated by the mean, it is nearly 100 % for temperature (mean ≈ 30 °C) even when the sensor barely follows the reference. We therefore also give the span-normalised accuracy 100 * (1 - RMSE / (max - min of reference)) and the absolute error in measurement units (Table 4).

**Table 4. Accuracy summary (headline = out-of-fold).**

{T4}

For the nutrient-temperature test the reference meter stayed at a constant {WATER['ref']:.1f} °C, so slope and intercept cannot be estimated and R² is undefined; the earlier "±0.00 °C after OLS" is a degenerate fit and has been withdrawn. The test is reported only as a fixed offset: the sensor read {WATER['bias']:.2f} °C relative to the meter (95 % CI ±{WATER['ci']:.3f} °C, n = {WATER['n']}; sensor SD {WATER['sd']:.3f} °C; MAE {WATER['mae']:.2f} °C).

## 1.5 Limitations (to be stated in the paper)
Each calibration comes from one session with one unit; three of the four records last under 11 minutes, and the EMS reference spans only {ed['Ref. span']:.1f} °C at 0.1 °C resolution, so the temperature response cannot be characterised. The lux reference (TSL2591) is itself a sensor, not a calibrated lux meter. The reported intervals therefore describe the repeatability of these specific sessions; multi-day, multi-unit validation over a wider range is required before claiming general accuracy.
"""
display(Markdown(Q1_TEXT))
