import { config } from './review-config.generated.js';

const ENUMS = ['ACCEPT_CURRENT', 'ACCEPT_WITH_EDIT', 'NEEDS_FURTHER_CLINICAL_OR_TERMINOLOGY_REVIEW'];
const MAX_BYTES = 65536;
function logUpstreamFailure(stage, error, status) {
  // Runtime exception text can contain response excerpts, credentials or user data.
  // Only known, context-free names/messages may pass through; never log the Error object.
  const names = ['Error', 'TypeError', 'SyntaxError', 'TimeoutError', 'AbortError'];
  const messages = ['privacy', 'upstream', 'response', 'fetch failed', 'Failed to fetch',
    'The operation was aborted due to timeout', 'The operation was aborted.',
    'Unexpected end of JSON input'];
  const diagnostic = {
    stage,
    name: names.includes(error?.name) ? error.name : 'Error',
    message: messages.includes(error?.message) ? error.message : '[redacted unsafe exception message]',
  };
  if (status !== undefined) diagnostic.status = status;
  console.error(diagnostic);
}
const isObject = x => x !== null && typeof x === 'object' && !Array.isArray(x);
function fail(message) { throw new Error(message); }
function string(value, max, required = true) {
  if (typeof value !== 'string' || value.length > max || (required && !value.trim())) fail('Puuttuva tai liian pitkä tekstikenttä.');
  return value.trim();
}
export function normalize(input) {
  if (!isObject(input)) fail('Virheellinen arvio.');
  for (const key of ['schema_version', 'review_run_id', 'review_candidate_commit', 'review_data_sha256']) {
    if (input[key] !== config[key]) fail('Arvion versio tai tarkistussumma ei täsmää.');
  }
  if (!isObject(input.reviewer)) fail('Arvioijan tiedot puuttuvat.');
  const reviewer = { name: string(input.reviewer.name, 120), role: string(input.reviewer.role, 240) };
  if (input.confirmation !== true) fail('Vahvistus puuttuu.');
  if (!Array.isArray(input.decisions) || input.decisions.length !== 6) fail('Tarvitaan kuusi päätöstä.');
  const byId = new Map();
  for (const d of input.decisions) {
    if (!isObject(d) || !config.units.some(u => u.unit_id === d.unit_id) || byId.has(d.unit_id)) fail('Tuntematon tai toistuva kohta.');
    if (!ENUMS.includes(d.decision)) fail('Tuntematon päätös.');
    byId.set(d.unit_id, d);
  }
  const decisions = config.units.map(unit => {
    const d = byId.get(unit.unit_id);
    if (!d) fail('Kohta puuttuu.');
    if (d.recommended_finnish !== undefined) string(d.recommended_finnish, 2000, false);
    const rationale = string(d.rationale ?? '', 1200, d.decision === ENUMS[2]);
    return { unit_id: unit.unit_id, source_text_sha256: config.source_sha256_by_unit[unit.unit_id],
      decision: d.decision, recommended_finnish: d.decision === ENUMS[1]
        ? string(d.recommended_finnish, 2000) : unit.current_candidate_fi, rationale };
  });
  return { schema_version: config.schema_version, review_run_id: config.review_run_id,
    review_candidate_commit: config.review_candidate_commit, review_data_sha256: config.review_data_sha256,
    reviewer, decisions, confirmation: true };
}
export function canonical(value) {
  if (Array.isArray(value)) return '[' + value.map(canonical).join(',') + ']';
  if (isObject(value)) return '{' + Object.keys(value).sort().map(k => JSON.stringify(k) + ':' + canonical(value[k])).join(',') + '}';
  return JSON.stringify(value);
}
async function digest(text) {
  return [...new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text)))].map(x => x.toString(16).padStart(2, '0')).join('');
}
function fence(text, language = '') {
  const runs = text.match(/`+/g) ?? [];
  const delimiter = '`'.repeat(Math.max(3, ...runs.map(x => x.length + 1)));
  return `${delimiter}${language}\n${text}\n${delimiter}`;
}
export function issueBody(evidence) {
  return ['# HUMAN DOMAIN REVIEW EVIDENCE — NOT G5 GATE PASS',
    'Incoming evidence only. Not adjudication, clinical validation or SPICT approval.',
    `Review run: ${evidence.review_run_id}`, `Frozen review candidate commit: ${evidence.review_candidate_commit}`,
    `Review data SHA-256: ${evidence.review_data_sha256}`, 'Reviewer name:\n' + fence(evidence.reviewer.name),
    'Reviewer role:\n' + fence(evidence.reviewer.role), `Submitted at UTC: ${evidence.submitted_at_utc}`,
    `Submission ID: ${evidence.submission_id}`,
    ...evidence.decisions.map(d => `## ${d.unit_id}\nDecision: ${d.decision}\n\nRecommended Finnish:\n${fence(d.recommended_finnish)}\n\nRationale:\n${fence(d.rationale)}`),
    '## Machine-readable normalized evidence', fence(JSON.stringify(evidence, null, 2), 'json')].join('\n\n');
}
async function readLimited(request) {
  if (Number(request.headers.get('content-length')) > MAX_BYTES) throw new RangeError();
  const reader = request.body?.getReader();
  if (!reader) fail('Tyhjä pyyntö.');
  const chunks = []; let size = 0;
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    size += value.byteLength;
    if (size > MAX_BYTES) { await reader.cancel(); throw new RangeError(); }
    chunks.push(value);
  }
  const bytes = new Uint8Array(size); let offset = 0;
  for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.length; }
  return JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(bytes));
}
export default {
  async fetch(request, env) {
    const origin = request.headers.get('origin');
    const allowed = env.ALLOWED_ORIGIN && env.ALLOWED_ORIGIN !== '*' && origin === env.ALLOWED_ORIGIN;
    const headers = { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store', 'Vary': 'Origin' };
    if (allowed) Object.assign(headers, { 'Access-Control-Allow-Origin': origin, 'Access-Control-Allow-Methods': 'POST, OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type' });
    const response = (status, body) => new Response(JSON.stringify(body), { status, headers });
    if (new URL(request.url).pathname !== '/submit') return response(404, { error: 'Reittiä ei löydy.' });
    if (!['POST', 'OPTIONS'].includes(request.method)) return response(405, { error: 'Menetelmä ei ole sallittu.' });
    if (!allowed) return response(403, { error: 'Alkuperä ei ole sallittu.' });
    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers });
    if (env.PUBLICATION_AUTHORIZED !== 'true') return response(503, { error: 'Julkaiseminen on estetty.' });
    if (request.headers.get('content-type')?.split(';')[0].trim().toLowerCase() !== 'application/json') return response(415, { error: 'Tarvitaan application/json.' });
    if (typeof env.REVIEW_ACCESS_CODE !== 'string' || env.REVIEW_ACCESS_CODE.length < 24 || env.REVIEW_ACCESS_CODE.length > 256 || !env.GITHUB_TOKEN || typeof env.GITHUB_EVIDENCE_REPOSITORY !== 'string' || !/^[A-Za-z0-9-]+\/[A-Za-z0-9_.-]+$/.test(env.GITHUB_EVIDENCE_REPOSITORY)) return response(503, { error: 'Palvelun asetukset puuttuvat.' });
    let normalized;
    try {
      const input = await readLimited(request);
      if (!isObject(input) || typeof input.access_code !== 'string' || input.access_code.length < 24 || input.access_code.length > 256 || input.access_code !== env.REVIEW_ACCESS_CODE) return response(403, { error: 'Virheellinen arviointikoodi.' });
      normalized = normalize(input);
    } catch (error) {
      return response(error instanceof RangeError ? 413 : 400, { error: 'Tarkista arvio: kenttä puuttuu, on virheellinen tai ylittää pituusrajan.' });
    }
    const evidence = { ...normalized, submitted_at_utc: new Date().toISOString() };
    evidence.submission_id = await digest(canonical(evidence));
    const body = issueBody(evidence);
    if (new TextEncoder().encode(body).byteLength > 60000) return response(413, { error: 'Arvio on liian suuri tallennettavaksi. Lyhennä tekstejä ja yritä uudelleen.' });
    let stage = 'GITHUB_REPOSITORY_METADATA_FETCH';
    let upstreamStatus;
    try {
      const repository = await fetch(`https://api.github.com/repos/${env.GITHUB_EVIDENCE_REPOSITORY}`, {
        headers: { Authorization: `Bearer ${env.GITHUB_TOKEN}`, Accept: 'application/vnd.github+json',
          'User-Agent': 'SPICT-G5-review', 'X-GitHub-Api-Version': '2022-11-28' },
        redirect: 'manual', signal: AbortSignal.timeout(15000),
      });
      upstreamStatus = repository.status;
      // Manual mode never follows Location; all redirects fail this exact status check.
      if (repository.status !== 200) throw new Error('privacy');
      stage = 'GITHUB_REPOSITORY_METADATA_PARSE_VALIDATE';
      const metadata = await repository.json();
      if (metadata.private !== true || typeof metadata.full_name !== 'string' || metadata.full_name.toLowerCase() !== env.GITHUB_EVIDENCE_REPOSITORY.toLowerCase()) {
        return response(503, { error: 'Arvion yksityistä tallennuspaikkaa ei voitu vahvistaa.' });
      }
      stage = 'GITHUB_ISSUE_POST_FETCH';
      upstreamStatus = undefined;
      const upstream = await fetch(`https://api.github.com/repos/${env.GITHUB_EVIDENCE_REPOSITORY}/issues`, {
        method: 'POST', headers: { 'Authorization': `Bearer ${env.GITHUB_TOKEN}`, 'Accept': 'application/vnd.github+json',
          'Content-Type': 'application/json', 'User-Agent': 'SPICT-G5-review', 'X-GitHub-Api-Version': '2022-11-28' },
        body: JSON.stringify({ title: `[G5 DOMAIN REVIEW] ${evidence.reviewer.name.replace(/[\r\n]/g, ' ')} — ${config.review_run_id} — ${evidence.submission_id}`, body }),
        redirect: 'manual', signal: AbortSignal.timeout(15000),
      });
      upstreamStatus = upstream.status;
      // Reject redirects before reading the response or making another request.
      if (upstream.status !== 201) throw new Error('upstream');
      stage = 'GITHUB_ISSUE_RESPONSE_PARSE_VALIDATE';
      const issue = await upstream.json();
      if (!Number.isInteger(issue.number) || issue.number < 1) throw new Error('response');
      return response(200, { ok: true, submission_id: evidence.submission_id, issue_number: issue.number,
        submitted_at_utc: evidence.submitted_at_utc });
    } catch (error) {
      logUpstreamFailure(stage, error, upstreamStatus);
      return response(502, { error: 'Arvion tallennusta ei voitu vahvistaa. Älä lähetä uudelleen ennen kuin ylläpitäjä on tarkistanut, syntyikö arvio.' });
    }
  },
};
