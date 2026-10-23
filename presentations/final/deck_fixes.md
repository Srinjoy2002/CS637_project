# Delay-attack deck: applied fixes

Updated 22 October 2026. The annotated 33-slide PDF was mapped by slide title to the open 37-slide LaTeX deck, which already included four speaker dividers. All 37 existing slides remain. Five reference/summary slides bring the revised deck to 42 frames.

The presentation uses Madrid, green, with continuous frame numbering. The latest supplied revision uses an 8pt base (retained in the 23 October review). Keep the existing `figures/` directory beside `main.tex`.

## Title and project details

- Shubham Tyagi — dummy roll number 20260001.
- Swarali Nilesh Savale — dummy roll number 20260002.
- Madhavi Singh — dummy roll number 20260003.
- Abhishek Sharma — dummy roll number 20260004.
- Srinjoy Chakraborty — dummy roll number 20260005.
- Course: Embedded and Cyber-Physical Systems, CS637.
- Date: 22 October 2026. No unconfirmed instructor or institution was invented.
- GitHub and Google Drive are explicitly marked editable dummy links on the second glossary slide. Change `\CPSOurRepoURL` and `\CPSOurDriveURL` before sharing. They are not evidence sources.

## Global presentation fixes

- [x] Disabled the title-box shadows and changed Beamer blocks to the flat default template. This removes the shadow paths responsible for the black bars over block titles.
- [x] One source-footer layout across all five speakers, with the paper DOI and local source context.
- [x] Continuous numbering, including the four retained speaker dividers and the five added frames. There is no counter reset or explicit trailing page break.
- [x] PAPER, OURS, PAPER / OURS, KEY and SOURCES tags in the footer distinguish evidence and purpose without crowding long headings.
- [x] British spelling in prose. Original `optimise_*.py` filenames remain correct.
- [x] Consistent geometric (χ²) test terminology; distinguish the textbook statistic from its algebraically equivalent implementation.
- [x] Removed visible rehearsal/editorial cues such as “Discuss”, “Read it”, “Extension hook” and “Do not conflate”. Their substantive explanations are retained in the slides or notes.
- [x] Added captions to the taxonomy, control-loop and timing schematics, published figures/table, code pipeline, reproduction chart and replay plots.
- [x] Replaced the two smallest code-structure layouts with readable tables and diagrams. The file roles, nine cases, driver mapping and code conventions are retained.

## Introduction: original PDF slides 1–7

- [x] Added confirmed full names, user-authorised dummy roll numbers, CS637 and the date.
- [x] Renamed the roadmap to **Presentation plan**, with **Paper’s results** and **Our reproduction**. Moved the “How the parts connect” script to speaker notes.
- [x] Explained `y` and `u` beneath the introductory diagram; clarified the periodic controller’s input/output and deadline.
- [x] Corrected the Stuxnet/data-forgery wording. Removed the inaccurate German-steel-mill data-forgery example as a factual correction.
- [x] Retitled the blind-spot box **What detectors don’t check** and qualified the claim: a plant-residual detector that uses the actual applied input can miss the timing attack; a controller/timing-aware detector can detect it.
- [x] Added the taxonomy citation **directly below the original page 4 diagram**, a schematic-placement caption, and a matching References entry.
- [x] Qualified the comparison table. Plant-model/data requirements depend on the attack; denial of service is not guaranteed to trigger a plant-residual detector.
- [x] Distinguished execution capability from worst-case planning knowledge. Execution requires sufficient priority or blocking capability; planning uses the plant/controller model, initial state and detector settings.
- [x] Reworded the research question and takeaways to specify a finite-horizon worst case and failure to reject normal behaviour.

### Decision: retain the buffered-measurement model

The suggested “missed job is dropped” wording was **not adopted**. Paper Eq. (3) states that a computation delayed by several periods completes using the stored measurement. During misses, the controller state and stored measurement remain frozen. This is compatible with Eqs. (4)–(6), not a drop-and-restart model.

## Model and detectors: original PDF slides 8–13

- [x] Retained the repeated motivation slide, as requested, and retitled it **Part 2: the model**. It now gives the model assumptions rather than editorial instructions.
- [x] Added two symbol glossary slides. They define state/signal/matrix notation, timing, detector quantities, costs, defender variables and session false-alarm notation.
- [x] Indexed the `11010` example from `k = 0`.
- [x] Added an explicit matrix slide transcribing `Phi_h` and `Phi_m` from paper Eqs. (5)–(6), including the `DK`, `DH` and `CB` blocks and the HOLD/ZERO `Delta` block.
- [x] Corrected references: Eq. (4) is the switched update; Eqs. (5)–(6) define the matrices; Eq. (7) is the full optimisation, which contains the watchdog constraint; Eqs. (9)–(11) are the statistical constraints.
- [x] Retitled the objective slide **From objective to effectiveness ω**, wrote out the stealth constraints, and distinguished the maximised terminal objective from the reported difference to nominal.
- [x] Kept both output weights and stated that terminal-cost optimisation does not score damage before the terminal sample.
- [x] Put the watchdog/binomial distinction in a readable block.
- [x] Defined `N = sum_r m_r` as the number of counted hit-to-hit intervals. REP’s forced boundary hits close all interior miss bursts. `N` is not simply the total count of time steps.

## Paper results: original PDF slides 14–22

- [x] Renamed the setup slide **Experimental setup** and removed the redundant section prefixes from content subtitles and the old section-specific source footer.
- [x] Used the paper’s actual sweep steps: windows `10, 12, …, 20` and nominal probabilities `.01, .03, …, .25`.
- [x] Qualified runtime: the authors estimate about two hours for the reduced experiment; a larger campaign depends on the grid, hardware and licence.
- [x] Replaced cross-plant raw-cost comparisons with the warning that different outputs, weights and units prevent direct magnitude comparisons.
- [x] Qualified the Furuta ZERO conclusion by plant and tested attack.
- [x] Retained Figs. 2–4 and Table 1, with captions and three concise takeaways per figure/table discussion.
- [x] Stated that the peak depends on the panel, around horizons 10–13, including the reproduced horizon-13 peak.
- [x] Described the binding geometric constraint in the plotted configurations without asserting universal detector dominance at equal false-alarm rates.
- [x] Explained “% in W” as critical count/window length: `6/10`, `7/12`, `8/14`.
- [x] Removed the unsupported “realistic thresholds 3–10” claim.
- [x] Renamed the transition **From the paper’s gaps to our extension**. It now separates completed reproduction/replay/partial sweep from planned cross-detector and false-alarm experiments. A live demonstration, multiple simultaneous windows and a completed configuration ranking are not claimed.

## Reproduction: original PDF slides 23–27

- [x] Preserved the code pipeline, filenames, nine-case mapping, driver settings, special cases, flowchart, worked example and reproduced curve.
- [x] Replaced “27 solves” with **27 loop iterations** (`a_length = 1..27`) and **25 intended positive-horizon plotted rows** (`ell = a_length - 2 = 1..25`). Successful saved rows additionally depend on solver status and licence. The two initial loop values are not positive attack horizons.
- [x] Described our reproduction as **independent exhaustive enumeration** of the same model and constraints, not a rerun of the authors’ Gurobi solver.
- [x] Used the textbook statistic on the worked example. For `0111000`, `0101010`, `0110100`, respectively: `N = 3`, `S = 20.111…, 13, 6.333…` and `T = N*S = 60.333…, 39, 19`. The limit is `S <= 11.345` for `a_bar = 3`, or equivalently `T <= 11.345*N ≈ 34.0`.
- [x] Overlaid our 25-point curve and a clearly labelled approximate graphical reading of the paper panel on the same axes.
- [x] Reported our peak `9.45 × 10^-5` at horizon 13 against the graphically read paper peak about `9.4 × 10^-5` at about 13.
- [x] Displayed the two published sequences: horizon 5, `11010`; horizon 15, `101011011101000`. The paper’s quoted examples use `a_bar = 4`; neither sequence needs more than three consecutive misses.
- [x] Kept the graphical comparison’s precision honest: the difference to the rounded reference points is below `0.08 × 10^-5`, while low-resolution digitisation uncertainty is about `0.15 × 10^-5`. This is not a raw-author-data error bound.

## Replay and defender study: original PDF slides 28–33

- [x] Preserved all replay schedules, plotted trajectories and reported numerical results.
- [x] Explained negative ω as a smaller terminal cost than nominal for that same schedule under the other policy. It is not a ZERO worst-case bound.
- [x] Marked published ZERO-optimised schedules versus HOLD replay values; renamed the additional 23-period cases **Extra**, with feasibility/no-optimality-certificate caveats.
- [x] Used the textbook statistic with critical value `13.277` on the replay slides (`a_bar = 4`, alpha `.01`). This differs from `11.345` because the watchdog cap/degrees of freedom differ; it is not a conflicting convention.
- [x] Retained the result that all three Table 1 attacks fail the geometric test even though they pass their active binomial/watchdog constraints.
- [x] Retitled the tank comparison **Policy comparison under a replayed schedule**. Added the need to optimise the attacker separately under ZERO before ranking policies by worst-case cost.
- [x] Formulated the defender problem **per measured nominal scenario**, subject to a session false-alarm limit. The defender does not choose the measured nominal miss probability.
- [x] Included binomial, geometric (χ²), and combined detector choices, with explicit completion status. Geometric/combined sweeps and session false-alarm estimation are planned, not completed.
- [x] Defined the intended empirical FA experiment: nominal Bernoulli sessions of a declared length, count sessions with at least one alarm, report uncertainty and whether watchdog shutdowns count.
- [x] Corrected the partial-grid opening. The displayed HOLD/alpha `.01` maxima cover horizons `{5,10,15,20}`; horizon 25 is missing.
- [x] Checked the actual saved notebook log: **Gurobi error 10010, “Model too large for size-limited license”**, not a timeout. A correctly configured unrestricted academic licence removes this model-size restriction.
- [x] Kept the Table 1 check `0.144120 / 0.021973 ≈ 6.56`, showing why the missing horizon matters.
- [x] Replaced audience-facing “supplied ZIP” and “earlier reviewed” language with project replay/notebook provenance and a glossary project-links pointer.

### Study counts and remaining work

The existing binomial design has 2 policies × 6 windows × 3 significance levels = **36 defender choices per scenario**. With 3 scenarios and 5 quick horizons, this is **540 calls**; 25 full horizons give **2,700**. The saved quick campaign has 432 completed rows and 108 failed horizon-25 calls. The plotted table is one HOLD/alpha `.01` slice, not all 432 results.

If the new campaign includes all three detectors, the geometric-only branch should not repeat a window-independent calculation for six windows. With that deduplication, the planned grid has **1,170 quick-horizon calls** or **5,850 full-horizon calls**: binomial and combined each contribute 540/2,700, geometric-only 90/450. These planned counts are not completed results.

No new defender optimisation campaign, physical experiment or Monte Carlo false-alarm study was performed while revising the slides. Do not claim a completed ranking, equal-FA detector superiority or a physical-safety certificate.

## New ending and verification

- [x] Added **Conclusion**, separating paper findings, our work and limitations.
- [x] Added **References**, including the delay-attack paper, official REP archive/repository and verified Teixeira taxonomy reference.
- [x] Kept all original content slides and all four speaker dividers. Corrections, captions and speaker-note moves are deliberate; no additional content slide was deleted.
- [x] Checked that the source contains no counter reset, `noframenumbering`, `newpage`, `clearpage`, or empty final frame.
- [x] Checked that all image paths still resolve in the existing figures folder.
- [x] Compiled the saved `main.tex` successfully with the desktop editor’s built-in compiler.

## Verified references

1. Nauta, Sandberg & Maggio. *Stealthy Computational Delay Attacks on Control Systems*. ICCPS 2025. [DOI 10.1145/3716550.3722013](https://doi.org/10.1145/3716550.3722013). Model details checked against the local paper, especially Eqs. (3)–(11), Section 5.4.1 and Appendix A.4.1.
2. Official REP v1.2 code. [Zenodo DOI 10.5281/zenodo.14792914](https://doi.org/10.5281/zenodo.14792914); [GitHub](https://github.com/Talitha-Nauta/REP/tree/v1.2). Driver bounds, objective sample, boundary hits and the scaled statistic were checked in `main_short.py` and `optimise_bin_chi2.py`.
3. Teixeira, Shames, Sandberg & Johansson. *A secure control framework for resource-limited adversaries*. Automatica 51 (2015), 135–148. [DOI 10.1016/j.automatica.2014.10.067](https://doi.org/10.1016/j.automatica.2014.10.067). This is reference 38 in the delay-attack paper and the source of its Figure 1 taxonomy.
4. [Gurobi’s explanation of the size-limited licence error](https://support.gurobi.com/hc/en-us/articles/360051597492-How-do-I-resolve-a-Model-too-large-for-size-limited-Gurobi-license-error). The actual failure message is present in the saved project notebook outputs.


## Review of latest pasted revision - 23 October 2026

- Used the newly pasted source as the revision baseline, retaining its 8pt class, footer fixes, slide order and all 42 frames. The font-size comment now agrees with the source.
- Disambiguated session length as H_sess; H already names a controller matrix.
- Put the small-expected-count limitation of the chi-square approximation on slide 17. The detector is still reproduced as specified by the paper.
- Qualified the 34.4% tank result: it compares constraint sets, not detectors calibrated to equal session false-alarm rates.
- Replaced the misleading ell<=20 saved-maximum label with the actual tested set {5,10,15,20}. Explained that a feasible attack supplies a lower bound on worst-case damage.
- Qualified the conclusion's optimisation guarantee: solver bounds or exhaustive search are needed to certify optimality.
- Labelled the three author-code explanation frames PAPER / OURS.
- Restored the five-column Furuta results table to full width; retained all entries.
- Prepared separate 4-5 minute scripts. Glossaries and matrix expansion remain reference slides, passed quickly in the short talk; no content frames were deleted.
- Assessment: 8/10 as a PhD paper-review seminar; the original extension remains preliminary (about 6.5/10 as a completed research contribution) pending complete solves, calibrated false-alarm measurements and reproducible project artifacts. These are editorial judgements, not a formal grading rubric.

## Follow-up against review.pdf - 23 October 2026

- Slide 14 matrix: already correct before this follow-up. The current hit matrix has row 2 `CA & DK & DH & CB` and row 4 `0 & K & H & 0`. The review's reported F/0 entries do not occur in the current source. No matrix or numerical result was changed.
- Slide 14 label: clarified that Eq. 4 is the switched model and Eq. 7 writes its binary-selection form. The source footer now covers Eqs. 3-7.
- Slide 33: the cap difference was already explained, but is now stated directly as our curve uses a-bar=3 and the paper's printed example sequences use a-bar=4. Neither quoted sequence needs a burst longer than three.
- Slides 13/33: clarified that the illustrative five decisions `11010` appear inside REP's stored `0 11010 0`, whose boundary zeros are forced hits. The illustrative slide's k=0..4 labels remain unchanged.
- Slide 9: clarified angle in radians versus angle-squared cost in rad^2.
- Slides 1, 10, 42: dummy rolls and project-link placeholders remain explicitly labelled, in accordance with the user's earlier instruction to retain dummy values. Real values were not supplied.
- Slide 1 date: retained the explicitly entered presentation date, 22 October 2026. The review date does not establish a replacement presentation date.
- The review confirms the existing detector equations, figure/table interpretations, reproduction values and licence/missing-horizon qualifications; those required no additional changes.
- All 42 frames and original content remain. The 4-5 minute spoken scripts require no changes because they do not recite the revised labels or placeholders.

## Consolidated project export - 23 October 2026

- The repository export exposed a 16pt body overflow on slide 35. Enabled Beamer's local fit-to-frame option on that slide so the negative-omega qualification remains visible above the footer. All text, plots, table values and the screenshot remain.
- The consolidated repository stores shared presentation images once, with relative paths adjusted in the packaged final/member sources. The open source retains its existing figures directory and editor tab.
