# Headline accuracy table: original in-sample vs out-of-sample, with 95% CI on the accuracy %
acc_rows = []
for r in ci_rows:
    k = r['k']; P = PROT[k]; y = P['y']; ref_mean = float(np.mean(y)); ref_span = float(y.max() - y.min())
    ins, blk = P['insample'], P['blocked']
    raw = metrics(P['x'], y)
    acc_lo, acc_hi = accuracy_pct(r['_rm_hi'], y), accuracy_pct(r['_rm_lo'], y)   # RMSE up -> accuracy down
    acc_rows.append({
        'Quantity': NAME[k], 'Unit': CFG[k]['rmse_unit'], 'Ref. mean': ref_mean,
        'Raw RMSE': raw['RMSE'], 'Raw accuracy %': accuracy_pct(raw['RMSE'], y),
        'In-sample RMSE': ins['RMSE'], 'In-sample accuracy %': accuracy_pct(ins['RMSE'], y),
        'Out-of-fold RMSE': blk['RMSE'], 'Out-of-fold accuracy % (vs mean)': accuracy_pct(blk['RMSE'], y),
        'Out-of-fold accuracy 95% CI': f'[{acc_lo:.2f}, {acc_hi:.2f}]',
        'Out-of-fold accuracy % (vs span)': span_accuracy_pct(blk['RMSE'], y),
        'Out-of-fold R2': blk['R2'], 'Reading uncertainty +-1.96*RMSE (OOF)': 1.96 * blk['RMSE'],
    })
accuracy_table = pd.DataFrame(acc_rows)
accuracy_table.to_csv('review_q1_accuracy_summary.csv', index=False)
print('TABLE R1-D  Accuracy % : in-sample (original) vs out-of-fold (honest) with block-bootstrap 95% CI')
display(accuracy_table.round(3))

# Nutrient-temperature test: reference was a constant 30.8 -> only a fixed-offset check is possible
dw_ = datasets['water_temp']; wx, wy = dw_['sensor'].to_numpy(float), dw_['meter'].to_numpy(float)
w_bias = float(np.mean(wx - wy)); w_sd = float(np.std(wx - wy, ddof=1)); w_n = len(wx)
w_ci = stats.t.ppf(0.975, w_n - 1) * w_sd / np.sqrt(w_n)
WATER = dict(n=w_n, bias=w_bias, sd=w_sd, ci=w_ci, mae=float(np.mean(np.abs(wx - wy))), rmse=float(np.sqrt(np.mean((wx - wy) ** 2))),
             ref=float(wy.mean()), sensor_min=float(wx.min()), sensor_max=float(wx.max()),
             acc=accuracy_pct(float(np.sqrt(np.mean((wx - wy) ** 2))), wy))
print(f"\nNutrient temperature: reference constant at {WATER['ref']:.1f} C (SD = {wy.std():.1e}) -> OLS slope/intercept are NOT identifiable.")
print(f"  Reportable only as a single-point offset: bias = {w_bias:.3f} C (95% CI +-{w_ci:.3f}, t-based), "
      f"MAE = {WATER['mae']:.3f} C, sensor SD = {w_sd:.3f} C, accuracy vs mean = {WATER['acc']:.1f} %")
print("  The earlier '+-0.00 C after OLS' is a degenerate fit (line forced through a constant) and must NOT be quoted.")
