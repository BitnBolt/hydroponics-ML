from IPython.display import display, Markdown

CFG = {c['key']: c for c in PLOT_CONFIGS}
# Sensors whose reference meter actually varied during the test (calibration is identifiable)
VALID_KEYS = [c['key'] for c in PLOT_CONFIGS if datasets[c['key']]['meter'].nunique() > 1]
NAME = {'tds': 'TDS', 'water_temp': 'Nutrient temp.', 'ems_temp': 'Air temp.', 'lux': 'Light'}


def resolution(a):
    """Smallest non-zero step between distinct logged values (= display/quantisation resolution)."""
    u = np.unique(np.round(np.asarray(a, float), 6))
    return float(np.diff(u).min()) if len(u) > 1 else float('nan')


rows = []
for cfg in PLOT_CONFIGS:
    k, d, meta = cfg['key'], datasets[cfg['key']], NARRATIVE_META[cfg['key']]
    dt = d['time'].diff().dt.total_seconds().dropna()
    rows.append({
        'Quantity': NAME[k], 'Node': meta['node'].replace(' node', ''),
        'Onboard sensor': meta['sensor_name'], 'Reference': meta['meter_name'],
        'Start': d['time'].iloc[0].strftime('%H:%M:%S'), 'End': d['time'].iloc[-1].strftime('%H:%M:%S'),
        'Duration (min)': (d['time'].iloc[-1] - d['time'].iloc[0]).total_seconds() / 60,
        'n pairs': len(d), 'Sampling (s)': float(dt.median()),
        'Ref. min': d['meter'].min(), 'Ref. max': d['meter'].max(), 'Ref. mean': d['meter'].mean(),
        'Ref. SD': d['meter'].std(ddof=0), 'Ref. span': d['meter'].max() - d['meter'].min(),
        'Ref. resolution': resolution(d['meter']), 'Sensor resolution': resolution(d['sensor']),
        'Reference varied?': 'yes' if d['meter'].nunique() > 1 else 'NO (constant)',
    })
collection_table = pd.DataFrame(rows)
collection_table.to_csv('review_q1_data_collection.csv', index=False)

print('TABLE R1-A  Data-collection summary (computed from the raw Excel logs; the logs hold clock time only, no calendar date)')
display(collection_table.round(4))
