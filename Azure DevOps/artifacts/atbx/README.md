# Sample editing toolbox (`.atbx`) build

Mocks project-specific names for docs and samples. Pipeline publishes `Sample_Editing_Tools_YYYY_MM_DD.atbx`.

Layout (not all files are committed; add locally or from your build):

```text
atbx/
  Sample_Editing_Tools.atbx          # source toolbox zip
  gp/                                # s01.py … sN.py (injection sources)
  config.json
  update_atbx.py
  artifacts/                         # output from CI (dated .atbx)
```

Release pipeline tasks under [../../tasks](../../tasks) expect artifact name pattern `Sample_Editing_Tools_*.atbx`.

`config.json` lists only opaque script paths. At build time, scripts are paired with toolbox `tool.script.execute.py` entries in **lexicographic order of zip paths** (same order as `s01`, `s02`, … in config). Adjust script order in config if a slot maps to the wrong tool.
