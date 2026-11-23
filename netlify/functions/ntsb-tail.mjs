// GA Accident Stats v0.38: live NTSB lookup for the section 9 tail-number search.
//
// GET /.netlify/functions/ntsb-tail?tail=N124LZ
//   -> {tail, asOf, cases:[{ntsb, mkey, type, date, city, st, status, closed, reportDate, highest,
//        fatal, serious, minor, pc, def:{name, group, phase}, findings:[{text, cause}],
//        ac:{reg, make, model, yb, damage}}]}
//
// Source: NTSB Public API, operation GetAviationCasesFiltered
//   https://api.ntsb.gov/public/api/Aviation/v1/GetAviationCasesFiltered/?aircraftRegistrationNumber=<N-number>
// checked 22-Nov-2026 in the NTSB developer portal (developer.ntsb.gov) with N124LZ: returned WPR25LA085,
// mKey 199623, completionStatus "Completed", reportDate 2026-11-03, narratives[].probableCause, and per
// aircraft events[] (isDefiningEvent) and findings[] (inProbableCause). 204 No Content = no cases.
// The subscription key is the Netlify environment variable NTSB_API_KEY (marked secret, Functions scope).
// It is sent in the Ocp-Apim-Subscription-Key header and never returned to the page.
// No dependencies (Node's built-in fetch).

const API = 'https://api.ntsb.gov/public/api/Aviation/v1/GetAviationCasesFiltered/';
const tailKey = s => String(s || '').toUpperCase().replace(/[\s-]/g, '');

const json = (status, body, cache) => new Response(JSON.stringify(body), {
  status,
  headers: {
    'Content-Type': 'application/json; charset=utf-8',
    // the NTSB data changes at most daily; cache a tail's answer at Netlify's edge for an hour
    'Cache-Control': 'public, max-age=300',
    'Netlify-CDN-Cache-Control': cache ? 'public, s-maxage=3600, stale-while-revalidate=600' : 'no-store',
  },
});

const num = v => (typeof v === 'number' && isFinite(v) ? v : 0);
const str = v => (v == null ? '' : String(v).trim());

function slim(c, tail) {
  const acs = Array.isArray(c.aircrafts) ? c.aircrafts : [];
  // multi-aircraft events: keep the aircraft with this tail number
  const ac = acs.find(a => tailKey(a.aircraftRegistrationNumber) === tail) || acs[0] || {};
  const narr = (Array.isArray(c.narratives) ? c.narratives : [])
    .find(n => n.aircraftNumber === ac.aircraftNumber) || (c.narratives || [])[0] || {};
  const evs = Array.isArray(ac.events) ? ac.events : [];
  const d = evs.find(e => e.isDefiningEvent);
  const fnd = (Array.isArray(ac.findings) ? ac.findings : [])
    .map(f => ({ text: str(f.findingReportText || f.findingDescription), cause: !!f.inProbableCause }))
    .filter(f => f.text);
  const dmg = (Array.isArray(ac.aircraftAccidents) ? ac.aircraftAccidents : [])[0] || {};
  return {
    ntsb: str(c.ntsbNumber),
    mkey: typeof c.mKey === 'number' ? c.mKey : null,
    type: str(c.eventType),
    date: str(c.eventDate).slice(0, 10),
    city: str(c.eventCity),
    st: str(c.eventStateOrRegion),
    status: str(c.completionStatus),
    closed: !!c.caseClosed,
    reportDate: str(c.reportDate || c.originalPublishedDate).slice(0, 10),
    highest: str(c.highestInjuryLevel),
    fatal: num(c.totalFatal), serious: num(c.totalSerious), minor: num(c.totalMinor),
    pc: str(narr.probableCause),
    def: d ? { name: str(d.eventTier2Name), group: str(d.cicttEventSOEGroup), phase: str(d.cicttPhaseSOEGroup) } : null,
    findings: fnd,
    ac: {
      reg: str(ac.aircraftRegistrationNumber),
      make: str(ac.aircraftMake || ac.aircraftManufacturer),
      model: str(ac.aircraftModel),
      yb: str(ac.yearOfManufacture),
      damage: str(dmg.damageLevel),
    },
  };
}

export default async (req) => {
  const url = new URL(req.url);
  let tail = tailKey(url.searchParams.get('tail'));
  if (tail && !tail.startsWith('N')) tail = 'N' + tail;
  if (!/^N[1-9][0-9A-Z]{0,4}$/.test(tail)) return json(400, { error: 'Not a US N-number' }, false);
  const key = process.env.NTSB_API_KEY;
  if (!key) return json(503, { error: 'Live NTSB lookup is not configured' }, false);

  const ctl = new AbortController();
  const timer = setTimeout(() => ctl.abort(), 9000);
  try {
    const r = await fetch(API + '?aircraftRegistrationNumber=' + encodeURIComponent(tail), {
      headers: { 'Ocp-Apim-Subscription-Key': key, 'Cache-Control': 'no-cache', Accept: 'application/json' },
      signal: ctl.signal,
    });
    const asOf = new Date().toISOString();
    if (r.status === 204) return json(200, { tail, asOf, cases: [] }, true);
    if (!r.ok) return json(502, { error: `NTSB answered ${r.status}` }, false);
    const body = await r.json();
    const list = Array.isArray(body?.data) ? body.data : Array.isArray(body) ? body : [];
    const cases = list.map(c => slim(c, tail)).filter(c => c.ntsb)
      .sort((a, b) => b.date.localeCompare(a.date));
    return json(200, { tail, asOf, cases }, true);
  } catch (e) {
    return json(504, { error: e.name === 'AbortError' ? 'NTSB did not answer in time' : 'NTSB lookup failed' }, false);
  } finally {
    clearTimeout(timer);
  }
};
