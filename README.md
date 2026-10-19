# Piston GA Stats

Live site: https://piston-ga-stats.netlify.app/ (GeezerGeek Pilot Apps)

Compares US accident records for two piston airplane types: accident category, phase of flight,
severity, rates per registered aircraft, top NTSB findings and the latest accidents.

## Layout
- `site/` — what Netlify publishes (see `netlify.toml`): `index.html` and `data/`.
- `build/` — scripts that rebuild `site/data/` from the NTSB and FAA source files.
- `.github/workflows/update-data.yml` — the monthly update job.

## Data updates
The job runs on the 2nd of each month (15:00 UTC) and can be run by hand:
GitHub > Actions > "Update NTSB and FAA data" > Run workflow (tick "force" to rebuild even when nothing changed).

It downloads `avall.zip` (NTSB, 2008 on), `Pre2008.zip` (NTSB, 1982-2007, cached) and the FAA
`ReleasableAircraft.zip`, rebuilds `site/data/`, runs `build/check_data.py`, and commits only if the checks
pass. Netlify redeploys from that commit. If the FAA download fails, the last good registry file is reused.
If a check fails, nothing is published and GitHub emails the repository owner.

Data dates (`ntsbAsOf`, `regAsOf`) come from the dates of `avall.mdb` and `MASTER.txt` inside the zips.

**Heads-up:** the NTSB says it will move this download to its Enterprise API (GetCasesByDateRangeV2) on
05-Apr-2027 (notice on data.ntsb.gov/avdata, read 19-Oct-2026). The download/convert steps must be
replaced before then.

## Rebuilding by hand (Linux/macOS with mdbtools)
The scripts read `~/data/{ntsb,pre}/csv/*.csv` and `~/data/reg/{MASTER,DEREG,ACFTREF}.txt`, import from
`~/scripts` (link it to `build/`) and write to `~/app/piston-ga-stats/data/` (link `~/app/piston-ga-stats` to `site/`).
Order: `codes.py`, `build_reg.py`, `build_all.py`, `bundle.py`. Set `NTSB_AS_OF` / `REG_AS_OF` (YYYY-MM-DD)
first. `patch_reg.py` refreshes only the registry numbers in an existing `accidents.json`.

Checked 19-Oct-2026: these scripts reproduce the live data exactly (43,024 accidents, all 22 columns,
all `causes-*.json` files) from avall.mdb 01-Oct-2026, Pre2008.mdb 06-Mar-2025 and the FAA registry 16-Oct-2026.
