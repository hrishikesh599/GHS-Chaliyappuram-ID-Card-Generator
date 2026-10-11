/* GHS Chaliyappuram - ID Card Generator (frontend) */
(() => {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];

  const form = $('#idForm');
  const genBtn = $('#genBtn');
  const photoInput = $('#photo');
  const drop = $('#drop');
  const thumbBox = $('.thumb');
  const thumbImg = $('#thumb');
  const dialog = $('#pdfDialog');
  const frame = $('#pdfFrame');
  const toastEl = $('#toast');

  let photoURL = null;
  let pdfURL = null;
  const MAX_PHOTO = 8 * 1024 * 1024;
  const TYPES = ['image/jpeg', 'image/png', 'image/webp'];

  const val = (id) => ($('#' + id).value || '').replace(/\s+/g, ' ').trim();

  /* ---------- toast ---------- */
  let toastTimer;
  function toast(msg, bad = false) {
    toastEl.textContent = msg;
    toastEl.classList.toggle('bad', bad);
    toastEl.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toastEl.classList.remove('show'), 3200);
  }

  /* ---------- live preview (SVG, same numbers + fonts as the PDF) ---------- */
  const D = window.CARD_DESIGN;
  const SVGNS = 'http://www.w3.org/2000/svg';
  const g = (id) => document.getElementById(id);
  const setSize = (el, pt) => { el.style.fontSize = (pt * D.pt) + 'px'; };
  const len = (el) => el.getComputedTextLength();

  // Put text in `el` at `pt`; return its width in mm.
  function measure(el, text, pt) { el.textContent = text; setSize(el, pt); return len(el); }

  // Largest size (<= base) at which text fits in maxMm, not below minPt.
  function fitPt(el, text, base, maxMm, minPt) {
    let pt = base;
    measure(el, text, pt);
    while (pt > minPt && len(el) > maxMm) { pt -= 0.1; setSize(el, pt); }
    return pt;
  }

  // Fit on one line; trim with "..." as a last resort.
  function fitLine(el, text, base, maxMm, minPt) {
    fitPt(el, text, base, maxMm, minPt);
    if (len(el) > maxMm) {
      let t = text;
      while (t && measure(el, t + '...', parseFloat(el.style.fontSize) / D.pt) > maxMm) t = t.slice(0, -1);
      el.textContent = t.trimEnd() + '...';
    }
  }

  function balancedTwo(el, text, pt) {
    const words = text.split(' ');
    if (words.length < 2) return null;
    let best = null, bestW = Infinity;
    for (let i = 1; i < words.length; i++) {
      const a = words.slice(0, i).join(' '), b = words.slice(i).join(' ');
      const w = Math.max(measure(el, a, pt), measure(el, b, pt));
      if (w < bestW) { best = [a, b]; bestW = w; }
    }
    return best;
  }

  function wrapLines(el, text, pt, maxMm, maxLines) {
    const lines = [];
    let cur = '';
    text.split(' ').forEach((wd) => {
      const trial = (cur + ' ' + wd).trim();
      if (!cur || measure(el, trial, pt) <= maxMm) cur = trial;
      else { lines.push(cur); cur = wd; }
    });
    if (cur) lines.push(cur);
    if (lines.length > maxLines) {
      let rest = lines.slice(maxLines - 1).join(' ');
      lines.length = maxLines - 1;
      while (rest && measure(el, rest + '...', pt) > maxMm) rest = rest.slice(0, -1);
      lines.push(rest.trimEnd() + '...');
    }
    return lines;
  }

  const dim = (el, empty) => el.setAttribute('opacity', empty ? '.35' : '1');

  function renderName(text, empty) {
    const n1 = g('f_name1'), n2 = g('f_name2'), N = D.name;
    n2.textContent = '';
    n1.setAttribute('y', N.y);
    const oneLine = fitPt(n1, text, N.base, N.max, 1);
    if (oneLine >= N.oneMin || !text.includes(' ')) {
      fitLine(n1, text, N.base, N.max, N.minPt);
    } else {
      const [a, b] = balancedTwo(n1, text, N.twoPt);
      const pt = Math.min(N.twoPt, fitPt(n1, a, N.twoPt, N.max, N.minPt), fitPt(n1, b, N.twoPt, N.max, N.minPt));
      n1.setAttribute('y', N.twoY[0]);
      measure(n1, a, pt);
      measure(n2, b, pt);
    }
    dim(n1, empty); dim(n2, empty);
  }

  function renderCapsule(cls, div) {
    const t = g('f_cap_text'), r = g('f_cap_rect');
    t.style.whiteSpace = 'pre';
    t.textContent = `CLASS ${cls || '–'}  ·  DIV ${div || '–'}`;
    const w = len(t) + 7;
    r.setAttribute('width', w);
    r.setAttribute('x', D.cx - w / 2);
  }

  function renderRow(i, id, text, wrapAllowed) {
    const V = D.value, a = g(id + '1'), b = g(id + '2'), y = V.rows[i];
    b.textContent = '';
    a.setAttribute('y', y);
    let hair = V.hair;
    const oneLine = fitPt(a, text, V.base, V.max, 1);
    const pair = wrapAllowed && oneLine < V.guardMin && text.includes(' ') ? balancedTwo(a, text, V.guardMin) : null;
    if (pair) {
      const pt = Math.min(V.guardMin, ...pair.map((t) => fitPt(a, t, V.guardMin, V.max, 4.2)));
      a.setAttribute('y', y + V.guardDy[0]);
      b.setAttribute('y', y + V.guardDy[1]);
      measure(a, pair[0], pt);
      measure(b, pair[1], pt);
      hair = V.guardHair;
    } else {
      fitLine(a, text, V.base, V.max, V.minPt);
    }
    const hl = g('f_hair' + i);
    if (hl) { hl.setAttribute('y1', y + hair); hl.setAttribute('y2', y + hair); }
  }

  function renderAddress(text, empty) {
    const el = g('b_addr'), A = D.addr;
    const pt = A.pt;
    const lines = wrapLines(el, text, pt, A.max, A.lines);
    el.textContent = '';
    lines.forEach((ln, i) => {
      const ts = document.createElementNS(SVGNS, 'tspan');
      ts.setAttribute('x', D.cx);
      ts.setAttribute('y', A.y + i * A.step);
      ts.textContent = ln;
      el.appendChild(ts);
    });
    dim(el, empty);
  }

  function refresh() {
    const mobile = val('mobile').replace(/\D/g, '');
    const cls = val('student_class'), div = val('division');
    const name = val('name').toUpperCase();
    const adm = val('admission_no').toUpperCase();
    const guardian = val('guardian').toUpperCase();
    const loc = val('locality');
    const addr = val('address');

    renderName(name || 'STUDENT NAME', !name);
    renderCapsule(cls, div);
    renderRow(0, 'f_adm', adm || '—', false);
    renderRow(1, 'f_guardian', guardian || '—', true);
    renderRow(2, 'f_mobile', mobile ? `${mobile.slice(0, 5)} ${mobile.slice(5)}`.trim() : '—', false);
    g('f_year').textContent = `ACADEMIC YEAR ${val('academic_year')}`;

    const locEl = g('b_loc');
    fitLine(locEl, loc || '—', D.loc.base, D.loc.max, D.loc.minPt);
    renderAddress(addr || 'Address will appear here', !addr);
  }

  // Photo: same crop as the server (centred, biased towards the top)
  function showPreviewPhoto(url) {
    const A = D.arch, im = new Image();
    im.onload = () => {
      const s = Math.max(A.w / im.naturalWidth, A.h / im.naturalHeight);
      const dw = im.naturalWidth * s, dh = im.naturalHeight * s;
      const ph = g('f_photo');
      ph.setAttribute('width', dw);
      ph.setAttribute('height', dh);
      ph.setAttribute('x', A.x + (A.w - dw) / 2);
      ph.setAttribute('y', A.top - (dh - A.h) * A.bias);
      ph.setAttribute('href', url);
      ph.setAttribute('visibility', 'visible');
      g('f_silhouette').setAttribute('visibility', 'hidden');
    };
    im.src = url;
  }
  function clearPreviewPhoto() {
    g('f_photo').setAttribute('visibility', 'hidden');
    g('f_photo').removeAttribute('href');
    g('f_silhouette').setAttribute('visibility', 'visible');
  }

  // Logo + signature appear as soon as the files exist in static/branding
  function loadBranding() {
    const t = Date.now();
    [['logo', ['f_logo', 'b_logo'], ['f_mono', 'b_mono']], ['signature', ['b_sig'], []]].forEach(([asset, imgs, monos]) => {
      const probe = new Image();
      probe.onload = () => {
        imgs.forEach((id) => { g(id).setAttribute('href', probe.src); g(id).setAttribute('visibility', 'visible'); });
        monos.forEach((id) => g(id).setAttribute('visibility', 'hidden'));
      };
      probe.src = `/branding/${asset}?t=${t}`;
    });
  }

  $$('input, select, textarea', form).forEach((el) => {
    el.addEventListener('input', () => { clearError(el.name); refresh(); });
    el.addEventListener('change', () => { clearError(el.name); refresh(); });
  });

  // Mobile: digits only
  $('#mobile').addEventListener('input', (e) => {
    e.target.value = e.target.value.replace(/\D/g, '').slice(0, 10);
  });

  /* ---------- errors ---------- */
  function clearError(name) {
    const msg = $(`[data-err="${name}"]`);
    if (msg) { msg.textContent = ''; msg.closest('.field')?.classList.remove('invalid'); }
  }
  function showErrors(errors) {
    let first = null;
    Object.entries(errors).forEach(([name, text]) => {
      const msg = $(`[data-err="${name}"]`);
      if (!msg) return;
      msg.textContent = text;
      const field = msg.closest('.field');
      field?.classList.add('invalid');
      first = first || field;
    });
    first?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  /* ---------- photo ---------- */
  function setPhoto(file) {
    clearError('photo');
    if (!file) return;
    if (!TYPES.includes(file.type)) { showErrors({ photo: 'Photo must be a JPG, PNG or WEBP image.' }); photoInput.value = ''; return; }
    if (file.size > MAX_PHOTO) { showErrors({ photo: 'Photo is too large (max 8 MB).' }); photoInput.value = ''; return; }
    if (photoURL) URL.revokeObjectURL(photoURL);
    photoURL = URL.createObjectURL(file);
    thumbImg.src = photoURL;
    thumbBox.classList.add('has');
    showPreviewPhoto(photoURL);
    $('#dropTitle').textContent = file.name.length > 34 ? file.name.slice(0, 31) + '…' : file.name;
  }

  photoInput.addEventListener('change', () => setPhoto(photoInput.files[0]));
  ['dragenter', 'dragover'].forEach((ev) =>
    drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.add('over'); }));
  ['dragleave', 'drop'].forEach((ev) =>
    drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.remove('over'); }));
  drop.addEventListener('drop', (e) => {
    const file = e.dataTransfer.files[0];
    if (!file) return;
    const dt = new DataTransfer();
    dt.items.add(file);
    photoInput.files = dt.files;
    setPhoto(file);
  });

  /* ---------- reset ---------- */
  $('#resetBtn').addEventListener('click', () => {
    const year = $('#academic_year').value;
    form.reset();
    $('#academic_year').value = year;
    if (photoURL) URL.revokeObjectURL(photoURL);
    photoURL = null;
    thumbImg.removeAttribute('src');
    clearPreviewPhoto();
    thumbBox.classList.remove('has');
    $('#dropTitle').textContent = 'Choose or drop a photo';
    $$('.err').forEach((e) => (e.textContent = ''));
    $$('.invalid').forEach((e) => e.classList.remove('invalid'));
    refresh();
  });

  /* ---------- generate ---------- */
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    $$('.err').forEach((x) => (x.textContent = ''));
    $$('.invalid').forEach((x) => x.classList.remove('invalid'));

    genBtn.disabled = true;
    const label = genBtn.textContent;
    genBtn.textContent = 'Generating…';

    try {
      const res = await fetch('/api/generate', { method: 'POST', body: new FormData(form) });
      if (!res.ok) {
        let errors = { photo: 'Something went wrong. Please try again.' };
        try { errors = (await res.json()).errors || errors; } catch (_) { /* ignore */ }
        showErrors(errors);
        toast('Please fix the highlighted fields.', true);
        return;
      }
      const blob = await res.blob();
      if (pdfURL) URL.revokeObjectURL(pdfURL);
      pdfURL = URL.createObjectURL(blob);

      const adm = val('admission_no').replace(/[^A-Za-z0-9_-]+/g, '_');
      const nm = val('name').toUpperCase().replace(/[^A-Z0-9]+/g, '_').replace(/^_|_$/g, '');
      $('#dlBtn').href = pdfURL;
      $('#dlBtn').download = `ID_${adm}_${nm}.pdf`;
      $('#openBtn').href = pdfURL;
      frame.src = pdfURL + '#toolbar=0&navpanes=0';
      dialog.showModal();
    } catch (err) {
      toast('Could not reach the local server. Is it still running?', true);
    } finally {
      genBtn.disabled = false;
      genBtn.textContent = label;
    }
  });

  $('#closeDlg').addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', (e) => { if (e.target === dialog) dialog.close(); });
  dialog.addEventListener('close', () => { frame.removeAttribute('src'); });

  loadBranding();
  const fontsReady = ['700 10px "Playfair GHS"', '500 10px "Montserrat GHS"', '600 10px "Montserrat GHS"', '700 10px "Montserrat GHS"']
    .map((f) => document.fonts.load(f));
  Promise.all(fontsReady).then(refresh, refresh);
  refresh();
})();
