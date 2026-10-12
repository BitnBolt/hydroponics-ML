K_FOLDS = 5          # contiguous (time-ordered) folds
TRAIN_FRAC = 0.70    # chronological hold-out


def fit_line(x, y):
    slope, intercept = np.polyfit(x, y, 1)
    return slope, intercept


def metrics(pred, true):
    pred, true = np.asarray(pred, float), np.asarray(true, float)
    e = pred - true
    sst = np.sum((true - true.mean()) ** 2)
    return dict(
        RMSE=float(np.sqrt(np.mean(e ** 2))), MAE=float(np.mean(np.abs(e))), Bias=float(np.mean(e)),
        R2=float(1 - np.sum(e ** 2) / sst) if sst > 1e-12 else float('nan'),
    )


def accuracy_pct(rmse, ref):
    """Headline accuracy (%) = 100 * (1 - RMSE / mean of reference)."""
    return 100.0 * (1.0 - rmse / float(np.mean(ref)))


def span_accuracy_pct(rmse, ref):
    """Span-normalised accuracy (%) = 100 * (1 - RMSE / (max - min of reference))."""
    span = float(np.max(ref) - np.min(ref))
    return 100.0 * (1.0 - rmse / span) if span > 0 else float('nan')


def oof_blocked(x, y, k=K_FOLDS):
    """Out-of-fold predictions with k CONTIGUOUS time blocks (each block is predicted by a line fitted on the rest)."""
    n = len(x); pred = np.empty(n)
    for fold in np.array_split(np.arange(n), k):
        train = np.setdiff1d(np.arange(n), fold)
        s, i = fit_line(x[train], y[train]); pred[fold] = s * x[fold] + i
    return pred


def oof_loo(x, y):
    """Leave-one-out (LEAKY for autocorrelated series -> shown only as a contrast)."""
    n = len(x); pred = np.empty(n)
    for j in range(n):
        m = np.ones(n, bool); m[j] = False
        s, i = fit_line(x[m], y[m]); pred[j] = s * x[j] + i
    return pred


PROT = {}
prot_rows = []
for k in VALID_KEYS:
    d = datasets[k]; x, y = d['sensor'].to_numpy(float), d['meter'].to_numpy(float); n = len(x)
    s, i = fit_line(x, y)
    ins = metrics(s * x + i, y)                       # (1) original: fit and score on the same data
    oof = oof_blocked(x, y); blk = metrics(oof, y)    # (2) blocked 5-fold CV (primary)
    c = int(round(TRAIN_FRAC * n)); sc, ic = fit_line(x[:c], y[:c])
    cho = metrics(sc * x[c:] + ic, y[c:])             # (3) first 70 % train -> last 30 % test
    raw_te = metrics(x[c:], y[c:])
    loo = metrics(oof_loo(x, y), y)                   # (4) LOO (leaky contrast)
    PROT[k] = dict(x=x, y=y, n=n, insample=ins, blocked=blk, chrono=cho, chrono_raw=raw_te, loo=loo,
                   oof=oof, n_train=c, n_test=n - c, chrono_line=(sc, ic), line=(s, i))
    for name, m, tgt in [('In-sample (original)', ins, y), ('Blocked 5-fold CV (out-of-fold)', blk, y),
                         ('Chronological 70/30 hold-out', cho, y[c:]), ('Leave-one-out (leaky)', loo, y)]:
        prot_rows.append({'Quantity': NAME[k], 'Protocol': name, 'RMSE': m['RMSE'], 'MAE': m['MAE'], 'Bias': m['Bias'],
                          'R2': m['R2'], 'Accuracy % (vs mean)': accuracy_pct(m['RMSE'], tgt)})

protocol_table = pd.DataFrame(prot_rows)
protocol_table.to_csv('review_q1_validation_protocols.csv', index=False)
print('TABLE R1-B  Same OLS model, four evaluation protocols (units as in each sensor; R2 = n/a if the test reference is constant)')
display(protocol_table.round(4))

# ---- Figure R1: blocked-CV timeline -------------------------------------------------------------
fig, axes = plt.subplots(len(VALID_KEYS), 1, figsize=(12, 3.6 * len(VALID_KEYS)))
for ax, k in zip(np.atleast_1d(axes), VALID_KEYS):
    d, P = datasets[k], PROT[k]
    for j, fold in enumerate(np.array_split(np.arange(P['n']), K_FOLDS)):
        if j % 2 == 0:
            ax.axvspan(d['time'].iloc[fold[0]], d['time'].iloc[fold[-1]], color='#d5d8dc', alpha=0.45, lw=0)
    ax.plot(d['time'], d['sensor'], color='#E67E22', lw=1.2, alpha=0.8, label='Raw sensor')
    ax.plot(d['time'], d['meter'], color='#2471A3', lw=1.6, ls='--', label='Reference meter')
    ax.plot(d['time'], P['oof'], color='#1E8449', lw=1.6, label='OLS prediction, fold held out (out-of-fold)')
    ax.set_title(f"{CFG[k]['y_label']}  |  n = {P['n']}  |  out-of-fold RMSE = {P['blocked']['RMSE']:.3g} {CFG[k]['rmse_unit']}",
                 fontsize=10)
    ax.set_ylabel(CFG[k]['y_label']); ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax.legend(loc='best', fontsize=8)
fig.suptitle('Blocked 5-fold cross-validation (grey/white bands = contiguous test folds, never shuffled)', y=1.0)
fig.tight_layout(); fig.savefig(FIG_DIR / 'review_q1_blocked_cv.png', dpi=200, bbox_inches='tight'); plt.show()
