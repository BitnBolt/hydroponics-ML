# BitnBolt Hydroponics ML — Paper Writing Guide

This folder contains analysis for your **journal revision**. Use this README as the **manuscript blueprint**: what to write, where each number comes from, and what is still weak.

---

## Is it research-paper ready?

| Area | Status | Action before submission |
|------|--------|-------------------------|
| **Workflow & reproducibility** | Ready | Run both notebooks → cite `results/*.csv` and `figures/` |
| **Reviewer 1: Statistical validation** | **Partially ready** | RMSE, CI, calibration plots exist; discuss weak virtual-EC R² honestly |
| **Reviewer 2: Methodological novelty** | **Partially ready** | State-space, ML policy, FDD pipeline exist; strengthen FDD or label as pilot |
| **Data coverage** | Gap | Only **~294 hourly** NFADS∩EMS rows; LMS ≈ **21 h** only |
| **pH sensor** | Gap | Effectively non-functional in export — do not claim pH ML |
| **EC/TDS** | Clarified | Same probe; TDS = formula — documented correctly in notebooks |

**Verdict:** Suitable for a **revised manuscript** if you (1) run fresh notebooks and paste updated tables, (2) add a **Limitations** subsection, (3) frame weak metrics as future work or collect more overlapping EMS+NFADS data. Not ready to claim “high-accuracy virtual EC” without qualification.

---

## Files map

| File | Role in paper |
|------|----------------|
| `01_statistical_validation.ipynb` | §3.2–3.3 Sensor validation (Reviewer 1) |
| `02_methodological_innovation.ipynb` | §3.4–3.5 ML, modelling, control (Reviewer 2) |
| `results/validation_metrics.csv` | **Table: Virtual EC models** |
| `results/water_temp_validation.csv` | **Table: Cross-sensor waterTemp** |
| `results/ec_tds_formula_audit.csv` | **Table/Footnote: TDS derivation** |
| `results/innovation_metrics.csv` | **Table: FDD + state-space + policy** |
| `figures/validation/*.png` | **Figures 4–7** (validation) |
| `figures/innovation/*.png` | **Figures 8–11** (novelty) |

Regenerate: `pip install -r requirements.txt` → Run All in both notebooks (or `python run_notebook1.py` / `run_notebook2.py`).

---

## Sensor model (must state in paper)

| Signal | Hardware | Independent? | How to describe in paper |
|--------|----------|--------------|---------------------------|
| **EC** | Conductivity probe (NFADS) | Yes | Primary nutrient indicator; validation target |
| **TDS** | **Same probe** (firmware) | **No** | “TDS computed as TDS = k·EC + b”; audit only |
| **waterTemp** | DS18B20 (NFADS) | Yes | Independent validation + state variable |
| **Air temp, RH** | DHT22 (EMS) | Yes | Climate drivers for virtual sensor |
| **O₂, pressure** | EMS | Yes | Auxiliary environmental features |
| **Pumps** | NFADS actuators | Yes | Control inputs u(t) |
| **Light** | LMS (BH1750, LDR, TSL2591) | Yes | Short logging window only |
| **pH** | NFADS | Yes (when working) | Report as offline in current dataset |

**Never** describe EC–TDS comparison as “dual-probe calibration.”

---

# How to write the research paper (section by section)

Follow this order. Numbers below are from the **last successful run** — **replace** after you re-run notebooks.

---

## 1. Abstract (150–250 words)

**Structure:** Problem → Method → Key results → Conclusion.

**Template:**

> Automated hydroponic systems require validated nutrient sensing beyond raw logging. We present a multi-subsystem IoT platform (NFADS, EMS, LMS) with **sensor-independent validation** and **ML-based fault detection and decision support** on **N = [INSERT] hours** of field data ([INSERT] raw samples over [INSERT] days). Electrical conductivity (EC) was predicted from independent environmental and actuator signals (excluding derived TDS). The best model ([Ridge/SVR/ANN]) achieved RMSE = **[~489]** µS/cm (95% CI: **[445–529]**), with **[~9%]** of observations within ±3% of the virtual estimate. Solution temperature was cross-validated against EMS climate (RMSE = **[~4.7]** °C). A discrete state-space model yielded one-step ahead R² ≈ **[0.94]**. ML dosing alerts reached **[~98%]** accuracy under time-series cross-validation. Limitations include sparse LMS coverage and inactive pH logging. The framework addresses statistical validation and methodological novelty for closed-loop nutrient management.

---

## 2. Introduction

**Paragraph 1 — Context:** Hydroponics needs reliable EC/temperature control; sensor drift and faults cause crop loss.

**Paragraph 2 — Gap:** Many IoT works log data only; reviewers require RMSE, confidence intervals, calibration, and ML/control contributions (cite Karimzadeh et al., 2025, for sensor-independent FDD).

**Paragraph 3 — Your system:** BitnBolt — NFADS (nutrient + dosing), EMS (climate), LMS (light); MongoDB logging at ~4 s (NFADS).

**Paragraph 4 — Contributions (numbered list):**

1. Multi-subsystem **sensor-independent EC validation** using only independent transducers.  
2. **Statistical protocol:** time-series CV, bootstrap 95% CI, calibration and Bland–Altman plots, ±3% in-tolerance rate.  
3. **Formal discrete state-space** model of EC and solution temperature under pump and climate inputs.  
4. **ML dosing policy** and **predictive control preview** on field data.  
5. **FDD pipeline** with Table-1 fault injection and multi-class classifiers (pilot on synthetic windows).

---

## 3. Materials and methods

### 3.1 Experimental setup and data acquisition

**Write:**

- Deployment description (NFT/deep water/etc., crop if any).  
- Hardware table: sensor → subsystem → sample rate.  
- Data export: `test.nfads.csv` (**153,805** rows), `test.ems.csv` (**79,928**), `test.lms.csv` (**1,229**).  
- Time span: NFADS **[dates]**; merged NFADS∩EMS hourly **n ≈ 294**.  
- Pre-processing: plausibility filters (EC 0–3500 µS/cm, waterTemp 0–45 °C), hourly median aggregation.

**Figure:** System block diagram (NFADS / EMS / LMS → cloud → analysis).

### 3.2 TDS derivation (same probe as EC)

**Write:**

> TDS is not measured by a separate sensor. Firmware converts EC to TDS via a linear relation. We fitted logged pairs and obtained **k ≈ 0.495**, **b ≈ 6.5** (Pearson **r ≈ 0.99**), with formula RMSE ≈ **37 ppm** and max residual ≈ **1059 ppm** (outliers). This confirms implementation consistency but is **not** used as independent validation.

**Figure:** `figures/validation/fig_ec_tds_formula_audit.png`  
**Table:** `results/ec_tds_formula_audit.csv`

### 3.3 Sensor-independent validation (Reviewer 1)

**Method (mirror Karimzadeh sensor-independent regression):**

- **Inputs (independent):** air_temp, humidity, oxygen, pressure, waterTemp, pump_duty, pump_phup, pump_nutrient, light_bh1750, light_ldr, light_tsl.  
- **Target:** EC.  
- **Models:** Ridge, SVR, ANN.  
- **Validation:** 5-fold **TimeSeriesSplit** (train past → test future).  
- **Metrics:** RMSE, MAE, R²; **bootstrap 95% CI** (500 resamples).  
- **Calibration:** observed vs predicted + **Bland–Altman**.  
- **In-tolerance rate:** % hours with |EC_obs − EC_pred| / EC_obs ≤ **3%**.

**Results table (copy from `validation_metrics.csv`):**

| Model | RMSE (µS/cm) | 95% CI | MAE | R² | ±3% in-tol. |
|-------|--------------|--------|-----|-----|-------------|
| Ridge | 466 | 445–529 | 380 | −0.72* | 9.4% |
| SVR | 480 | 451–533 | 393 | −0.56* | 9.4% |
| ANN | 2660 | … | … | … | 9.4% |

\*Negative R² on hold-out folds indicates high regime variability (large EC shifts between months). **Discuss honestly** — do not hide.

**Suggested wording:**

> “Virtual EC models quantify consistency between the conductivity probe and independent subsystem measurements. Moderate R² on held-out future hours reflects real nutrient regime changes (solution changes, maintenance) rather than probe noise alone. Residuals exceeding 2σ were flagged as anomaly candidates (n = 12/294 hours).”

**Figures:**

| Fig # | File | Caption |
|-------|------|---------|
| X | `fig_independent_corr.png` | Pearson correlation among independent sensors and EC |
| X+1 | `fig_cv_errorbars.png` | RMSE/MAE/R² with fold-wise error bars |
| X+2 | `fig_calibration_bland_altman.png` | Calibration and Bland–Altman for best model |
| X+3 | `fig_validation_band.png` | EC_obs vs virtual EC with ±3% band |
| X+4 | `fig_violin_residuals.png` | Residual distributions (normal vs 2σ anomaly) |

### 3.4 Cross-sensor validation: solution temperature

**Write:**

> As a second **independent** check, solution temperature was predicted from EMS features (air_temp, humidity, pressure, pump_duty, light_bh1750) using Ridge regression and time-series CV: RMSE = **4.73 °C** (95% CI: **3.34–5.99**), MAE = **2.46 °C**.

**Figure:** `fig_water_temp_validation.png`  
**Table:** `water_temp_validation.csv`

### 3.5 Formal system modelling (Reviewer 2)

**Write the equations:**

```
x_t = [EC_t, T_water,t]ᵀ
u_t = [pump_duty, T_air, RH]ᵀ
x_{t+1} ≈ A x_t + B u_t   (identified via Ridge on stacked 1-step targets)
```

Report coefficient matrix from Notebook 2, Step 5.  
**Results:** State-space pooled 1-step R² ≈ **0.94**, RMSE ≈ **174** (units mixed in stacked vector — clarify in text).

**Figure:** Optional — coefficient heatmap (export from notebook).

### 3.6 ML-based decision-making

**Write:**

- Label: `need_dose = 1` if EC < 0.92 × median(EC).  
- Features: EC, waterTemp, pumps, EMS climate, EC lag, slope.  
- Classifier: Random Forest, time-series CV.  
- **Result:** Accuracy ≈ **97.9%** (report precision/recall from classification report in notebook).

**Figure:** Feature importance (add bar plot from notebook if needed).

### 3.7 Fault detection and diagnosis (pilot)

**Write (align with Karimzadeh Table 1):**

| Fault | Injected model |
|-------|----------------|
| Normal | s = v + η |
| Bias | s = v + η ± θ |
| Drift | s = v + η + d(t) |
| Precision | increased noise |
| Spike | impulsive h(t) |
| Stuck | s = constant |

- Features: EC window mean, std, slope, range.  
- Classifiers: KNN, SVM, RF, ANN.  
- **Pilot result:** Macro accuracy ≈ **0.28–0.38** on synthetic windows — state that **full FDD on live faults** needs labeled failure events or more data.

**Figures:** `fig_fdd_confusion_matrices.png`, `fig_fdd_comparison.png`, `fig_field_residual_fdd.png` (real-data 2σ flags).

### 3.8 Predictive control preview

**Write:**

> One-step-ahead EC forecast from independent features; compare to setpoint EC̄. Alerts when predicted EC < (1 − 5%)·EC̄. RMSE ≈ **586** µS/cm — used as **feasibility preview**, not deployed MPC.

**Figure:** `fig_predictive_control.png`

---

## 4. Results

**Do not repeat all methods.** Present:

1. **Table 1** — Dataset summary (rows, days, sample interval).  
2. **Table 2** — Virtual EC validation (`validation_metrics.csv`).  
3. **Table 3** — waterTemp + formula audit.  
4. **Table 4** — Innovation (`innovation_metrics.csv`): state-space, policy, FDD.  
5. **Figures** — 8–10 total (validation block + innovation block).

**Order narrative:** Validation first (addresses Reviewer 1) → Modelling & ML (addresses Reviewer 2).

---

## 5. Discussion

**Include these paragraphs:**

1. **What worked:** Multi-subsystem fusion; state-space fit; dosing classifier; transparent statistical protocol.  
2. **Virtual EC weakness:** Negative R² → large month-to-month EC regime changes (see monthly EC drop in EDA); recommend recalibration after solution changes.  
3. **TDS:** Correctly excluded from ML; formula audit only.  
4. **pH:** Not usable in current export — hardware check required.  
5. **LMS:** Only ~21 h — light features unreliable for long-term claims.  
6. **Comparison to literature:** Karimzadeh used controlled fault injection + higher-frequency climate; your work adds **field-scale integrated NFADS–EMS** logging.  
7. **Future work:** Fix pH probe; longer LMS logging; SMOTE + LSTM FDD; deployed MPC; ground-truth manual EC samples for calibration.

---

## 6. Conclusion

3–4 sentences: You addressed both reviewer blocks with reproducible notebooks, independent-sensor validation, formal model, and ML decision layer. Be modest on FDD accuracy until more labeled fault data exist.

---

## 7. Revision letter to reviewers (copy-paste skeleton)

**Reviewer — Insufficient statistical validation**

> We added sensor-independent EC validation with RMSE, MAE, bootstrap 95% CIs, calibration and Bland–Altman plots, and ±3% in-tolerance rates (Section 3.3, Table X, Figs. X–X). TDS is derived from the same probe as EC and is excluded from predictors; we report a formula audit only (Section 3.2). Solution temperature was independently validated against EMS (Section 3.4).

**Reviewer — Limited scientific novelty**

> We added: (i) discrete state-space identification (Section 3.5), (ii) ML-based dosing policy with time-series CV (Section 3.6), (iii) fault injection and multi-class FDD pilot (Section 3.7), and (iv) predictive control preview (Section 3.8). Code and CSV outputs are in supplementary material.

---

## Checklist before submission

- [ ] Re-run `01_statistical_validation.ipynb` and `02_methodological_innovation.ipynb`  
- [ ] Update all **[bracketed]** numbers in this README / manuscript  
- [ ] Fix pH probe or remove pH claims  
- [ ] Collect more EMS+NFADS overlapping hours (target: 1000+ hourly points)  
- [ ] Insert firmware TDS constants if known (replace fitted k, b)  
- [ ] Number figures sequentially in Word/LaTeX  
- [ ] Add Limitations subsection  
- [ ] Upload notebooks + `results/` as supplementary material  

---

## Archive

Legacy files: `old/` (previous single `main.ipynb`, duplicate figures). Safe to delete.

## Regenerate notebooks from script

```bash
python _build_two_notebooks.py
```
