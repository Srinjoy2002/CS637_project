# CPS: the project behind the final presentation

**Start here.** This is the curated `project_github` project, assembled 23 October 2026. It contains one chosen scientific codebase, one copy of the authors' REP v1.2 artifact, the exact numerical evidence used in the final 42-slide deck, all five member decks, visualisations and presentation scripts. It is a local folder/ZIP; nothing has been published to GitHub.

## What to open

| Purpose | Chosen file |
|---|---|
| Reviewed combined presentation | `presentations/final/main.pdf` |
| Combined editable LaTeX | `presentations/final/main.tex` |
| Original member presentations | `presentations/members/{shubham,swarali,madhavi,abhishek,srinjoy}/` |
| Short Swarali/Srinjoy scripts | `presentations/scripts/short_scripts_and_review.pdf` |
| Detailed presenter guide | `presentations/scripts/detailed_presenter_guide.pdf` |
| File-to-slide explanation | `docs/PPT_FILE_MAP.md` |
| One local code entry point | `main.py` |
| Guided notebook | `notebooks/PPT_evidence.ipynb` |
| Exact Table 1 Furuta dashboard | `visualisations/furuta_table1_dashboard.html` |
| Tank physical-model replay | `visualisations/tank_verified_replay.html` |

The final presentation remains a LaTeX/Beamer deck with PDF output. A native PowerPoint file is included only where originally supplied (Shubham); the combined deck is not falsely labelled PPTX.

## Why these versions were selected

- `vendor/REP_v1.2/`: the single original REP artifact from `REP_base`; its mathematical scripts are unchanged and hash-verified. This is the `main.py` discussed by Abhishek, not the new root convenience launcher.
- Scientific core (`models/`, `simulation/`, `attack/`, `rep_audit.py`, `author_drivers.py`): selected from the most complete native-PC package. The extracted duplicate matrix function was replaced by an AST loader of the single author `main_short.py`; its parameter sweeps are never executed on import.
- `rep_paper_visuals.py` and the Furuta dashboard: selected from the Full Paper Defender Visualisation package used for the Table 1 replay and Srinjoy's screenshot. That package does not supply the other seven slide cases or completed defender data.
- `data/ppt/`: Abhishek's 25-point curve, Srinjoy's ten exact schedules/results and 18 partial-summary points. These, with the final TeX coordinates, determine what is actually presented.
- `evidence/defender_saved_notebook.ipynb`: the original saved notebook output supporting the 432/540 completion claim and error 10010. Read its saved output for evidence. It is historical and is **not** the recommended notebook to Run All; use the lightweight notebook above.
- The later PC package's 648-configuration `{5,10}` stored grid and older standalone presentation/demo variants are not silently substituted for the deck's different partial 540-run campaign. Duplicate project directories, ZIPs, copied REP run workspaces, virtual environments and build caches are excluded.

`docs/SELECTION_AND_DEDUPLICATION.md` explains the selection. `docs/source_manifest.csv` records original source paths, hashes and every path adjustment. Original files were left untouched.

## Run locally (Python 3.11 or 3.12 recommended)

From a terminal in this folder:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py info
python main.py verify
python main.py replay
```

`verify` independently replays the ten cases / both policies and checks their costs and detector values against the exact CSVs. `replay` also writes scientific PNGs and JSON under `outputs/ppt_replay/`. It does not solve a new attack optimisation.

The two HTML files work by double-clicking, without Python. Or use `python main.py dashboard --system furuta` / `--system tank`.

The editable native animation/widget source is `visualization/native_view.py`. For the optional interactive notebook lab, install `requirements-visualisation.txt` in your environment, then uncomment the last cell of the guided notebook. This preserves the later PC animation source without bundling a second whole project tree.

For the notebook, install Jupyter in your chosen environment and run `python -m jupyterlab notebooks/PPT_evidence.ipynb`. Choose that environment's kernel.

## Independent enumeration (the method behind slide 33)

```powershell
python main.py enumerate --max-ell 10
```

This searches binary schedules using the paper matrices and constraints. For the full 1-25 range install Numba (`python -m pip install numba`) and use `--max-ell 25`. This is an explicit, potentially expensive computation. Float64 enumeration is not an interval-arithmetic safety certificate. The historic plotted values remain in `data/ppt/omega_main_short.csv`; new runs do not overwrite them.

## Authors' actual main.py / main_short.py

```powershell
python -m pip install -r requirements-solver.txt
python main.py author --script main_short.py
python main.py author --script main_short.py --run
```

The first command after installation prepares/verifies a new run but does not optimise. `--run` executes the authors' actual source through `tools/run_author_driver.py`, preserving outputs in a fresh dated run. Use `--script main.py` only if you intend the expensive full sweep. All source scripts are stored once under `vendor/REP_v1.2`; duplicate past run copies are not packaged.

The author driver has 27 loop iterations but only 25 intended positive horizons. Gurobi needs an appropriate local licence for the larger models. A size-limited licence can fail at error 10010. No licence file or activation credential is included. Do not infer success merely from process exit zero; inspect coverage and replay validation.

## Defender extension

```powershell
python main.py defender
python main.py defender --run
```

Without `--run`, this prints the requested call count (default 540) and stops. The runnable configuration is `config/defender_config.json`. The planned all-detector configuration is provided separately as a template; it is not a claim of completed results. To use it, explicitly replace/edit the active configuration.

`rep_defender_driver.py` runs the unmodified official optimiser scripts, with only file locations adapted to the consolidated layout. New outputs go to `outputs/defender_official/`. This route preserves the source driver’s resume/status behaviour; a saved optimal row alone does not supply a bound/gap certificate. Independent replay, complete horizon coverage and empirical session false-alarm estimates remain necessary before ranking defences. This package does not invent missing solves or completed false-alarm experiments.

The saved PPT campaign has 432 of 540 calls saved; all 108 calls at ell=25 failed. The plotted 18-row summary covers HOLD, alpha=.01 and ell in {5,10,15,20}. The Table 1 attack at matching settings has cost .144120 versus .021973 in the partial summary: about 6.56 times larger. That feasible attack supplies a lower bound on worst-case damage, not a safety upper bound.

## Presentation builds and assets

Compile from `presentations/final/`: `latexmk -pdf main.tex` (or run pdfLaTeX twice). Keep `presentations/assets/` in its relative location. All shared images are stored once; individual member sources also reference that directory. Each member directory has a README.

The individual slides are the supplied decks, preserved for provenance; the reviewed content corrections live in the final combined deck. The only edits to member sources are relative asset paths. The final packaged TeX likewise only adjusts asset paths compared with the open reviewed source.

Dummy roll numbers and dummy GitHub/Drive links remain explicitly labelled at the user's request. Replace them before a formal submission. The title's 22 October date is the explicitly entered presentation date, not the package assembly date.

## Scientific scope

The finite-horizon score is terminal output cost minus the same-initial-state nominal cost. Furuta plots may use degrees while costs use rad^2. Tank output costs equal the author REP state-weighted costs divided by four. Tank ZERO sets input deviation to zero; it does not switch physical pumps off. Same-schedule replays do not rank independently optimised policies. Extra 23-period cases are feasible examples without optimality proof. Geometric chi-square thresholds require care for small expected counts. The independent Bernoulli nominal-miss assumption and per-test alpha do not guarantee a calibrated session false-alarm probability. These simulations do not claim a new project hardware experiment.

## Verification

Run `python -m unittest discover -s tests -v` after installing the base requirements. The seven tests cover author hashes, all twenty policy replays, plant/memory updates, tank output scaling, run-count patterns, the worked chi-square example and independent enumeration versus brute force. They do not request Gurobi or optional notebook widget dependencies. Package validation also checks the extracted ZIP and all presentation asset paths. No full solver sweep or new hardware experiment was run during consolidation.

## Attribution

Nauta, Sandberg & Maggio, *Stealthy Computational Delay Attacks on Control Systems*, ICCPS 2025, DOI 10.1145/3716550.3722013. Author code: https://github.com/Talitha-Nauta/REP/tree/v1.2 and https://doi.org/10.5281/zenodo.14792914. See `THIRD_PARTY_NOTICES.md`. No new licence is imposed on the authors' work.
