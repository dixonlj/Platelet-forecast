# Seed check 2026-11-25

**Verdict: MATCH**

One fresh draw of reserved demand seed `20261121` matches the saved on-disk network. The runner’s own loader, called directly and not through `main`, returns the same dates, site ids, site types, and `units_issued`. `confirmatory_run.py` was not executed. `results/confirmatory/` was not modified. The work tree stayed clean.

## Environment

- HEAD: `5f079cee3da55e9727f204f74aa2db45fe8654ad` (detached)
- `git status --porcelain --untracked-files=all`: empty before and after
- Python: `3.13.5 (main, Jul 23 2025, 00:37:22) [Clang 20.1.4 ]` from `.venv-confirmatory/bin/python`

## How the runner draws the network

`load_confirmatory_network` is the only network draw on the confirmatory path. It does not write a file.

`scripts/confirmatory_run.py` lines 837–850:

```python
def load_confirmatory_network(*, confirmatory: bool):
    """Draw the 16-hospital series with demand seed 20261121.

    Called only when confirmatory is true. The 3-site exploratory generator is
    not a substitute and is not called with this seed. Nothing is written to disk.
    """
    if not confirmatory:
        raise ConfirmatoryRefused(
            "Network seeds 20261121 and 20261122 are confirmatory. Pass --confirmatory. "
            "This process will not generate that series.")
    gen = _cinderwell_module()
    frame, _wide, _expected, _sites, _factors = gen.make_network(
        NETWORK_SEED, confirmatory_caller=True)
    return _hospitals_from_frame(frame)
```

- Function: `make_synthetic_network_2021_2030.make_network`
- Arguments: positional seed `NETWORK_SEED`, keyword `confirmatory_caller=True`
- Seed: `NETWORK_SEED = 20261121` (`scripts/confirmatory_run.py` line 159)
- Caller flag: `confirmatory_caller=True`. Without it, `make_network` calls `_refuse_reserved_seed` and exits before any draw (`scripts/make_synthetic_network_2021_2030.py` lines 37–45 and 171–178).
- `write_network` always calls that guard with `confirmatory_caller=False` (lines 335–344), so the command line cannot write this seed.
- The frame the analysis keeps is built by `_hospitals_from_frame` (lines 811–834): one `SiteSeries` per `site_id`, with `name` set to the site id, `site_type`, `demand` from `units_issued` as float, and `dates`. It does not keep `site_name` or `expected_rate`.

`run_network_step` (line 863) calls `load_confirmatory_network(confirmatory=True)` and does not read a CSV.

## Check 1 — same draw, written with the generator’s CSV writer

A new Python process called `make_network(20261121, confirmatory_caller=True)`, then ` _write_csv` and `_headers` for the long table. `generator_parameters.json` was written with the same dictionary `write_network` uses (lines 359–375). Files were written only under `/opt/cursor/artifacts/seed_check_2026-11-25/regenerated/`.

Saved copy: `/opt/cursor/artifacts/confirmatory_2026-11-25/network_seed_20261121/`.

| Check | Result |
| --- | --- |
| Long CSV SHA-256, saved | `0b5ad57cb53b252c8b0c46597538a324e6f555acf620195bc9d7b04d5455f8eb` |
| Long CSV SHA-256, this draw | `0b5ad57cb53b252c8b0c46597538a324e6f555acf620195bc9d7b04d5455f8eb` |
| Matches the expected hash | yes |
| Rows | 58,432 saved, 58,432 rewritten, 58,432 in memory (16 sites × 3,652 days) |
| `DataFrame.equals` of the two CSVs, original row order, every column | true |
| Columns | `date`, `site_id`, `site_name`, `site_type`, `units_issued`, `expected_rate` |
| In-memory frame versus the saved CSV, aligned on `date` and `site_id` | exact on every column, including `units_issued` and `expected_rate` |
| `generator_parameters.json` SHA-256 | `04c01fcb259f8a86f2c4dfca8aa051b725751953782d21a9eefefeaadd65757d` on both copies; parsed JSON equal |

The other generator files also matched byte for byte:

| File | SHA-256 |
| --- | --- |
| `SYNTHETIC_cinderwell_network_2021-2030_wide.csv` | `be6997fae338152371ba3565513096969b224da28523ff684eff4cede331972e` |
| `SYNTHETIC_cinderwell_network_2021-2030_expected_rate.csv` | `fde94f4b46949b92acd26d8ba8d45df0dc0ef7ae76a4783aea18ebfe29c8d95c` |
| `SYNTHETIC_cinderwell_network_2021-2030_shared_factors.csv` | `b91dda2a80f57d8dcc9b82a4c374d4832c5fad07e2f4c09e19b6be5d485b475d` |
| `SYNTHETIC_cinderwell_network_sites.csv` | `612450143864ad5151d09c277e5e3a8fa73e04bcc3cd160649a180b9095e478b` |

No column differed. There is no row-level diff to list.

## Check 2 — `load_confirmatory_network(confirmatory=True)`

A second Python process imported `confirmatory_run` and called `load_confirmatory_network(confirmatory=True)`. It did not call `main`. The constant `NETWORK_SEED` was 20261121. The call returned 16 sites and 58,432 demand rows.

Compared with the saved long CSV, every site matched on dates, `units_issued` (exact float equality with the loader’s `float` demand), and `site_type`. The 16-site frame of those columns equals the CSV after sorting by `site_id` and `date`. `site_name` and `expected_rate` are in the CSV and are not fields on the loader’s `SiteSeries`.

## What was not done

- `confirmatory_run.py` was not run.
- No forecast, bootstrap, or inventory replay was run.
- `results/confirmatory/` file sizes and timestamps were unchanged.
- Nothing was committed, pushed, or opened as a pull request.
