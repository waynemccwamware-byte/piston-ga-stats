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
rest of the page (years, purpose, Part 91/135). The category follows Type A unless picked; link key
`sc=ps|pm|t`. The measure opens on Fatal accidents every time (v0.28; not kept in the link).

## Fatal by default (v0.29, 03-Nov-2026)
Every All/Fatal toggle (sections 3, 4, 5 and 7) opens on Fatal accidents, including after a preset or "Back to the
default", and none is kept in the page link (old `s`, `ps`, `tm` and `sm` keys are ignored). Section 4's toggle also
filters Top NTSB findings (8) and Latest accidents (9), so those open on fatal accidents too; the "Fatal only" chip
in section 9 clears it. The JetPROP is left out (unreliable fleet). Chosen instead of a numeric "safest" rank (Wayne,
03-Nov-2026), because ranks overstate tiny differences and the rates are per registered aircraft, not per hour.
Pan/zoom (v0.26): the view is kept in data space and the chart redrawn (no CSS scaling). Pinch (two pointers;
Safari Mac trackpad via gesture events), Ctrl/Cmd + wheel, or the − + Reset buttons; drag pans once zoomed. Up to
25×, clamped to the full view. One finger scrolls the page until zoomed (touch-action pan-y, then none). A change
of category, measure or filters returns to the full view; picking types keeps it. Zoom is not saved in the link.
Labels (v0.30): Types A and B always; once zoomed in, every dot, like the Airports Visited map. Each label tries
right, left, above, then below its dot and is skipped if it would overlap another label, a dot or the plot edge, so
more names appear as you zoom.
Type designators (v0.31): when zoomed, types other than A and B are labeled by ICAO type designator (`SF_DES` in
index.html), checked against FAA Order JO 7360.1K (issued 10-Apr-2025) by reading the Order's PDF tables. A family
spanning several designators is labeled with the one most common in its own accident records (model text mapped by
the Order's model lists; e.g. Baron 55/58 -> BE55, 210 -> T210, 401-421 -> C402); the popup lists them all. TBM: the
registry calls every TBM a 700, so year built splits it (2006 on = 850, 2014 on = 900 series); 700 and 850 tie, label
TBM7. Shared designators as in the Order: 172 Hawk XP = C172, DA40 NG = DA40. JetPROP = P46T (JETPROP DLX).
If families change in build/families.py, update SF_DES to match.
Full view (v0.32): "Open full view ↗" opens the same page with `view=funnel` in its own window (re-clicking reloads
that window with the new settings). In that mode (`body.fv`) only section 3 shows, the chart is drawn at the window's
own size (1 SVG unit = 1 CSS px, redrawn on resize/rotation), and a top bar gives what's shown, Full screen (only
where the browser allows it for a page element; not on iPhone) and Close (or "Full page" when opened from a link).
The window's link carries `sm=all` when needed; changes made there don't touch the page that opened it.

Tail-number search (v0.37, 22-Nov-2026): a search box in section 9 finds every accident for one N-number across the
whole database, ignoring the type, year, Part, purpose and Fatal settings (a search limited to the selection would
show a clean record for any tail outside it). Input is forgiving (`162gl`, `N-162GL`). Kept in the link as `tail=`;
a `tail=` link opens on section 9. Rows from neither Type A nor B get a grey swatch. When the records show more than
one type, or more than one year built, the note says the number was likely reassigned. A miss says the tail isn't in
this app's types, not that it has a clean record. Each expanded accident links the NTSB case page, the FAA Registry
N-number page (registry.faa.gov/AircraftInquiry/Search/NNumberResult?nNumberTxt=<N-number>, checked 22-Nov-2026;
shows the current holder of the number) and "All accidents for <N-number>". Picking Both/Type A/Type B or the chip's
✕ ends the search.

Live NTSB check (v0.38, 22-Nov-2026): a tail-number search also asks `netlify/functions/ntsb-tail.mjs`, which calls the
NTSB Public API `GetAviationCasesFiltered?aircraftRegistrationNumber=<N-number>` (api.ntsb.gov, checked 22-Nov-2026 in
the developer portal with N124LZ) using the `NTSB_API_KEY` Netlify environment variable (secret; header
`Ocp-Apim-Subscription-Key`). The function returns only status, report date, probable cause, defining event, findings,
injuries and aircraft; Netlify's edge caches each tail's answer for an hour. In the page, a case already in the bundle
shows a "Live from NTSB" box (status, probable cause, defining event, findings, report PDF via the mkey:
data.ntsb.gov/carol-repgen/api/Aviation/ReportMain/GenerateNewestReport/<mkey>/pdf) and a "NEW NTSB REPORT" tag when
the report date is on or after the bundle's NTSB date; cases the bundle lacks are listed under "Also on file at the
NTSB", never counted in statistics. If the function fails the bundled data stands with a one-line note. The NTSB says
the monthly avall download moves to this API platform on 05-Apr-2027 (data.ntsb.gov/avdata).

Per-accident live check (v0.40): every expanded accident (any view) has "Check NTSB for a newer report", which asks the
same function for that accident's tail number and matches the NTSB case number; answers are kept per tail for the visit
and shared with the tail search. A tail search with a single accident opens its details (v0.39).

Tail-number popup (v0.41): "Check latest NTSB status on a specific tail number" under the purpose line opens a dialog
with its own search box. While it is open it borrows section 9's result blocks (tailInfo, recentChip, recentList,
liveExtra, moreWrap are moved into the dialog and moved back on close), so it shows exactly what the tail search shows,
live NTSB check included. Closing it (✕, Escape, backdrop, or the chip's ✕) ends the tail search.
