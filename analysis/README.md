# analysis/

One-off and exploratory scripts used while writing the reports in `reports/`.
They are kept for provenance, not as a supported interface. The supported
entry points are in `pipeline/`.

Every script here expects its trace files under a `data/` folder relative to
the directory you run it from (normally the repo root). That folder is not in
the package because the files run to hundreds of megabytes. Regenerate them:

```bash
mkdir data
# SQLite trace databases, straight from the schema (no Gryphon needed):
python pipeline/mp_enumerate.py models/healthcareDelivery_corrected.mp   data/healthcare_traces.db
python pipeline/mp_enumerate.py models/Smart_Home_Energy_Composed.mp     data/smart_home_constrained_traces.db
# Or load a Gryphon .gry you already have:
python pipeline/gry_parse.py models/Smart_Home_Energy_Composed.mp data/constrained.gry data/smart_home_constrained_traces.db
```

File names each script looks for are at the top of the script.
`differential_*.py` also need scipy (`pip install -r requirements-analysis.txt`).
`legacy/` holds the spring per-model parsers, superseded by `pipeline/gry_parse.py`.
