"""Plots from audited records. Missing or unproven optima remain visible gaps."""
import numpy as np
import matplotlib.pyplot as plt
from rep_audit import coverage, experiment_configs, rank_defender

PVALUES = (.09, .17, .25)
COLORS = ('blue', 'red', '#c57c31')
MARKERS = ('o','o','x')


def plot_figure(number, rows, horizons=range(1,26), label='Independent cached reconstruction'):
    horizons = list(horizons)
    if number == 2:
        fig, axes = plt.subplots(2,4,figsize=(15,6),sharex=True,sharey='row')
        panels = [(r,c,s,{'amax':c+1}) for r,s in enumerate(('qt_nmp','furuta_zero')) for c in range(4)]
    elif number == 3:
        fig, axes = plt.subplots(3,2,figsize=(10,9),sharex=True,sharey='col')
        panels = [(r,c,s,{'detector':d}) for r,d in enumerate(('bin','bin_chi2','chi2'))
                  for c,s in enumerate(('qt_nmp','furuta_zero'))]
    elif number == 4:
        fig, axes = plt.subplots(2,5,figsize=(16,6),sharex=True,sharey='row')
        panels = [(r,c,s,{'window':w}) for r,s in enumerate(('furuta_zero','furuta_hold'))
                  for c,w in enumerate((10,12,14,16,18))]
    else:
        raise ValueError('Figure must be 2, 3 or 4.')
    for r,c,system,filters in panels:
        axis = axes[r,c]
        for p,color,marker in zip(PVALUES,COLORS,MARKERS):
            selected = [row for row in rows if row['system']==system and row['config']['p']==p
                        and all(row['config'][key]==value for key,value in filters.items())]
            # Index by horizon; no interpolation or line bridging across missing solves.
            values = {row['ell']:row['omega'] for row in selected if row.get('proven_optimal')}
            y = [values.get(ell,np.nan) for ell in horizons]
            axis.plot(horizons,y,marker=marker,color=color,markersize=4,
                      markerfacecolor='none' if p==.17 else color,label=f'p-hat={p}')
        title = system.replace('qt_nmp','Tank HOLD').replace('furuta_','Furuta ')
        axis.set_title(title+'\n'+', '.join(f'{key}={value}' for key,value in filters.items()),fontsize=10)
        axis.set_xlim(min(horizons),max(horizons))
        axis.grid(alpha=.3)
        if r==axes.shape[0]-1:axis.set_xlabel('attack horizon ell [periods]')
        if c==0:axis.set_ylabel('attack effectiveness omega')
    handles, labels = axes[0,0].get_legend_handles_labels()
    fig.legend(handles,labels,loc='upper center',ncol=3,bbox_to_anchor=(.5,.95))
    fig.suptitle(f'Figure {number}: {label}',y=.995,fontsize=13)
    fig.tight_layout(rect=(0,.04,1,.87))
    fig.text(.5,.01,'Each marker is a separate optimization. Missing/unproven results are gaps; no extrapolation.',ha='center',fontsize=9)
    return fig, coverage(rows,experiment_configs(number),horizons)


def defender_heatmap(summary, system='furuta_hold', detector='bin', alpha=.01, amax=4):
    selected = summary[(summary.system==system)&(summary.detector==detector)
                       &(summary.alpha==alpha)&(summary.amax==amax)]
    windows=(10,12,14,16,18,20)
    z=np.full((3,6),np.nan)
    for i,p in enumerate(PVALUES):
        for j,w in enumerate(windows):
            row=selected[(selected.p==p)&(selected.window==w)]
            if len(row)==1 and bool(row.iloc[0]['complete']):z[i,j]=row.iloc[0]['worst_omega']
    fig,axis=plt.subplots(figsize=(10,4.6),constrained_layout=True)
    cmap=plt.get_cmap('viridis').copy();cmap.set_bad('#d9d9d9')
    im=axis.imshow(np.ma.masked_invalid(z),origin='lower',aspect='auto',cmap=cmap)
    fig.colorbar(im,ax=axis,label='max omega over explicitly requested horizons')
    axis.set_xticks(range(6),windows);axis.set_yticks(range(3),PVALUES)
    axis.set_xlabel('window n_w');axis.set_ylabel('assumed nominal miss probability')
    axis.set_title(f'{system}, {detector}, alpha={alpha}, amax={amax}\nIncomplete configurations are gray, excluded from ranking')
    for i in range(3):
        for j in range(6):
            axis.text(j,i,'MISSING' if np.isnan(z[i,j]) else f'{z[i,j]:.2e}',ha='center',va='center',fontsize=8,
                      color='black' if np.isnan(z[i,j]) else 'white')
    return fig
