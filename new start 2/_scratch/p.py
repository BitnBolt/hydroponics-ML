import numpy as np, pandas as pd
from scipy import stats
D='data/'
files={'tds':'Dosing_TDS.xlsx','water_temp':'Dosing_Water Temp (1).xlsx','ems_temp':'EMS_temp_sensor (1).xlsx','lux':'LMS_Lux (1).xlsx'}
dat={}
for k,f in files.items():
    d=pd.read_excel(D+f).dropna(how='all'); d.columns=['t','s','m']; d['t']=pd.to_datetime('2026-06-03 '+d['t'].astype(str)); dat[k]=d.dropna().reset_index(drop=True)
for k,d in dat.items():
    dt=d.t.diff().dt.total_seconds().dropna()
    print(k,len(d),'dt median',dt.median(),'unique dt',sorted(dt.unique())[:6],'gaps>med',(dt>dt.median()).sum())
    print(' sensor uniq',d.s.nunique(),'meter uniq',d.m.nunique(), 'meter span',d.m.max()-d.m.min())
    # step resolution
    for c in ['s','m']:
        u=np.sort(d[c].unique()); df=np.diff(u); print('  ',c,'min step',df.min() if len(df) else None)
def fit(x,y):
    sl,ic,r,p,se=stats.linregress(x,y); return sl,ic
def met(p,y):
    e=p-y; sse=(e**2).sum(); sst=((y-y.mean())**2).sum()
    return dict(rmse=np.sqrt((e**2).mean()),mae=np.abs(e).mean(),bias=e.mean(),r2=1-sse/sst if sst>0 else np.nan)
for k in ['tds','ems_temp','lux']:
    d=dat[k]; x=d.s.values.astype(float); y=d.m.values.astype(float); n=len(x)
    # blocked 5-fold
    K=5; idx=np.array_split(np.arange(n),K); pred=np.empty(n)
    for f in idx:
        tr=np.setdiff1d(np.arange(n),f); sl,ic=fit(x[tr],y[tr]); pred[f]=sl*x[f]+ic
    print(k,'blockedCV',met(pred,y))
    # chronological 70/30
    c=int(.7*n); sl,ic=fit(x[:c],y[:c]); print(k,'chrono70/30 test',met(sl*x[c:]+ic,y[c:]),'raw test',met(x[c:],y[c:]))
    # random LOO
    pr=np.empty(n)
    for i in range(n):
        m=np.ones(n,bool); m[i]=False; sl,ic=fit(x[m],y[m]); pr[i]=sl*x[i]+ic
    print(k,'LOO',met(pr,y))
    # autocorr of residual
    sl,ic=fit(x,y); r=y-(sl*x+ic); r1=np.corrcoef(r[:-1],r[1:])[0,1]; dw=((np.diff(r))**2).sum()/(r**2).sum()
    print(k,'lag1',r1,'DW',dw,'neff',n*(1-r1)/(1+r1))
