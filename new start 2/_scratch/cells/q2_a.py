# R2 = 1 - SSE/SST  =  r^2 - (r - s_sensor/s_ref)^2 - (bias/s_ref)^2      (exact identity, population SDs)
def r2_decomposition(sensor, ref):
    s, y = np.asarray(sensor, float), np.asarray(ref, float)
    sd_s, sd_y = s.std(ddof=0), y.std(ddof=0)
    if sd_y < 1e-12:
        return None
    r = np.corrcoef(s, y)[0, 1]; bias = s.mean() - y.mean(); k_ratio = sd_s / sd_y
    sse, sst = np.sum((s - y) ** 2), np.sum((y - y.mean()) ** 2)
    corr_term, scale_term, bias_term = r ** 2, (r - k_ratio) ** 2, (bias / sd_y) ** 2
    return dict(n=len(s), ref_mean=y.mean(), ref_sd=sd_y, sensor_sd=sd_s, r=r, bias=bias,
                SST=sst, SSE=sse, MSE=sse / len(s), R2=1 - sse / sst,
                corr_term=corr_term, scale_term=scale_term, bias_term=bias_term,
                R2_identity=corr_term - scale_term - bias_term, bias_over_sd=abs(bias) / sd_y,
                bias_share_of_MSE=bias ** 2 / (sse / len(s)))


dec_rows = []
DEC = {}
for cfg in PLOT_CONFIGS:
    k = cfg['key']; d = datasets[k]; dec = r2_decomposition(d['sensor'], d['meter'])
    if dec is None:
        dec_rows.append({'Quantity': NAME[k], 'n': len(d), 'Ref. SD': 0.0, 'R2 (raw)': float('nan')}); continue
    dec_rows.append({
        'Quantity': NAME[k], 'n': dec['n'], 'Unit': cfg['rmse_unit'], 'Ref. mean': dec['ref_mean'], 'Ref. SD': dec['ref_sd'],
        'Sensor SD': dec['sensor_sd'], 'Pearson r': dec['r'], 'Bias (sensor-ref)': dec['bias'],
        'SST = sum(ref-mean)^2': dec['SST'], 'SSE = sum(sensor-ref)^2': dec['SSE'], 'SSE/SST': dec['SSE'] / dec['SST'],
        'R2 (raw)': dec['R2'], 'r^2 (+)': dec['corr_term'], 'scale term (-)': dec['scale_term'], 'bias term (-)': dec['bias_term'],
        'R2 via identity': dec['R2_identity'], '|bias|/Ref.SD': dec['bias_over_sd'], 'Bias share of MSE %': 100 * dec['bias_share_of_MSE'],
    })
    DEC[k] = dec
dec_table = pd.DataFrame(dec_rows)
dec_table.to_csv('review_q2_r2_decomposition.csv', index=False)
print('TABLE R2-A  Why raw R2 goes negative: exact decomposition  R2 = r^2 - (r - s_sensor/s_ref)^2 - (bias/s_ref)^2')
display(dec_table.round(4).T)

# --- Is the weak correlation (r ~ 0.70) partly a resolution artefact?  (Sheppard-type quantisation noise)
E = DEC['ems_temp']; ye, xe = datasets['ems_temp']['meter'].to_numpy(float), datasets['ems_temp']['sensor'].to_numpy(float)
q_ref, q_sen = resolution(ye), resolution(xe)
var_q_ref, var_q_sen = q_ref ** 2 / 12, q_sen ** 2 / 12          # variance of rounding error of a uniform quantiser
rel_ref, rel_sen = 1 - var_q_ref / ye.var(), 1 - var_q_sen / xe.var()
r_max = float(np.sqrt(rel_ref * rel_sen))
QUANT = dict(q_ref=q_ref, q_sen=q_sen, sd_q=float(np.sqrt(var_q_ref)), rel_ref=rel_ref, rel_sen=rel_sen, r_max=r_max, r2_max=r_max ** 2,
             share_ref=var_q_ref / ye.var(), share_sen=var_q_sen / xe.var(), distinct_ref=int(np.unique(ye).size), distinct_sen=int(np.unique(xe).size))
print(f"\nEMS quantisation: reference & sensor both log in {q_ref:.1f} C steps -> only {QUANT['distinct_ref']} (ref) / {QUANT['distinct_sen']} (sensor) distinct values.")
print(f"  rounding noise SD = {QUANT['sd_q']:.4f} C = {100*QUANT['share_ref']:.1f}% of reference variance ({100*QUANT['share_sen']:.1f}% of sensor variance)")
print(f"  => attainable r <= ~{r_max:.2f}, attainable R2 after calibration <= ~{r_max**2:.2f}   (observed r = {E['r']:.3f}, in-sample R2 = {E['r']**2:.3f})")

# --- Figure R3 --------------------------------------------------------------------------------------
dE = datasets['ems_temp']; tE = dE['time']
fig, ax = plt.subplots(2, 2, figsize=(13, 9.2))

a = ax[0, 0]
a.plot(tE, dE['sensor'], color='#E67E22', marker='o', ms=3.5, lw=1.2, label=f"Raw sensor (mean {E['ref_mean'] + E['bias']:.3f} C)")
a.plot(tE, dE['meter'], color='#2471A3', marker='s', ms=3.5, lw=1.2, ls='--', label=f"Reference (mean {E['ref_mean']:.3f} C)")
a.axhline(E['ref_mean'], color='#2471A3', lw=0.8, alpha=0.6)
a.axhspan(E['ref_mean'] - E['ref_sd'], E['ref_mean'] + E['ref_sd'], color='#2471A3', alpha=0.12, label=f"Reference +-1 SD (= {E['ref_sd']:.3f} C)")
a.annotate('', xy=(tE.iloc[-8], E['ref_mean']), xytext=(tE.iloc[-8], E['ref_mean'] + E['bias']),
           arrowprops=dict(arrowstyle='<->', color='crimson'))
a.text(tE.iloc[-7], E['ref_mean'] + E['bias'] / 2, f"offset\n{E['bias']:+.3f} C", color='crimson', fontsize=9, va='center')
a.set_title('(a) Reference barely moves; sensor sits ~2.4 reference-SDs below it', fontsize=10)
a.set_ylabel('Air temperature (C)'); a.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S')); a.legend(fontsize=8)

a = ax[0, 1]
steps = [('r$^2$\n(correlation)', E['corr_term']), ('scale\nmismatch', -E['scale_term']), ('constant\noffset (bias)', -E['bias_term'])]
cum = 0.0
for j, (lab, v) in enumerate(steps):
    a.bar(j, v, bottom=cum, color='#1E8449' if v > 0 else '#C0392B', width=0.6); a.text(j, cum + v + (0.15 if v > 0 else -0.35), f'{v:+.3f}', ha='center', fontsize=9)
    cum += v
a.bar(len(steps), cum, color='#34495e', width=0.6); a.text(len(steps), cum - 0.4, f'R$^2$ = {cum:.3f}', ha='center', fontsize=10, color='#34495e')
a.axhline(0, color='k', lw=0.8); a.set_xticks(range(len(steps) + 1)); a.set_xticklabels([s[0] for s in steps] + ['raw R$^2$'])
a.set_title(f"(b) R$^2$ = r$^2$ - (r - s$_{{sensor}}$/s$_{{ref}}$)$^2$ - (bias/s$_{{ref}}$)$^2$  [bias term = {100*E['bias_share_of_MSE']:.0f}% of MSE]", fontsize=10)
a.set_ylabel('contribution to R$^2$'); a.set_ylim(cum - 1.0, 1.4)

a = ax[1, 0]
xr = np.linspace(0, 3, 300)
a.plot(xr, 1 - xr ** 2, color='k', lw=1.5, label='ceiling: R$^2$ <= 1 - (bias/s$_{ref}$)$^2$')
a.axhline(0, color='grey', lw=0.8); a.axvline(1, color='grey', lw=0.8, ls=':')
for k, col, mk in [('tds', '#2471A3', 'o'), ('lux', '#E67E22', 's'), ('ems_temp', '#C0392B', 'D')]:
    a.scatter(DEC[k]['bias_over_sd'], DEC[k]['R2'], s=90, color=col, marker=mk, zorder=5,
              label=f"{NAME[k]}: |bias|/s$_{{ref}}$ = {DEC[k]['bias_over_sd']:.2f}, R$^2$ = {DEC[k]['R2']:.2f}")
a.set_xlabel('|bias| / SD of reference  (how large the offset is relative to the signal that R$^2$ must explain)')
a.set_ylabel('raw R$^2$'); a.set_ylim(-6, 1.2); a.set_xlim(0, 3)
a.set_title('(c) Any offset larger than the reference spread forces R$^2$ < 0', fontsize=10); a.legend(fontsize=8, loc='lower left')

a = ax[1, 1]
ols_e = PROT['ems_temp']['line']; cal_e = ols_e[0] * dE['sensor'].to_numpy(float) + ols_e[1]
ref_e = dE['meter'].to_numpy(float)
for vals, col, lab in [(dE['sensor'].to_numpy(float), '#E67E22', f"raw: bias {E['bias']:+.3f}"), (cal_e, '#1E8449', 'after OLS: bias 0')]:
    mean_ab, diff_ab = (vals + ref_e) / 2, vals - ref_e
    jitter = np.random.default_rng(0).uniform(-0.004, 0.004, len(diff_ab))
    a.scatter(mean_ab, diff_ab + (jitter if col == '#E67E22' else 0), s=22, color=col, alpha=0.8, label=lab)
    sd_d = diff_ab.std(ddof=1); a.axhline(diff_ab.mean(), color=col, lw=1.2)
    a.axhline(diff_ab.mean() + 1.96 * sd_d, color=col, lw=0.8, ls='--'); a.axhline(diff_ab.mean() - 1.96 * sd_d, color=col, lw=0.8, ls='--')
a.set_xlabel('mean of sensor and reference (C)'); a.set_ylabel('sensor - reference (C)')
a.set_title(f"(d) Bland-Altman: after OLS R$^2$ = {PROT['ems_temp']['insample']['R2']:.2f} (in-sample), "
            f"{PROT['ems_temp']['blocked']['R2']:.2f} (out-of-fold)", fontsize=10); a.legend(fontsize=8)
fig.suptitle('Why the pre-calibration air-temperature R$^2$ is negative (EMS node)', y=1.0, fontsize=12)
fig.tight_layout(); fig.savefig(FIG_DIR / 'review_q2_negative_r2.png', dpi=200, bbox_inches='tight'); plt.show()

# Bland-Altman limits of agreement (raw), a unit-bearing alternative to R2 for near-constant temperatures
d_raw = xe - ye
LOA = dict(bias=float(d_raw.mean()), sd=float(d_raw.std(ddof=1)))
LOA['lo'], LOA['hi'] = LOA['bias'] - 1.96 * LOA['sd'], LOA['bias'] + 1.96 * LOA['sd']
print(f"Bland-Altman (raw EMS air temp): bias = {LOA['bias']:.3f} C, 95% limits of agreement [{LOA['lo']:.3f}, {LOA['hi']:.3f}] C")
