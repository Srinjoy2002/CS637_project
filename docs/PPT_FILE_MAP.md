# Which files support which slides?

Slide numbers refer to the final 42-frame deck, not to the old member PDFs.

| Slides | What is presented | Actual source in this folder |
|---|---|---|
| 1-17 | Intro, glossaries, plant/controller model, hit/miss matrices, objective and detectors | `presentations/final/main.tex`; `docs/paper/source_paper.pdf`; author definitions/constraints in `vendor/REP_v1.2/` |
| 19-26 | Paper experiments, Figures 2-4 and Table 1 | Original paper images in `presentations/assets/madhavi/`; paper PDF |
| 27 | Project extension scope / done versus planned | Final deck; no completed all-detector sweep is implied |
| 29-31 | Authors' code organisation, nine cases and reduced driver | `vendor/REP_v1.2/main.py`, `main_short.py`, `main_fig*.py`, `optimise_*.py` |
| 32 | ell=5 worked schedule and costs | Interior `11010`, stored `0110100`; same model/replay and detector functions used by `tools/ppt_evidence.py` |
| 33 | Independent Furuta curve, cap=3 | `data/ppt/omega_main_short.csv`; independent enumerator `attack/exhaustive.py`; paper overlay is approximate graphical digitisation in final TeX |
| 35 | Three Table 1 HOLD schedules; same-schedule ZERO comparison; Furuta screenshot | First three rows of `data/ppt/case_results.csv`; `rep_paper_visuals.py`; `visualisations/furuta_table1_dashboard.html`; exact screenshot `presentations/assets/srinjoy/furuta_dashboard.png` |
| 36 | Published ZERO schedules at ell=5,15,25; extra ell=23 replay | Rows `fig2_furuta_*` and `audited_furuta` in `data/ppt/case_results.csv`; `tools/ppt_evidence.py` reproduces all costs |
| 37 | Tank detector comparison and 34.4% result | `tank_bin`, `tank_bin_chi2`, `audited_tank` in the same CSV; `models/paper.py`, `attack/exhaustive.py` |
| 38 | Tank ZERO extension, fixed-schedule policy comparison | Same three tank rows; `models/paper.py` changes only the actuator-memory block for `qt_zero` |
| 39 | Defender formulation/status and requested grid | `config/defender_config.json`, planned template, `rep_defender_driver.py`; session false-alarm validation remains planned |
| 40 | Partial sweep, 432/540 and missing horizon effect | `data/ppt/defender_available_summary.csv` plus saved cell outputs in `evidence/defender_saved_notebook.ipynb`; Table 1 row for 25-period comparison |
| 41-42 | Conclusion and references | Final reviewed deck and above evidence |

## Visualisations: use these two

1. **Furuta dashboard:** the exact three Table 1 schedules used for the dashboard screenshot. This is the direct visualisation associated with slide 35. It contains only these three Furuta presets.
2. **Tank verified replay:** the later native-PC tank animation, provided as a companion view. It is not a claim that the Full Paper Furuta package contains a tank dashboard. For exact numerical verification of all three tank rows, run `python main.py replay`.

The final scientific plots are editable PGFPlots coordinates inside `presentations/final/main.tex`; they are not screenshots taken indiscriminately from every demo version. The old physical animations are schematic linear-model illustrations, not hardware video.

## Three different things often confused

- `vendor/REP_v1.2/main.py` is the authors' full Gurobi campaign.
- Root `main.py` is a convenience launcher added for this consolidated folder.
- The historic full 25-point curve in slide 33 came from independent enumeration, not 25 newly successful Gurobi solves. The saved defender notebook is a separate partial campaign.
