"use strict";
const $ = id => document.getElementById(id);

// On Render the page and API share one origin, so API is "". Only when the HTML is
// opened from a file or a dev server do we talk to the local FastAPI directly.
const DEV_PORTS = ["5500", "5501", "3000", "5173"];
const API = (location.protocol === "file:" || DEV_PORTS.includes(location.port)) ? "http://127.0.0.1:8000" : "";

const MB = 1024 * 1024;
const MAX_FILE_BYTES = 25 * MB, MAX_TOTAL_BYTES = 100 * MB, MAX_FILES = 50;   // match the server limits

const picked = new Map();            // name(lower) -> {name, custom}
let files = [], lastResults = [], act = -1, items = [], timer, searchSeq = 0, GROUPS = null;

function el(tag, cls, text, attrs = {}) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text != null) e.textContent = text;
  Object.entries(attrs).forEach(([k, v]) => e.setAttribute(k, v));
  return e;
}
function status(msg, isErr = false) {
  $("status").textContent = msg;
  $("status").className = isErr ? "err" : "mute";
}
const sleep = ms => new Promise(r => setTimeout(r, ms));

// ---------- network ----------
// One place for every request: timeout, one retry for a sleeping server, and real error messages.
async function call(path, opts = {}, { retries = 1, timeout = 120000 } = {}) {
  let lastErr;
  for (let i = 0; i <= retries; i++) {
    const ctrl = new AbortController();
    const t = setTimeout(() => ctrl.abort(), timeout);
    try {
      const res = await fetch(API + path, { ...opts, signal: ctrl.signal });
      if (res.ok) return res;
      if ([502, 503, 504].includes(res.status)) {
        lastErr = new Error("The server is starting up. Please wait a moment and try again.");
      } else {
        let msg = `Server error (${res.status})`;
        try { const d = (await res.json()).detail; if (typeof d === "string") msg = d; } catch {}
        const e = new Error(msg); e.http = true; throw e;
      }
    } catch (e) {
      if (e.http) throw e;
      lastErr = e;
    } finally { clearTimeout(t); }
    if (i < retries) await sleep(4000);
  }
  throw lastErr;
}
function explain(e) {
  if (e.name === "AbortError") return "Timed out. The server may be waking up, try again in a minute.";
  if (e instanceof TypeError) return "Network error, or your phone could not read the file. Check your connection and re-select the files.";
  return e.message || "Request failed";
}
function saveBlob(blob, name) {
  const url = URL.createObjectURL(blob);
  const a = el("a", "", "", { href: url, download: name });
  document.body.append(a); a.click(); a.remove();     // must be in the DOM for iOS Safari
  setTimeout(() => URL.revokeObjectURL(url), 15000);
}

// Free Render instances sleep. Wake the server first and say so.
async function wake() {
  const note = setTimeout(() => status("Waking up the server (free hosting can take up to a minute)..."), 1500);
  try { await call("/health", {}, { retries: 3, timeout: 30000 }); status(""); return true; }
  catch (e) { status(explain(e), true); return false; }
  finally { clearTimeout(note); }
}

// ---------- skills ----------
function addSkill(name, custom = false) {
  name = name.trim();
  if (!name || picked.has(name.toLowerCase())) return;
  picked.set(name.toLowerCase(), { name, custom });
  renderPicked();
}
function renderPicked() {
  const box = $("picked"); box.replaceChildren();
  picked.forEach((s, k) => {
    const c = el("button", "chip" + (s.custom ? " custom" : ""), s.name + "  ×",
      { type: "button", title: s.custom ? "Custom skill (searched as typed)" : "Remove" });
    c.onclick = () => { picked.delete(k); renderPicked(); };
    box.append(c);
  });
}
function closeSugg() { $("sugg").hidden = true; act = -1; }

function addTyped() {                       // typed text -> custom skills
  const v = $("q").value;
  if (!v.trim()) return false;
  v.split(",").forEach(s => addSkill(s, true));
  $("q").value = ""; closeSugg();
  return true;
}

async function search(q) {
  const seq = ++searchSeq;
  if (!q.trim()) return closeSugg();
  let r;
  try { r = await (await call("/api/suggest?q=" + encodeURIComponent(q), {}, { retries: 0, timeout: 15000 })).json(); }
  catch { return; }
  if (seq !== searchSeq) return;             // a newer search already started
  items = [
    ...r.groups.map(g => ({ type: "group", name: g.name, count: g.count })),
    ...r.skills.map(s => ({ type: "skill", name: s.skill, group: s.group })),
  ];
  const box = $("sugg"); box.replaceChildren(); act = -1;
  items.forEach((it, i) => {
    const d = el("div");
    if (it.type === "group") d.append(el("span", "grp", `Add all ${it.count} ${it.name} skills`));
    else d.append(el("span", "", it.name), el("small", "", it.group));
    d.addEventListener("pointerdown", e => { e.preventDefault(); choose(i); });   // works for touch too
    box.append(d);
  });
  if (!items.length) box.append(el("div", "", `No match. Press Enter or tap Add to use "${q.trim()}" as a custom skill`));
  box.hidden = false;
}
async function loadGroups() {
  if (GROUPS) return GROUPS;
  GROUPS = await (await call("/api/groups", {}, { retries: 2, timeout: 30000 })).json();
  return GROUPS;
}
async function addGroup(name) {
  try { ((await loadGroups()).groups[name] || []).forEach(s => addSkill(s)); }
  catch (e) { status(explain(e), true); }
}
function choose(i) {
  const it = items[i]; if (!it) return;
  it.type === "group" ? addGroup(it.name) : addSkill(it.name);
  $("q").value = ""; closeSugg();
}

$("q").addEventListener("input", e => { clearTimeout(timer); timer = setTimeout(() => search(e.target.value), 150); });
$("q").addEventListener("keydown", e => {
  const rows = [...$("sugg").children];
  if (e.key === "ArrowDown" && items.length) act = (act + 1) % items.length;
  else if (e.key === "ArrowUp" && items.length) act = (act - 1 + items.length) % items.length;
  else if (e.key === "Enter") {
    e.preventDefault();
    if (act >= 0) choose(act); else addTyped();
    return;
  } else if (e.key === "Escape") return closeSugg();
  else return;
  e.preventDefault(); rows.forEach((r, i) => r.classList.toggle("act", i === act));
});
$("q").addEventListener("blur", () => setTimeout(closeSugg, 200));

// Phones have no easy Enter key: give them an Add button next to the box.
const addBtn = el("button", "btn ghost", "Add", { type: "button" });
addBtn.onclick = addTyped;
$("q").after(addBtn);

async function initGroups() {            // browse by field
  if (!(await wake())) return;
  let data;
  try { data = await loadGroups(); } catch (e) { return status(explain(e), true); }
  $("browseHead").textContent = `Or browse ${data.total} skills by field`;
  Object.entries(data.groups).forEach(([g, list]) => {
    const b = el("button", "gbtn", `${g} (${list.length})`, { type: "button" });
    b.onclick = () => {
      document.querySelectorAll(".gbtn").forEach(x => x.classList.remove("on")); b.classList.add("on");
      const box = $("groupSkills"); box.replaceChildren();
      const all = el("button", "btn ghost", "Add all", { type: "button" }); all.onclick = () => list.forEach(s => addSkill(s));
      box.append(all);
      list.forEach(s => { const c = el("button", "chip", "+ " + s, { type: "button" }); c.onclick = () => addSkill(s); box.append(c); });
    };
    $("groups").append(b);
  });
}
initGroups();

// ---------- files ----------
// Copy the picked files into memory straight away. On phones a file from Drive/iCloud can
// become unreadable after the first upload, which broke the second request (shortlist).
async function setFiles(list) {
  list = [...list];
  $("results").replaceChildren(); lastResults = [];
  if (!list.length) { files = []; $("fileInfo").textContent = ""; return; }
  if (list.length > MAX_FILES) return fileError(`Too many files (max ${MAX_FILES}). Put them in a ZIP instead.`);
  const big = list.find(f => f.size > MAX_FILE_BYTES);
  if (big) return fileError(`${big.name} is larger than ${MAX_FILE_BYTES / MB} MB.`);
  if (list.reduce((n, f) => n + f.size, 0) > MAX_TOTAL_BYTES) return fileError(`Files are larger than ${MAX_TOTAL_BYTES / MB} MB in total.`);
  $("fileInfo").textContent = "Reading files...";
  try {
    files = await Promise.all(list.map(async f => new File([await f.arrayBuffer()], f.name, { type: f.type })));
  } catch {
    return fileError("Could not read the selected files. Save them on the phone (Downloads) and pick them again.");
  }
  $("fileInfo").textContent = files.map(f => f.name).join(", ");
  status("");
}
function fileError(msg) { files = []; $("fileInfo").textContent = ""; status(msg, true); }

$("file").onchange = async e => { await setFiles(e.target.files); e.target.value = ""; };
["dragover", "dragenter"].forEach(t => $("drop").addEventListener(t, e => { e.preventDefault(); $("drop").classList.add("over"); }));
["dragleave", "drop"].forEach(t => $("drop").addEventListener(t, () => $("drop").classList.remove("over")));
$("drop").addEventListener("drop", e => { e.preventDefault(); setFiles(e.dataTransfer.files); });

// ---------- threshold ----------
const threshold = () => parseFloat($("thrR").value);
$("thrR").addEventListener("input", () => { $("thrV").textContent = $("thrR").value; if (lastResults.length) render(lastResults); });

// ---------- analyze ----------
function skillsField() { return [...picked.values()].map(s => s.name).join(","); }

$("go").onclick = async () => {
  addTyped();                                  // don't lose a skill that was typed but not added
  if (!files.length) return status("Upload a resume first.", true);
  if (!picked.size) return status("Add at least one skill.", true);
  $("go").disabled = true; status("Checking...");
  const slow = setTimeout(() => status("Still working. The server may be waking up..."), 4000);
  const fd = new FormData();
  files.forEach(f => fd.append("files", f));
  fd.append("skills", skillsField());
  try {
    const res = await call("/api/analyze", { method: "POST", body: fd });
    lastResults = (await res.json()).results; render(lastResults); status("");
  } catch (e) { console.error("Analyze failed:", e); status(explain(e), true); }
  clearTimeout(slow);
  $("go").disabled = false;
};

async function downloadShortlist() {
  const t = threshold();
  const names = lastResults.filter(r => !r.error && r.match_percent >= t).map(r => r.filename);
  if (!names.length) return status("No resume reached the minimum match.", true);
  const fd = new FormData();
  files.forEach(f => fd.append("files", f));
  fd.append("names", JSON.stringify(names));
  status("Preparing zip...");
  try {
    saveBlob(await (await call("/api/shortlist", { method: "POST", body: fd })).blob(), "shortlisted_resumes.zip");
    status("");
  } catch (e) { status(explain(e), true); }
}

function chips(list, cls) {
  const w = el("div", "chips");
  list.forEach(m => w.append(el("span", `chip static ${cls}`, m.skill + (m.match === "fuzzy" ? " (close spelling)" : ""))));
  return w;
}
function render(results) {
  const box = $("results"); box.replaceChildren();
  const t = threshold(), pass = results.filter(r => !r.error && r.match_percent >= t).length;
  const sum = el("div", "card row"); sum.append(el("b", "", `${pass} of ${results.length} resumes reach ${t}% or more`));
  const dl = el("button", "btn", "Download shortlisted resumes (.zip)", { type: "button" });
  dl.disabled = !pass; dl.onclick = downloadShortlist;
  sum.append(dl); box.append(sum);
  results.forEach(r => {
    const ok = !r.error && r.match_percent >= t;
    const c = el("div", "card");
    const head = el("div", "row"); head.append(el("b", "", r.filename));
    if (ok) head.append(el("span", "chip ok static", "Shortlisted"));
    if (r.error) { c.append(head, el("p", "err", r.error)); box.append(c); return; }
    head.append(el("span", "score", r.match_percent + "%"));
    const bar = el("div", "bar"); const i = el("i"); i.style.width = r.match_percent + "%"; bar.append(i);
    c.append(head, bar, el("p", "mute", `${r.verdict}. ${r.matched.length} of ${r.total} skills found.`));
    c.append(el("b", "", "Matched"), chips(r.matched, "ok"), el("b", "", "Missing"), chips(r.missing, "bad"));
    const ul = el("ul"); r.suggestions.forEach(s => ul.append(el("li", "", s)));
    c.append(el("b", "", "Suggestions"), ul); box.append(c);
  });
  const z = el("button", "btn ghost", "Download analysis report (.zip)", { type: "button" });
  z.onclick = async () => {
    try {
      const res = await call("/api/report-zip", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ results: lastResults }),
      });
      saveBlob(await res.blob(), "resumelens_report.zip");
    } catch (e) { status(explain(e), true); }
  };
  box.append(z);
}
