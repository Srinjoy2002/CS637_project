# Selection and duplication audit

Inspected 596 relevant files in the supplied project tree after excluding virtual environments, Git internals, caches and auxiliary build products. Found 101 groups of byte-identical input files across the old project versions.

Only one source tree was selected for the scientific core. One REP source artifact remains under `vendor/REP_v1.2`; repeated copies from REP_runs and older ZIP extractions were not included. One final combined deck and five distinct supplied member decks are retained. All six image assets are stored once and referenced from those decks. The final main.tex differs from the reviewed open source only in asset paths.

Not selected: whole older CPS_Delay_Attack_Project and CPS_Delay_Attack_Reviewed trees, duplicate extracted ZIPs, generic v4 presentation, older combined PDFs, hand-annotated draft, old local setup wrappers, duplicated workspaces, screenshots unrelated to the deck and the later native notebook's separate 648-configuration stored grid. Those originals were not modified or deleted.

The two retained HTMLs have different purposes: exact three-case Table 1 Furuta dashboard and native-PC tank companion animation. The two script PDFs have different purposes: detailed rehearsal and timed short delivery. These are not competing project versions.

Original author files with different required filenames are preserved byte-for-byte even if their content is identical. Any such required upstream duplication is recorded in the final package validation rather than rewriting upstream code. Repeated content inside self-contained HTML/PDF exports is part of those file formats and is not a duplicate project directory.

`source_inventory.csv` records each inspected source. `source_manifest.csv` records selected files, provenance, transformations and checksums. `PACKAGE_VALIDATION.json` records the final file/hash audit and execution checks. No Python environment, Gurobi licence, private credential file or Git history is bundled.
