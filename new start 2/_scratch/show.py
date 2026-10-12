exec(open('_scratch/harness.py',encoding='utf-8-sig').read().split("for n in ['q1_a'")[0])
for n in ['q1_a','q1_b','q1_c','q1_d','q2_a']:
    import io, contextlib
    with contextlib.redirect_stdout(io.StringIO()): run(open(f'_scratch/cells/{n}.py',encoding='utf8').read(),n)
import pandas as pd
pd.set_option('display.width',250); pd.set_option('display.max_columns',50); pd.set_option('display.max_colwidth',40)
print(g['collection_table'].T.to_string())
print(g['protocol_table'].round(4).to_string())
print(g['ci_table'][[c for c in g['ci_table'].columns if not c.startswith('_')]].T.to_string())
print(g['accuracy_table'].round(3).T.to_string())
print(g['dec_table'].round(4).T.to_string())
print(g['QUANT']); print(g['PROT']['ems_temp']['chrono'],g['PROT']['ems_temp']['n_test'])

