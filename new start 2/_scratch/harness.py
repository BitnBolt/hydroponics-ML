import json, sys, matplotlib
matplotlib.use('Agg')
nb=json.load(open('main.ipynb',encoding='utf8'))
g={}
import builtins
def run(src,name):
    src=''.join(l for l in src.splitlines(True) if not l.startswith('%matplotlib'))
    exec(compile(src,name,'exec'),g)
import io, contextlib
for i in [1,2,3,6,8]:
    buf=io.StringIO()
    with contextlib.redirect_stdout(buf): run(''.join(nb['cells'][i]['source']),f'cell{i}')
for n in ['q1_a','q1_b','q1_c','q1_d','q2_a']:
    print('########',n)
    run(open(f'_scratch/cells/{n}.py',encoding='utf8').read(),n)
