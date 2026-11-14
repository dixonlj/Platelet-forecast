#!/usr/bin/env python3
"""Reproducible v4 tables from existing results (public aggregate Aachen data only).
Run: OMP_NUM_THREADS=1 .venv/bin/python scripts/22_tables_v4.py
No clinical use. No plotting: v4 replaces the misleading mean/error-bar figure with a table.
"""
from pathlib import Path
import numpy as np
import pandas as pd
P=Path(__file__).resolve().parent.parent
T=P/'paper/tables'; R=P/'results'
N={'dow4':'Weekday average','hgbr':'Gradient boosting','chronos':'Chronos-Bolt','sarima':'SARIMA','lasso':"Authors’ LASSO",'rnn':"Authors’ RNN",'naive':'Yesterday','last7':'Last 7 days','same_dow':'Same weekday last week'}
MS=['dow4','hgbr','chronos','sarima','lasso','rnn']
def md(name,cols,rows,cap=18,widths=None):
    # Separator dash counts set relative column widths in pandoc (proportional to the longest cell).
    wid=[max([len(w) + 3 for w in str(cols[i]).split()] + [min(len(str(r[i])), cap) + 2 for r in rows] + [10])
         for i in range(len(cols))]
    if widths: wid=widths
    s='| '+' | '.join(cols)+' |\n|'+'|'.join(['-'*wid[0]]+['-'*(w-1)+':' for w in wid[1:]])+'|\n'
    s+=''.join('| '+' | '.join(map(str,r))+' |\n' for r in rows)
    (T/(name+'_v4.md')).write_text(s)
def p(x): return '<0.001' if x<.001 else ('1.00' if x>=.9995 else f'{x:.3g}')
inv=pd.concat([pd.read_csv(R/'m5/08_multiyear_inventory.csv'),pd.read_csv(R/'m6/13_multiyear_inventory.csv').query("model=='sarima'")])
h=inv.query("target=='hospital'")
md('table2',['Forecast','Mean waste %','Mean lost units/year'],[[N[m],f'{h[h.model==m].waste_pct_mean.mean():.2f}',f'{h[h.model==m].wasted_plus_emergency_mean.mean():.0f}'] for m in MS])
for col,n,title,fmt in [('waste_pct_mean','annual_waste','Waste %','.2f'),('wasted_plus_emergency_mean','annual_lost','Lost units','.0f')]:
    pv=h.pivot(index='year',columns='model',values=col)
    md(n,['Year']+[N[m] for m in MS],[[int(y)]+[format(pv.loc[y,m],fmt) for m in MS] for y in pv.index])
dm=pd.read_csv(R/'m8/20_dm_1day_holm.csv')
for sel,n in [(~dm.model.str.contains('sarima'),'dm'),(dm.model.str.contains('sarima'),'sarima_dm')]:
    rows=[]
    for _,r in dm[sel].sort_values(['model','year']).iterrows():
        a,b=r.model[3:].split('_vs_'); rows.append([int(r.year),N[a]+' vs '+N[b],f'{r.mean_abs_err_diff:.3f}',p(r.dm_p),p(r.holm_p)])
    md(n,['Year','Comparison','MAE difference','Raw p','Holm p (35 tests)'],rows)
a=pd.read_csv(R/'m8/20_accuracy_by_horizon.csv')
dmh=pd.read_csv(R/'m8/20_dm_by_horizon.csv')
rows=[]
for n in [1,2,4]:
    for m in MS:
        g=a[(a.model==m)&(a.horizon_days==n)]
        if g.empty: continue
        wa=a[(a.model=='dow4')&(a.horizon_days==n)].set_index('year').mae
        if m=='dow4': yb=pv_='—'; hs='—'
        else:
            yb=f"{int((g.set_index('year').mae<wa).sum())}/7"
            d=dmh[(dmh.model==m)&(dmh.horizon_days==n)]
            pv_=p(float(d[d.year=='pooled 2012-2018'].dm_p.iloc[0]))
            hs=str(int((d[d.year!='pooled 2012-2018'].holm_p_within_horizon.astype(float)<.05).sum()))
            if n==1:  # 1-day: use the paper's family of all 35 one-day tests (script 20, part B)
                hs=str(int((dm[dm.model==f'DM_{m}_vs_dow4'].holm_p<.05).sum()))
        rows.append([f'{n}-day' if n>1 else '1-day',N[m],f'{g.mae.mean():.2f}',f'{g.mean_error_actual_minus_fc.mean():+.2f}',yb,hs,pv_])
md('accuracy_horizon',['Horizon (total of next n days)','Forecast','Mean MAE (units)','Mean bias (actual − forecast)','Years more accurate than WA','Years significant after Holm*','Pooled DM p (2012–2018)'],rows)
x=pd.read_csv(R/'m8/20_year_level_tests.csv')
for prior,n in [(False,'year_tests'),(True,'prior_tests')]:
    rows=[]
    for _,r in x[x.analysis.str.startswith('cushion')==prior].iterrows():
        rows.append([r.outcome,N[r.model],str(r.years_better)+'/7',p(r.sign_p),p(r.wilcoxon_p),f'{r.mean_diff:+.2f} ({r.ci_lo:+.2f} to {r.ci_hi:+.2f})'])
    md(n,['Outcome','Forecast vs weekday average','Years lower','Sign p','Wilcoxon p','Mean difference (95% CI)'],rows)
pr=pd.read_csv(R/'m8/19_prior_year_cushion.csv')
md('prior_summary',['Forecast','Waste %','Short days/year','Emergency units/year','Lost units/year'],[[N[m]]+[f'{pr[pr.model==m][c].mean():.2f}' for c in ['waste_pct_mean','short_days_mean','emergency_units_mean','wasted_plus_emergency_mean']] for m in MS])
md('prior_annual',['Year','Forecast','Fixed k','Waste %','Short days','Emergency units','Lost units'],[[int(r.year),N[r.model],f'{r.k_prior_year:.3f}',f'{r.waste_pct_mean:.2f}',f'{r.short_days_mean:.2f}',f'{r.emergency_units_mean:.1f}',f'{r.wasted_plus_emergency_mean:.1f}'] for _,r in pr.iterrows()])
r=pd.read_csv(R/'m8/21_robustness_summary.csv')
rb=pd.read_csv(R/'m8/21_multiyear_robustness.csv')
from scipy import stats as _st
def _ci(sc,m,col):
    g=rb[rb.scenario==sc].pivot(index='year',columns='model',values=col); d=g[m]-g.dow4
    se=d.std(ddof=1)/np.sqrt(len(d)); t=_st.t.ppf(.975,len(d)-1); return d.mean()-t*se,d.mean()+t*se
rows=[]
for _,z in r.iterrows():
    if z.model=='dow4':
        rows.append([z.scenario,N[z.model],f'{z.mean_waste_pct:.2f}','—',f'{z.mean_lost_units:.0f}','—']); continue
    a,b=_ci(z.scenario,z.model,'waste_pct_mean'); c,d=_ci(z.scenario,z.model,'wasted_plus_emergency_mean')
    rows.append([z.scenario,N[z.model],f'{z.mean_waste_pct:.2f}',f'{z.mean_waste_gap_pts:+.2f} ({a:+.2f} to {b:+.2f}); {int(z.years_less_waste_than_wa)}/7',
                 f'{z.mean_lost_units:.0f}',f'{z.mean_lost_gap_units:+.0f} ({c:+.0f} to {d:+.0f}); {int(z.years_fewer_lost_than_wa)}/7'])
md('robustness',['Scenario','Forecast','Waste %','Waste gap, points (95% CI); years lower','Lost per year','Lost gap (95% CI); years lower'],rows,widths=[22,15,12,26,12,22])
# Winner counts with SARIMA included; an absolute difference <=0.1 unit/year
# (or <=0.002 percentage points on waste) is labelled a descriptive numerical tie.
rows=[]
for target,g in inv.groupby('target'):
    for col,lab,tol in [('waste_pct_mean','Waste',.002),('wasted_plus_emergency_mean','Lost units',.1)]:
        for scope,mods in [('All nine forecasts',list(N)),('Four main forecasts',MS[:4])]:
            wins={}; ties={}
            for Y,gy in g[g.model.isin(mods)].groupby('year'):
                best=gy[col].min(); mm=gy[gy[col]<=best+tol].model.tolist()
                key=' / '.join(N[m] for m in sorted(mm)); dest=ties if len(mm)>1 else wins
                dest[key]=dest.get(key,0)+1
            for dest,desc in [(wins,'Lowest'),(ties,'Numerical tie')]:
                for k,v in dest.items(): rows.append([{'hospital':'Recorded hospital count','fixed20':'20 short days','fixed50':'50 short days'}[target],lab,scope,k,desc,v])
md('wins',['Short-day target','Outcome','Comparison','Forecast','Status','Years (of 7)'],rows)
# Integer-year replacement for the old floating-year table.
b=pd.read_csv(R/'m5/08_hospital_by_year.csv')
md('hosp_monday',['Year','Recorded Monday share of purchase days'],[[int(z.year),f'{z.monday_share_of_purchase_days:.2f}'] for _,z in b.iterrows()])
# 43% row, alongside the pre-existing shelf-life sweep: split waste and win counts.
b=pd.read_csv(R/'m6/15_models_life_sweep.csv')
rows=[]
for share in [0,.3,.43,.6,1]:
    if share==.43:
        g=pd.read_csv(R/'m8/21_multiyear_robustness.csv');g=g[g.scenario.str.startswith('43%')].rename(columns={'waste_pct_mean':'waste_pct','wasted_plus_emergency_mean':'lost_units'})
    else: g=b[b.share_3day==share]
    w=g.pivot(index='year',columns='model',values='waste_pct'); l=g.pivot(index='year',columns='model',values='lost_units')
    for m in MS[:4]: rows.append([f'{share:.0%}',N[m],f'{w[m].mean():.2f}','—' if m=='dow4' else f'{int((w[m]<w.dow4).sum())}/7','—' if m=='dow4' else f'{int((l[m]<l.dow4).sum())}/7'])
md('life_models',['Share arriving with 3 days','Forecast','Mean waste %','Years less waste than WA','Years fewer lost than WA'],rows)
# Save the five pooled daily tests as explicitly supplementary exploratory results.
b=pd.read_csv(R/'m8/20_dm_1day_pooled.csv')
md('pooled_dm',['Comparison','Test days','Mean MAE difference','Raw p'],[[' vs '.join(N[k] for k in z.comparison.split(' vs ')),int(z.n_days),f'{z.mean_abs_err_diff:.3f}',p(z.dm_p)] for _,z in b.iterrows()])
print('v4 tables generated')

# Compact main tables: per-year values, win counts and full tests in the supplement.
main=x[~x.analysis.str.startswith('cushion')]
rows=[]
for m in MS:
    g=h[h.model==m]
    base_=[N[m],f'{g.waste_pct_mean.mean():.2f}',f'{g.wasted_plus_emergency_mean.mean():.0f}']
    gaps=[]
    for o,fmt in [('Waste (points)','+.2f'),('Wasted + emergency units a year','+.0f')]:
        if m=='dow4': gaps.append('—')
        else:
            z=main[(main.model==m)&(main.outcome==o)].iloc[0]
            gaps.append(f'{z.mean_diff:{fmt}} ({z.ci_lo:{fmt}} to {z.ci_hi:{fmt}})')
    rows.append(base_+gaps)
md('table2',['Forecast','Waste %','Lost units/year','Waste gap (95% CI)','Lost gap (95% CI)'],rows)
pri=x[x.analysis.str.startswith('cushion')]
rows=[]
for m in MS:
    g=pr[pr.model==m]
    row=[N[m],f'{g.short_days_mean.mean():.1f}',f'{g.waste_pct_mean.mean():.2f}',f'{g.wasted_plus_emergency_mean.mean():.0f}']
    if m=='dow4': row.append('—')
    else:
        z=pri[(pri.model==m)&(pri.outcome=='Wasted + emergency units a year')].iloc[0]
        row.append(f'{z.mean_diff:+.0f} ({z.ci_lo:+.0f} to {z.ci_hi:+.0f})')
    rows.append(row)
md('table3',['Forecast','Short days','Waste %','Lost units/year','Lost gap (95% CI)'],rows)
print('compact main tables 2 and 3 written')

# v5: SARIMA runner-up order check (script 24), if present.
ru = R / 'm8/24_sarima_runner_up.csv'
if ru.exists():
    d = pd.read_csv(ru)
    md('sarima_runner_up', ['Horizon', 'MAE, selected order', 'MAE, runner-up order', 'Mean difference', 'Largest yearly absolute difference'],
       [[f'{n}-day', f'{g.mae_selected.mean():.3f}', f'{g.mae_runner_up.mean():.3f}', f'{g.difference.mean():+.3f}',
         f'{g.difference.abs().max():.3f}'] for n, g in d.groupby('horizon_days')])
    print('runner-up table written')
