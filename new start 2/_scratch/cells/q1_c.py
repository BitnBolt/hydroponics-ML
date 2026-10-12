N_BOOT = 2000
SEED = 42


def acf(r, nlags=15):
    r = np.asarray(r, float) - np.mean(r)
    den = np.sum(r ** 2)
    return np.array([np.sum(r[:len(r) - l] * r[l:]) / den for l in range(nlags + 1)])


def block_bootstrap_ols(x, y, b, B=N_BOOT, seed=SEED):
    """Moving-block bootstrap of (sensor, reference) pairs -> B refits of (slope, intercept)."""
    rng = np.random.default_rng(seed); n = len(x); nb = int(np.ceil(n / b)); off = np.arange(b)
    out = np.empty((B, 2))
    for j in range(B):
        idx = (rng.integers(0, n - b + 1, nb)[:, None] + off).ravel()[:n]
        out[j] = np.polyfit(x[idx], y[idx], 1)
    return out


def block_bootstrap_rmse(err, b, B=N_BOOT, seed=SEED):
    rng = np.random.default_rng(seed); n = len(err); nb = int(np.ceil(n / b)); off = np.arange(b); e2 = err ** 2
    return np.array([np.sqrt(e2[(rng.integers(0, n - b + 1, nb)[:, None] + off).ravel()[:n]].mean()) for _ in range(B)])


ci_rows = []
for k in VALID_KEYS:
    P = PROT[k]; x, y, n = P['x'], P['y'], P['n']
    ols = ols_calibration(x, y)                         # classical (t-based) CI from the original notebook
    resid = y - (ols['slope'] * x + ols['intercept'])
    rho = acf(resid, 1)[1]
    dw = np.sum(np.diff(resid) ** 2) / np.sum(resid ** 2)
    n_eff = n * (1 - rho) / (1 + rho)
    b = int(min(max(np.ceil(2 * n / n_eff), 3), n // 4))
    bs = block_bootstrap_ols(x, y, b)
    s_lo, s_hi = np.percentile(bs[:, 0], [2.5, 97.5]); i_lo, i_hi = np.percentile(bs[:, 1], [2.5, 97.5])

    oof_err = P['oof'] - y
    rm_b = block_bootstrap_rmse(oof_err, b); rm_lo, rm_hi = np.percentile(rm_b, [2.5, 97.5])
    rmse_oof = P['blocked']['RMSE']
    band = 1.96 * rmse_oof
    ci_rows.append({
        'k': k, 'Quantity': NAME[k], 'n': n, 'lag-1 autocorr. of residuals': rho, 'Durbin-Watson': dw,
        'n_eff (AR1)': n_eff, 'Block length b': b,
        'Slope (OLS)': ols['slope'], 'Slope 95% CI classical': f"[{ols['slope_ci_lo']:.4f}, {ols['slope_ci_hi']:.4f}]",
        'Slope 95% CI block-bootstrap': f'[{s_lo:.4f}, {s_hi:.4f}]',
        'Slope CI width ratio (boot/classical)': (s_hi - s_lo) / (ols['slope_ci_hi'] - ols['slope_ci_lo']),
        'Intercept (OLS)': ols['intercept'],
        'Intercept 95% CI classical': f"[{ols['intercept_ci_lo']:.3f}, {ols['intercept_ci_hi']:.3f}]",
        'Intercept 95% CI block-bootstrap': f'[{i_lo:.3f}, {i_hi:.3f}]',
        'Intercept CI width ratio (boot/classical)': (i_hi - i_lo) / (ols['intercept_ci_hi'] - ols['intercept_ci_lo']),
        'OOF RMSE': rmse_oof, 'OOF RMSE 95% CI (block-boot)': f'[{rm_lo:.4g}, {rm_hi:.4g}]',
        '+-1.96*RMSE band (OOF)': band,
        'Empirical coverage of band (OOF) %': 100 * np.mean(np.abs(oof_err) <= band),
        'Empirical 95th pct |error| (OOF)': np.percentile(np.abs(oof_err), 95),
        '_rm_lo': rm_lo, '_rm_hi': rm_hi, '_bs': bs, '_ols': ols, '_resid': resid, '_ci': (s_lo, s_hi, i_lo, i_hi),
    })
    PROT[k].update(rho=rho, n_eff=n_eff, b=b, resid=resid)

ci_table = pd.DataFrame(ci_rows)
public_cols = [c for c in ci_table.columns if not c.startswith('_') and c != 'k']
ci_table[public_cols].to_csv('review_q1_confidence_intervals.csv', index=False)
print('TABLE R1-C  Classical (iid) vs autocorrelation-aware (moving-block bootstrap) 95% intervals')
display(ci_table[public_cols].round(4).T)

# ---- Figure R2: autocorrelation + bootstrap distributions ----------------------------------------
fig, axes = plt.subplots(2, len(VALID_KEYS), figsize=(4.6 * len(VALID_KEYS), 7.2))
for j, r in enumerate(ci_rows):
    k = r['k']; n = r['n']
    ax = axes[0, j]; a = acf(r['_resid'], 15)
    ax.bar(range(len(a)), a, color='#2471A3', width=0.6)
    ax.axhspan(-1.96 / np.sqrt(n), 1.96 / np.sqrt(n), color='#E67E22', alpha=0.3, label='iid 95% band')
    ax.set_ylim(-0.4, 1.05); ax.set_xlabel('lag (samples)'); ax.set_ylabel('ACF of OLS residuals')
    ax.set_title(f"{NAME[k]}: lag-1 r = {r['lag-1 autocorr. of residuals']:.2f}, n_eff ~ {r['n_eff (AR1)']:.0f} of {n}", fontsize=9)
    ax.legend(fontsize=8)
    ax = axes[1, j]; ols = r['_ols']
    ax.hist(r['_bs'][:, 0], bins=40, color='#95a5a6', alpha=0.85)
    ax.axvline(ols['slope'], color='k', lw=1.2, label='OLS slope')
    ax.axvspan(ols['slope_ci_lo'], ols['slope_ci_hi'], color='#E67E22', alpha=0.35, label='classical 95% CI')
    ax.axvline(r['_ci'][0], color='#1E8449', ls='--'); ax.axvline(r['_ci'][1], color='#1E8449', ls='--', label='block-bootstrap 95% CI')
    ax.set_xlabel('slope'); ax.set_ylabel('bootstrap count'); ax.legend(fontsize=7)
    ax.set_title(f"{NAME[k]}: slope CI width x{r['Slope CI width ratio (boot/classical)']:.1f}", fontsize=9)
fig.tight_layout(); fig.savefig(FIG_DIR / 'review_q1_ci_autocorrelation.png', dpi=200, bbox_inches='tight'); plt.show()
