"""REP v1.2 Furuta visualisation and statistical attack-sequence audits.

Loads the authors' define_system function *without* running main_short.py.
The complete closed-loop dynamics come from the authors' exact matrices.
Designed for use inside the companion Colab notebook.
"""
from __future__ import annotations

import ast
import json
import math
import re
from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import binom, chi2

PAPER_T1 = {
    10: '1110111000111000111011100',
    12: '1011110001101000111101100',
    14: '1101111000110001111011000',
}


def load_define_system(main_short_path: str | Path):
    """Extract only define_system AST from the official main_short.py."""
    path = Path(main_short_path)
    tree = ast.parse(path.read_text(encoding='utf-8'))
    matches = [n for n in tree.body if isinstance(n, ast.FunctionDef)
               and n.name == 'define_system']
    if len(matches) != 1:
        raise RuntimeError('Expected exactly one define_system() in official main_short.py')
    sandbox = {'np': np}
    astmod = ast.Module(body=matches, type_ignores=[])
    exec(compile(astmod, str(path), 'exec'), sandbox)
    fun = sandbox['define_system']
    # Sanity checks without solver.
    for policy in ('furuta_zero', 'furuta_hold'):
        miss, hit, C, Q, x0, nx = fun(policy)
        assert nx == 7 and miss.shape == (7,7) and hit.shape == (7,7)
        assert Q.shape == (7,7) and len(x0) == 7
        assert np.isclose(Q[0,0], 1.0)
    return fun


def as_bits(seq: Sequence[int] | str) -> np.ndarray:
    if isinstance(seq, str):
        cleaned = re.sub(r'\s+', '', seq)
        if not cleaned or any(c not in '01' for c in cleaned):
            raise ValueError('Attack string must consist only of 0s and 1s')
        return np.fromiter((int(c) for c in cleaned), dtype=np.int64)
    arr = np.asarray(seq, dtype=int).ravel()
    if not len(arr) or not np.isin(arr,[0,1]).all():
        raise ValueError('Sequence must be nonempty and binary')
    return arr


def read_official_attack(txt_path: str | Path, ell: int = 25):
    """Returns the paper-length internal bits (excludes forced boundary hits)."""
    path = Path(txt_path)
    if not path.is_file():
        return None
    n = ell + 2
    for line in path.read_text(errors='replace').splitlines():
        if not re.match(rf'^\s*{n}\s*,', line):
            continue
        arrays = re.findall(r'\[[^\[\]]*\]', line)
        if not arrays:
            continue
        a = ast.literal_eval(arrays[0])
        if len(a) == n and a[0] == 0 and a[-1] == 0 and set(a) <= {0,1}:
            return np.asarray(a[1:-1], dtype=np.int64)
    return None


def longest_miss_run(bits):
    return max((len(s) for s in ''.join(map(str,bits)).split('0')), default=0)


def audit_sequence(bits, *, a_max=4, window=10, p_miss=.25, alpha=.01,
                   detector='bin'):
    """Check precisely the author's constraints for a *specified* binary sequence.

    Counts include the author's first and last forced successful completion.
    A geometric/chi-square result is informational if detector='bin'.
    This tests model feasibility, not calibrated detection rates on stochastic data.
    """
    z_internal = as_bits(bits)
    z = np.r_[0, z_internal, 0]
    n = len(z)
    longest = longest_miss_run(z)
    watchdog_pass = longest <= a_max
    cutoff = int(binom.ppf(1-alpha, window, p_miss))
    if n > window:
        misses = np.asarray([sum(z[k:k+window]) for k in range(n-window+1)], dtype=int)
        highest = int(misses.max())
    else:
        misses = np.asarray([int(z.sum())], dtype=int)
        highest = int(z.sum())
    bin_pass = highest <= cutoff

    counts = np.zeros(a_max+1, dtype=int)
    for k in range(a_max+1):
        # Matches the pks max_() pattern in official optimise_chi2.py exactly:
        # a hit, followed by k misses, followed by a hit.
        for i in range(n-k-1):
            v = int(1-z[i]) + int(z[i+1:i+1+k].sum()) + int(1-z[i+1+k]) - (k+1)
            counts[k] += max(v, 0)
    completed = int(counts.sum())
    probs = np.array([(1-p_miss)*(p_miss**k) for k in range(a_max)]
                     + [p_miss**a_max], dtype=float)
    assert np.isclose(probs.sum(),1.0)
    if completed:
        # The authors multiply the usual chi-square inequality by N.
        lhs = float(np.sum((counts - probs*completed)**2/probs))
        bound = float(chi2.ppf(1-alpha, a_max)*completed)
        statistic = lhs / completed
        chi_pass = bool(lhs <= bound + 1e-9)
    else:
        lhs = bound = statistic = 0.0
        chi_pass = True

    det = detector.lower()
    if det not in ('bin', 'chi2', 'bin_chi2'):
        raise ValueError('detector must be bin / chi2 / bin_chi2')
    active_bin = det in ('bin','bin_chi2')
    active_chi = det in ('chi2','bin_chi2')
    all_pass = watchdog_pass and (not active_bin or bin_pass) and (not active_chi or chi_pass)

    return dict(ell=len(z_internal), stored_length=n, misses=int(z_internal.sum()),
                miss_fraction=float(z_internal.mean()),
                longest_run=longest, a_max=a_max, watchdog_pass=bool(watchdog_pass),
                window=window, p_miss=float(p_miss), alpha=float(alpha),
                allowed_in_window=cutoff, max_in_window=highest,
                binomial_pass=bool(bin_pass), chi2_pass=bool(chi_pass),
                category_counts=counts.tolist(), category_probabilities=probs.tolist(),
                complete_jobs=completed, chi2_statistic=statistic,
                chi2_critical=float(chi2.ppf(1-alpha,a_max)),
                active_binomial=active_bin, active_chi2=active_chi,
                active_detector=det, all_constraints_pass=bool(all_pass),
                sliding_counts=misses.tolist())


def simulate_exact_furuta(define_system, bits, policy):
    """Author REP matrices; first and last z are forced 0.

    The optimizer's objective is xs[-2]^T Q xs[-2], i.e. after
    first forced hit + ell attack decisions but before last forced hit.
    plot time=0 at the state *after* the initial forced hit.
    """
    bits = as_bits(bits)
    sys_name = 'furuta_' + policy
    miss, hit, C, Q, x0, nx = define_system(sys_name)
    states = [hit @ x0]  # official first z=0
    for b in bits:
        states.append((miss if b else hit) @ states[-1])
    xx = np.asarray(states, dtype=float)
    nominal = np.asarray([states[0]] + [None] * len(bits), dtype=object)
    nstates=[states[0].copy()]
    for b in bits:
        nstates.append(hit @ nstates[-1])
    nominal = np.asarray(nstates, dtype=float)
    jj = np.einsum('ki,ij,kj->k',xx,Q,xx)
    j0 = np.einsum('ki,ij,kj->k',nominal,Q,nominal)
    Ts=0.005
    return dict(policy=policy, state=xx, nominal_state=nominal,
                score=jj, nominal_score=j0, omega_trace=jj-j0,
                omega=float(jj[-1]-j0[-1]), attack_score=float(jj[-1]),
                nominal_final=float(j0[-1]),
                angle_rad=xx[:,0], nominal_angle_rad=nominal[:,0],
                sample_time=Ts, time=np.arange(len(xx))*Ts,
                velocity=xx[:,1], arm_rate=xx[:,2],
                augmented_last_state=xx[:,-1])


def build_scenario(define_system, name, bits, *, a_max=4, window=10,
                   p_miss=.25, alpha=.01, detector='bin', source='paper Table 1',
                   paper_objective=None, angle_limit_rad=None):
    bits=as_bits(bits)
    audit=audit_sequence(bits,a_max=a_max,window=window,p_miss=p_miss,
                         alpha=alpha,detector=detector)
    hold=simulate_exact_furuta(define_system,bits,'hold')
    zero=simulate_exact_furuta(define_system,bits,'zero')
    if paper_objective is not None:
        # Objective check applies to the policy on which Gurobi was run.
        pass
    res=dict(id=re.sub('[^a-z0-9]+','_',name.lower()), name=name,
             bits=''.join(map(str,bits)), source=source,
             params=dict(a_max=a_max, window=window, p_miss=p_miss,
                         alpha=alpha, detector=detector), audit=audit)
    for key,r in [('hold',hold),('zero',zero)]:
        res[key] = dict(t=r['time'].tolist(), theta=np.degrees(r['angle_rad']).tolist(),
                        nominal_theta=np.degrees(r['nominal_angle_rad']).tolist(),
                        velocity=r['velocity'].tolist(), arm_rate=r['arm_rate'].tolist(),
                        actuator=r['augmented_last_state'].tolist(),
                        impact=r['omega_trace'].tolist(),
                        objective=r['score'].tolist(),
                        nominal_objective=r['nominal_score'].tolist(),
                        omega=r['omega'], attack_score=r['attack_score'],
                        nominal_score=r['nominal_final'],
                        peak_abs_angle_deg=float(np.degrees(np.abs(r['angle_rad'])).max()),
                        final_angle_deg=float(np.degrees(r['angle_rad'][-1])))
    res['angle_limit_deg']=(None if angle_limit_rad is None else float(np.degrees(angle_limit_rad)))
    return res


def plot_scenario(scenario):
    """Clean, annotated inline static preview from the exact REP matrices."""
    bits=np.array([int(c) for c in scenario['bits']])
    a=scenario['audit']
    t=np.asarray(scenario['hold']['t'])
    fig,axs=plt.subplots(4,2,figsize=(14,12),sharex='col',
                         gridspec_kw={'height_ratios':[2.2,1.0,1.0,.7]})
    cc={'hold':'#b42332','zero':'#087f8c'}
    for col,pol in enumerate(('hold','zero')):
        dat=scenario[pol]
        ax=axs[0,col]
        ax.plot(t,dat['theta'],color=cc[pol],lw=2.2,label=f'{pol.upper()} attacked')
        ax.plot(t,dat['nominal_theta'],color='#5e6874',ls='--',lw=1.5,label='No attack')
        if scenario['angle_limit_deg'] is not None:
            lim=scenario['angle_limit_deg']
            ax.axhline(lim,color='darkorange',ls=':',label='User safety limit')
            ax.axhline(-lim,color='darkorange',ls=':')
        ax.set_title(f'{pol.upper()} | final ω = {dat["omega"]:.4g} | peak |θ| = {dat["peak_abs_angle_deg"]:.3g}°',fontsize=11)
        ax.set_ylabel('Furuta angle θ (deg)'); ax.grid(alpha=.25); ax.legend(fontsize=9)
        axs[1,col].step(t,dat['actuator'],where='post',color=cc[pol],lw=1.6)
        axs[1,col].set_ylabel('Augmented control state'); axs[1,col].grid(alpha=.25)
        axs[2,col].plot(t,dat['impact'],color=cc[pol],lw=1.7)
        axs[2,col].axhline(0,color='black',lw=.6)
        axs[2,col].set_ylabel('J(k)−J_nom(k)'); axs[2,col].grid(alpha=.25)
        axs[3,col].step(t[1:],bits,where='post',lw=1.1,color=cc[pol])
        axs[3,col].set_ylim(-.2,1.2); axs[3,col].set_yticks([0,1],['Hit','Miss'])
        axs[3,col].set_xlabel('Time since initial forced hit (s)'); axs[3,col].grid(alpha=.25)
    fig.suptitle(f"{scenario['name']} — identical attack schedule, original REP Furuta matrices\n"
                 f"Watchdog {'PASS' if a['watchdog_pass'] else 'FAIL'}  |  "
                 f"Binomial {'PASS' if a['binomial_pass'] else 'FAIL'}  |  "
                 f"Chi² {'PASS' if a['chi2_pass'] else 'FAIL'}"
                 f" (chi² {'active' if a['active_chi2'] else 'informational only'})",fontsize=14,y=1.015)
    fig.tight_layout()
    plt.show()
    return fig


def make_dashboard(scenarios, outfile, *, title='REP Furuta | Attack timing and physical response'):
    """Offline HTML dashboard with animated schematic and exact precomputed REP traces."""
    outfile=Path(outfile)
    outfile.parent.mkdir(parents=True,exist_ok=True)
    dataset=json.dumps(scenarios,allow_nan=False,separators=(',',':'))
    # Escape </script> sequence from any user scenario title to protect embedding.
    dataset=dataset.replace('</','<\\/')
    template = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>REP Furuta — Model-based Interactive Attack Viewer</title>
<style>
:root{--bg:#0c1524;--pane:#14243a;--soft:#1b304b;--ink:#f3f7fb;--muted:#a6bdd2;--hold:#ef6671;--zero:#59d6d5;--nom:#abb9c7;--ok:#75dda3;--fail:#ffa5a0;--line:#324860}
*{box-sizing:border-box}body{font:15px/1.46 system-ui,-apple-system,Segoe UI,sans-serif;background:var(--bg);color:var(--ink);margin:0}header{padding:20px min(3.5vw,35px) 12px;border-bottom:1px solid var(--line)}h1{font-size:24px;letter-spacing:-.5px;margin:0 0 5px}p{margin:6px 0;color:var(--muted)}main{max-width:1550px;margin:auto;padding:18px 22px 42px}.controls{display:flex;align-items:center;flex-wrap:wrap;gap:10px;padding:13px;background:var(--pane);border-radius:14px;margin-bottom:16px}button,select{border:1px solid #425a73;border-radius:9px;padding:10px 13px;background:var(--soft);color:var(--ink);cursor:pointer;font:inherit}button:hover,select:hover{border-color:var(--zero)}input[type=range]{accent-color:var(--zero);width:min(30vw,280px)}.side{display:grid;grid-template-columns:1fr 1fr;gap:16px}.panel{background:var(--pane);border:1px solid #213a53;border-radius:13px;padding:14px;min-width:0}.panel h2{font-size:18px;margin:0 0 8px}.panel.hold h2{color:var(--hold)}.panel.zero h2{color:var(--zero)}.viz{display:flex;gap:9px;align-items:center;justify-content:center}.sketch{width:38%;max-width:190px;aspect-ratio:1;min-width:95px}.lineplot{flex:1;width:100%;height:225px;display:block}.metrics{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:10px 0}.metric{padding:9px;border-radius:7px;background:var(--soft)}.metric small{display:block;color:var(--muted)}.metric b{font-size:17px;font-variant-numeric:tabular-nums}.wide{margin-top:15px}.wide canvas{width:100%;height:150px;display:block}.stats{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0}.pill{border:1px solid #435973;background:#192b40;border-radius:20px;padding:7px 11px}.pill.ok{color:var(--ok)}.pill.fail{color:var(--fail)}.annotation{background:#102136;border-left:3px solid #58bfbb;padding:11px 13px;margin-top:13px;color:#d4e0ea}code{color:#d8f2f1;overflow-wrap:anywhere}footer{font-size:13px;color:var(--muted);padding-top:15px}.small{font-size:13px;color:var(--muted)}@media(max-width:850px){.side{grid-template-columns:1fr}.viz{flex-wrap:wrap}.sketch{max-width:125px}.lineplot{min-width:240px}header h1{font-size:20px}main{padding:12px}.controls{gap:8px}}
</style></head>
<body><header><h1>Stealthy computational delay attacks — Furuta pendulum</h1>
<p>Original REP v1.2 closed-loop matrices • 0.005 s sampling • same attack schedule under HOLD and ZERO • statistical checks shown separately</p></header>
<main><div class="controls"><label>Attack scenario <select id="scenario"></select></label>
<button id="play">▶ Play</button><button id="restart">↺ Reset</button><label>Step <input id="scrub" type="range" min="0" max="25" value="0"></label>
<span id="time" class="small"></span><label>Trajectory graph <select id="series"><option value="theta">Pendulum angle</option><option value="actuator">Applied-control state</option><option value="impact">Accumulated objective difference</option></select></label><label>Playback <select id="speed"><option value="600">Slow</option><option value="280" selected>Normal</option><option value="100">Fast</option></select></label></div>
<div class="side"><section class="panel hold"><h2>HOLD — reuse previous command</h2><div class="viz"><canvas class="sketch" id="pend_hold"></canvas><canvas class="lineplot" id="plot_hold"></canvas></div><div class="metrics" id="met_hold"></div></section>
<section class="panel zero"><h2>ZERO — input set to zero</h2><div class="viz"><canvas class="sketch" id="pend_zero"></canvas><canvas class="lineplot" id="plot_zero"></canvas></div><div class="metrics" id="met_zero"></div></section></div>
<section class="panel wide"><h2>Deadline-miss schedule, actuator command and attack impact</h2><canvas id="raster"></canvas><p class="small">Red bars: deadline misses. Teal bars: successful executions. Both policies receive exactly the same 0/1 schedule in this comparison.</p></section>
<section class="panel wide"><h2>How the timing detectors interpret the sequence</h2><div class="side"><div><h3 class="small">Binomial: worst missed-deadline count per sliding window</h3><canvas id="binplot" style="width:100%;height:160px"></canvas></div><div><h3 class="small">Geometric/χ²: observed completed-run patterns versus expected</h3><canvas id="catplot" style="width:100%;height:160px"></canvas></div></div><h2 style="margin-top:10px">Detector audit</h2><div id="stats" class="stats"></div><div id="detail" class="small"></div><div class="annotation" id="interpret"></div></section>
<footer><strong>Scientific scope:</strong> These are discrete-time simulations of the exact matrices in the authors' REP repository, not measurements from hardware. The moving rod is a <em>schematic</em> visualization of the model's pendulum angle, not a geometric animation of the full rotating-arm apparatus. 'Passed detector constraints' is a property of the examined binary sequence under the stated nominal parameters, not proof against every detector. No physical falling boundary is inferred unless a user-defined threshold is supplied. Source: Nauta, Sandberg &amp; Maggio, ICCPS 2025; REP v1.2.</footer></main>
<script id="rep-data" type="application/json">__REPDATA__</script>
<script>
'use strict';
const D=JSON.parse(document.getElementById('rep-data').textContent);const $=id=>document.getElementById(id);
let item=D[0], step=0, playing=false, ticker=null;
const opts=$('scenario');D.forEach((s,i)=>{let o=document.createElement('option');o.value=i;o.textContent=s.name;opts.appendChild(o)});
function fmt(x){if(x===null||!Number.isFinite(x))return 'n/a';const a=Math.abs(x);return (a>0&&a<.001)?x.toExponential(3):x.toPrecision(5)};
function dprCanvas(canvas){const dpr=window.devicePixelRatio||1;const r=canvas.getBoundingClientRect();const w=Math.max(150,r.width),h=Math.max(95,r.height);canvas.width=Math.floor(w*dpr);canvas.height=Math.floor(h*dpr);const ctx=canvas.getContext('2d');ctx.setTransform(dpr,0,0,dpr,0,0);return {ctx,w,h}}
function pendulum(c,pol){const {ctx:g,w,h}=dprCanvas(c);const rad=item[pol].theta[step]*Math.PI/180,centerX=w*.5,centerY=h*.67,L=Math.min(w*.34,h*.38);g.clearRect(0,0,w,h);g.strokeStyle='#62758b';g.lineWidth=4;g.beginPath();g.moveTo(centerX-L*.6,centerY);g.lineTo(centerX+L*.6,centerY);g.stroke();g.strokeStyle='#566b80';g.setLineDash([3,6]);g.beginPath();g.moveTo(centerX,centerY);g.lineTo(centerX,centerY-L*1.12);g.stroke();g.setLineDash([]);let a=pol==='hold'?'#ef6671':'#59d6d5';g.strokeStyle=a;g.lineWidth=8;g.lineCap='round';g.beginPath();g.moveTo(centerX,centerY);g.lineTo(centerX+L*Math.sin(rad),centerY-L*Math.cos(rad));g.stroke();g.fillStyle=a;g.beginPath();g.arc(centerX+L*Math.sin(rad),centerY-L*Math.cos(rad),9,0,2*Math.PI);g.fill();g.fillStyle='#b3c6d8';g.beginPath();g.arc(centerX,centerY,5,0,2*Math.PI);g.fill();g.font='13px sans-serif';g.fillStyle='#c4d3df';g.textAlign='center';g.fillText(item[pol].theta[step].toFixed(2)+'°',centerX,h-8)}
function lineplot(canvas,pol){const {ctx:g,w,h}=dprCanvas(canvas),d=item[pol];const mode=$('series').value;
let observed=mode==='actuator'?d.actuator:(mode==='impact'?d.impact:d.theta);
let baseline=mode==='theta'?d.nominal_theta:new Array(observed.length).fill(0);
let Y=[...observed,...baseline];let absmax=Math.max(0.00001,...Y.map(Math.abs));const b=mode==='theta'?item.angle_limit_deg:null;if(b!==null)absmax=Math.max(absmax,b);const m={l:38,r:12,t:12,b:30};const pW=w-m.l-m.r,pH=h-m.t-m.b,lim=absmax*1.2;let x=i=>m.l+(i/(d.theta.length-1))*pW,y=v=>m.t+(.5-v/(2*lim))*pH;g.clearRect(0,0,w,h);g.strokeStyle='#4d657c';g.lineWidth=.8;g.beginPath();g.moveTo(m.l,y(0));g.lineTo(w-m.r,y(0));g.stroke();if(b!==null){g.setLineDash([4,4]);g.strokeStyle='#e0a96d';for(let bb of [b,-b]){g.beginPath();g.moveTo(m.l,y(bb));g.lineTo(w-m.r,y(bb));g.stroke()}g.setLineDash([])}
function path(vals,color,dash,weight){g.strokeStyle=color;g.lineWidth=weight;g.setLineDash(dash);g.beginPath();vals.forEach((v,i)=>{if(i===0)g.moveTo(x(i),y(v));else g.lineTo(x(i),y(v))});g.stroke();g.setLineDash([])}path(baseline,'#a5b6c8',[4,3],1.3);path(observed,pol==='hold'?'#ef6671':'#59d6d5',[],2.2);g.strokeStyle='#fff';g.fillStyle='#fff';g.beginPath();g.arc(x(step),y(observed[step]),3.2,0,2*Math.PI);g.fill();g.font='12px sans-serif';g.fillStyle='#adc1d2';g.fillText(lim.toFixed(1)+'°',2,m.t+10);g.fillText('-'+lim.toFixed(1)+'°',2,h-32);g.fillText('time '+d.t[step].toFixed(3)+' s',m.l,h-8)}
function metric(pol){const d=item[pol];$('met_'+pol).innerHTML='<div class="metric"><small>Final extra cost ω</small><b>'+fmt(d.omega)+'</b></div><div class="metric"><small>Peak |θ| across attack</small><b>'+fmt(d.peak_abs_angle_deg)+'°</b></div><div class="metric"><small>Current control-related state</small><b>'+fmt(d.actuator[step])+'</b></div><div class="metric"><small>Current θ̇ (rad/s)</small><b>'+fmt(d.velocity[step])+'</b></div>'}
function raster(){const c=$('raster'),{ctx:g,w,h}=dprCanvas(c);const z=item.bits.split('').map(Number),n=z.length;let left=42,right=18,top=12;let dx=(w-left-right)/n;g.clearRect(0,0,w,h);z.forEach((b,i)=>{g.fillStyle=b?'#e65b66':'#287e83';let x=left+i*dx;g.fillRect(x+1,top,Math.max(1,dx-2),48);if(i===step-1){g.strokeStyle='#fff';g.lineWidth=2;g.strokeRect(x,top-2,Math.max(2,dx),52)}});g.fillStyle='#c4d2df';g.font='12px sans-serif';g.fillText('zₖ',8,top+24);g.fillText('0',left,h-12);g.fillText(String(n),w-right-16,h-12);g.fillText('1 = artificial miss, 0 = deadline hit',left,h-12);}
function detectionPlots(){
const a=item.audit;
const c=$('binplot'),info=dprCanvas(c),g=info.ctx,w=info.w,h=info.h;
const data=a.sliding_counts,lim=Math.max(1,a.allowed_in_window+1,...data),pad={l:34,r:10,t:15,b:25};
const x=i=>pad.l+(i+.5)*(w-pad.l-pad.r)/Math.max(1,data.length),y=v=>h-pad.b-v*(h-pad.b-pad.t)/lim;
g.clearRect(0,0,w,h);g.fillStyle='#bfcedd';g.font='11px sans-serif';g.fillText(String(lim),6,pad.t+6);g.fillText('0',18,h-pad.b+3);
g.strokeStyle='#e7af70';g.setLineDash([4,4]);g.beginPath();g.moveTo(pad.l,y(a.allowed_in_window));g.lineTo(w-pad.r,y(a.allowed_in_window));g.stroke();g.setLineDash([]);
const bw=(w-pad.l-pad.r)/Math.max(1,data.length);
data.forEach((v,i)=>{g.fillStyle=v>a.allowed_in_window?'#ef6671':'#59c6c5';g.fillRect(x(i)-bw*.32,y(v),Math.max(2,bw*.64),h-pad.b-y(v))});
g.fillStyle='#9db3c9';g.fillText('allowed '+a.allowed_in_window,pad.l+4,pad.t+10);g.fillText('sliding window index',pad.l+4,h-4);
const cb=$('catplot'),r=dprCanvas(cb),h2=r.h,w2=r.w,cc=r.ctx;
const obs=a.category_counts,exp=a.category_probabilities.map(q=>q*a.complete_jobs);
const ymax=Math.max(1,...obs,...exp)*1.2,L=33,R=12,T=15,B=27;
cc.clearRect(0,0,w2,h2);cc.fillStyle='#bfcedd';cc.font='11px sans-serif';cc.fillText('count',4,T+8);
let ww=(w2-L-R)/obs.length;
obs.forEach((v,i)=>{let xpos=L+(i+.5)*ww;cc.fillStyle='#ef6671';cc.fillRect(xpos-ww*.29,h2-B-v/ymax*(h2-B-T),Math.max(2,ww*.23),v/ymax*(h2-B-T));let e=exp[i];cc.fillStyle='#59d6d5';cc.fillRect(xpos+ww*.03,h2-B-e/ymax*(h2-B-T),Math.max(2,ww*.23),e/ymax*(h2-B-T));cc.fillStyle='#cbd6e2';cc.fillText(String(i),xpos-4,h2-9)});
cc.fillText('red: observed',L+10,12);cc.fillStyle='#59d6d5';cc.fillText('teal: expected',L+107,12)
}
function verdict(label,pass,active){return '<span class="pill '+(pass?'ok':'fail')+'">'+(active?'● ':'○ ')+label+': '+(pass?'PASS':'FAIL')+(active?'':' (not enforced)')+'</span>'}
function aud(){let a=item.audit,p=item.params;$('stats').innerHTML=verdict('Watchdog',a.watchdog_pass,true)+verdict('Binomial',a.binomial_pass,a.active_binomial)+verdict('Geometric χ²',a.chi2_pass,a.active_chi2)+verdict('Selected detector constraints',a.all_constraints_pass,true);$('detail').textContent='ℓ='+a.ell+' · miss count='+a.misses+' ('+(a.miss_fraction*100).toFixed(1)+'%) · max run='+a.longest_run+'/'+a.a_max+' · window='+a.window+' · worst window count='+a.max_in_window+' / permitted '+a.allowed_in_window+' · χ² statistic='+fmt(a.chi2_statistic)+' / critical '+fmt(a.chi2_critical)+' · p̂='+p.p_miss+' · α='+p.alpha+'.  ○ = informational only.';let delta=item.hold.omega-item.zero.omega;$('interpret').textContent='Source: '+item.source+'. At this fixed attack schedule the final impact is ω_hold='+fmt(item.hold.omega)+' and ω_zero='+fmt(item.zero.omega)+'. Difference (HOLD−ZERO) = '+fmt(delta)+'. Both results use the same original REP initial condition and matrices; the attacker was not re-optimized separately for the other policy.'}
function draw(){let last=item.bits.length;step=Math.max(0,Math.min(last,step));$('scrub').max=last;$('scrub').value=step;$('time').textContent='period '+step+' / '+last+' · '+(step*.005).toFixed(3)+' s';for(let p of ['hold','zero']){pendulum($('pend_'+p),p);lineplot($('plot_'+p),p);metric(p)}raster();detectionPlots();aud()}
function stop(){playing=false;clearInterval(ticker);ticker=null;$('play').textContent='▶ Play'}
function begin(){stop();playing=true;$('play').textContent='⏸ Pause';ticker=setInterval(()=>{if(step>=item.bits.length){stop();return}step++;draw()},Number($('speed').value))}
$('scenario').addEventListener('change',()=>{stop();item=D[Number(opts.value)];step=0;draw()});$('play').onclick=()=>playing?stop():begin();$('restart').onclick=()=>{stop();step=0;draw()};$('scrub').oninput=e=>{stop();step=Number(e.target.value);draw()};$('speed').onchange=()=>{if(playing)begin()};$('series').onchange=draw;window.addEventListener('resize',draw);draw();
</script></body></html>'''
    html=template.replace('__REPDATA__',dataset).replace('<\\/','</') if False else template.replace('__REPDATA__',dataset)
    outfile.write_text(html,encoding='utf-8')
    return outfile
