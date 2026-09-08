import test from 'node:test';
import assert from 'node:assert/strict';
import { webcrypto } from 'node:crypto';
import worker, { canonical, normalize, issueBody } from '../src/index.js';
import { config } from '../src/review-config.generated.js';
if (!globalThis.crypto) globalThis.crypto = webcrypto;
const env = { ALLOWED_ORIGIN: 'https://foxrav.github.io', GITHUB_EVIDENCE_REPOSITORY: 'Example/private-review-evidence',
  PUBLICATION_AUTHORIZED: 'true', REVIEW_ACCESS_CODE: 'test-only-placeholder-not-a-real-code', GITHUB_TOKEN: 'test-only-token' };
const payload = () => ({ schema_version: config.schema_version, review_run_id: config.review_run_id,
  review_candidate_commit: config.review_candidate_commit, review_data_sha256: config.review_data_sha256,
  reviewer: { name: 'Test Reviewer', role: 'Test role' }, confirmation: true, access_code: env.REVIEW_ACCESS_CODE,
  decisions: config.units.map(u => ({ unit_id: u.unit_id, decision: 'ACCEPT_CURRENT', recommended_finnish: u.current_candidate_fi, rationale: '' })) });
const request = (p, options = {}) => new Request('https://worker.invalid/submit', { method: 'POST', headers: { 'Content-Type': 'application/json', Origin: env.ALLOWED_ORIGIN }, body: JSON.stringify(p), ...options });
test('valid submission creates exactly one issue and returns only safe fields', async t => {
  let calls = 0, body;
  t.mock.method(globalThis, 'fetch', async (url, options) => {
    if (options.method !== 'POST') {
      assert.equal(url, `https://api.github.com/repos/${env.GITHUB_EVIDENCE_REPOSITORY}`);
      return Response.json({ private: true, full_name: env.GITHUB_EVIDENCE_REPOSITORY });
    }
    calls++; assert.equal(url, `https://api.github.com/repos/${env.GITHUB_EVIDENCE_REPOSITORY}/issues`);
    body = JSON.parse(options.body);
    return Response.json({ number: 123, html_url: 'https://github.com/FoxRav/SPICT-4ALL-FI-2026/issues/123' }, { status: 201 });
  });
  const result = await worker.fetch(request(payload()), env);
  assert.equal(result.status, 200); assert.equal(calls, 1);
  const data = await result.json();
  assert.deepEqual(Object.keys(data).sort(), ['issue_number', 'ok', 'submission_id', 'submitted_at_utc']);
  assert.match(body.body, /HUMAN DOMAIN REVIEW EVIDENCE — NOT G5 GATE PASS/);
  const evidence = JSON.parse(body.body.match(/```json\n([\s\S]*?)\n```/)[1]);
  assert.equal(evidence.decisions.length, 6);
  assert.equal(evidence.review_candidate_commit, config.review_candidate_commit);
  assert.equal(evidence.decisions[0].source_text_sha256, config.source_sha256_by_unit[config.units[0].unit_id]);
  const id = evidence.submission_id; delete evidence.submission_id;
  const hash = Buffer.from(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(canonical(evidence)))).toString('hex');
  assert.equal(id, hash);
  for (const secret of [env.REVIEW_ACCESS_CODE, env.GITHUB_TOKEN]) {
    assert.ok(!body.body.includes(secret)); assert.ok(!JSON.stringify(data).includes(secret));
  }
});
const cases = {
  'too-short submitted code': p => { p.access_code = 'x'.repeat(23); },
  'missing unit': p => p.decisions.pop(),
  'duplicate unit': p => { p.decisions[1] = p.decisions[0]; },
  'unknown unit': p => { p.decisions[0].unit_id = 'unknown'; },
  'invalid enum': p => { p.decisions[0].decision = 'REJECT_AND_REWRITE'; },
  'missing correction': p => { Object.assign(p.decisions[0], { decision: 'ACCEPT_WITH_EDIT', recommended_finnish: '  ' }); },
  'missing rationale': p => { p.decisions[0].decision = 'NEEDS_FURTHER_CLINICAL_OR_TERMINOLOGY_REVIEW'; },
  'wrong candidate': p => { p.review_candidate_commit = 'a'.repeat(40); },
  'wrong hash': p => { p.review_data_sha256 = 'a'.repeat(64); },
  'wrong run': p => { p.review_run_id = 'G6'; },
  'wrong schema': p => { p.schema_version = '2'; },
  'invalid access code': p => { p.access_code = 'wrong'; },
  'missing reviewer': p => { delete p.reviewer; },
  'blank name': p => { p.reviewer.name = ' '; },
  'blank role': p => { p.reviewer.role = ''; },
  'false confirmation': p => { p.confirmation = false; },
  'long correction': p => { p.decisions[0].recommended_finnish = 'x'.repeat(2001); },
  'long rationale': p => { p.decisions[0].rationale = 'x'.repeat(1201); },
};
for (const [name, mutate] of Object.entries(cases)) test(name, async t => {
  t.mock.method(globalThis, 'fetch', () => { assert.fail('must not contact GitHub'); });
  const p = payload(); mutate(p); const result = await worker.fetch(request(p), env);
  assert.ok(result.status >= 400 && result.status < 500);
  const text = await result.text(); assert.ok(!text.includes(env.REVIEW_ACCESS_CODE)); assert.ok(!text.includes(env.GITHUB_TOKEN));
});

for (const value of ['', undefined, 'bad/path/extra']) test(`missing or invalid evidence repository: ${value}`, async t => {
  t.mock.method(globalThis, 'fetch', () => assert.fail('no API call allowed'));
  assert.equal((await worker.fetch(request(payload()), { ...env, GITHUB_EVIDENCE_REPOSITORY: value })).status, 503);
});
for (const value of ['x'.repeat(23), 'x'.repeat(257)]) test(`invalid configured secret length ${value.length}`, async t => {
  t.mock.method(globalThis, 'fetch', () => assert.fail('no API call allowed'));
  assert.equal((await worker.fetch(request(payload()), { ...env, REVIEW_ACCESS_CODE: value })).status, 503);
});
for (const metadata of [{ private: false }, {}, { private: 'true' }, { private: true, full_name: 'Other/repo' }]) {
  test(`privacy must be confirmed: ${JSON.stringify(metadata)}`, async t => {
    let calls = 0;
    t.mock.method(globalThis, 'fetch', async (url, options) => {
      calls++; assert.notEqual(options.method, 'POST');
      return Response.json({ full_name: env.GITHUB_EVIDENCE_REPOSITORY, ...metadata });
    });
    const result = await worker.fetch(request(payload()), env);
    assert.equal(result.status, 503); assert.equal(calls, 1);
    assert.ok(!(await result.text()).includes(env.GITHUB_TOKEN));
  });
}
test('field length boundaries accepted', () => {
  const p = payload();
  p.decisions[0] = { ...p.decisions[0], decision: 'ACCEPT_WITH_EDIT', recommended_finnish: 'x'.repeat(2000), rationale: 'x'.repeat(1200) };
  assert.equal(normalize(p).decisions[0].recommended_finnish.length, 2000);
});
// Construct exact body-byte boundaries using valid field lengths and multibyte text.
function sizedPayload(target) {
  const p = payload();
  for (const d of p.decisions) Object.assign(d, { decision: 'ACCEPT_WITH_EDIT', recommended_finnish: 'a'.repeat(2000), rationale: 'a'.repeat(1200) });
  const measure = () => Buffer.byteLength(issueBody({ ...normalize(p), submitted_at_utc: '2026-09-08T00:00:00.000Z', submission_id: '0'.repeat(64) }));
  let delta = target - measure();
  if (delta % 2 !== 0) {
    p.reviewer.name += '"'; // One extra JSON escape changes byte parity.
    delta = target - measure();
  }
  assert.ok(delta >= 0 && delta % 2 === 0);
  for (const d of p.decisions) {
    for (const key of ['recommended_finnish', 'rationale']) {
      const count = Math.min(delta / 2, d[key].length);
      d[key] = 'ä'.repeat(count) + d[key].slice(count); delta -= count * 2;
    }
  }
  assert.equal(delta, 0); assert.equal(measure(), target); return p;
}
test('exact 60000 byte body accepted', async t => {
  let posts = 0;
  t.mock.method(globalThis, 'fetch', async (url, options) => {
    if (options.method !== 'POST') return Response.json({ private: true, full_name: env.GITHUB_EVIDENCE_REPOSITORY });
    posts++; assert.equal(Buffer.byteLength(JSON.parse(options.body).body), 60000);
    return Response.json({ number: 1 }, { status: 201 });
  });
  assert.equal((await worker.fetch(request(sizedPayload(60000)), env)).status, 200); assert.equal(posts, 1);
});
test('oversized final body rejected before any GitHub API call', async t => {
  t.mock.method(globalThis, 'fetch', () => assert.fail('no GitHub API call allowed'));
  const result = await worker.fetch(request(sizedPayload(60001)), env);
  assert.equal(result.status, 413); assert.match((await result.json()).error, /liian suuri/);
});
test('normalized text, canonical ordering, no arbitrary fields', () => {
  const p = payload(); p.decisions.reverse(); p.extra = 'discard';
  p.decisions[0].recommended_finnish = 'forged';
  p.decisions[1].decision = 'ACCEPT_WITH_EDIT'; p.decisions[1].recommended_finnish = ' Test edit ';
  p.decisions[2].decision = 'NEEDS_FURTHER_CLINICAL_OR_TERMINOLOGY_REVIEW'; p.decisions[2].rationale = ' Needs human review ';
  const n = normalize(p);
  assert.deepEqual(n.decisions.map(d => d.unit_id), config.units.map(u => u.unit_id));
  assert.equal(n.decisions[5].recommended_finnish, config.units[5].current_candidate_fi);
  assert.equal(n.decisions[4].recommended_finnish, 'Test edit'); assert.equal(n.decisions[3].rationale, 'Needs human review');
  assert.ok(!('access_code' in n)); assert.ok(!('extra' in n));
  n.reviewer.name = '```\n# injected'; assert.ok(issueBody(n).includes('````\n```\n# injected\n````'));
});
test('routing, CORS, content type, body limits and permission', async t => {
  t.mock.method(globalThis, 'fetch', () => assert.fail('unexpected upstream'));
  assert.equal((await worker.fetch(new Request('https://worker.invalid/nope'), env)).status, 404);
  assert.equal((await worker.fetch(new Request('https://worker.invalid/submit'), env)).status, 405);
  const options = new Request('https://worker.invalid/submit', { method: 'OPTIONS', headers: { Origin: env.ALLOWED_ORIGIN } });
  const preflight = await worker.fetch(options, env); assert.equal(preflight.status, 204);
  assert.equal(preflight.headers.get('Access-Control-Allow-Origin'), env.ALLOWED_ORIGIN);
  const denied = await worker.fetch(request(payload(), { headers: { Origin: 'https://evil.invalid' } }), env);
  assert.equal(denied.status, 403); assert.equal(denied.headers.get('Access-Control-Allow-Origin'), null);
  assert.equal((await worker.fetch(request(payload()), { ...env, ALLOWED_ORIGIN: '*' })).status, 403);
  assert.equal((await worker.fetch(request(payload()), { ...env, PUBLICATION_AUTHORIZED: 'false' })).status, 503);
  assert.equal((await worker.fetch(request(payload(), { headers: { Origin: env.ALLOWED_ORIGIN, 'Content-Type': 'text/plain' } }), env)).status, 415);
  assert.equal((await worker.fetch(request(payload(), { body: '{' }), env)).status, 400);
  assert.equal((await worker.fetch(request(payload(), { body: 'x'.repeat(65537) }), env)).status, 413);
});
test('upstream failures are safe and are never retried', async t => {
  let calls = 0;
  t.mock.method(globalThis, 'fetch', async () => { calls++; return new Response(env.GITHUB_TOKEN, { status: 500 }); });
  const result = await worker.fetch(request(payload()), env); assert.equal(result.status, 502); assert.equal(calls, 1);
  assert.ok(!(await result.text()).includes(env.GITHUB_TOKEN));
});
test('Issue API failure after successful privacy check is safe and not retried', async t => {
  let posts = 0;
  t.mock.method(globalThis, 'fetch', async (url, options) => {
    if (options.method !== 'POST') return Response.json({ private: true, full_name: env.GITHUB_EVIDENCE_REPOSITORY });
    posts++; return new Response(env.GITHUB_TOKEN, { status: 500 });
  });
  const result = await worker.fetch(request(payload()), env);
  assert.equal(result.status, 502); assert.equal(posts, 1);
  assert.ok(!(await result.text()).includes(env.GITHUB_TOKEN));
});

const diagnosticCases = [
  ['repository network', 'GITHUB_REPOSITORY_METADATA_FETCH', undefined, 'network'],
  ['repository HTTP', 'GITHUB_REPOSITORY_METADATA_FETCH', 403, 'http'],
  ['repository JSON', 'GITHUB_REPOSITORY_METADATA_PARSE_VALIDATE', 200, 'json'],
  ['repository validation exception', 'GITHUB_REPOSITORY_METADATA_PARSE_VALIDATE', 200, 'null'],
  ['issue network', 'GITHUB_ISSUE_POST_FETCH', undefined, 'network'],
  ['issue HTTP', 'GITHUB_ISSUE_POST_FETCH', 422, 'http'],
  ['issue JSON', 'GITHUB_ISSUE_RESPONSE_PARSE_VALIDATE', 201, 'json'],
  ['issue validation', 'GITHUB_ISSUE_RESPONSE_PARSE_VALIDATE', 201, 'invalid'],
];
for (const [label, stage, status, mode] of diagnosticCases) test(`safe diagnostic: ${label}`, async t => {
  const logs = [];
  t.mock.method(console, 'error', (...args) => logs.push(args));
  const p = payload();
  const sensitive = [env.GITHUB_TOKEN, env.REVIEW_ACCESS_CODE, p.reviewer.name, p.reviewer.role,
    p.decisions[0].recommended_finnish, JSON.stringify(p), 'Authorization: Bearer'];
  const hostileError = new Error(sensitive.join(' '));
  hostileError.name = sensitive.join(' ');
  t.mock.method(globalThis, 'fetch', async (url, options) => {
    assert.equal(options.redirect, 'manual'); assert.ok(options.signal instanceof AbortSignal);
    const issue = options.method === 'POST';
    if (!issue && label.startsWith('issue')) return Response.json({ private: true, full_name: env.GITHUB_EVIDENCE_REPOSITORY });
    if (mode === 'network') throw hostileError;
    if (mode === 'http') return new Response(sensitive.join(' '), { status });
    if (mode === 'json') return new Response(sensitive.join(' '), { status });
    if (mode === 'null') return Response.json(null);
    return Response.json({ number: 'not-an-integer' }, { status });
  });
  const result = await worker.fetch(request(p), env);
  assert.equal(result.status, 502);
  const client = await result.text();
  assert.match(client, /Arvion tallennusta ei voitu vahvistaa/);
  assert.ok(!client.includes(stage));
  assert.equal(logs.length, 1); assert.equal(logs[0].length, 1);
  const diagnostic = logs[0][0];
  assert.equal(diagnostic.stage, stage); assert.equal(diagnostic.status, status);
  assert.deepEqual(Object.keys(diagnostic).sort(), status === undefined ? ['message', 'name', 'stage'] : ['message', 'name', 'stage', 'status']);
  for (const value of sensitive) { assert.ok(!JSON.stringify(logs).includes(value)); assert.ok(!client.includes(value)); }
});

test('successful submission emits no diagnostics', async t => {
  t.mock.method(console, 'error', () => assert.fail('success must not log'));
  let posts = 0;
  t.mock.method(globalThis, 'fetch', async (url, options) => {
    if (options.method !== 'POST') return Response.json({ private: true, full_name: env.GITHUB_EVIDENCE_REPOSITORY });
    posts++; return Response.json({ number: 123 }, { status: 201 });
  });
  const result = await worker.fetch(request(payload()), env);
  assert.equal(result.status, 200); assert.equal(posts, 1);
  assert.deepEqual(Object.keys(await result.json()).sort(), ['issue_number', 'ok', 'submission_id', 'submitted_at_utc']);
});

for (const phase of ['repository', 'issue']) {
  for (const status of [301, 302, 307, 308]) test(`${phase} redirect ${status} rejected without following Location`, async t => {
    const logs = [];
    t.mock.method(console, 'error', (...args) => logs.push(args));
    const calls = [];
    const target = 'https://redirect-target.invalid/do-not-fetch';
    t.mock.method(globalThis, 'fetch', async (url, options) => {
      calls.push(url);
      assert.notEqual(url, target);
      assert.equal(options.redirect, 'manual');
      assert.ok(options.signal instanceof AbortSignal);
      const base = `https://api.github.com/repos/${env.GITHUB_EVIDENCE_REPOSITORY}`;
      if (phase === 'issue' && url === base) return Response.json({ private: true, full_name: env.GITHUB_EVIDENCE_REPOSITORY });
      assert.equal(url, phase === 'repository' ? base : `${base}/issues`);
      const response = new Response('not JSON', { status, headers: { Location: target } });
      response.json = () => assert.fail('redirect body must not be parsed');
      return response;
    });
    const result = await worker.fetch(request(payload()), env);
    assert.equal(result.status, 502);
    assert.equal(calls.length, phase === 'repository' ? 1 : 2);
    assert.equal(logs.length, 1);
    assert.equal(logs[0][0].stage, phase === 'repository' ? 'GITHUB_REPOSITORY_METADATA_FETCH' : 'GITHUB_ISSUE_POST_FETCH');
    assert.equal(logs[0][0].status, status);
    const client = await result.text();
    for (const secret of [env.GITHUB_TOKEN, env.REVIEW_ACCESS_CODE]) {
      assert.ok(!JSON.stringify(logs).includes(secret)); assert.ok(!client.includes(secret));
    }
    assert.ok(!JSON.stringify(logs).includes(target));
  });
}
