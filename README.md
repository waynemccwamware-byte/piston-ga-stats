# GA Accident Stats

Live site: https://piston-ga-stats.netlify.app/ (GeezerGeek Pilot Apps). Named Piston GA Stats until v0.18
(03-Nov-2026); the repo and site name were kept so shared links still work.

Compares US accident records for piston and turboprop airplane types (one or several per side): accident category, phase of flight,
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
The scripts read `~/data/{ntsb,pre}/csv/*.csv` and `~/data/reg/{MASTER,DEREG,ACFTREF,ENGINE}.txt`, import from
`~/scripts` (link it to `build/`) and write to `~/app/piston-ga-stats/data/` (link `~/app/piston-ga-stats` to `site/`).
Order: `codes.py`, `build_reg.py`, `build_all.py`, `bundle.py`. Set `NTSB_AS_OF` / `REG_AS_OF` (YYYY-MM-DD)
first. `patch_reg.py` refreshes only the registry numbers in an existing `accidents.json`.

Checked 19-Oct-2026: these scripts reproduce the live data exactly (43,024 accidents, all 22 columns,
all `causes-*.json` files) from avall.mdb 01-Oct-2026, Pre2008.mdb 06-Mar-2025 and the FAA registry 16-Oct-2026.

## Turboprops (v0.18, 03-Nov-2026)
PC-12, TBM (700, 850 and 900 series as one type), PA-46 turbines (Meridian/M500/M600/M700 and PT6 JetPROP conversions) and the
Epic E1000. Notes from the probe of the FAA and NTSB files:
- TBMs are one type (Wayne's call, 03-Nov-2026). A split was tried: the registry files every 850 and 900-series
  airplane as "TBM 700"/"TBM 700N", so it needed serial number (1000 on = 900 series) and year built (2006 on = 850).
- JetPROPs are found by a PT6 in `ENGINE.txt` for the registration, or the NTSB engine type TP. The registration's own
  TYPE ENGINE code is unreliable (piston Mirages carry the turboprop code). Most JetPROPs still show their piston
  engine on the registry, so the JetPROP fleet is undercounted; the app shows no rate for it.
- Turbine conversions of piston types (PA-31T, Soloy 206, turbine 210/Bonanza...) stay out of the piston families.
- Part 135 accidents are kept and tagged (`part` column); the app defaults to Part 91, as before.

## Safety within category (v0.25, 03-Nov-2026)
Section 3 (moved up from 7 in v0.27, right after the Summary) is a funnel plot: every type in one category (piston singles, piston twins or turboprops) as a dot,
average registered fleet (log scale) against accidents or fatal accidents per 1,000 registered aircraft-years.
The band is the 95% Poisson limit around the category's pooled rate for that exposure (fleet x years); dashed
lines are 99.8%. "Below/above the funnel" uses an exact two-sided Poisson test (p < 0.05). Same filters as the
rest of the page (years, purpose, Part 91/135). The category follows Type A unless picked; link keys `sm=fatal`
and `sc=ps|pm|t`. The JetPROP is left out (unreliable fleet). Chosen instead of a numeric "safest" rank (Wayne,
03-Nov-2026), because ranks overstate tiny differences and the rates are per registered aircraft, not per hour.
Pan/zoom (v0.26): the view is kept in data space and the chart redrawn (no CSS scaling). Pinch (two pointers;
Safari Mac trackpad via gesture events), Ctrl/Cmd + wheel, or the − + Reset buttons; drag pans once zoomed. Up to
25×, clamped to the full view. One finger scrolls the page until zoomed (touch-action pan-y, then none). A change
of category, measure or filters returns to the full view; picking types keeps it. Zoom is not saved in the link.
