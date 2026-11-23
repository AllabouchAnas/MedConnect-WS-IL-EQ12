"use strict";
/* MedConnect – Module Agenda (SPA sans build : HTML + JS natif, API REST + JWT) */
const $app = document.getElementById("app");
const SKEY = "mc_session";
const state = { date: null, flash: null };
let routeId = 0, timer = null;

const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const $ = (id) => document.getElementById(id);
const pad = (n) => String(n).padStart(2, "0");
const today = () => { const d = new Date(); return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`; };
const fmtDate = (iso) => iso.split("-").reverse().join("/");
const ROLES = { Medecin: "Médecin", Secretaire: "Secrétaire" };
const BADGE = { "Planifié": "b-plan", "Salle d'attente": "b-salle", "Consultation": "b-cons", "Terminé": "b-term", "Annulé": "b-annul" };
const badge = (s) => `<span class="badge ${BADGE[s] || ""}">${esc(s)}</span>`;

/* ---------- session & API ---------- */
function loadSession() { try { return JSON.parse(localStorage.getItem(SKEY) || sessionStorage.getItem(SKEY) || "null"); } catch { return null; } }
function saveSession(s, remember) { clearSession(); (remember ? localStorage : sessionStorage).setItem(SKEY, JSON.stringify(s)); }
function clearSession() { localStorage.removeItem(SKEY); sessionStorage.removeItem(SKEY); }
function updateSession(patch) {
  const s = loadSession(); if (!s) return;
  (localStorage.getItem(SKEY) ? localStorage : sessionStorage).setItem(SKEY, JSON.stringify({ ...s, ...patch }));
}

class ApiError extends Error { constructor(msg, status, data) { super(msg); this.status = status; this.data = data || {}; } }

function extractMessage(d) {
  if (!d) return "";
  if (typeof d === "string") return d;
  if (d.detail) return String(d.detail);
  const flat = (v) => Array.isArray(v) ? v.flatMap(flat) : (v && typeof v === "object") ? Object.values(v).flatMap(flat) : [String(v)];
  return flat(Object.values(d)).join(" ");
}

async function api(path, { method = "GET", body, auth = true } = {}, retry = true) {
  const headers = { "Content-Type": "application/json" };
  const s = loadSession();
  if (auth && s) headers.Authorization = "Bearer " + s.access;
  const res = await fetch(path, { method, headers, body: body === undefined ? undefined : JSON.stringify(body) });
  if (res.status === 401 && auth && s) {
    if (retry && s.refresh) {
      const r = await fetch("/api/auth/refresh/", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ refresh: s.refresh }) });
      if (r.ok) { updateSession({ access: (await r.json()).access }); return api(path, { method, body, auth }, false); }
    }
    clearSession(); location.hash = "#/login";
    throw new ApiError("Session expirée, veuillez vous reconnecter.", 401);
  }
  let data = null; try { data = await res.json(); } catch { /* corps vide */ }
  if (!res.ok) throw new ApiError(extractMessage(data) || "Erreur " + res.status, res.status, data);
  return data;
}

/* ---------- mise en page ---------- */
function shell(active, html) {
  const s = loadSession();
  const link = (h, label, key) => `<a href="${h}" class="${active === key ? "active" : ""}">${label}</a>`;
  $app.innerHTML = `<header class="topbar"><div class="wrap">
    <a class="logo" href="#/agenda">Med<b>Connect</b></a>
    <nav>${link("#/agenda", "Agenda", "agenda")}${link("#/salle", "Salle d'attente", "salle")}</nav>
    <div class="user">${esc(s.user.username)} · ${esc(ROLES[s.user.role] || s.user.role || "")}
      <button class="btn" id="logout">Déconnexion</button></div></div></header>
    <main class="wrap">${state.flash ? `<div class="ok">${esc(state.flash)}</div>` : ""}${html}</main>`;
  state.flash = null;
  $("logout").onclick = logout;
}

async function logout() {
  const s = loadSession();
  try { if (s) await api("/api/auth/logout/", { method: "POST", body: { refresh: s.refresh }, auth: false }); } catch { /* ignore */ }
  clearSession(); location.hash = "#/login";
}

function openCancelModal(rdv, onDone) {
  const ov = document.createElement("div");
  ov.className = "overlay";
  ov.innerHTML = `<div class="modal"><h2>Annuler le rendez-vous</h2>
    <p>Patient : ${esc(rdv.patient_nom)} (CIN : ${esc(rdv.patient)}) · Créneau : ${fmtDate(rdv.date)} à ${esc(rdv.heure)} · ${esc(rdv.medecin_nom)}</p>
    <label for="mo">Motif d'annulation *</label><textarea id="mo" rows="3"></textarea>
    <div class="field-err" id="moerr"></div>
    <p style="margin-top:10px">Le rendez-vous restera consultable dans l'agenda avec le statut Annulé.</p>
    <div class="row-btns"><button class="btn" id="mback">Retour</button><button class="btn btn-danger" id="mok">Confirmer l'annulation</button></div></div>`;
  document.body.appendChild(ov);
  const close = () => ov.remove();
  ov.querySelector("#mback").onclick = close;
  ov.querySelector("#mok").onclick = async () => {
    const motif = ov.querySelector("#mo").value.trim();
    if (!motif) { ov.querySelector("#moerr").textContent = "Le motif d'annulation est obligatoire."; return; }
    try { await api(`/api/agenda/rdv/${rdv.id}/annuler/`, { method: "POST", body: { motif_annulation: motif } }); close(); state.flash = "Rendez-vous annulé."; onDone(); }
    catch (e) { ov.querySelector("#moerr").textContent = e.message; }
  };
}

/* ---------- pages ---------- */
function pageLogin() {
  $app.innerHTML = `<header class="topbar"><div class="wrap"><span class="logo">Med<b>Connect</b></span></div></header>
  <main class="wrap"><div class="card login"><h1>Connexion</h1><p>Accédez à votre espace cabinet</p>
    <div id="err"></div>
    <div class="field"><label for="u">Identifiant *</label><input id="u" autocomplete="username"></div>
    <div class="field"><label for="p">Mot de passe *</label><input id="p" type="password" autocomplete="current-password"></div>
    <div class="check"><input type="checkbox" id="r"><label for="r">Se souvenir de moi</label></div>
    <button class="btn btn-primary" id="go" style="width:100%">Se connecter</button></div></main>`;
  const submit = async () => {
    $("err").innerHTML = "";
    const username = $("u").value.trim(), password = $("p").value;
    if (!username || !password) { $("err").innerHTML = `<div class="alert">L'identifiant et le mot de passe sont obligatoires.</div>`; return; }
    try {
      const d = await api("/api/auth/login/", { method: "POST", body: { username, password }, auth: false });
      saveSession({ access: d.access, refresh: d.refresh, user: d.user }, $("r").checked);
      location.hash = "#/agenda";
    } catch (e) { $("err").innerHTML = `<div class="alert">${esc(e.message)}</div>`; }
  };
  $("go").onclick = submit;
  $("p").onkeydown = (e) => { if (e.key === "Enter") submit(); };
}

function agendaRows(list) {
  if (!list.length) return `<tr><td colspan="6" class="empty">Aucun rendez-vous pour cette date.</td></tr>`;
  return list.map((r) => {
    let btns = "";
    if (r.statut === "Planifié") btns += `<button class="btn btn-primary btn-sm" data-act="avancer" data-id="${r.id}">Enregistrer l'arrivée</button>`;
    if (r.statut === "Consultation") btns += `<button class="btn btn-primary btn-sm" data-act="avancer" data-id="${r.id}">Terminer</button>`;
    if (["Planifié", "Salle d'attente", "Consultation"].includes(r.statut)) btns += `<button class="btn btn-sm" data-act="annuler" data-id="${r.id}">Annuler</button>`;
    return `<tr><td>${esc(r.heure)}</td><td><a href="#/rdv/${r.id}"><b>${esc(r.patient_nom)}</b></a></td><td>${esc(r.medecin_nom)}</td><td>${esc(r.motif)}</td>
      <td>${badge(r.statut)}${r.statut === "Annulé" && r.motif_annulation ? `<div class="sub">${esc(r.motif_annulation)}</div>` : ""}</td><td class="act">${btns}</td></tr>`;
  }).join("");
}

async function pageAgenda() {
  const my = ++routeId;
  const date = state.date || (state.date = today());
  shell("agenda", `<div class="page-head"><h1>Agenda du jour</h1><div class="actions">
    <input type="date" id="d" value="${esc(date)}"><a class="btn btn-primary" href="#/rdv/new">+ Nouveau rendez-vous</a></div></div>
    <div id="msg"></div><div class="card"><table><thead><tr><th>Heure</th><th>Patient</th><th>Médecin</th><th>Motif</th><th>Statut</th><th></th></tr></thead>
    <tbody id="rows"><tr><td colspan="6" class="empty">Chargement…</td></tr></tbody></table></div>`);
  $("d").onchange = (e) => { if (e.target.value) { state.date = e.target.value; pageAgenda(); } };
  let list = [];
  try { list = await api("/api/agenda/rdv/?date=" + encodeURIComponent(date)); }
  catch (e) { if (my === routeId) $("msg").innerHTML = `<div class="alert">${esc(e.message)}</div>`; return; }
  if (my !== routeId) return;
  $("rows").innerHTML = agendaRows(list);
  $("rows").onclick = async (e) => {
    const b = e.target.closest("button[data-act]"); if (!b) return;
    const rdv = list.find((x) => String(x.id) === b.dataset.id);
    if (b.dataset.act === "annuler") return openCancelModal(rdv, pageAgenda);
    b.disabled = true;
    try { await api(`/api/agenda/rdv/${rdv.id}/avancer/`, { method: "POST" }); pageAgenda(); }
    catch (err) { b.disabled = false; $("msg").innerHTML = `<div class="alert">${esc(err.message)}</div>`; }
  };
}

async function pageNew() {
  const my = ++routeId;
  shell("agenda", `<div class="page-head"><h1>Nouveau rendez-vous</h1><a class="btn" href="#/agenda">← Retour à l'agenda</a></div><div id="box" class="card">Chargement…</div>`);
  let patients, medecins;
  try { [patients, medecins] = await Promise.all([api("/api/patients/"), api("/api/agenda/medecins/")]); }
  catch (e) { if (my === routeId) $("box").innerHTML = `<div class="alert">${esc(e.message)}</div>`; return; }
  if (my !== routeId) return;
  $("box").innerHTML = `<div id="err"></div><div class="grid">
    <div><label for="pt">Patient *</label><select id="pt"><option value="">— choisir —</option>${patients.map((p) => `<option value="${esc(p.cin)}">${esc(p.cin)} — ${esc(p.prenom)} ${esc(p.nom)}</option>`).join("")}</select></div>
    <div><label for="md">Médecin *</label><select id="md"><option value="">— choisir —</option>${medecins.map((m) => `<option value="${m.id}">${esc(m.nom)}</option>`).join("")}</select></div>
    <div><label for="dh">Date et heure *</label><input type="datetime-local" id="dh" step="60"><div class="field-err" id="dherr"></div></div>
    <div class="full"><label for="mt">Motif</label><input id="mt" maxlength="255"></div></div>
    <div class="row-btns"><button class="btn btn-primary" id="save">Planifier</button><a class="btn" href="#/agenda">Annuler</a></div>`;
  $("save").onclick = async () => {
    $("err").innerHTML = ""; $("dherr").textContent = ""; $("dh").classList.remove("invalid");
    const patient = $("pt").value, medecin = $("md").value, dh = $("dh").value;
    if (!patient || !medecin || !dh) { $("err").innerHTML = `<div class="alert">Patient, médecin, date et heure sont obligatoires.</div>`; return; }
    $("save").disabled = true;
    try {
      const r = await api("/api/agenda/rdv/", { method: "POST", body: { patient, medecin: Number(medecin), date_heure: dh, motif: $("mt").value.trim() } });
      state.date = r.date; state.flash = `Rendez-vous planifié le ${fmtDate(r.date)} à ${r.heure}.`; location.hash = "#/agenda";
    } catch (e) {
      $("save").disabled = false;
      const d = e.data && e.data.date_heure;
      if (d) { $("err").innerHTML = `<div class="alert"><b>Conflit de disponibilité</b>Ce médecin a déjà un rendez-vous à cette date et heure.</div>`; $("dh").classList.add("invalid"); $("dherr").textContent = [].concat(d).join(" "); }
      else $("err").innerHTML = `<div class="alert">${esc(e.message)}</div>`;
    }
  };
}

async function pageDetail(id) {
  const my = ++routeId;
  shell("agenda", `<div class="card" id="box">Chargement…</div>`);
  let r;
  try { r = await api(`/api/agenda/rdv/${encodeURIComponent(id)}/`); }
  catch (e) { if (my === routeId) $("box").innerHTML = `<div class="alert">${e.status === 404 ? "Aucun rendez-vous trouvé avec l'ID " + esc(id) + "." : esc(e.message)}</div><a class="btn" href="#/agenda">← Agenda</a>`; return; }
  if (my !== routeId) return;
  const ORDER = ["Planifié", "Salle d'attente", "Consultation", "Terminé"], idx = ORDER.indexOf(r.statut);
  const steps = ORDER.map((s, i) => `<div class="step ${i < idx || r.statut === "Terminé" ? "done" : i === idx ? "cur" : ""}"><div class="dot">${i < idx || r.statut === "Terminé" ? "✓" : i + 1}</div>${esc(s)}</div>`).join("");
  const open = ["Planifié", "Salle d'attente", "Consultation"].includes(r.statut);
  $("box").innerHTML = `<div class="page-head"><h1>Rendez-vous du ${fmtDate(r.date)} – ${esc(r.heure)} ${badge(r.statut)}</h1><a class="btn" href="#/agenda">← Agenda</a></div>
    <div id="err"></div><dl><div><dt>Patient</dt><dd>${esc(r.patient_nom)}</dd></div><div><dt>CIN</dt><dd>${esc(r.patient)}</dd></div>
    <div><dt>Médecin</dt><dd>${esc(r.medecin_nom)}</dd></div><div><dt>Date et heure</dt><dd>${fmtDate(r.date)} à ${esc(r.heure)}</dd></div>
    <div><dt>Motif de consultation</dt><dd>${esc(r.motif) || "—"}</dd></div>
    <div><dt>Statut actuel</dt><dd>${badge(r.statut)}${r.arrivee_heure ? ` <small>Arrivée enregistrée à ${esc(r.arrivee_heure)} par ${esc(r.arrivee_par_nom)}</small>` : ""}</dd></div>
    ${r.statut === "Annulé" ? `<div class="full" style="grid-column:1/-1"><dt>Motif d'annulation</dt><dd>${esc(r.motif_annulation)}</dd></div>` : ""}</dl>
    ${r.statut !== "Annulé" ? `<div class="sec-title">Progression du rendez-vous</div><div class="steps">${steps}</div>` : ""}
    ${open ? `<div class="row-btns" style="justify-content:space-between"><button class="btn" id="cancel">✕ Annuler le rendez-vous</button>
      ${r.statut !== "Terminé" ? `<button class="btn btn-primary" id="next">→ Avancer le statut</button>` : ""}</div>` : ""}`;
  if (open) {
    $("cancel").onclick = () => openCancelModal(r, () => pageDetail(id));
    if ($("next")) $("next").onclick = async () => {
      $("next").disabled = true;
      try { await api(`/api/agenda/rdv/${r.id}/avancer/`, { method: "POST" }); pageDetail(id); }
      catch (e) { $("next").disabled = false; $("err").innerHTML = `<div class="alert">${esc(e.message)}</div>`; }
    };
  }
}

async function pageSalle() {
  const my = ++routeId;
  shell("salle", `<div class="page-head"><h1>Salle d'attente</h1><span class="live">Mise à jour automatique</span></div><div id="msg"></div>
    <div class="card"><table><thead><tr><th>Heure</th><th>Patient</th><th>Médecin</th><th>Statut</th><th></th></tr></thead><tbody id="rows"></tbody></table></div>`);
  const load = async () => {
    try {
      const list = await api("/api/agenda/rdv/salle-attente/");
      if (my !== routeId) return;
      $("msg").innerHTML = "";
      $("rows").innerHTML = list.length ? list.map((r) => `<tr><td>${esc(r.heure)}</td><td><a href="#/rdv/${r.id}"><b>${esc(r.patient_nom)}</b></a></td><td>${esc(r.medecin_nom)}</td><td>${badge(r.statut)}</td>
        <td class="act"><button class="btn btn-primary btn-sm" data-id="${r.id}">Appeler le patient</button></td></tr>`).join("") : `<tr><td colspan="5" class="empty">Aucun patient en salle d'attente.</td></tr>`;
    } catch (e) { if (my === routeId) $("msg").innerHTML = `<div class="alert">${esc(e.message)}</div>`; }
  };
  $("rows").onclick = async (e) => {
    const b = e.target.closest("button[data-id]"); if (!b) return; b.disabled = true;
    try { await api(`/api/agenda/rdv/${b.dataset.id}/avancer/`, { method: "POST" }); } catch (err) { $("msg").innerHTML = `<div class="alert">${esc(err.message)}</div>`; }
    load();
  };
  await load();
  timer = setInterval(load, 5000);
}

/* ---------- routeur ---------- */
function route() {
  clearInterval(timer); timer = null;
  const h = location.hash || "#/agenda", s = loadSession();
  if (h === "#/login") { routeId++; return s ? (location.hash = "#/agenda") : pageLogin(); }
  if (!s) { location.hash = "#/login"; return; }
  if (h === "#/rdv/new") return pageNew();
  const m = h.match(/^#\/rdv\/([^/]+)$/);
  if (m) return pageDetail(m[1]);
  if (h === "#/salle") return pageSalle();
  return pageAgenda();
}
window.addEventListener("hashchange", route);
route();
