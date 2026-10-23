# Exact models and interpretation

Source: Talitha Nauta, Henrik Sandberg and Martina Maggio, *Stealthy Computational Delay Attacks on Control Systems*, ICCPS 2025, DOI https://doi.org/10.1145/3716550.3722013. Numerical source: REP v1.2, commit `d3dbcaa0670bf1d99bf37b3164267b0b9a9398fd`.

## Notation that must not be conflated

The paper uses **x** for the physical plant state, **z** for controller memory, **a** for the attack, and **ψ** for the augmented state. REP uses `xs` for the augmented state and `zs` for the binary attack. This project's Python `x` arrays follow REP's augmented-state naming; UI `z[k]` denotes the binary attack requested in the project specification. This naming translation is deliberate. It does not redefine the paper's physical output y.

| Quantity | Furuta | Quadruple tank | Meaning / units |
|---|---|---|---|
| Physical plant x | 3 | 4 | Furuta: angle [rad], pendulum speed [rad/s], arm speed [rad/s]. Tank: four level deviations, retained in source model units; no unsupported cm calibration |
| Physical output y=Cx | 3 | 2 | Furuta all physical states; tank half the lower-level state values |
| Buffered measurement y-tilde | 3 | 2 | Frozen during deadline misses |
| Controller memory z (paper) | 0 | 4 | Furuta static LQR, tank dynamic LQG |
| Actuator u | 1 | 2 | Model command/deviation units; no torque/voltage calibration asserted |
| Augmented ψ (project x) | 7 | 12 | [plant, buffer, controller memory, current actuator] |
| Sampling period | 0.005 s | 0.1 s | Paper sections 5.3 and 5.2 |
| Q in paper output objective | diag(1,0,0) | I₂ | Fixed by experiment, not controlled by attacker |
| Q in REP state objective | diag(1,0,0,0,0,0,0) | diag(1,1,0,...,0) | Tank REP values are four times the paper output cost |
| z[k] (project attack) | 0 / 1 | 0 / 1 | Deadline hit / miss; dimensionless |
| ℓ | periods | periods | Interior attack horizon |
| p̂ₘ | probability | probability | Assumed nominal miss probability, NOT attack success probability |
| ā | misses | misses | Allowed consecutive misses; alarm above this maximum |
| n_w | periods | periods | Binomial window length |
| α | probability | probability | Nominal per-test significance, not session false-alarm probability |

## Equations (1)–(6): plant, controller, and timing

The plant is `x[k+1]=A x[k]+B u[k]`, `y[k]=C x[k]+D u[k]` (Eq. 1). The controller computes `z[k+1]=F z[k]+G y[k]`, `u[k+1]=H z[k]+K y[k]` (Eq. 2). Both supplied systems have D=0. With misses, the in-progress controller uses its buffered measurement (Eq. 3). Thus the augmented transitions are:

```
Phi_hit = [ A    0    0    B  ]
          [ CA   DK   DH   CB ]
          [ 0    G    F    0  ]
          [ 0    K    H    0  ]

Phi_miss= [ A    0    0    B     ]
          [ 0    I    0    0     ]
          [ 0    0    I    0     ]
          [ 0    0    0    Delta ]
```

These are Eqs. (5) and (6). Delta=I for HOLD and Delta=0 for ZERO. The physical plant always evolves using the current u[k]. A miss at k changes u[k+1], not the already-applied u[k]. The buffered measurement and controller memory remain frozen. When execution finishes, the command uses that buffered measurement; the next buffer receives the new output. Replacing this mechanism with instantaneous state feedback would be a different model.

`models/official_definition.py` contains the exact author function, not the rounded matrices printed on page 7. `get_model` exposes its blocks. Furuta gain K=[0.428,0.0307,0.0119]. Tank F is hit[6:10,6:10], G=hit[6:10,4:6], H=hit[10:12,6:10], K=hit[10:12,4:6]. Initial arrays come directly from that function and are printed in the inspection panel. Both policies and nominal reference use identical initial arrays.

## Eq. (7): implemented objective and bounds

The mathematical objective is max y_ℓᵀQy_ℓ. REP stores L=ℓ+2 binary entries, forces the first and last to zero, generates L+1 augmented states, and maximizes `xs[-2] @ Q @ xs[-2]`, i.e. x[L−1]. The nominal comparison is `Phi_hit**(L−1) @ x0`. Consequently a Table 1 replay MUST retain the leading boundary hit; merely simulating the printed 25 bits from x0 gives a different number. This project evaluates at x[ℓ+1], before the final forced-hit transition, exactly as REP does.

For the tank C selects half the lower levels. The paper's output cost is (x₁²+x₂²)/4. REP optimizes x₁²+x₂²; `fig/maxa.tex` and `fig/tests.tex` divide attack-minus-nominal by four. Multiplying an objective by a positive constant preserves the optimizer, but not its numerical value. Exports retain both `attack_rep`/`rep_omega` and physical-output `objective`/`omega`.

The decision variables are binary zs[k], continuous augmented xs[k] in [-1000,1000], and (for geometric tests) integer category counts ms[k] in [0,1000], integer total N, binary pattern flags and auxiliary integer expressions. Indicator constraints select hit/miss recurrences. This is nonconvex maximization of a convex quadratic, with mixed-integer constraints; the geometric test adds a quadratic constraint. The explicit state bounds are implementation constraints, not physical safety limits.

## Eqs. (8)–(11): detection

Binomial: b = scipy.stats.binom.ppf(1−α,n_w,p̂ₘ). Each complete sliding window has at most b misses. If L≤n_w, REP compares the total L-entry count with the **n_w-based** threshold. It does not replace n_w by L. For p̂ₘ=.25 and α=.01, n_w=10,12,14 gives b=6,7,8. No fabricated prehistory is added beyond the author boundary hits.

Geometric: count each closed pattern `0 1^j 0` as m_j. Adjacent zeros count category zero. An unfinished run is not yet counted. Under the watchdog, categories run from 0 to ā. Set π_j=(1−p̂ₘ)p̂ₘ^j for j<ā and π_ā=p̂ₘ^ā. Then N=sum m_j, E_j=Nπ_j, and χ²=sum (m_j−E_j)²/E_j. Reject if χ²>chi2.ppf(1−α,ā). REP multiplies through by N and constrains sum (m_j−Nπ_j)²/π_j ≤ chi2_quantile*N. This avoids division by a decision variable. The final category is a probability tail multiplied by N; the paper's text around its final expected-frequency expression is dimensionally ambiguous, while the code is explicit.

Combined means BOTH statistical tests plus watchdog. Multiwindow is a project extension requiring all of (10,20,40) binomial windows plus watchdog. Every UI reports individual verdicts. A seven-miss run can pass ā=8 while violating the n_w=10, b=6 binomial detector.

### Two implementation limitations exposed by the audit

1. REP checks the geometric constraint on the completed schedule, not at every prefix. A final-compatible attack can have a rejected prefix. This app shows both and never equates them. Prefix monitoring is an explicit project extension without invented historical counts.
2. In the author geometric files, `ms[k] == sum(pks)` is inside the pattern-position loop. When there are zero possible positions (`k>=L−1`), that category is left unconstrained. For ℓ<ā, the independent enumerator fixes its physically observed count to zero and therefore implements the intended counting definition rather than this source edge case. Such short-horizon reconstruction points are labeled. The unchanged Gurobi adapter retains the author behavior. All ell=5 validation cases with ā=4, Table 1, and the bundled defender horizons 5 and 10 avoid this edge case.

Expected counts are often small; the χ² reference law is approximate. Nominal α is not an empirical false-alarm guarantee. The Monte Carlo module reports its seed, number of trials, session length and imposed boundary convention.

## Visualization and extension limits

Furuta physical angle is exact. Arm position is absent in the three-state plant, so the drawing integrates arm velocity by the trapezoidal rule, with arm angle zero initially. Schematic arm/rod lengths (0.62 and 0.88 drawing units) do NOT enter the model. Camera motion and rendering do not affect simulation. The 0.2-radian warning is a chosen heuristic, not a sourced domain-of-validity bound. No nonlinear model or experimentally validated fall is claimed.

Tank surfaces are centered deviation gauges with a disclosed automatic display range. Source matrices and operating point do not justify absolute water height, pump power, gravity flow in physical volumetric units, overflow or empty-tank events. The local app obtains an equivalent continuous linear generator from log([[A,B],[0,I]])/Ts; exp(generator*Ts) reconstructs the supplied discrete plant. Its signed pump/drain contributions are **flow deviations**, not actual absolute flow rates. Negative values indicate reductions relative to equilibrium. Routing follows pump 1→tank 1 and tank 4, pump 2→tank 2 and tank 3; upper tanks drain to the same-column lower tank. Colab shows routing without a flow-rate animation.

Tank ZERO changes only the input block of Phi_miss to zero. In deviation coordinates this means equilibrium command, not physically switching off pumps. It is an explicitly labeled extension.

Initial-condition experiments scale the complete consistent initial state. Without state-bound activation, linearity implies costs scale quadratically. Cumulative and peak objectives use the same fixed output weights, on samples 1..ℓ+1 and 0..ℓ+1 respectively. These are separate project objectives, not changed baseline experiments.
