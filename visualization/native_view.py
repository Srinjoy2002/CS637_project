"""Inline Plotly animation: exact Python samples feed physical views and plots."""
import json,math
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from IPython.display import display,HTML,clear_output
import ipywidgets as widgets
from simulation.closed_loop import compare
from attack.detector_diagnostics import Config,diagnose,prefix_diagnostics
from attack.schedule_loader import scenarios

COLORS=['#e49b35','#368bdf','#18a684']

def animation(result,cfg,system='furuta',view='3D',duration=220):
    tank=system=='tank';z=result['z'];N=len(z);time=np.arange(N+1)*result['dt'];srs=result['series']
    kind='xy' if tank else 'scene'
    fig=make_subplots(rows=4,cols=2,specs=[[{'type':kind},{'type':kind}],[{'colspan':2},None],[{'colspan':2},None],[{'colspan':2},None]],
        row_heights=[.46,.23,.21,.10],vertical_spacing=.07,
        subplot_titles=['HOLD · paper model','ZERO · '+('project extension' if tank else 'paper model'),'Plant response · shared initial condition and schedule','Applied actuator command u[k]','Timing decisions: 0 hit / 1 miss'])
    dynamic=[]
    # Fixed schematic geometry, dynamic states only. Tank display is explicitly a deviation gauge.
    maxlevel=max(.1,max(abs(v) for s in srs for a in s['x'] for v in a[:4])) if tank else 1
    nominal_arms=[]
    if not tank:
        for s in srs:
            n=np.array(s['nominal']);nominal_arms.append(np.r_[0,np.cumsum((n[:-1,2]+n[1:,2])*.5*result['dt'])])
    def physical(frame):
        traces=[]
        for j,s in enumerate(srs):
            x=s['x'][frame];nom=s['nominal'][frame]
            if tank:
                # Diagram coordinates have no absolute physical height interpretation.
                for i,(a,b) in enumerate([(0,0),(3,0),(0,3),(3,3)]):
                    level=b+1+x[i]/maxlevel*.8;nl=b+1+nom[i]/maxlevel*.8
                    traces += [go.Scatter(x=[a,a+1.3,a+1.3,a,a],y=[b,b,level,level,b],fill='toself',fillcolor='rgba(45,158,214,.35)',line_color=COLORS[j],mode='lines',showlegend=False,hovertemplate=f'Tank {i+1}: deviation {x[i]:.6f}<extra></extra>'),
                               go.Scatter(x=[a,a+1.3],y=[nl,nl],mode='lines',line=dict(color=COLORS[2],dash='dash'),showlegend=False,hoverinfo='skip'),
                               go.Scatter(x=[a+.65],y=[b+1.8],text=[f'T{i+1}: {x[i]:.4f}'],mode='text',textfont=dict(size=12),showlegend=False,hoverinfo='skip')]
            else:
                for nominal in [False,True]:
                    a=nominal_arms[j][frame] if nominal else s['arm'][frame];theta=nom[0] if nominal else x[0]
                    if view=='2D side': a=0.0  # co-rotating projection: preserve the pendulum angle
                    pivot=np.array([.62*np.cos(a),.62*np.sin(a),.25]);tip=pivot+np.array([-.88*np.sin(theta)*np.sin(a),.88*np.sin(theta)*np.cos(a),.88*np.cos(theta)])
                    col=COLORS[2] if nominal else COLORS[j]
                    traces.append(go.Scatter3d(x=[0,pivot[0],tip[0]],y=[0,pivot[1],tip[1]],z=[.25,pivot[2],tip[2]],mode='lines+markers',line=dict(color=col,width=4 if nominal else 8,dash='dash' if nominal else 'solid'),marker=dict(size=4),showlegend=False,hovertemplate=('Nominal' if nominal else 'Attack')+f'<br>θ={theta:.6f} rad<extra></extra>'))
        return traces
    first=physical(0);per=len(first)//2
    for j in range(2):
        for tr in first[j*per:(j+1)*per]:dynamic.append(len(fig.data));fig.add_trace(tr,row=1,col=j+1)
        if tank:
            for a,b in [(0,0),(3,0),(0,3),(3,3)]:
                fig.add_trace(go.Scatter(x=[a,a,a+1.3,a+1.3],y=[b+2,b,b,b+2],mode='lines',line_color='#7f96ad',showlegend=False,hoverinfo='skip'),row=1,col=j+1)
                fig.add_trace(go.Scatter(x=[a,a+1.3],y=[b+1,b+1],mode='lines',line=dict(color='#8796a4',dash='dot'),showlegend=False,hoverinfo='skip'),row=1,col=j+1)
            # Real topology; flow magnitude is not invented from unknown equilibrium data.
            pipes=[([.65,.65],[3,2]),([3.65,3.65],[3,2]),([-1,-1,.65],[-.6,2.5,2.5]),([-1,-1,3.65,3.65],[2.5,5.5,5.5,5]),([5.3,5.3,3.65],[-.6,2.5,2.5]),([5.3,5.3,.65,.65],[2.5,5.8,5.8,5]),([.65,.65],[0,-.6]),([3.65,3.65],[0,-.6])]
            for px,py in pipes:fig.add_trace(go.Scatter(x=px,y=py,mode='lines',line=dict(color='#9bbad1',width=3),showlegend=False,hoverinfo='skip'),row=1,col=j+1)
            fig.add_trace(go.Scatter(x=[-1,5.3],y=[-.6,-.6],text=['Pump 1','Pump 2'],mode='markers+text',textposition='bottom center',marker=dict(size=18,color='#368bdf'),showlegend=False),row=1,col=j+1)
            fig.update_xaxes(range=[-1.8,6.2],visible=False,row=1,col=j+1);fig.update_yaxes(range=[-1.5,6.3],visible=False,row=1,col=j+1)
        else:
            fig.add_trace(go.Scatter3d(x=[0,0],y=[0,0],z=[0,.5],mode='lines',line=dict(color='#8499b0',width=12),showlegend=False),row=1,col=j+1)
            theta=np.linspace(0,2*np.pi,60);fig.add_trace(go.Scatter3d(x=.62*np.cos(theta),y=.62*np.sin(theta),z=np.full(60,.25),mode='lines',line=dict(color='#9caab8',width=2,dash='dot'),showlegend=False),row=1,col=j+1)
    for j,s in enumerate(srs):
        for i in range(2 if tank else 1):fig.add_trace(go.Scatter(x=time,y=np.array(s['x'])[:,i],name=('HOLD' if j==0 else 'ZERO')+(f' T{i+1}' if tank else ' angle'),line=dict(color=COLORS[j],dash='dash' if i else 'solid')),row=2,col=1)
        for i in range(len(s['u'][0])):fig.add_trace(go.Scatter(x=time,y=np.array(s['u'])[:,i],name=('HOLD' if j==0 else 'ZERO')+f' u{i+1}',line=dict(color=COLORS[j],shape='hv',dash='dash' if i else 'solid')),row=3,col=1)
    for i in range(2 if tank else 1):fig.add_trace(go.Scatter(x=time,y=np.array(srs[0]['nominal'])[:,i],name='Nominal'+(f' T{i+1}' if tank else ''),line=dict(color=COLORS[2],dash='dot')),row=2,col=1)
    fig.add_trace(go.Bar(x=time[:-1],y=np.ones(N),width=result['dt']*.85,marker_color=['#f36b7f' if b else '#4dc9a5' for b in z],customdata=z,hovertemplate='t=%{x}<br>z=%{customdata}<extra></extra>',showlegend=False),row=4,col=1)
    base_annotations=list(fig.layout.annotations);prefix=prefix_diagnostics(z,cfg)
    def frame_layout(f):
        d=prefix[f-1] if f else None;period=min(f,N-1)
        text=f'k={f} · t={f*result["dt"]:.3f}s · '+('complete' if f==N else f'z[k]={z[period]} · '+('deadline MISS' if z[period] else 'deadline HIT'))
        if d:text+=f' | prefix: WD {"pass" if d["watchdog"] else "FAIL"} · Bin {"pass" if d["binomial"] else "FAIL"} · χ²={d["chi_square"] if d["chi_square"] is not None else "n/a"}'
        text+='<br>'+ ' | '.join(('HOLD' if j==0 else 'ZERO')+' u[k]='+str([round(v,5) for v in s['u'][f]])+' → u[k+1]='+str([round(v,5) for v in s['u'][min(f+1,N)]]) for j,s in enumerate(srs))
        if not tank and any(abs(s['x'][f][0])>.2 for s in srs):text+='<br>SMALL-ANGLE CAUTION: |θ| &gt; 0.2 rad; no physical-fall claim.'
        shapes=[]
        for row in [2,3,4]:
            axis=('x'+str(row+1)) if tank else ('x' if row==2 else 'x'+str(row-1))
            # Obtain actual subplot axis references instead of relying on scene numbering.
            subplot=fig.get_subplot(row,1);xref=subplot.xaxis.plotly_name.replace('axis','');yref=subplot.yaxis.plotly_name.replace('axis','')+' domain'
            shapes.append(dict(type='line',x0=time[f],x1=time[f],y0=0,y1=1,xref=xref,yref=yref,line=dict(color='#e65b74',width=1)))
        return go.Layout(annotations=base_annotations+[dict(text=text,x=.5,y=-.10,xref='paper',yref='paper',showarrow=False,font=dict(size=11))],shapes=shapes)
    fig.frames=[go.Frame(name=str(f),data=physical(f),traces=dynamic,layout=frame_layout(f)) for f in range(N+1)]
    fig.update_layout(frame_layout(0));fig.update_layout(template='plotly_white',height=1050,margin=dict(l=60,r=35,t=95,b=190),
        title=dict(text=('Quadruple-tank deviation replay' if tank else 'Furuta rotary pendulum · exact linear model')+'<br><sup>Orange HOLD · blue ZERO · green nominal. Playback is slowed for teaching.</sup>'),
        legend=dict(orientation='h',y=1.08),
        updatemenus=[dict(type='buttons',x=0,y=-.19,buttons=[dict(label='▶ Play / resume',method='animate',args=[None,dict(frame=dict(duration=duration,redraw=True),transition=dict(duration=0),fromcurrent=True)]),dict(label='Ⅱ Pause',method='animate',args=[[None],dict(frame=dict(duration=0,redraw=False),mode='immediate')]),dict(label='Reset',method='animate',args=[['0'],dict(frame=dict(duration=0,redraw=True),mode='immediate')])])],
        sliders=[dict(active=0,y=-.04,len=.98,currentvalue=dict(prefix='Sample '),steps=[dict(label=str(f),method='animate',args=[[str(f)],dict(mode='immediate',frame=dict(duration=0,redraw=True),transition=dict(duration=0))]) for f in range(N+1)])])
    for row in (2,3,4):fig.update_xaxes(title_text='Time [s]',range=[0,time[-1]],row=row,col=1)
    fig.update_yaxes(title_text='Deviation [model units]' if tank else 'θ [rad]',row=2,col=1);fig.update_yaxes(title_text='Input [REP units]',row=3,col=1)
    if not tank:
        scene=dict(xaxis=dict(range=[-1.3,1.3],title='schematic x'),yaxis=dict(range=[-1.3,1.3],title='schematic y'),zaxis=dict(range=[0,1.4],title='upright axis'),aspectmode='cube',camera=dict(eye=dict(x=2,y=0,z=.3) if view=='2D side' else dict(x=1.5,y=1.5,z=1)))
        fig.update_layout(scene=scene,scene2=scene)
    return fig

def native_lab(system='furuta',case_data=None,runner=None,results_dir=None):
    """Native Jupyter widget laboratory; Gurobi is the optional optimizer."""
    if case_data is None:case_data=scenarios()
    available=[c for c in case_data if c['system']==system]
    preset=widgets.Dropdown(options=[(c['title'],i) for i,c in enumerate(available)],description='Scenario:',layout=widgets.Layout(width='650px'))
    seq=widgets.Text(value=''.join(map(str,available[0]['interior'])),description='Schedule:',layout=widgets.Layout(width='650px'))
    detector=widgets.Dropdown(options=[('Binomial','bin'),('Geometric / χ²','chi2'),('Combined','bin_chi2'),('Multiwindow extension','multi')],value=available[0]['config']['detector'],description='Detector:')
    window=widgets.IntSlider(value=available[0]['config']['window'],min=2,max=40,description='Window:');p=widgets.FloatSlider(value=.25,min=.01,max=.4,step=.01,description='Nominal p:')
    alpha=widgets.Dropdown(options=[.005,.01,.05],value=.01,description='α:');amax=widgets.IntSlider(value=4,min=1,max=8,description='Max run:')
    scale=widgets.FloatSlider(value=1,min=.1,max=2,step=.1,description='x₀ scale:');tail=widgets.IntSlider(value=20,min=0,max=150,step=5,description='Tail hits:')
    safety=widgets.FloatText(value=.2 if system=='furuta' else .5,description='Threshold:')
    view=widgets.Dropdown(options=['3D','2D side'],description='View:');speed=widgets.Dropdown(options=[('Slow',450),('Normal',220),('Fast',70)],value=220,description='Frame ms:')
    play=widgets.Button(description='Build / demonstrate attack',button_style='success',layout=widgets.Layout(width='230px'))
    normal=widgets.Button(description='Normal operation');download=widgets.Button(description='Save replay JSON')
    opt=widgets.Button(description='Optimize with Gurobi');ell=widgets.IntSlider(value=10,min=1,max=25,description='Opt. ℓ:')
    output=widgets.Output();latest={}
    def settings():return Config(p.value,alpha.value,window.value,amax.value,detector.value)
    def change(change):
        c=available[preset.value];seq.value=''.join(map(str,c['interior']));window.value=c['config']['window'];detector.value=c['config']['detector'];p.value=c['config']['p'];amax.value=c['config']['amax'];alpha.value=c['config']['alpha']
    preset.observe(change,names='value')
    def render(_=None):
        with output:
            clear_output(wait=True)
            try:
                cfg=settings();r=compare(system,seq.value,tail.value,scale.value,safety.value);d=diagnose(r['z'][:r['ell']+2],cfg)
                latest.update(result=r,diagnostics=d)
                label='Exact REP linear model. '+('Tank ZERO is a project extension; surfaces show deviations, NOT absolute cm. Pipes show routing in this inline view; signed flow animation is available in the local dashboard.' if system=='tank' else 'Rotary geometry is schematic; arm orientation integrates the modeled angular velocity. The 0.2-rad small-angle caution is a heuristic, not a certified boundary.')
                display(HTML('<div style="padding:15px;background:#eaf3fb;color:#17334d;border-left:4px solid #2576a7">'+label+'</div>'))
                def word(v):return 'not evaluated' if v is None else 'PASS' if v else 'FAIL'
                print('Final REP checks:',{a:word(d[a]) for a in ['watchdog','binomial','geometric','accepted']})
                print(f'Binomial threshold={d["binomial_threshold"]}; χ²={d["chi_square"]}; threshold={d["chi_threshold"]:.6f}; closed runs={d["run_counts"]}')
                for s in r['series']:
                    m=s['metrics'];print(f'{s["name"]}: J={m["terminal"]:.10g}, nominal={m["nominal"]:.10g}, ω={m["omega"]:.10g}; peak cost={m["peak"]:.6g}; threshold exceeded={s["safety"]["violated"]}')
                print('All diagnoses use the same exact state arrays as the animation and plots. Prefix checks below are an online-monitor extension.')
                fig=animation(r,cfg,system,view.value,speed.value)
                display(HTML(fig.to_html(full_html=False,include_plotlyjs=True,auto_play=False)))
            except Exception as e:print(type(e).__name__+': '+str(e))
    def solve(_):
        with output:
            clear_output(wait=True);print('Original REP Gurobi optimization requested. New result, not a published table entry.')
            try:
                if runner is None or not runner.preflight_passed:
                    raise RuntimeError('Run the notebook local-license cell successfully first.')
                if scale.value!=1:
                    raise ValueError('Official optimizer uses the paper initial state; reset x0 scale to 1.')
                if settings().detector=='multi':
                    raise ValueError('Multiple windows are a project extension; the original optimizer supports bin, chi2, and bin_chi2.')
                r=runner.solve('furuta_hold' if system=='furuta' else 'qt_nmp',ell.value,settings(),
                               results_dir or 'outputs/widget_runs')
                print({k:r.get(k) for k in ('status','gap','bound','omega','validation_passed','proven_optimal')})
                if not r.get('schedule'):return
                seq.value=''.join(map(str,r['interior']))
            except Exception as e:print(type(e).__name__+': '+str(e));return
        render()
    def save(_):
        if not latest:return
        from pathlib import Path
        path=Path(results_dir or 'outputs')/(system+'_replay.json')
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(latest,indent=2));print('Saved',path.resolve())
    def nominal(_):seq.value='0'*25;render()
    play.on_click(render);normal.on_click(nominal);opt.on_click(solve);download.on_click(save)
    display(widgets.VBox([preset,seq,widgets.HBox([detector,alpha,view]),widgets.HBox([window,p]),widgets.HBox([amax,scale]),widgets.HBox([tail,safety,speed]),widgets.HBox([play,normal,download]),widgets.HBox([ell,opt]),output]))
    render()
    return latest
