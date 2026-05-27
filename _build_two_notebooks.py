"""Build 01_statistical_validation.ipynb and 02_methodological_innovation.ipynb."""
import json
from pathlib import Path

def md(*lines):
    return {"cell_type": "markdown", "metadata": {}, "source": [l + "\n" for l in lines]}

def code(*lines):
    return {"cell_type": "code", "metadata": {}, "outputs": [], "execution_count": None,
            "source": [l + "\n" for l in lines]}

def nb(cells, name):
    return {
        "nbformat": 4, "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.10.0"},
        },
        "cells": cells,
    }

# ---------- shared setup snippet ----------
SETUP = [
    "from pathlib import Path",
    "import warnings; warnings.filterwarnings('ignore')",
    "import numpy as np",
    "import pandas as pd",
    "import matplotlib.pyplot as plt",
    "import seaborn as sns",
    "from scipy import stats",
    "from sklearn.model_selection import TimeSeriesSplit",
    "from sklearn.preprocessing import StandardScaler",
    "from sklearn.linear_model import Ridge",
    "from sklearn.svm import SVR",
    "from sklearn.neural_network import MLPRegressor",
    "from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier",
    "from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score",
    "from sklearn.metrics import accuracy_score, f1_score, confusion_matrix, classification_report",
    "",
    "try:",
    "    from IPython.display import display",
    "except ImportError:",
    "    display = print",
    "",
    "DATA_DIR = Path('.')",
    "FIG_DIR = DATA_DIR / 'figures'",
    "FIG_DIR.mkdir(exist_ok=True)",
    "RANDOM_STATE = 42",
    "np.random.seed(RANDOM_STATE)",
    "sns.set_theme(style='whitegrid')",
]

LOAD_DATA = [
    "def load_nfads():",
    "    cols = ['ec','tds','ph','waterTemp','createdAt','peristalticPumpA','peristalticPumpB',",
    "            'peristalticPumpPhup','peristalticPumpPhdown']",
    "    chunks = [c for c in pd.read_csv(DATA_DIR/'test.nfads.csv', usecols=cols, chunksize=50_000)]",
    "    df = pd.concat(chunks, ignore_index=True)",
    "    df['createdAt'] = pd.to_datetime(df['createdAt'], utc=True)",
    "    for c in ['ec','tds','ph','waterTemp']: df[c] = pd.to_numeric(df[c], errors='coerce')",
    "    for c in ['peristalticPumpA','peristalticPumpB','peristalticPumpPhup','peristalticPumpPhdown']:",
    "        df[c] = df[c].astype(str).str.lower().eq('true')",
    "    df['pump_any'] = df[['peristalticPumpA','peristalticPumpB','peristalticPumpPhup','peristalticPumpPhdown']].any(axis=1)",
    "    return df.sort_values('createdAt')",
    "",
    "def load_ems():",
    "    cols = ['dht22Temp','dht22Moisture','oxygen','pressure','createdAt']",
    "    df = pd.read_csv(DATA_DIR/'test.ems.csv', usecols=cols)",
    "    df['createdAt'] = pd.to_datetime(df['createdAt'], utc=True)",
    "    for c in ['dht22Temp','dht22Moisture','oxygen','pressure']:",
    "        df[c] = pd.to_numeric(df[c], errors='coerce')",
    "    return df.sort_values('createdAt')",
    "",
    "def load_lms():",
    "    cols = ['bh1750','ldr','tsl2591','createdAt']",
    "    df = pd.read_csv(DATA_DIR/'test.lms.csv', usecols=cols)",
    "    df['createdAt'] = pd.to_datetime(df['createdAt'], utc=True)",
    "    for c in ['bh1750','ldr','tsl2591']: df[c] = pd.to_numeric(df[c], errors='coerce')",
    "    return df.sort_values('createdAt')",
    "",
    "def merge_hourly(nf, ems, lms):",
    "    nf = nf[(nf.ec.between(0,3500)) & (nf.tds.between(0,2500)) & (nf.waterTemp.between(0,45))].copy()",
    "    nf['hour'] = nf.createdAt.dt.floor('h')",
    "    ems_ok = ems[ems.dht22Temp.between(0,60) & ems.dht22Moisture.between(0,100)].copy()",
    "    ems_ok['hour'] = ems_ok.createdAt.dt.floor('h')",
    "    lms['hour'] = lms.createdAt.dt.floor('h')",
    "    h_nf = nf.groupby('hour').agg(",
    "        ec=('ec','median'), tds=('tds','median'),  # tds kept only for formula audit",
    "        waterTemp=('waterTemp','median'),",
    "        pump_duty=('pump_any','mean'),",
    "        pump_phup=('peristalticPumpPhup','mean'),",
    "        pump_nutrient=('peristalticPumpA','mean'),",
    "    ).reset_index()",
    "    h_ems = ems_ok.groupby('hour').agg(",
    "        air_temp=('dht22Temp','median'), humidity=('dht22Moisture','median'),",
    "        oxygen=('oxygen','median'), pressure=('pressure','median'),",
    "    ).reset_index()",
    "    h_lms = lms.groupby('hour').agg(",
    "        light_bh1750=('bh1750','median'), light_ldr=('ldr','median'),",
    "        light_tsl=('tsl2591','median'),",
    "    ).reset_index()",
    "    m = pd.merge(h_nf, h_ems, on='hour', how='inner')",
    "    m = pd.merge(m, h_lms, on='hour', how='left')  # LMS sparse — OK",
    "    for c in ['light_bh1750','light_ldr','light_tsl']:",
    "        m[c] = m[c].fillna(m[c].median())",
    "    return m.sort_values('hour').reset_index(drop=True)",
    "",
    "# Independent sensors only (for ML features — never use derived TDS to predict EC)",
    "INDEPENDENT_FEATURES = [",
    "    'air_temp', 'humidity', 'oxygen', 'pressure',",
    "    'waterTemp', 'pump_duty', 'pump_phup', 'pump_nutrient',",
    "    'light_bh1750', 'light_ldr', 'light_tsl',",
    "]",
    "",
    "sensor_map = pd.DataFrame([",
    "    ['EC', 'NFADS', 'Conductivity probe', 'Independent', 'Target for virtual sensor'],",
    "    ['TDS', 'NFADS', 'Derived', 'NO — TDS = f(EC) firmware', 'Audit formula only'],",
    "    ['waterTemp', 'NFADS', 'DS18B20', 'Independent', 'Feature + validation target'],",
    "    ['pump_*', 'NFADS', 'Actuators', 'Independent', 'Control inputs'],",
    "    ['air_temp', 'EMS', 'DHT22', 'Independent', 'Feature'],",
    "    ['humidity', 'EMS', 'DHT22', 'Independent', 'Feature'],",
    "    ['oxygen', 'EMS', 'O2 sensor', 'Independent', 'Feature'],",
    "    ['pressure', 'EMS', 'Barometric', 'Independent', 'Feature'],",
    "    ['light_*', 'LMS', 'BH1750/LDR/TSL', 'Independent', 'Feature (when logged)'],",
    "    ['pH', 'NFADS', 'pH probe', 'Independent (when working)', 'Future — currently sparse'],",
    "], columns=['Signal','Subsystem','Hardware','Use in ML','Role'])",
    "",
    "nf_raw = load_nfads()",
    "ems_raw = load_ems()",
    "lms_raw = load_lms()",
    "hourly = merge_hourly(nf_raw, ems_raw, lms_raw)",
    "print(f'Hourly merged records: {len(hourly)}')",
    "display(sensor_map)",
    "display(hourly[INDEPENDENT_FEATURES + ['ec','tds']].describe().round(2))",
]

METRICS_FUNCS = [
    "def regression_metrics(y_true, y_pred):",
    "    y_true, y_pred = np.asarray(y_true), np.asarray(y_pred)",
    "    return dict(RMSE=float(np.sqrt(mean_squared_error(y_true, y_pred))),",
    "                MAE=float(mean_absolute_error(y_true, y_pred)),",
    "                R2=float(r2_score(y_true, y_pred)), n=len(y_true))",
    "",
    "def bootstrap_ci(y_true, y_pred, n_boot=500):",
    "    rng = np.random.default_rng(RANDOM_STATE)",
    "    n = len(y_true); rmse_s, mae_s, r2_s = [], [], []",
    "    for _ in range(n_boot):",
    "        idx = rng.integers(0, n, n)",
    "        m = regression_metrics(np.asarray(y_true)[idx], np.asarray(y_pred)[idx])",
    "        rmse_s.append(m['RMSE']); mae_s.append(m['MAE']); r2_s.append(m['R2'])",
    "    return {k: np.quantile(v, [0.025, 0.975]) for k, v in",
    "            zip(['RMSE','MAE','R2'], [rmse_s, mae_s, r2_s])}",
    "",
    "def cv_metrics_ts(X, y, model, n_splits=5):",
    "    \"\"\"Time-series CV: return per-fold metrics + mean/std for error bars (like Fig. 8 paper).\"\"\"",
    "    tscv = TimeSeriesSplit(n_splits=n_splits)",
    "    folds = []",
    "    for tr, te in tscv.split(X):",
    "        m = model.__class__(**model.get_params())",
    "        m.fit(X.iloc[tr], y.iloc[tr])",
    "        pred = m.predict(X.iloc[te])",
    "        folds.append(regression_metrics(y.iloc[te], pred))",
    "    df = pd.DataFrame(folds)",
    "    summary = df.mean().to_dict()",
    "    summary.update({f'{k}_std': df[k].std() for k in ['RMSE','MAE','R2']})",
    "    return df, summary",
]

# ==================== NOTEBOOK 1 ====================
c1 = []
c1.append(md(
    "# Notebook 1 — Statistical Sensor Validation",
    "",
    "**Reviewer concern:** *Insufficient statistical validation — sensor validation lacks RMSE, confidence intervals, and calibration analysis.*",
    "",
    "**Reference methodology:** Karimzadeh et al. (*Computers and Electronics in Agriculture*, 2025) use **sensor-independent regression**: predict EC from environmental/operational variables, then quantify agreement with **RMSE, MAE, R²** and confidence bands.",
    "",
    "**Important (BitnBolt hardware):** **EC and TDS come from the same probe.** TDS is computed in firmware as $TDS = k \\cdot EC + b$. ",
    "They are **not** independent — we never use TDS to predict EC (that would be circular).",
    "",
    "**Our validation uses only independent sensors:**",
    "- **EMS:** air temperature, humidity, O₂, pressure (DHT22 + environment)",
    "- **NFADS:** solution temperature (DS18B20), peristaltic pump duty",
    "- **LMS:** BH1750, LDR, TSL2591 (light — when logged)",
    "",
    "**Methods:** virtual EC sensor, virtual water-temperature check, EC→TDS formula audit, RMSE/MAE/R², bootstrap 95% CI, calibration + Bland–Altman.",
    "",
    "**Outputs:** `results/validation_metrics.csv`, figures in `figures/validation/`",
))

c1.append(md("## Step 1 — Setup"))
c1.append(code("# pip install -r requirements.txt", *SETUP, "VAL_DIR = FIG_DIR / 'validation'; VAL_DIR.mkdir(parents=True, exist_ok=True)",
               "(DATA_DIR/'results').mkdir(exist_ok=True)", *METRICS_FUNCS))

c1.append(md(
    "## Step 2 — Load, merge, and sensor inventory",
    "",
    "**Intuition:** Validation must use **physically independent** measurements. ",
    "TDS is excluded from all predictors because it is algebraically tied to EC.",
))
c1.append(code(*LOAD_DATA))

c1.append(md(
    "## Step 2b — Pearson correlation (independent sensors only)",
    "",
    "**Intuition (paper §3.4.2):** Correlation matrix shows which environmental drivers co-vary with EC — motivates feature selection.",
))
c1.append(code(
    "indep = hourly[INDEPENDENT_FEATURES + ['ec']]",
    "corr = indep.corr()",
    "fig, ax = plt.subplots(figsize=(10, 8))",
    "sns.heatmap(corr, annot=True, fmt='.2f', cmap='RdBu_r', center=0, ax=ax)",
    "ax.set_title('Independent sensors + EC (hourly) — note: TDS omitted (derived)')",
    "plt.tight_layout(); plt.savefig(VAL_DIR/'fig_independent_corr.png', dpi=150, bbox_inches='tight'); plt.show()",
    "print('Top |r| with EC:')",
    "print(corr['ec'].drop('ec').abs().sort_values(ascending=False).head(6).round(3))",
))

c1.append(md(
    "## Step 3 — Virtual EC sensor (independent features only)",
    "",
    "**Intuition:** Predict EC from climate + solution temperature + pumps + light — **never from TDS**. ",
    "Large residuals $|EC_{obs} - EC_{pred}|$ flag drift/bias/faults (Karimzadeh et al., sensor-independent FDD).",
    "",
    "Models: **Ridge**, **SVR**, **ANN** with time-series CV.",
))
c1.append(code(
    "FEATURES = [c for c in INDEPENDENT_FEATURES if c in hourly.columns]",
    "TARGET = 'ec'",
    "X = hourly[FEATURES]; y = hourly[TARGET]",
    "",
    "models = {",
    "    'Ridge': Ridge(alpha=1.0),",
    "    'SVR': SVR(C=100, gamma='scale'),",
    "    'ANN': MLPRegressor(hidden_layer_sizes=(64,32), max_iter=500, random_state=RANDOM_STATE),",
    "}",
    "",
    "val_rows = []",
    "pred_store = {}",
    "tscv = TimeSeriesSplit(n_splits=5)",
    "for name, model in models.items():",
    "    fold_df, summary = cv_metrics_ts(X, y, model)",
    "    pred_full = np.full(len(y), np.nan)",
    "    for tr, te in tscv.split(X):",
    "        m = model.__class__(**model.get_params())",
    "        m.fit(X.iloc[tr], y.iloc[tr])",
    "        pred_full[te] = m.predict(X.iloc[te])",
    "    ok = ~np.isnan(pred_full)",
    "    ci = bootstrap_ci(y[ok], pred_full[ok])",
    "    row = {'model': name, **summary,",
    "           'RMSE_CI_lo': ci['RMSE'][0], 'RMSE_CI_hi': ci['RMSE'][1],",
    "           'MAE_CI_lo': ci['MAE'][0], 'MAE_CI_hi': ci['MAE'][1]}",
    "    val_rows.append(row)",
    "    pred_store[name] = pred_full",
    "    print(f\"{name}: RMSE={summary['RMSE']:.2f} +/- {summary['RMSE_std']:.2f}, R2={summary['R2']:.4f}\")",
    "",
    "val_df = pd.DataFrame(val_rows)",
    "display(val_df.round(4))",
))

c1.append(md(
    "## Step 4 — Cross-validation error bars (replicates paper Fig. 8c)",
    "",
    "**Intuition:** A single RMSE is insufficient. Error bars show **stability across time folds**.",
))
c1.append(code(
    "fig, axes = plt.subplots(1, 3, figsize=(12, 4))",
    "metrics = ['RMSE', 'MAE', 'R2']",
    "colors = ['#2ecc71', '#3498db', '#9b59b6']",
    "x = np.arange(len(val_df))",
    "for ax, met, c in zip(axes, metrics, colors):",
    "    means = val_df[met].values",
    "    stds = val_df[f'{met}_std'].values",
    "    ax.bar(x, means, yerr=stds, capsize=5, color=c, alpha=0.85)",
    "    ax.set_xticks(x); ax.set_xticklabels(val_df['model'], rotation=15)",
    "    ax.set_title(met); ax.set_ylabel(met)",
    "plt.suptitle('Sensor-independent EC prediction — time-series CV (error bars = fold std)')",
    "plt.tight_layout()",
    "plt.savefig(VAL_DIR/'fig_cv_errorbars.png', dpi=150, bbox_inches='tight')",
    "plt.show()",
))

c1.append(md(
    "## Step 5 — Calibration analysis (observed vs predicted)",
    "",
    "**Intuition:** Ideal calibration: predicted = observed (slope=1, intercept=0). ",
    "**Bland–Altman** plots reveal systematic bias vs magnitude.",
))
c1.append(code(
    "best_name = val_df.loc[val_df['RMSE'].idxmin(), 'model']",
    "y_pred = pred_store[best_name]",
    "ok = ~np.isnan(y_pred)",
    "y_pred = y_pred[ok]; y_true = y.values[ok]",
    "",
    "fig, axes = plt.subplots(1, 2, figsize=(11, 4))",
    "mn, mx = min(y_true.min(), y_pred.min()), max(y_true.max(), y_pred.max())",
    "axes[0].scatter(y_true, y_pred, alpha=0.5, s=20)",
    "axes[0].plot([mn,mx],[mn,mx],'r--',label='1:1 line')",
    "slope, intercept, r, _, _ = stats.linregress(y_true, y_pred)",
    "axes[0].plot([mn,mx], slope*np.array([mn,mx])+intercept, 'g-', label=f'fit: y={slope:.2f}x+{intercept:.1f}')",
    "axes[0].set(xlabel='EC observed (uS/cm)', ylabel='EC predicted', title=f'Calibration — {best_name}')",
    "axes[0].legend()",
    "diff = y_pred - y_true; mean = (y_pred + y_true)/2",
    "axes[1].scatter(mean, diff, alpha=0.5, s=20)",
    "axes[1].axhline(diff.mean(), color='r', ls='--', label=f'bias={diff.mean():.1f}')",
    "lo, hi = diff.mean()-1.96*diff.std(), diff.mean()+1.96*diff.std()",
    "axes[1].axhline(lo, color='gray', ls=':'); axes[1].axhline(hi, color='gray', ls=':')",
    "axes[1].set(xlabel='Mean(EC_obs, EC_pred)', ylabel='Pred - Obs', title='Bland-Altman')",
    "axes[1].legend()",
    "plt.tight_layout()",
    "plt.savefig(VAL_DIR/'fig_calibration_bland_altman.png', dpi=150, bbox_inches='tight')",
    "plt.show()",
    "",
    "m_final = regression_metrics(y_true, y_pred)",
    "ci_final = bootstrap_ci(y_true, y_pred)",
    "print(f'Best model ({best_name}): RMSE={m_final[\"RMSE\"]:.2f} [{ci_final[\"RMSE\"][0]:.2f}, {ci_final[\"RMSE\"][1]:.2f}]')",
    "print(f'  MAE={m_final[\"MAE\"]:.2f}, R2={m_final[\"R2\"]:.4f}')",
))

c1.append(md(
    "## Step 6 — EC→TDS formula audit (same probe — NOT independent validation)",
    "",
    "**Intuition:** Firmware computes $TDS = k \\cdot EC + b$. We fit $(k,b)$ on data to check **implementation consistency** ",
    "(max residual, RMSE). High R² here is **expected** — do not cite this as cross-sensor validation in the paper.",
))
c1.append(code(
    "sub = nf_raw[nf_raw.ec.between(0,3500) & nf_raw.tds.between(0,2500)].sample(",
    "    n=min(25000, len(nf_raw)), random_state=RANDOM_STATE)",
    "k, b, r, _, _ = stats.linregress(sub.ec, sub.tds)",
    "tds_from_ec = k * sub.ec + b",
    "resid_formula = sub.tds - tds_from_ec",
    "formula_audit = {",
    "    'k_fitted': k, 'b_fitted': b, 'pearson_r': r,",
    "    'max_abs_residual_ppm': float(resid_formula.abs().max()),",
    "    'rmse_formula_ppm': float(np.sqrt((resid_formula**2).mean())),",
    "    'note': 'Same sensor — formula check only',",
    "}",
    "fig, ax = plt.subplots(figsize=(6,5))",
    "ax.scatter(sub.ec, sub.tds, s=3, alpha=0.15, label='logged')",
    "xx = np.linspace(sub.ec.min(), sub.ec.max(), 100)",
    "ax.plot(xx, k*xx+b, 'r-', lw=2, label=f'Fitted TDS={k:.3f}*EC+{b:.1f}')",
    "ax.set(xlabel='EC (uS/cm)', ylabel='TDS (ppm)', title='Formula audit (derived TDS, not 2nd probe)')",
    "ax.legend(); plt.tight_layout()",
    "plt.savefig(VAL_DIR/'fig_ec_tds_formula_audit.png', dpi=150, bbox_inches='tight'); plt.show()",
    "print(formula_audit)",
))

c1.append(md(
    "## Step 6b — Virtual water temperature (cross-subsystem validation)",
    "",
    "**Intuition:** `waterTemp` (DS18B20 in solution) should relate to `air_temp` and `humidity` (EMS) but is a **separate sensor** — valid second validation target.",
))
c1.append(code(
    "WT_FEATURES = ['air_temp','humidity','pressure','pump_duty','light_bh1750']",
    "X_wt = hourly[WT_FEATURES]; y_wt = hourly['waterTemp']",
    "pred_wt = np.full(len(y_wt), np.nan)",
    "for tr, te in TimeSeriesSplit(5).split(X_wt):",
    "    m = Ridge(1.0); m.fit(X_wt.iloc[tr], y_wt.iloc[tr]); pred_wt[te] = m.predict(X_wt.iloc[te])",
    "ok_wt = ~np.isnan(pred_wt)",
    "m_wt = regression_metrics(y_wt[ok_wt], pred_wt[ok_wt])",
    "ci_wt = bootstrap_ci(y_wt[ok_wt], pred_wt[ok_wt])",
    "print(f'Virtual waterTemp: RMSE={m_wt[\"RMSE\"]:.2f} C [{ci_wt[\"RMSE\"][0]:.2f},{ci_wt[\"RMSE\"][1]:.2f}], R2={m_wt[\"R2\"]:.3f}')",
    "fig, ax = plt.subplots(figsize=(5,5))",
    "ax.scatter(y_wt[ok_wt], pred_wt[ok_wt], alpha=0.5, s=25)",
    "mn, mx = y_wt[ok_wt].min(), y_wt[ok_wt].max()",
    "ax.plot([mn,mx],[mn,mx],'r--'); ax.set(xlabel='waterTemp observed', ylabel='waterTemp predicted')",
    "ax.set_title('Independent validation: solution temperature'); plt.tight_layout()",
    "plt.savefig(VAL_DIR/'fig_water_temp_validation.png', dpi=150, bbox_inches='tight'); plt.show()",
))

c1.append(md(
    "## Step 7 — Residual-based validation band (±3% rule, paper Eq. 11 spirit)",
    "",
    "**Intuition:** Paper flags faults when predictions fall outside sensor accuracy (±3%). ",
    "We compute **in-tolerance rate** = fraction of hours where relative error < 3%.",
))
c1.append(code(
    "rel_err = np.abs(y_pred - y_true) / np.maximum(np.abs(y_true), 1) * 100",
    "TOL = 3.0  # percent",
    "in_tol = (rel_err <= TOL).mean() * 100",
    "print(f'Hours within +/-{TOL}% of virtual sensor: {in_tol:.1f}%')",
    "",
    "hourly_plot = hourly.iloc[ok].copy().reset_index(drop=True)",
    "hourly_plot['ec_pred'] = y_pred",
    "hourly_plot['residual'] = hourly_plot['ec'] - hourly_plot['ec_pred']",
    "fig, ax = plt.subplots(figsize=(12, 3.5))",
    "ax.plot(hourly_plot['hour'], hourly_plot['ec'], label='EC observed', lw=0.8)",
    "ax.plot(hourly_plot['hour'], hourly_plot['ec_pred'], label='EC virtual', lw=0.8, alpha=0.8)",
    "ax.fill_between(hourly_plot['hour'], hourly_plot['ec_pred']*0.97, hourly_plot['ec_pred']*1.03,",
    "                alpha=0.2, label='+/-3% band')",
    "ax.set(xlabel='Time', ylabel='EC'); ax.legend(); ax.set_title('Sensor-independent validation band')",
    "plt.tight_layout(); plt.savefig(VAL_DIR/'fig_validation_band.png', dpi=150, bbox_inches='tight'); plt.show()",
))

c1.append(md(
    "## Step 8 — Distribution analysis (violin plots, paper Fig. 4 style)",
    "",
    "Compare **normal** residuals vs **anomaly** (large |residual|) to show statistical separation.",
))
c1.append(code(
    "hourly_plot['status'] = np.where(np.abs(hourly_plot['residual']) > hourly_plot['residual'].std()*2,",
    "                                 'anomaly', 'normal')",
    "fig, ax = plt.subplots(figsize=(7, 4))",
    "sns.violinplot(data=hourly_plot, x='status', y='residual', ax=ax, inner='box')",
    "ax.axhline(0, color='k', lw=0.5)",
    "ax.set(title='Residual distribution: normal vs anomaly (2-sigma rule)', ylabel='EC_obs - EC_virtual')",
    "plt.tight_layout(); plt.savefig(VAL_DIR/'fig_violin_residuals.png', dpi=150, bbox_inches='tight'); plt.show()",
    "",
    "for s in ['normal','anomaly']:",
    "    r = hourly_plot.loc[hourly_plot.status==s, 'residual']",
    "    print(f'{s}: mean={r.mean():.1f}, std={r.std():.1f}, n={len(r)}')",
))

c1.append(md(
    "## Step 9 — Export validation table for manuscript",
    "",
    "**Copy Table:** Include RMSE (95% CI), MAE, R², in-tolerance %, calibration k.",
))
c1.append(code(
    "val_df['in_tolerance_pct_3'] = in_tol",
    "val_df['features'] = ', '.join(FEATURES)",
    "val_df.to_csv(DATA_DIR/'results'/'validation_metrics.csv', index=False)",
    "pd.DataFrame([formula_audit]).to_csv(DATA_DIR/'results'/'ec_tds_formula_audit.csv', index=False)",
    "pd.DataFrame([{**m_wt, 'target': 'waterTemp', **{f'RMSE_CI_{i}': ci_wt['RMSE'][j] for j,i in enumerate(['lo','hi'])}}]).to_csv(",
    "    DATA_DIR/'results'/'water_temp_validation.csv', index=False)",
    "print('Saved results/*.csv')",
    "",
    "print('\\n--- Suggested manuscript paragraph ---')",
    "print(f'EC was validated using a sensor-independent virtual model ({best_name}) built from '",
    "      f'EMS climate, solution temperature, actuators, and LMS light — excluding derived TDS. '",
    "      f'RMSE = {m_final[\"RMSE\"]:.1f} uS/cm (95% CI: {ci_final[\"RMSE\"][0]:.1f}-{ci_final[\"RMSE\"][1]:.1f}), '",
    "      f'R2 = {m_final[\"R2\"]:.3f}; {in_tol:.1f}% within +/-3%. '",
    "      f'Separately, water temperature was predicted from independent EMS features (RMSE = {m_wt[\"RMSE\"]:.2f} C). '",
    "      f'TDS tracks EC via firmware conversion (k={k:.3f}); max formula residual = {formula_audit[\"max_abs_residual_ppm\"]:.1f} ppm.')",
))

# ==================== NOTEBOOK 2 ====================
c2 = []
c2.append(md(
    "# Notebook 2 — Methodological Innovation (ML, Modelling, Control)",
    "",
    "**Reviewer concern:** *Limited scientific novelty — primarily system integration; lacks advanced control, ML decision-making, and formal system modelling.*",
    "",
    "**Reference:** Karimzadeh et al. (2025) FDD workflow: fault formulation → ML classifiers (RF, SVM, ANN, LSTM) → diagnosis.",
    "",
    "**Hardware note:** TDS = $f(EC)$ on one probe — state-space and ML use **EC + waterTemp + EMS + LMS** only.",
    "",
    "**Our extensions:**",
    "1. **Formal fault models** (Table 1) on real EC traces",
    "2. **FDD** with independent environmental context (EMS/LMS/pumps)",
    "3. **State-space** $[EC, T_{solution}]$ — no derived TDS state",
    "4. **ML dosing policy** from independent sensors + EC",
    "5. **Predictive control** preview using non-derived features",
    "",
    "**Outputs:** `results/innovation_metrics.csv`, figures in `figures/innovation/`",
))

c2.append(md("## Step 1 — Setup"))
c2.append(code("# pip install -r requirements.txt", *SETUP,
               "from sklearn.svm import SVC",
               "from sklearn.neighbors import KNeighborsClassifier",
               "from sklearn.neural_network import MLPClassifier",
               "INN_DIR = FIG_DIR / 'innovation'; INN_DIR.mkdir(parents=True, exist_ok=True)",
               "(DATA_DIR/'results').mkdir(exist_ok=True)",
               *LOAD_DATA[:],  # load functions only - need fault helpers after
))

# Fix c2 setup - split load and fault models
c2[-1] = code(
    "# pip install -r requirements.txt", *SETUP,
    "from sklearn.svm import SVC",
    "from sklearn.neighbors import KNeighborsClassifier",
    "from sklearn.neural_network import MLPClassifier",
    "INN_DIR = FIG_DIR / 'innovation'; INN_DIR.mkdir(parents=True, exist_ok=True)",
    "(DATA_DIR/'results').mkdir(exist_ok=True)",
    *METRICS_FUNCS,
    *LOAD_DATA,
)

c2.append(md(
    "## Step 2 — Formal fault models (paper Table 1)",
    "",
    "| Fault | Model |",
    "|-------|-------|",
    "| Normal | $s(t) = v(t) + \\eta$ |",
    "| Bias | $s(t) = v(t) + \\eta + \\theta$ |",
    "| Drift | $s(t) = v(t) + \\eta + d(t)$ |",
    "| Precision | higher variance $\\gamma$ |",
    "| Spike | rare pulses $h(t)$ |",
    "| Stuck | $s(t) = S$ constant |",
    "",
    "**Intuition:** We inject faults on real EC traces so ML learns patterns relevant to *your* hardware.",
))
c2.append(code(
    "def inject_faults(ec_series, rng=None):",
    "    rng = rng or np.random.default_rng(RANDOM_STATE)",
    "    v = np.asarray(ec_series, dtype=float).copy()",
    "    n = len(v)",
    "    rows = []",
    "    # Normal",
    "    eta = rng.normal(0, v.std()*0.02, n)",
    "    rows.append(('normal', v + eta))",
    "    # Bias up/down",
    "    rows.append(('bias_up', v + eta + 0.15*v.mean()))",
    "    rows.append(('bias_down', v + eta - 0.15*v.mean()))",
    "    # Drift",
    "    d = np.linspace(0, 0.2*v.mean(), n)",
    "    rows.append(('drift_up', v + eta + d))",
    "    rows.append(('drift_down', v + eta - d))",
    "    # Precision degradation",
    "    rows.append(('precision', v + rng.normal(0, v.std()*0.25, n)))",
    "    # Spike",
    "    s = v.copy(); idx = rng.choice(n, size=max(1,n//50), replace=False)",
    "    s[idx] += rng.choice([-1,1], size=len(idx)) * v.std() * 5",
    "    rows.append(('spike', s))",
    "    # Stuck",
    "    rows.append(('stuck', np.full(n, v.mean())))",
    "    return rows",
    "",
    "# Build synthetic FDD dataset from stable EC windows",
    "stable = hourly[hourly['ec'].between(hourly['ec'].quantile(0.2), hourly['ec'].quantile(0.8))]",
    "windows = []",
    "for i in range(0, min(len(stable)-24, 200), 12):",
    "    seg = stable['ec'].iloc[i:i+24].values",
    "    if len(seg) < 24: continue",
    "    for label, sig in inject_faults(seg):",
    "        windows.append({'label': label, 'ec_mean': sig.mean(), 'ec_std': sig.std(),",
    "                        'ec_slope': np.polyfit(range(len(sig)), sig, 1)[0],",
    "                        'ec_range': sig.max()-sig.min()})",
    "fdd = pd.DataFrame(windows)",
    "print(fdd['label'].value_counts())",
))

c2.append(md(
    "## Step 3 — FDD features from EC dynamics (synthetic faults)",
    "",
    "Features are **statistics of EC windows** (mean, std, slope) after Table-1 fault injection.",
))
c2.append(code(
    "feat_fdd = ['ec_mean','ec_std','ec_slope','ec_range']",
    "X_fdd = fdd[feat_fdd]; y_fdd = fdd['label']",
    "split = int(0.7 * len(X_fdd))",
    "X_tr, X_te = X_fdd.iloc[:split], X_fdd.iloc[split:]",
    "y_tr, y_te = y_fdd.iloc[:split], y_fdd.iloc[split:]",
    "sc = StandardScaler(); X_tr_s = sc.fit_transform(X_tr); X_te_s = sc.transform(X_te)",
))

c2.append(md("## Step 4 — Multi-class fault diagnosis (paper Fig. 5 / 7)"))
c2.append(code(
    "clf_models = {",
    "    'KNN': KNeighborsClassifier(n_neighbors=5),",
    "    'SVM': SVC(kernel='rbf', C=100, gamma='scale'),",
    "    'RF': RandomForestClassifier(n_estimators=100, random_state=RANDOM_STATE),",
    "    'ANN': MLPClassifier(hidden_layer_sizes=(64,32), max_iter=400, random_state=RANDOM_STATE),",
    "}",
    "fdd_results = []",
    "fig, axes = plt.subplots(2, 2, figsize=(10, 9)); axes = axes.ravel()",
    "for ax, (name, clf) in zip(axes, clf_models.items()):",
    "    clf.fit(X_tr_s, y_tr)",
    "    pred = clf.predict(X_te_s)",
    "    acc = accuracy_score(y_te, pred)",
    "    f1 = f1_score(y_te, pred, average='macro')",
    "    fdd_results.append({'model': name, 'accuracy': acc, 'macro_f1': f1})",
    "  cm = confusion_matrix(y_te, pred, labels=sorted(y_fdd.unique()))",
    "    sns.heatmap(cm, annot=True, fmt='d', ax=ax, xticklabels=sorted(y_fdd.unique()),",
    "                yticklabels=sorted(y_fdd.unique()), cbar=False)",
    "    ax.set_title(f'{name}: acc={acc:.3f}')",
    "plt.suptitle('Fault detection & diagnosis — EC feature space'); plt.tight_layout()",
    "plt.savefig(INN_DIR/'fig_fdd_confusion_matrices.png', dpi=150, bbox_inches='tight'); plt.show()",
    "display(pd.DataFrame(fdd_results).round(4))",
))

c2.append(md(
    "## Step 5 — Formal state-space (independent states only)",
    "",
    "$$\\mathbf{x}_t = [EC_t,\\, T_{water,t}]^T, \\quad u_t = [pump\\_duty,\\, T_{air},\\, RH]^T$$",
    "",
    "TDS is **not** a state variable (algebraic function of EC).",
))
c2.append(code(
    "ss = hourly.copy()",
    "ss['ec_next'] = ss['ec'].shift(-1)",
    "ss['wt_next'] = ss['waterTemp'].shift(-1)",
    "ss = ss.dropna()",
    "X_ss = ss[['ec','waterTemp','pump_duty','air_temp','humidity']].values",
    "Y_ss = ss[['ec_next','wt_next']].values",
    "n_tr = int(0.8*len(X_ss))",
    "lr = Ridge(alpha=0.1).fit(X_ss[:n_tr], Y_ss[:n_tr])",
    "Y_hat = lr.predict(X_ss[n_tr:])",
    "ss_m = regression_metrics(Y_ss[n_tr:].ravel(), Y_hat.ravel())",
    "print('State-space 1-step ahead (EC + waterTemp):'); print(pd.Series(ss_m))",
    "coef_df = pd.DataFrame(lr.coef_, columns=['EC','WT','pump','Tair','RH'], index=['dEC','dWT'])",
    "display(coef_df.round(4))",
))

c2.append(md(
    "## Step 6 — ML-based decision-making (dosing alert policy)",
    "",
    "**Intuition:** Map system state → action. Label: need dosing if EC below setpoint.",
))
c2.append(code(
    "EC_SET = hourly['ec'].median()  # data-driven setpoint",
    "pol = hourly.copy()",
    "pol['need_dose'] = (pol['ec'] < EC_SET * 0.92).astype(int)",
    "pol['ec_lag'] = pol['ec'].shift(1); pol['slope'] = pol['ec'].diff(); pol = pol.dropna()",
    "POL_FEATURES = ['ec','waterTemp','pump_duty','pump_phup','air_temp','humidity','oxygen','pressure','ec_lag','slope']",
    "X_p = pol[POL_FEATURES]",
    "y_p = pol['need_dose']",
    "pred_p = np.full(len(y_p), -1)",
    "for tr, te in TimeSeriesSplit(5).split(X_p):",
    "    c = RandomForestClassifier(100, max_depth=8, random_state=RANDOM_STATE)",
    "    c.fit(X_p.iloc[tr], y_p.iloc[tr]); pred_p[te] = c.predict(X_p.iloc[te])",
    "m = pred_p >= 0",
    "print(classification_report(y_p[m], pred_p[m], target_names=['OK','dose']))",
    "policy_acc = accuracy_score(y_p[m], pred_p[m])",
))

c2.append(md(
    "## Step 7 — Predictive control preview (forecast + act)",
    "",
    "**Intuition:** MPC philosophy: predict EC one step ahead; trigger action if forecast violates band.",
))
c2.append(code(
    "pc = hourly.copy(); pc['ec_next'] = pc['ec'].shift(-1); pc = pc.dropna()",
    "FC_FEATURES = ['ec','waterTemp','pump_duty','air_temp','humidity','oxygen','pressure','light_bh1750']",
    "X_fc = pc[FC_FEATURES]",
    "y_fc = pc['ec_next']",
    "pred_fc = np.full(len(y_fc), np.nan)",
    "for tr, te in TimeSeriesSplit(5).split(X_fc):",
    "    r = Ridge(1.0); r.fit(X_fc.iloc[tr], y_fc.iloc[tr]); pred_fc[te] = r.predict(X_fc.iloc[te])",
    "ok = ~np.isnan(pred_fc)",
    "m_fc = regression_metrics(y_fc[ok], pred_fc[ok])",
    "pc_ok = pc.iloc[ok.nonzero()[0]].copy()",
    "pc_ok['ec_pred'] = pred_fc[ok]",
    "BAND = 0.05",
    "pc_ok['alert'] = (pc_ok['ec_pred'] < EC_SET * (1-BAND)).astype(int)",
    "print('Predictive EC:', m_fc)",
    "print(f'Would-trigger alerts: {pc_ok[\"alert\"].sum()} / {len(pc_ok)} hours')",
    "fig, ax = plt.subplots(figsize=(11,3))",
    "ax.plot(pc_ok['hour'], pc_ok['ec'], label='observed'); ax.plot(pc_ok['hour'], pc_ok['ec_pred'], label='1-step forecast')",
    "ax.axhline(EC_SET, color='g', ls='--', label='setpoint'); ax.legend(); ax.set_title('Predictive control preview')",
    "plt.tight_layout(); plt.savefig(INN_DIR/'fig_predictive_control.png', dpi=150, bbox_inches='tight'); plt.show()",
))

c2.append(md(
    "## Step 8 — Real-data anomaly flags from virtual EC residuals",
    "",
    "Use **independent** virtual EC (Ridge on `INDEPENDENT_FEATURES`) — large $|residual|$ flags potential sensor faults on field data.",
))
c2.append(code(
    "X_v = hourly[INDEPENDENT_FEATURES]; y_v = hourly['ec']",
    "pred_v = np.full(len(y_v), np.nan)",
    "for tr, te in TimeSeriesSplit(5).split(X_v):",
    "    r = Ridge(1.0); r.fit(X_v.iloc[tr], y_v.iloc[tr]); pred_v[te] = r.predict(X_v.iloc[te])",
    "hourly['ec_virtual'] = pred_v",
    "hourly['residual'] = hourly['ec'] - hourly['ec_virtual']",
    "thr = hourly['residual'].std() * 2",
    "hourly['fault_flag'] = (hourly['residual'].abs() > thr).astype(int)",
    "print(f'Anomaly hours (|res|>2sigma): {hourly[\"fault_flag\"].sum()} / {len(hourly)}')",
    "fig, ax = plt.subplots(figsize=(11,3))",
    "ax.plot(hourly['hour'], hourly['residual'], lw=0.8)",
    "ax.axhline(thr, color='r', ls='--'); ax.axhline(-thr, color='r', ls='--')",
    "ax.set(title='Sensor-independent residual (field data)', ylabel='EC - EC_virtual')",
    "plt.tight_layout(); plt.savefig(INN_DIR/'fig_field_residual_fdd.png', dpi=150, bbox_inches='tight'); plt.show()",
))

c2.append(md("## Step 9 — Model comparison bar chart (paper Fig. 8a style)"))
c2.append(code(
    "fdd_df = pd.DataFrame(fdd_results)",
    "fig, ax = plt.subplots(figsize=(7,4))",
    "x = np.arange(len(fdd_df)); w = 0.35",
    "ax.bar(x-w/2, fdd_df['accuracy'], w, label='Accuracy')",
    "ax.bar(x+w/2, fdd_df['macro_f1'], w, label='Macro F1')",
    "ax.set_xticks(x); ax.set_xticklabels(fdd_df['model'])",
    "ax.set_ylim(0,1.05); ax.legend(); ax.set_title('FDD classifier comparison')",
    "plt.tight_layout(); plt.savefig(INN_DIR/'fig_fdd_comparison.png', dpi=150, bbox_inches='tight'); plt.show()",
))

c2.append(md("## Step 10 — Export & manuscript checklist"))
c2.append(code(
    "innov = pd.DataFrame(fdd_results)",
    "innov['state_space_RMSE'] = ss_m['RMSE']",
    "innov['state_space_R2'] = ss_m['R2']",
    "innov['policy_accuracy'] = policy_acc",
    "innov['predictive_RMSE'] = m_fc['RMSE']",
    "innov.to_csv(DATA_DIR/'results'/'innovation_metrics.csv', index=False)",
    "print('Saved results/innovation_metrics.csv')",
    "print('\\nManuscript checklist:')",
    "print('[ ] Table 1 fault models referenced')",
    "print('[ ] FDD confusion matrices (Fig)')",
    "print('[ ] State-space A,B coefficients reported')",
    "print('[ ] ML dosing policy accuracy stated')",
    "print('[ ] Predictive control preview discussed')",
))

# Fix typo in c2 confusion matrix cell (extra space before cm)
for i, cell in enumerate(c2):
    if cell["cell_type"] == "code" and "  cm = confusion_matrix" in "".join(cell["source"]):
        src = "".join(cell["source"]).replace("  cm =", "    cm =")
        c2[i] = code(*src.split("\n"))

Path("01_statistical_validation.ipynb").write_text(
    json.dumps(nb(c1, "01"), indent=1), encoding="utf-8")
Path("02_methodological_innovation.ipynb").write_text(
    json.dumps(nb(c2, "02"), indent=1), encoding="utf-8")
print(f"Notebook 1: {len(c1)} cells")
print(f"Notebook 2: {len(c2)} cells")
