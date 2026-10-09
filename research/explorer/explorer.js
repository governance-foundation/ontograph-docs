const $ = (selector) => document.querySelector(selector);
const views = ['conceptual', 'organisational', 'owl-gufo'];
const titles = { conceptual: 'Explicit conceptual commitments', organisational: 'Appointments and people', 'owl-gufo': 'A purpose-specific projection' };
const descriptions = {
  conceptual: 'Kinds, a role, relators, quality and event meaning come from explicit source declarations. Select a row to inspect its source and proposed mapping.',
  organisational: 'People and organisations connect through separately identified appointments. Membership and participation have their own explicit qualifications.',
  'owl-gufo': 'Expected generated IRIs connect to source identities. Runtime observations are separately labelled; a generated representation is not an accepted canonical object.'
};
let data, state, dataVerified = false, diagramBlobUrl = null;

function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined && text !== null) node.textContent = text;
  if (className) node.className = className;
  return node;
}
function paragraph(text, className) { return element('p', text, className); }
function code(text) { return element('code', text); }
function badge(text, type = '') { return element('span', text, `badge ${type}`); }
function link(label, href) {
  const node = element('a', label);
  // Only packaged relative assets and explicit HTTPS evidence are navigable.
  const url = new URL(href, document.baseURI);
  if (url.protocol !== 'https:' && !(url.origin === location.origin && ['http:', 'file:'].includes(url.protocol))) throw new Error('Unsafe evidence link');
  node.href = href;
  return node;
}
function packagedEvidence(href) {
  return typeof href === 'string' && (/^data\/recorded\/[a-zA-Z0-9_.-]+$/.test(href) || /^https:\/\//.test(href));
}
function bulletList(items) {
  const ul = element('ul');
  for (const item of items) ul.append(element('li', item));
  return ul;
}
function assert(condition, message) { if (!condition) throw new Error(message); }
function unique(items, name) {
  const ids = new Set();
  for (const row of items) { assert(typeof row.id === 'string' && !ids.has(row.id), `Duplicate or missing ${name} identity`); ids.add(row.id); }
  return ids;
}
async function verifiedFile(file) {
  assert(typeof file.path === 'string' && /^data\/[a-zA-Z0-9/_.,-]+$/.test(file.path) && !file.path.includes('..'), 'Invalid packaged artifact path');
  assert(Number.isInteger(file.bytes) && file.bytes >= 0 && /^[0-9a-f]{64}$/.test(file.sha256), 'Invalid artifact digest declaration');
  const response = await fetch(file.path, { cache: 'no-store' });
  assert(response.ok, `Missing artifact: ${file.id} (HTTP ${response.status})`);
  const bytes = await response.arrayBuffer();
  assert(bytes.byteLength === file.bytes, `Artifact byte count mismatch: ${file.id}`);
  assert(globalThis.crypto?.subtle, 'Secure-context checksum verification unavailable; use HTTPS or localhost');
  const hash = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)), b => b.toString(16).padStart(2, '0')).join('');
  assert(hash === file.sha256, `Artifact checksum mismatch: ${file.id}`);
  return { bytes, text: new TextDecoder('utf-8', { fatal: true }).decode(bytes), file };
}
function sourceObject(ref) {
  const [name, pointer] = ref.split('#');
  let obj = name === 'source:model' ? data.model : name === 'source:instances' ? data.instances : undefined;
  assert(obj && pointer?.startsWith('/'), `Unresolved source reference: ${ref}`);
  for (const token of pointer.slice(1).split('/')) {
    const key = token.replace(/~1/g, '/').replace(/~0/g, '~');
    assert(Object.hasOwn(obj, key), `Unresolved source pointer: ${ref}`);
    obj = obj[key];
  }
  return obj;
}
function sourceFile(ref) { return data.manifest.files.find(f => f.id === (ref.startsWith('source:model') ? 'model' : 'instances')); }

function validateData() {
  assert(data.dossier.schemaVersion === 'ontograph.research.case.v1', 'Unsupported case dossier contract');
  assert(data.mappings.schemaVersion === 'ontograph.research.mappings.v1' && data.claims.schemaVersion === 'ontograph.research.claims.v1', 'Unsupported mapping or claim contract');
  const ids = unique(data.dossier.identityMap, 'source');
  const mappingIds = unique(data.mappings.mappings, 'mapping');
  const claimIds = unique(data.claims.claims, 'claim');
  unique(data.gaps.gaps, 'gap');
  assert(ids.size === 31, 'Unexpected frozen source identity count');
  for (const identity of data.dossier.identityMap) {
    assert(identity.canonicalRef === null && identity.candidateRef === null, 'Frozen source dossier has an unexpected acceptance identity');
    const obj = sourceObject(identity.sourceElementRef);
    assert(identity.id === `identity:${obj.id}`, 'Source identity does not match its source pointer');
  }
  for (const view of Object.values(data.viewpoints)) {
    assert(view.schemaVersion === 'ontograph.research.viewpoint.v1' && view.caseRef === data.dossier.caseRef, 'Viewpoint contract mismatch');
    assert(view.mode === 'fixture' && view.datasetRef === null && view.revisionRef === null, 'Unexpected live/revision fixture claim');
    unique([...view.entities, ...view.relations], 'display');
    for (const row of [...view.entities, ...view.relations]) {
      assert(ids.has(row.identityMapRef), 'Unresolved viewpoint identity');
      assert(row.mappingRefs.every(id => mappingIds.has(id)) && row.claimRefs.every(id => claimIds.has(id)), 'Unresolved mapping or claim');
    }
  }
  for (const mapping of data.mappings.mappings) {
    assert(mapping.status !== 'accepted-enrichment' || mapping.decisionRef, 'Unjustified accepted enrichment');
    assert(mapping.sourceRefs.every(ref => sourceObject(ref)), 'Unresolved mapping source');
  }
  if (data.recording) {
    const r = data.recording;
    assert(r.schemaVersion === 'ontograph.research.explorer-recording.v1', 'Unsupported recorded evidence contract');
    for (const key of ['model', 'instances', 'expectations']) {
      const file = data.manifest.files.find(f => f.id === key);
      assert(r.inputDigests[key] === file.sha256, `Recording/source mismatch: ${key}`);
    }
    assert(/^[0-9a-f]{40}$/.test(r.sourceCommit) && /^[0-9a-f]{40}$/.test(r.runtimeIdentity.sourceCommit) && /^[0-9a-f]{64}$/.test(r.runtimeIdentity.binarySha256), 'Incomplete recorded runtime identity');
    assert(Array.isArray(r.cases) && r.cases.length === 5 && packagedEvidence(r.receiptHref), 'Incomplete recorded journey');
    assert(r.cases.every(c => typeof c.owlConsistent === 'boolean' && typeof c.shaclConforms === 'boolean' && Array.isArray(c.activeRoleIds) && packagedEvidence(c.evidenceHref)), 'Incomplete recorded observations');
    unique(r.cases, 'recorded case');
    const actual = data.actualResults, verification = data.actualVerification;
    assert(actual.mode === 'actual' && actual.adopted === false && actual.comprehensiveGateCredit === 0, 'Unexpected recorded authority claim');
    assert(actual.modelSha256 === r.inputDigests.model && actual.instanceSha256 === r.inputDigests.instances && actual.oracleSha256 === r.inputDigests.expectations, 'Actual result/source digest mismatch');
    assert(verification.inputSourceCommit === r.sourceCommit && verification.runtimeCommit === r.runtimeIdentity.sourceCommit && actual.runtimeCommit === r.runtimeIdentity.sourceCommit && actual.binarySha256 === r.runtimeIdentity.binarySha256, 'Actual result/runtime identity mismatch');
    for (const c of r.cases) {
      const a = actual.cases.find(a => a.id === c.id);
      assert(a && a.sourceOutcome === c.sourceOutcome && a.owlConsistent === c.owlConsistent && a.shacl.conforms === c.shaclConforms && a.answers.organisationAppointments.rows.length === c.organisationAppointments && JSON.stringify(a.activeRoleIds) === JSON.stringify(c.activeRoleIds), 'Observation overlay does not match retained actual output');
    }
    const valid = actual.cases.find(c => c.id === 'valid');
    assert(data.files.get('recorded-graph').file.sha256 === valid.graphSha256 && data.actualComposition.graphDigest === `sha256:${valid.graphSha256}`, 'Recorded generated graph digest mismatch');
    assert(data.actualComposition.canonicalStateMutated === false && data.actualComposition.comprehensiveConformance === false, 'Unexpected recorded composition authority');
    if (r.reviewState === 'independently-reviewed') {
      const review = data.actualIndependentReview;
      assert(review && review.schemaVersion === 'ontograph.research.independent-review.v1' && review.independent === true && review.outcome === 'accepted-bounded-organisational-journey' && review.findings.length === 0, 'Missing accepted independent journey receipt');
      assert(review.reviewedHead === r.producerSourceCommit && review.runtimeCommit === r.runtimeIdentity.sourceCommit && review.binarySha256 === r.runtimeIdentity.binarySha256 && review.semanticCasesExactAuthorEquality === true, 'Independent review/producer identity mismatch');
      assert(packagedEvidence(r.reviewReceiptHref), 'Invalid independent review evidence link');
      for (const c of r.cases) {
        const reviewed = review.cases.find(a => a.id === c.id);
        assert(reviewed && reviewed.sourceOutcome === c.sourceOutcome && reviewed.owlConsistent === c.owlConsistent && reviewed.shaclConforms === c.shaclConforms && JSON.stringify(reviewed.activeRoleIds) === JSON.stringify(c.activeRoleIds), 'Independent reviewed outcomes mismatch');
      }
    }
  }
}

async function load() {
  dataVerified = false;
  $('#load-error').hidden = true; $('#application').hidden = true; $('#loading').hidden = false;
  try {
    const response = await fetch('data/manifest.json', { cache: 'no-store' });
    assert(response.ok, `Manifest unavailable (HTTP ${response.status})`);
    const manifest = await response.json();
    assert(manifest.schemaVersion === 'ontograph.research.explorer-assets.v1' && Array.isArray(manifest.files), 'Unsupported explorer asset manifest');
    unique(manifest.files, 'artifact');
    const verified = await Promise.all(manifest.files.map(verifiedFile));
    const files = new Map(verified.map(f => [f.file.id, f]));
    const get = id => { assert(files.has(id), `Required artifact missing: ${id}`); return JSON.parse(files.get(id).text); };
    data = { manifest, files, dossier: get('dossier'), model: get('model'), instances: get('instances'), expectations: get('expectations'), mappings: get('mappings'), claims: get('claims'), gaps: get('gaps'), viewpoints: Object.fromEntries(views.map(v => [v, get(`viewpoint-${v}`)])), recording: manifest.recordingRef ? get(manifest.recordingRef) : null, actualResults: manifest.recordingRef ? get('recorded-results') : null, actualVerification: manifest.recordingRef ? get('recorded-verification') : null, actualComposition: manifest.recordingRef ? get('recorded-composition') : null };
    data.actualIndependentReview = files.has('recorded-independent-review') ? get('recorded-independent-review') : null;
    validateData(); dataVerified = true;
    $('#loading').hidden = true; $('#application').hidden = false;
    renderMode(); state = readState(); render();
  } catch (error) {
    dataVerified = false; $('#loading').hidden = true; $('#application').hidden = true; $('#load-error').hidden = false;
    $('#error-detail').textContent = error instanceof Error ? error.message : 'Unknown artifact verification failure';
    $('#mode-note').replaceChildren(element('strong', 'Data verification failed — no view is available.'));
  }
}
function readState() {
  const params = new URLSearchParams(location.search);
  const requested = params.get('id');
  return {
    view: params.has('view') ? params.get('view') : 'organisational',
    id: requested === null ? 'identity:person:a' : requested,
    query: params.get('q') || '', domain: ['source-model', 'source-instance'].includes(params.get('domain')) ? params.get('domain') : 'all'
  };
}
function navigate(next, replace = false) {
  const changedIdentity = next.id !== undefined && next.id !== state.id;
  state = { ...state, ...next };
  const params = new URLSearchParams({ view: state.view, id: state.id });
  if (state.query) params.set('q', state.query);
  if (state.domain !== 'all') params.set('domain', state.domain);
  history[replace ? 'replaceState' : 'pushState'](null, '', `${location.pathname}?${params}`);
  render();
  if (changedIdentity) $('#inspector').scrollTop = 0;
}
function choose(id) {
  navigate({ id });
  const mobile = matchMedia('(max-width:740px)').matches;
  $('#inspector').focus({ preventScroll: !mobile });
  if (mobile) $('#inspector').scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion:reduce)').matches ? 'instant' : 'smooth', block: 'start' });
}
function renderMode() {
  const note = $('#mode-note');
  const heading = element('strong', data.recording ? 'Recorded observations, with source fixture views.' : 'Source fixture mode — actual outcomes are not shown yet.');
  const p = paragraph(data.recording ? 'Immutable recorded product outcomes are shown separately from the unchanged proposed source claims. There is no live connection and no accepted canonical revision.' : 'These views illustrate the reviewed source case. Generated identities and outcomes are proposed until exact-byte product execution and independent review are recorded. There is no live connection.');
  const ref = paragraph('Bound source dossier: ', 'small'); ref.append(code(data.manifest.sourceCommit), ' · ', link('Source and checksum manifest', 'data/manifest.json'));
  note.replaceChildren(heading, p, ref);
}
function viewRows(view = state.view) { const dto = data.viewpoints[view]; return [...dto.entities, ...dto.relations]; }
function identity(id) { return data.dossier.identityMap.find(row => row.id === id); }
function sourceLabel(obj) { return obj.label || obj.name?.en || obj.id; }
function kindLabel(obj) {
  if (obj.stereotype) return `${obj.type || 'Class'} · ${obj.stereotype}`;
  if (obj.type) return obj.type;
  if (obj.mediations) return 'Relator instance';
  if (obj.bearerRef) return 'Quality instance';
  if (obj.roleRef) return 'Qualified role membership';
  if (obj.participantRef) return 'Qualified participation';
  return 'Individual';
}
function renderVisual() {
  const box = $('#view-visual'); box.replaceChildren();
  if (state.view === 'conceptual') {
    const img = element('img');
    if (!diagramBlobUrl) diagramBlobUrl = URL.createObjectURL(new Blob([data.files.get('diagram-svg').bytes], { type: 'image/svg+xml' }));
    img.src = diagramBlobUrl;
    img.alt = 'Explicit source diagram: Person and Organization Kinds, Researcher Role, Appointment Relator with separate minimum-one mediations, Mass Quality and Seminar Event. Full text alternative follows.';
    const details = element('details'); details.append(element('summary', 'Complete diagram text alternative'), paragraph(data.files.get('diagram-text').text));
    box.append(img, details);
  } else if (state.view === 'organisational') {
    box.append(paragraph('Two appointments, one shared person identity', 'visual-heading'));
    const cards = element('div', undefined, 'record-flow');
    for (const relator of data.instances.relators) {
      const card = element('article', undefined, 'flow-card');
      const inspect = element('button', relator.id); inspect.type = 'button'; inspect.addEventListener('click', () => choose(`identity:${relator.id}`));
      card.append(element('h3', 'Appointment relator'), inspect, paragraph(relator.mediations.flatMap(m => m.participantRefs).join(' ↔ ')), paragraph(`${relator.interval.begin} → ${relator.interval.end}`)); cards.append(card);
    }
    box.append(cards, paragraph('Source-declared links. The role-membership intervals are separately supplied. A recorded link is not a staffing entitlement.', 'visual-note'));
  } else {
    box.append(paragraph('Expected target identity, explicit source lineage', 'visual-heading'), paragraph('Source ID → typed source declaration → proposed generated IRI', 'identity-label'), paragraph('gUFO retains selected classification, mediation and quality meaning. Composition vocabulary retains explicitly qualified role/participation records. Full modal and normative preservation is open.', 'visual-note'));
  }
}
function render() {
  if (!dataVerified) return;
  if (!views.includes(state.view)) {
    for (const button of document.querySelectorAll('[data-view]')) { button.setAttribute('aria-selected', 'false'); button.tabIndex = 0; }
    $('#view-kind').textContent = 'Unsupported viewpoint';
    $('#view-title').textContent = 'Requested viewpoint is unavailable';
    $('#view-description').textContent = `This package does not represent “${state.view}”. Choose a supported conceptual, organisational or OWL/gUFO tab. No live mode is supplied.`;
    $('#view-visual').replaceChildren(); $('#records').replaceChildren(); $('#record-table-wrap').hidden = true; $('#empty').hidden = true; $('#result-count').textContent = 'No substitute view is shown.';
    $('#selection-state').textContent = 'Identity selection is retained in the URL. Choose a supported viewpoint to inspect it.'; $('#inspection').replaceChildren(); $('#view-limitations').replaceChildren(paragraph('Unsupported views do not become a nearby supported view.')); return;
  }
  for (const button of document.querySelectorAll('[data-view]')) {
    const active = button.dataset.view === state.view;
    button.setAttribute('aria-selected', String(active)); button.tabIndex = active ? 0 : -1;
  }
  $('#view-panel').setAttribute('aria-labelledby', `tab-${state.view}`);
  $('#view-kind').textContent = `${state.view === 'owl-gufo' ? 'OWL / gUFO' : state.view} viewpoint · source fixture`;
  $('#view-title').textContent = titles[state.view]; $('#view-description').textContent = descriptions[state.view];
  $('#search').value = state.query; $('#domain').value = state.domain;
  renderVisual();
  const rows = viewRows().filter(row => {
    const item = identity(row.identityMapRef); const source = sourceObject(item.sourceElementRef);
    const haystack = [sourceLabel(source), source.id, ...row.mappingRefs, kindLabel(source)].join(' ').toLocaleLowerCase();
    return haystack.includes(state.query.toLocaleLowerCase()) && (state.domain === 'all' || item.identityDomain === state.domain);
  });
  $('#result-count').textContent = `${rows.length} of ${viewRows().length} records · ${state.view === 'owl-gufo' ? 'proposed projection identities' : 'source-declared identities'}`;
  $('#empty').hidden = rows.length !== 0; $('#record-table-wrap').hidden = rows.length === 0;
  const body = $('#records'); body.replaceChildren();
  for (const row of rows) {
    const item = identity(row.identityMapRef); const obj = sourceObject(item.sourceElementRef);
    const tr = element('tr', undefined, row.identityMapRef === state.id ? 'selected' : '');
    const th = element('th'); th.scope = 'row';
    const button = element('button', undefined, 'identity-button'); button.type = 'button'; button.dataset.identity = item.id;
    button.setAttribute('aria-pressed', String(item.id === state.id)); button.append(element('strong', sourceLabel(obj)), code(obj.id)); button.addEventListener('click', () => choose(item.id)); th.append(button);
    const status = element('td'); status.append(badge(state.view === 'owl-gufo' ? 'Source proposal' : 'Source fixture'));
    tr.append(th, element('td', kindLabel(obj)), status); body.append(tr);
  }
  $('#view-limitations').replaceChildren(bulletList(data.viewpoints[state.view].limitations), paragraph('Class-specific mediation minima and full modal/normative preservation remain explicit gaps.'));
  renderInspector(rows);
}
function factRow(label, content) {
  const row = element('div'); const dd = element('dd'); dd.append(typeof content === 'string' ? document.createTextNode(content) : content);
  row.append(element('dt', label), dd); return row;
}
function renderInspector(visibleRows) {
  const root = $('#inspection'); root.replaceChildren();
  const item = identity(state.id);
  if (!item) {
    $('#selection-state').textContent = 'The requested source identity is not present in this bound dossier. No substitute is selected.';
    root.append(paragraph('Select an available identity from the table. Unknown identifiers do not resolve through a nearby label.')); return;
  }
  const obj = sourceObject(item.sourceElementRef);
  $('#selection-state').textContent = visibleRows.some(r => r.identityMapRef === state.id) ? 'Selection is in the current results.' : 'Selection is retained outside the current view or filter; no substitute is selected.';
  root.append(paragraph(sourceLabel(obj), 'identity-label'), code(obj.id), paragraph(kindLabel(obj), 'small'));
  const facts = element('dl', undefined, 'identity-facts');
  facts.append(factRow('Domain', item.identityDomain), factRow('Candidate', 'Not yet bound in this source dossier'), factRow('Canonical', 'None demonstrated (null)'), factRow('Lifecycle', 'Source candidate; no Review, Decision or Promotion'), factRow('Source', code(item.sourceElementRef)));
  root.append(facts, element('h3', 'Trace this identity across views'));
  const cross = element('div', undefined, 'cross-views');
  for (const view of views) {
    const present = viewRows(view).some(r => r.identityMapRef === item.id);
    if (present) {
      const button = element('button', view === 'owl-gufo' ? 'OWL / gUFO' : view[0].toUpperCase() + view.slice(1)); button.type = 'button'; button.setAttribute('aria-pressed', String(view === state.view));
      button.addEventListener('click', () => navigate({ view })); cross.append(button);
    } else cross.append(element('span', `${view === 'owl-gufo' ? 'OWL / gUFO' : view}: no same-identity row`, 'absent'));
  }
  root.append(cross);
  if (obj.classRef) {
    const parent = element('button', `Inspect declared type ${obj.classRef}`, 'identity-button'); parent.type = 'button'; parent.addEventListener('click', () => { navigate({ id: `identity:${obj.classRef}`, view: 'conceptual' }); $('#inspector').focus({ preventScroll: true }); });
    root.append(paragraph('The declared type has a separate identity; it is not this individual.'), parent);
  }
  root.append(element('h3', 'Source statement'));
  const raw = element('details'); raw.append(element('summary', 'Inspect the complete source record'), element('pre', JSON.stringify(obj, null, 2)));
  root.append(link('Exact source document', sourceFile(item.sourceElementRef).path), raw);
  root.append(element('h3', 'Mapping and intended reduction'));
  const mappings = data.mappings.mappings.filter(m => m.sourceRefs.includes(item.sourceElementRef));
  for (const mapping of mappings) {
    const card = element('article', undefined, 'mapping-card');
    card.append(code(mapping.id), paragraph(`${mapping.status} source commitment · proposed target mapping`), paragraph(mapping.purpose), paragraph(mapping.rationale));
    card.append(element('strong', 'Retained meaning'), bulletList(mapping.retainedMeaning), element('strong', 'Reductions / limits'), bulletList(mapping.reductions));
    if (mapping.targetRefs.length) {
      card.append(element('strong', 'Expected generated identity (not canonical acceptance)'), ...mapping.targetRefs.map(t => paragraph(t, 'small')));
    } else card.append(paragraph('This source record is preserved without a separately identified generated target node.'));
    card.append(paragraph(`Enrichment decision: ${mapping.decisionRef || 'none'}.`)); root.append(card);
  }
  root.append(element('h3', 'Source claim status'));
  for (const claim of data.claims.claims.filter(c => c.id === 'claim:source-case' || c.id === (state.view === 'owl-gufo' ? 'claim:projection' : 'claim:temporal'))) {
    const card = element('article', undefined, 'claim-card'); card.append(badge(claim.status, claim.status === 'open' ? 'open' : ''), paragraph(claim.statement), paragraph(`Review state in original source receipt: ${claim.reviewState}. Runtime observations below do not rewrite this receipt.`, 'scope-text')); root.append(card);
  }
  renderRecording(root, item);
  root.append(element('h3', 'Original source gap register'));
  const selectedGaps = new Set([...item.gapRefs, ...mappings.flatMap(m => m.gapRefs), 'gap:typed-mediations']);
  for (const gap of data.gaps.gaps.filter(g => selectedGaps.has(g.id))) {
    const card = element('article', undefined, 'gap-card'); card.append(code(gap.id), paragraph(gap.statement));
    if (gap.id === 'gap:runtime-unexecuted' && data.recording) card.append(paragraph('Historical gap at source authoring. The separately retained recorded journey above now supplies actual observations for these exact input hashes; the original source record is preserved.', 'small'));
    root.append(card);
  }
}
function renderRecording(root, item) {
  root.append(element('h3', 'Recorded observations'));
  if (!data.recording) {
    root.append(paragraph('Not supplied for these source bytes. Expected outcomes are not observed results. No live or canonical revision is invented.')); return;
  }
  const r = data.recording;
  root.append(badge('Recorded · read-only', 'recorded'), paragraph('The immutable journey binds these exact source input hashes. Observations are specific to its declared runtime and cases; they confer no canonical adoption or normative authority.'), paragraph(`Recorded output review state: ${r.reviewState || 'unreviewed'}. The source DTO receipt above remains unchanged.`), link('Exact recorded producer receipt', r.receiptHref));
  if (r.reviewReceiptHref) root.append(paragraph(r.reviewScope), link('Independent bounded-journey review', r.reviewReceiptHref));
  const facts = element('dl', undefined, 'identity-facts'); facts.append(factRow('Source commit', code(r.sourceCommit)), factRow('Runtime commit', code(r.runtimeIdentity.sourceCommit)), factRow('Binary SHA-256', code(r.runtimeIdentity.binarySha256)), factRow('Canonical revision', 'Not established by this source-candidate journey')); root.append(facts);
  const obj = sourceObject(item.sourceElementRef);
  const actualMappings = data.actualComposition.sourceTargetMappings.filter(m => m.sourceId === obj.id && item.projectionRefs.includes(m.targetIri) && data.files.get('recorded-graph').text.includes(`<${m.targetIri}>`));
  if (actualMappings.length) {
    root.append(element('h3', 'Recorded generated identity'), paragraph('The valid-case product mapping names this source ID and a target IRI present in the exact retained generated graph. This is a generated identity, not an accepted canonical object.'), link('Exact generated graph', 'data/recorded/generated.ttl'), document.createTextNode(' · '), link('Exact product mapping report', 'data/recorded/composition.json'));
    for (const m of actualMappings) {
      const card = element('article', undefined, 'mapping-card'); card.append(code(m.targetIri), paragraph(`Mapping rule: ${m.ruleRef}; product source pointer: ${m.sourcePointer}.`), paragraph(`Product mapping source digest: ${m.sourceDigest}.`, 'small')); root.append(card);
    }
    root.append(paragraph(`Original input-file SHA-256: ${sourceFile(item.sourceElementRef).sha256}. Product mapping source digest may bind serialized instanceSource bytes; the two digest domains are not assumed equal.`, 'small'));
  } else root.append(paragraph('No generated node identity is proved for this selected source record by the retained target-IRI mapping. It remains a source fixture; property-end/generalization commitments may be represented as axioms without their own target node.'));
  root.append(element('h3', 'Case-level journey context'), paragraph('These observations describe the case, not a claim that every result applies to this selected identity.'));
  for (const c of r.cases) {
    const actual = data.actualResults.cases.find(a => a.id === c.id);
    const card = element('article', undefined, 'claim-card');
    card.append(element('strong', c.id), paragraph(`Source validation: ${c.sourceOutcome}. OWL: ${c.owlConsistent ? 'consistent' : 'inconsistent'}. SHACL: ${c.shaclConforms ? 'conformant' : 'nonconformant'}.`), paragraph(`Declared active membership IDs: ${c.activeRoleIds.length ? c.activeRoleIds.join(', ') : 'none'}. Complete recorded appointment links: ${c.organisationAppointments}.`));
    const explain = element('details'); explain.append(element('summary', 'Reasoning, selected query rows and diagnostics'));
    explain.append(paragraph(`Positive mediation entailment: ${actual.entailments.mediation}. Timeless-role entailment: ${actual.entailments['timeless-role']}. Quality-equality entailment: ${actual.entailments['quality-equality']}. False here means non-entailment, not negation.`));
    const matched = Object.entries(actual.answers).flatMap(([name, answer]) => (answer.rows || []).filter(row => Object.values(row).some(term => item.projectionRefs.includes(term.value))).map(row => ({ query: name, row })));
    explain.append(paragraph(matched.length ? 'Exact typed query bindings that mention this selected generated identity:' : 'No retained query row binds this selected identity; no nearby result is substituted.'));
    if (matched.length) explain.append(element('pre', JSON.stringify(matched, null, 2)));
    explain.append(paragraph('Actual SHACL diagnostics (case-level; inspect focusNode to determine relevance):'), element('pre', JSON.stringify(actual.shacl.shaclResults, null, 2)));
    card.append(explain, paragraph(`Staged reload graph isomorphic: ${actual.reloadIsomorphic}. Source-assisted reimport equal: ${actual.sourceAssistedReimportEqual}. Canonical bytes unchanged: ${actual.canonicalUnchanged}.`), link('Exact full case output', c.evidenceHref)); root.append(card);
  }
  root.append(bulletList(r.limitations));
}

for (const tab of document.querySelectorAll('[data-view]')) {
  tab.addEventListener('click', () => dataVerified && navigate({ view: tab.dataset.view }));
  tab.addEventListener('keydown', event => {
    const offset = { ArrowRight: 1, ArrowLeft: -1 }[event.key];
    if (offset === undefined && !['Home', 'End'].includes(event.key)) return;
    event.preventDefault(); if (!dataVerified) return;
    const next = event.key === 'Home' ? 0 : event.key === 'End' ? views.length - 1 : (views.indexOf(state.view) + offset + views.length) % views.length;
    navigate({ view: views[next] }); $(`#tab-${views[next]}`).focus();
  });
}
$('#filters').addEventListener('submit', event => event.preventDefault());
$('#search').addEventListener('input', event => navigate({ query: event.target.value }, true));
$('#domain').addEventListener('change', event => navigate({ domain: event.target.value }));
$('#clear-filter').addEventListener('click', () => { navigate({ query: '', domain: 'all' }); $('#search').focus(); });
$('#retry').addEventListener('click', load);
addEventListener('popstate', () => { if (dataVerified) { state = readState(); render(); } });
load();
