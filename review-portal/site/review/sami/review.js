'use strict';
(async () => {
  const $ = id => document.getElementById(id);
  const labels = { ACCEPT_CURRENT: 'Ei korjattavaa', ACCEPT_WITH_EDIT: 'Korjattava', NEEDS_FURTHER_CLINICAL_OR_TERMINOLOGY_REVIEW: 'Vaatii vielä kliinistä / terminologista lisäarviota' };
  const node = (tag, text, parent, cls) => { const n = document.createElement(tag); if (text) n.textContent = text; if (cls) n.className = cls; parent?.append(n); return n; };
  let busy = false, submitted = false, storageWarning = false;
  try {
    const [dataResponse, metaResponse] = await Promise.all([fetch('review-data.json'), fetch('review-meta.json')]);
    if (!dataResponse.ok || !metaResponse.ok) throw new Error('data');
    const bytes = await dataResponse.arrayBuffer();
    const meta = await metaResponse.json();
    const hash = [...new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))].map(x => x.toString(16).padStart(2, '0')).join('');
    if (hash !== meta.review_data_sha256) throw new Error('hash');
    const units = JSON.parse(new TextDecoder().decode(bytes));
    if (units.length !== 6) throw new Error('units');
    for (const [key, label] of [['review_run_id', 'Arviointikierros'], ['review_candidate_commit', 'Arvioitava versio'], ['review_data_sha256', 'review_data_sha256']]) {
      node('dt', label, $('metadata')); node('dd', meta[key], $('metadata'));
    }
    const draftKey = `spict-sami:${meta.review_candidate_commit}:${hash}`;
    let draft = {};
    try { draft = JSON.parse(localStorage.getItem(draftKey) || '{}') || {}; } catch { storageWarning = true; }
    let endpoint = '';
    try { const url = new URL(window.REVIEW_RUNTIME_CONFIG.workerSubmitUrl); if (url.protocol === 'https:' && !url.username && !url.password && !url.search && !url.hash && url.pathname === '/submit') endpoint = url.href; } catch { /* Blank endpoint is intentionally disabled. */ }
    $('endpoint').textContent = endpoint ? 'Arvio lähetetään suojatun yhteyden kautta.' : 'Submission endpoint not configured';
    const controls = units.map(unit => {
      const card = node('section', '', $('cards'), 'card');
      node('h2', unit.unit_id, card);
      const texts = node('div', '', card, 'texts');
      for (const [caption, text, cls] of [['ALKUPERÄINEN ENGLANTI', unit.source_text_en, 'source'], ['NYKYINEN SUOMENNOS', unit.current_candidate_fi, 'candidate']]) {
        const box = node('div', '', texts, cls); node('p', caption, box, 'caption'); node('p', text, box, 'text');
      }
      const details = node('details', '', card); node('summary', 'Miksi tämä kohta on tarkistettavana?', details);
      node('p', unit.neutral_review_question, details);
      if (unit.existing_human_decision_note) node('p', unit.existing_human_decision_note, details);
      const fieldset = node('fieldset', '', card); node('legend', 'Arviosi', fieldset);
      const saved = draft.decisions?.find?.(d => d.unit_id === unit.unit_id) || {};
      const radios = Object.entries(labels).map(([value, label]) => {
        const wrap = node('label', '', fieldset, 'choice'); const input = node('input', '', wrap);
        input.type = 'radio'; input.name = unit.unit_id; input.value = value; input.required = true;
        input.checked = saved.decision === value; node('span', label, wrap); return input;
      });
      const editBox = node('div', '', card); const editLabel = node('label', 'Korjattu suomenkielinen teksti', editBox);
      const edit = $('correction-template').content.firstElementChild.cloneNode(true); editBox.append(edit); edit.id = `${unit.unit_id}-edit`; editLabel.htmlFor = edit.id; edit.maxLength = 2000;
      edit.value = typeof saved.recommended_finnish === 'string' ? saved.recommended_finnish : unit.current_candidate_fi;
      const rationaleLabel = node('label', 'Perustelu (valinnainen)', card);
      const rationale = $('rationale-template').content.firstElementChild.cloneNode(true); card.append(rationale); rationale.id = `${unit.unit_id}-rationale`; rationaleLabel.htmlFor = rationale.id;
      rationale.maxLength = 1200; rationale.value = typeof saved.rationale === 'string' ? saved.rationale : '';
      return { unit, radios, editBox, edit, rationale, rationaleLabel };
    });
    const decisions = () => controls.map(c => ({ unit_id: c.unit.unit_id, decision: c.radios.find(r => r.checked)?.value || '', recommended_finnish: c.radios[1].checked ? c.edit.value : c.unit.current_candidate_fi, rationale: c.rationale.value }));
    function update(save = true) {
      let completed = 0;
      for (const c of controls) {
        c.editBox.hidden = !c.radios[1].checked; c.edit.required = c.radios[1].checked;
        c.rationale.required = c.radios[2].checked;
        c.rationaleLabel.textContent = c.rationale.required ? 'Perustelu / mitä pitää selvittää' : 'Perustelu (valinnainen)';
        if (c.radios.some(r => r.checked) && (!c.edit.required || (c.edit.value.trim() && c.edit.value.length <= 2000)) && c.rationale.value.length <= 1200 && (!c.rationale.required || c.rationale.value.trim())) completed++;
      }
      $('progress').textContent = `${completed} / 6 tarkistettu`;
      $('submit').disabled = busy || submitted || !endpoint || completed !== 6 || !$('reviewer-name').value.trim() || !$('reviewer-role').value.trim() || $('access-code').value.length < 24 || $('access-code').value.length > 256 || !$('confirmation').checked || !$('review-form').checkValidity();
      if (save && !submitted) {
        try { localStorage.setItem(draftKey, JSON.stringify({ decisions: decisions() })); } catch { storageWarning = true; }
      }
      if (storageWarning && !submitted) $('status').textContent = 'Selaimen luonnostallennus ei ole käytettävissä. Säilytä sivu avoinna.';
    }
    $('review-form').addEventListener('input', () => update());
    $('clear').addEventListener('click', () => {
      try { localStorage.removeItem(draftKey); } catch { storageWarning = true; }
      $('review-form').reset();
      for (const c of controls) { c.radios.forEach(r => { r.checked = false; }); c.edit.value = c.unit.current_candidate_fi; c.rationale.value = ''; }
      $('access-code').value = ''; update(false);
    });
    $('review-form').addEventListener('submit', async event => {
      event.preventDefault(); update(false); if ($('submit').disabled) return;
      busy = true; update(false); $('status').textContent = 'Lähetetään…';
      const payload = { ...meta, reviewer: { name: $('reviewer-name').value, role: $('reviewer-role').value }, decisions: decisions(), confirmation: $('confirmation').checked, access_code: $('access-code').value };
      // Freeze form controls until the request resolves; there is no automatic retry.
      const formControls = [...$('review-form').querySelectorAll('input, textarea, button')];
      formControls.forEach(control => { control.disabled = true; });
      try {
        const response = await fetch(endpoint, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload), credentials: 'omit', referrerPolicy: 'no-referrer', signal: AbortSignal.timeout(30000) });
        const result = await response.json();
        if (!response.ok || result.ok !== true) throw new Error(result.error || 'Tallennusta ei voitu vahvistaa.');
        if (!/^[a-f0-9]{64}$/.test(result.submission_id)) throw new Error('Tallennuksen vastausta ei voitu vahvistaa.');
        submitted = true;
        try { localStorage.removeItem(draftKey); storageWarning = false; } catch { storageWarning = true; $('status').textContent = 'Arvio tallennettiin, mutta selaimen luonnos on tyhjennettävä selaimen asetuksista.'; }
        $('review-form').hidden = true; $('success').hidden = false;
        $('submission-id').textContent = `Lähetyksen tunniste: ${result.submission_id}`;
        if (!storageWarning) $('status').textContent = 'Arvio tallennettu. Kiitos arviostasi.';
      } catch (error) {
        $('status').textContent = `${error.message} Luonnos säilyy. Jos yhteys katkesi, pyydä ylläpitäjää tarkistamaan tallennus ennen uutta lähetystä.`;
      } finally {
        $('access-code').value = ''; delete payload.access_code; busy = false;
        formControls.forEach(control => { control.disabled = false; }); update(false); $('status').focus();
      }
    });
    update(false);
  } catch {
    $('status').textContent = 'Arviointiaineistoa ei voitu ladata tai tarkistaa. Lähettäminen on estetty.';
    $('submit').disabled = true;
  }
})();
