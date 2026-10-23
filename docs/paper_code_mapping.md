# Paper-to-code audit

The complete 11-page paper, including references, Figures 1–4 and Table 1 was read. Model equations and table/figure pages were also visually inspected. The original source PDF is included for verification.

| Paper content | Author source | Project implementation / evidence |
|---|---|---|
| §§1–2: timing-attack motivation and taxonomy, Fig. 1 | Not executable | Overview and presentation script. Simulator models consequences; it does not starve a real CPU |
| Eq. (1), §§5.2–5.3: plant | main.py define_system | official_definition.py, exact decimal entries |
| Eqs. (2)–(3): stale measurement and controller | Blocks in Phi_hit / Phi_miss | models/paper.py; policy-update tests |
| Def. 4.3, Eqs. (4)–(6): augmented recurrence | All main*.py define_system copies | simulation/closed_loop.py; dimensional and recurrence tests |
| Eq. (7): attacker optimization | optimise_bin.py, optimise_chi2.py, optimise_bin_chi2.py | Unchanged execution in attack/rep_adapter.py; independent exhaustive.py |
| Maximum miss-run condition | for k in range(a_length-a_max) | longest_run and exact-search pruning |
| Eqs. (8)–(9): binomial | binom.ppf and sliding sums | detector_diagnostics.py, including short-window behavior |
| Eqs. (10)–(11): geometric | pks, aux, ms, N, chi2_sum | closed-pattern counters and statistic; empty-loop caveat documented |
| Def. 5.1: effectiveness | value − nominal_value | metrics in physical-output and REP scales |
| Fig. 2 | main_fig2.py / fig/maxa.tex | 2 systems × ā=1..4 × p=.09,.17,.25; combined; n_w=20, α=.01 |
| Fig. 3 | main_fig3.py / fig/tests.tex | 2 systems × 3 detectors × 3 p values; ā=4,n_w=20,α=.01 |
| Fig. 4 | main_fig4.py / fig/zerohold.tex | Furuta HOLD/ZERO × n_w=10,12,14,16,18 × 3 p; binomial,ā=4,α=.01 |
| Table 1, page 9 | README: L=27; strip two boundary zeros | table1.json, three published 25-bit strings and tests |
| Short smoke workflow | main_short.py | Furuta ZERO,ā=3,p=.25,n_w=20, combined, L=1..27. Still potentially hours |
| Full author sweep | main.py | All systems,ā=1..5, n_w=10:2:20, p=.01:.02:.25, all detectors |
| Plot wrappers | plot.tex, plot_fig2/3/4.tex, plot_short.tex, Makefile | Kept untouched. LaTeX expects generated results paths |
| §5.4 / hardware video | https://youtu.be/L15ab0cy-7Q | Referenced as authors' experiment; this project does not claim a hardware repetition |
| §6 / limitations | Paper discussion | Model fidelity, detector assumptions, no robust finite-grid guarantee |

## Source precision, plotting and provenance

All main*.py drivers were inspected for parameter selection. The plot files use x=`length-2`. Tank y=`(attack-nominal)/4`; Furuta y=`attack-nominal`. Original markers: blue filled circle=.09; red open circle=.17; brown x=.25. Figures 2–4 are collections of independent maximizations at different horizons. A falling curve is not evidence that a plant trajectory returns to zero: it says the best terminal cost at a different horizon changed.

The v1.2 archive contains code and LaTeX plotting instructions, **no numeric result CSV/TXT datasets**. Original figure crops are explicitly attributed to the paper. Newly computed enumeration files are labeled independent reconstructions. The default bundled curves stop at horizon 10; missing 11–25 points are not fabricated. Table 1's full 25-period result is separately replayed, and the window-10 optimum was independently enumerated.

`tools/reproduce.py` supports selective original-script Gurobi runs and independent enumeration. Each official run gets a fresh output directory so the author's append-only files do not silently duplicate data. Full original drivers remain in `vendor/REP_v1.2`. When running them, use a copied working directory and the authors' requirements. No long optimization runs on app startup.

Gurobi execution controls are applied by an environment proxy: TimeLimit and Threads. Mathematical source is unchanged. Status, incumbent, bound, gap and replay discrepancy are recorded, including failures. A solver status called OPTIMAL reflects its tolerances; the reported gap is never discarded. Gurobi 12 was used for the recorded smoke validations because the available Gurobi 11 restricted license was expired. This differs from the authors' 11.0.1 environment.

## Reproduction versus extensions

Baseline: exact plant/controller matrices, x0, original miss policies, objective indexing and statistical constraints. Project additions: physical visualization; explicit state/actuator replay; tank ZERO; finite-grid defender ranking; multiple binomial windows; initial-state scaling; cumulative/peak objective experiments; prefix geometric monitoring; nominal false-alarm Monte Carlo; independent enumerator. No nonlinear physical model has been silently inserted.
