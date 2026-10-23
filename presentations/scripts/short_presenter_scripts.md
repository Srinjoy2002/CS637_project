# CPS: 4-5 minute presenter scripts

Timing is per speaker. Read speech aloud; follow silent cues.

## Swarali Nilesh Savale

### 0:00-0:16 | Slide 8: Problem Formulation

*Silent cue: Face the audience. Then advance through slides 9 and 10 as indicated.*

Thank you, Shubham. I will explain how the paper turns delayed control computations into an attack optimisation problem, and what makes an attack statistically stealthy.

### 0:16-0:27 | Slide 9: Symbol glossary: plant, controller and timing

*Silent cue: Point briefly to x, y and u. Do not read the table. Advance.*

Here, x is the physical state, y the sensor reading, and u the applied control input.

### 0:27-0:38 | Slide 10: Symbol glossary: detectors, costs and project links

*Silent cue: Point to omega. Advance immediately to slide 11.*

Omega measures extra terminal cost relative to the no-attack run. The remaining symbols are a reference.

### 0:38-1:01 | Slide 11: Part 2: the model

*Silent cue: Trace controller to plant in the diagram, then point to the attacker. Advance.*

Imagine balancing a stick on your palm. Your correction may be mathematically correct, but arriving late still matters. Here, an attacker delays the controller without changing sensor values. Crucially, the physical plant keeps moving while the computation waits.

### 1:01-1:38 | Slide 12: Discrete-time plant and controller

*Silent cue: Point first to Equation 1, then Equation 2, then u with subscript k+1. Advance.*

Equation one describes the plant: the next state depends on its current state and the input already being applied. Equation two describes the controller, whose internal state is z. Notice the timing: during period k, the plant uses u-k, while the controller computes u-k-plus-one. This one-period convention is essential. A missed deadline affects the availability of the next command, not whether the physical plant evolves.

### 1:38-2:16 | Slide 13: Computational delay attack and switched dynamics

*Silent cue: Point to the augmented state, then the binary switched equation. Advance.*

We collect the plant, stored measurement, controller state and applied input into one augmented state, psi. The attack bit a is zero for a hit and one for a miss. A hit selects Phi-h; a miss selects Phi-m. During a miss, the controller state and stored measurement freeze. HOLD retains the old input; ZERO applies zero. In this model, the delayed job eventually completes using its stored measurement.

### 2:16-2:37 | Slide 14: Hit and miss matrices in the paper

*Silent cue: Point to A and B in both first rows, then the identity blocks and Delta in the miss matrix. Advance; do not read every entry.*

The first row of both matrices keeps the plant evolving. These identity blocks preserve the stored information during a miss. Delta selects HOLD or ZERO. The matrices simply encode the behaviour we just described.

### 2:37-3:17 | Slide 15: From objective to effectiveness omega

*Silent cue: Point to max, then Q, then omega. Briefly indicate the limitation box. Advance.*

The attacker chooses a binary miss sequence to maximise the final weighted output cost, while satisfying the dynamics and detector constraints. Q specifies which outputs matter. Omega subtracts the nominal cost from the attacked cost, using the same initial state. Therefore, maximising either gives the same attack for that configuration. The limitation is important: this objective scores the endpoint. It does not directly measure the largest excursion along the way.

### 3:17-3:57 | Slide 16: Detection I: watchdog and binomial test

*Silent cue: Point left to the watchdog, then right to the window sum and threshold. Advance.*

The watchdog limits consecutive misses: with a cap of two, three misses in a row are forbidden. The binomial test instead limits the total misses in a window. It assumes independent nominal misses with an estimated probability. For twenty jobs, probability one-quarter and significance one percent, the implemented critical count is ten. Passing these tests means no alarm under these rules; it does not prove that there is no attack.

### 3:57-4:32 | Slide 17: Detection II: the geometric chi-square test

*Silent cue: Point to run categories, expected counts, then the statistic. Pause before the handover. Advance to Madhavi’s title, slide 18.*

Finally, the geometric chi-square test checks the distribution of burst lengths. We compare observed run counts with the counts expected under normal operation. A large discrepancy triggers rejection. Small expected counts weaken the chi-square approximation, so false-alarm calibration still matters. Together, these constraints define the attacks the optimiser may choose. Madhavi will now show their physical consequences in the paper's experiments.

## Srinjoy Chakraborty

### 0:00-0:14 | Slide 34: Visualisation Cases and Defender Extension

*Silent cue: Face the audience. Advance to slide 35.*

Thank you, Abhishek. I will explain our replay results and defender extension: what the evidence supports, and what still needs validation.

### 0:14-0:57 | Slide 35: Furuta: the three published HOLD attacks

*Silent cue: Trace the falling HOLD curves, point to the near-zero dashed curve, then the chi-square values. Advance.*

We replay the paper's three HOLD-optimised attacks with the same initial state under both policies. The first HOLD case reaches about twenty-two degrees from upright; the same schedule under ZERO stays much closer. All three schedules pass their watchdog and binomial constraints, but fail the geometric test. The small negative omega values mean lower terminal cost than nominal for these particular ZERO replays. They do not establish ZERO's worst case, because these attacks were designed for HOLD.

### 0:57-1:31 | Slide 36: Furuta: horizon and detector validation

*Silent cue: Point to the ZERO column: lengths 5, 15 and 25. Then indicate the extra-case row. Advance.*

For the published ZERO cases, terminal effectiveness rises from length five to fifteen, then falls at twenty-five. So longer attacks need not produce greater terminal damage. Those three schedules pass the combined detector. The extra twenty-three-period case passes only its binomial setting and has no proof of optimality. These are different attack problems, so we keep their assumptions explicit.

### 1:31-2:11 | Slide 37: Quadruple tank: detector comparison and replay

*Silent cue: Point to the first two table rows and the 34.4 percent result. Advance.*

For the tank, we enumerate all one thousand and twenty-four schedules over ten periods. Adding the geometric constraint reduces the maximum effectiveness from about zero-point-zero-zero-three-one-six to zero-point-zero-zero-two-zero-seven: a thirty-four-point-four percent reduction. This is an exact finite search for the stated model and horizon. It compares the constraint sets; a fair detector ranking must also compare session false-alarm rates. The plotted trace is one output, while the objective scores both regulated outputs.

### 2:11-2:46 | Slide 38: Quadruple tank: policy comparison under a replayed schedule

*Silent cue: Point to the paired bars, then the policy-ranking box. Advance.*

Now imagine applying the pendulum's ZERO policy to the tank. For all three replayed tank schedules, ZERO produces more terminal cost, by roughly two to three times. Here zero means zero input deviation around equilibrium, not switching the pumps off. This demonstrates plant and schedule dependence. To rank policies by worst-case performance, we must optimise the attacker separately for each policy.

### 2:46-3:26 | Slide 39: Defender study: formulation and completion status

*Silent cue: Read the equation visually from omega-star to max to min, then point to the false-alarm constraint and Planned rows. Advance.*

Our extension reverses the design question: which defence makes the worst accepted attack least damaging? Omega-star already optimises the attack. We then take the worst tested horizon and choose the defence with the smallest such cost, subject to a session false-alarm limit. The nominal miss probability is measured, not a protection knob. Replays and a partial binomial sweep are available. Geometric and combined sweeps, and session false-alarm simulation, remain planned.

### 3:26-3:59 | Slide 40: Defender validation: horizon coverage changes the conclusion

*Silent cue: Point to the two values in the table and the factor 6.56. Slow down for the final sentence. Advance.*

This table shows why completion matters. The saved maximum over the available horizons is about zero-point-zero-two-two. A known feasible twenty-five-period attack reaches zero-point-one-four-four, about six-point-six times larger. The missing solves failed because of the size-limited Gurobi licence. A feasible attack gives a lower bound on worst-case damage. The smaller partial maximum cannot serve as a safety guarantee.

### 3:59-4:22 | Slide 41: Conclusion

*Silent cue: Point to What we did, then Limitations. Advance to references.*

Our contribution is an independent reproduction, policy replays and a defender formulation with partial evidence. The key finding is that timing, policy and detection interact. Completing the horizon coverage and false-alarm validation is necessary before claiming a best defence.

### 4:22-4:28 | Slide 42: References

*Silent cue: Leave references visible. Face the audience.*

Thank you. We welcome questions.
