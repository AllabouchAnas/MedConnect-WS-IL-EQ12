"use strict";
/* ==========================================================================
   MedConnect — Frontend SPA Universel (F001 à F007)
   Consomme l'API REST Django (DRF) sécurisée par JWT et RBAC
   Groupe 12 | Master Excellence Ingénierie Logicielle — FSA Agadir
   ========================================================================== */

const $app = document.getElementById("app");
const SKEY = "mc_session";
const state = { date: null, flash: null, searchQ: "" };
let routeId = 0, timer = null;

const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
}[c]));
const $ = (id) => document.getElementById(id);
const pad = (n) => String(n).padStart(2, "0");
const today = () => {
  const d = new Date();
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
};
const fmtDate = (iso) => (iso ? iso.split("-").reverse().join("/") : "");
const ROLES = { Medecin: "Médecin", Secretaire: "Secrétaire" };
const BADGE = {
  "Planifié": "b-plan", "Salle d'attente": "b-salle",
  "Consultation": "b-cons", "Terminé": "b-term", "Annulé": "b-annul"
};
const badge = (s) => `<span class="badge ${BADGE[s] || ""}">${esc(s)}</span>`;

/* ── Gestion session & JWT ─────────────────────────────────────────────────── */
function loadSession() {
  try { return JSON.parse(localStorage.getItem(SKEY) || sessionStorage.getItem(SKEY) || "null"); }
  catch { return null; }
}
function saveSession(s, remember) {
  clearSession();
  (remember ? localStorage : sessionStorage).setItem(SKEY, JSON.stringify(s));
}
function clearSession() {
  localStorage.removeItem(SKEY);
  sessionStorage.removeItem(SKEY);
}
function updateSession(patch) {
  const s = loadSession();
  if (!s) return;
  (localStorage.getItem(SKEY) ? localStorage : sessionStorage).setItem(SKEY, JSON.stringify({ ...s, ...patch }));
}

class ApiError extends Error {
  constructor(msg, status, data) {
    super(msg);
    this.status = status;
    this.data = data || {};
  }
}

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
  const res = await fetch(path, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body)
  });
  if (res.status === 401 && auth && s) {
    if (retry && s.refresh) {
      const r = await fetch("/api/auth/refresh/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh: s.refresh })
      });
      if (r.ok) {
        updateSession({ access: (await r.json()).access });
        return api(path, { method, body, auth }, false);
      }
    }
    clearSession();
    location.hash = "#/login";
    throw new ApiError("Session expirée, veuillez vous reconnecter.", 401);
  }
  let data = null;
  try { data = await res.json(); } catch { /* corps vide */ }
  if (!res.ok) throw new ApiError(extractMessage(data) || "Erreur " + res.status, res.status, data);
  return data;
}

/* ── Barre supérieure & gabarit commun ────────────────────────────────────── */
function shell(active, html) {
  const s = loadSession();
  const isMed = s && s.user && s.user.role === "Medecin";
  const link = (h, label, key) => `<a href="${h}" class="${active === key ? "active" : ""}">${label}</a>`;

  $app.innerHTML = `
    <header class="topbar">
      <div class="wrap">
        <a class="logo" href="#/">Med<b>Connect</b></a>
        <nav>
          ${link("#/", "Accueil", "accueil")}
          ${link("#/patients", "Patients", "patients")}
          ${link("#/agenda", "Agenda", "agenda")}
          ${link("#/salle", "Salle d'attente", "salle")}
          ${isMed ? link("#/dossier", "Dossier médical", "dossier") : ""}
        </nav>
        <div class="user">
          <span>${esc(s.user.username)} · ${esc(ROLES[s.user.role] || s.user.role)}</span>
          <button class="btn btn-sm" id="switch-role" title="Changer d'utilisateur démo">
            ${isMed ? "Passer Secrétaire ➔" : "Passer Médecin ➔"}
          </button>
          <button class="btn btn-sm" id="logout">Déconnexion</button>
        </div>
      </div>
    </header>
    <main class="wrap">
      ${state.flash ? `<div class="ok">${esc(state.flash)}</div>` : ""}
      ${html}
    </main>
  `;
  state.flash = null;

  $("logout").onclick = logout;
  $("switch-role").onclick = async () => {
    const targetUser = isMed ? "sec.demo" : "dr.demo";
    try {
      const d = await api("/api/auth/login/", {
        method: "POST",
        body: { username: targetUser, password: "Demo@1234" },
        auth: false
      });
      saveSession({ access: d.access, refresh: d.refresh, user: d.user }, true);
      state.flash = `Connecté en tant que ${targetUser} (${ROLES[d.user.role]}).`;
      route();
    } catch (e) {
      alert("Erreur de connexion : " + e.message);
    }
  };
}

async function logout() {
  const s = loadSession();
  try {
    if (s) await api("/api/auth/logout/", { method: "POST", body: { refresh: s.refresh }, auth: false });
  } catch { /* ignore */ }
  clearSession();
  location.hash = "#/login";
}

/* ══════════════════════════════════════════════════════════════════════════
   F001 — Authentification utilisateur (Figure 1)
   ══════════════════════════════════════════════════════════════════════════ */
function pageLogin() {
  $app.innerHTML = `
    <header class="topbar">
      <div class="wrap"><span class="logo">Med<b>Connect</b></span></div>
    </header>
    <main class="wrap">
      <div class="card login">
        <h1>Connexion</h1>
        <p>Accédez à votre espace cabinet</p>
        <div id="err"></div>
        <div class="field">
          <label for="u">Identifiant *</label>
          <input id="u" value="sec.demo" autocomplete="username">
        </div>
        <div class="field">
          <label for="p">Mot de passe *</label>
          <input id="p" type="password" value="Demo@1234" autocomplete="current-password">
        </div>
        <div class="check">
          <input type="checkbox" id="r" checked>
          <label for="r">Se souvenir de moi</label>
        </div>
        <button class="btn btn-primary" id="go" style="width:100%">Se connecter</button>
      </div>
    </main>
  `;
  const submit = async () => {
    $("err").innerHTML = "";
    const username = $("u").value.trim(), password = $("p").value;
    if (!username || !password) {
      $("err").innerHTML = `<div class="alert">L'identifiant et le mot de passe sont obligatoires.</div>`;
      return;
    }
    try {
      const d = await api("/api/auth/login/", { method: "POST", body: { username, password }, auth: false });
      saveSession({ access: d.access, refresh: d.refresh, user: d.user }, $("r").checked);
      location.hash = "#/";
    } catch (e) {
      $("err").innerHTML = `<div class="alert">${esc(e.message)}</div>`;
    }
  };
  $("go").onclick = submit;
  $("p").onkeydown = (e) => { if (e.key === "Enter") submit(); };
}

/* ══════════════════════════════════════════════════════════════════════════
   F002 — Gestion des patients (Figures 2 à 6)
   ══════════════════════════════════════════════════════════════════════════ */
async function pagePatients() {
  const my = ++routeId;
  const q = state.searchQ || "";
  shell("patients", `
    <div class="page-head">
      <h1>Patients</h1>
      <a class="btn btn-primary" href="#/patients/new">+ Nouveau patient</a>
    </div>
    <div class="actions" style="margin-bottom:16px">
      <input type="text" id="sq" value="${esc(q)}" placeholder="Rechercher par CIN" style="width:240px">
      <button class="btn btn-primary" id="sbtn">Rechercher</button>
      ${q ? `<button class="btn" id="sclr">Tous les patients</button>` : ""}
    </div>
    <div id="msg"></div>
    <div class="card">
      <table>
        <thead>
          <tr>
            <th>CIN</th><th>NOM</th><th>PRÉNOM</th><th>NAISSANCE</th><th>TÉLÉPHONE</th><th></th>
          </tr>
        </thead>
        <tbody id="rows"><tr><td colspan="6" class="empty">Chargement…</td></tr></tbody>
      </table>
    </div>
  `);

  $("sbtn").onclick = () => { state.searchQ = $("sq").value.trim(); pagePatients(); };
  $("sq").onkeydown = (e) => { if (e.key === "Enter") $("sbtn").click(); };
  if ($("sclr")) $("sclr").onclick = () => { state.searchQ = ""; pagePatients(); };

  let list = [];
  try {
    const url = "/api/patients/" + (q ? "?search=" + encodeURIComponent(q) : "");
    list = await api(url);
  } catch (e) {
    if (my === routeId) $("msg").innerHTML = `<div class="alert">${esc(e.message)}</div>`;
    return;
  }
  if (my !== routeId) return;

  if (!list.length) {
    $("rows").innerHTML = `<tr><td colspan="6" class="empty">Aucun patient trouvé.</td></tr>`;
    return;
  }

  $("rows").innerHTML = list.map((p) => `
    <tr>
      <td>${esc(p.cin)}</td>
      <td><b>${esc(p.nom)}</b></td>
      <td>${esc(p.prenom)}</td>
      <td>${fmtDate(p.date_naissance)}</td>
      <td>${esc(p.telephone)}</td>
      <td class="act"><a class="btn btn-sm" href="#/patients/${encodeURIComponent(p.cin)}">Détail</a></td>
    </tr>
  `).join("");
}

async function pagePatientNew() {
  const my = ++routeId;
  shell("patients", `
    <div class="page-head">
      <h1>Nouveau patient</h1>
      <a class="btn" href="#/patients">Annuler</a>
    </div>
    <div class="card" id="box">
      <div id="err"></div>
      <div class="grid">
        <div><label for="cin">CIN *</label><input id="cin" placeholder="ex : AB123456"></div>
        <div><label for="nom">Nom *</label><input id="nom" placeholder="ex : Benali"></div>
        <div><label for="prenom">Prénom *</label><input id="prenom" placeholder="ex : Sara"></div>
        <div><label for="dn">Date de naissance *</label><input type="date" id="dn"></div>
        <div><label for="tel">Téléphone *</label><input id="tel" placeholder="ex : 0600000001"></div>
        <div>
          <label for="gs">Groupe sanguin</label>
          <select id="gs">
            <option value="">—</option>
            <option value="A+">A+</option><option value="A-">A-</option>
            <option value="B+">B+</option><option value="B-">B-</option>
            <option value="AB+">AB+</option><option value="AB-">AB-</option>
            <option value="O+">O+</option><option value="O-">O-</option>
          </select>
        </div>
        <div class="full"><label for="alg">Allergies (séparées par des virgules)</label><input id="alg" placeholder="ex : Pénicilline"></div>
        <div class="full"><label for="cu">Contact d'urgence</label><input id="cu" placeholder="ex : 0600000009"></div>
      </div>
      <div class="row-btns">
        <button class="btn btn-primary" id="save">Enregistrer</button>
        <a class="btn" href="#/patients">Annuler</a>
      </div>
    </div>
  `);

  $("save").onclick = async () => {
    $("err").innerHTML = "";
    const payload = {
      cin: $("cin").value.trim(),
      nom: $("nom").value.trim(),
      prenom: $("prenom").value.trim(),
      date_naissance: $("dn").value,
      telephone: $("tel").value.trim(),
      groupe_sanguin: $("gs").value,
      allergies: $("alg").value.trim(),
      contact_urgence: $("cu").value.trim(),
    };
    if (!payload.cin || !payload.nom || !payload.prenom || !payload.date_naissance || !payload.telephone) {
      $("err").innerHTML = `<div class="alert">Tous les champs obligatoires (*) doivent être renseignés.</div>`;
      return;
    }
    $("save").disabled = true;
    try {
      await api("/api/patients/", { method: "POST", body: payload });
      state.flash = `Patient ${payload.prenom} ${payload.nom} (${payload.cin}) ajouté avec succès.`;
      location.hash = `#/patients/${encodeURIComponent(payload.cin)}`;
    } catch (e) {
      $("save").disabled = false;
      $("err").innerHTML = `<div class="alert">${esc(e.message)}</div>`;
    }
  };
}

async function pagePatientDetail(cin) {
  const my = ++routeId;
  shell("patients", `<div class="card" id="box">Chargement…</div>`);
  let p;
  try { p = await api(`/api/patients/${encodeURIComponent(cin)}/`); }
  catch (e) {
    if (my === routeId) $("box").innerHTML = `<div class="alert">${esc(e.message)}</div><a class="btn" href="#/patients">← Patients</a>`;
    return;
  }
  if (my !== routeId) return;

  $("box").innerHTML = `
    <div class="page-head">
      <h1>${esc(p.prenom)} ${esc(p.nom)}</h1>
      <a class="btn" href="#/patients">← Patients</a>
    </div>
    <div id="err"></div>
    <dl>
      <div><dt>CIN</dt><dd>${esc(p.cin)}</dd></div>
      <div><dt>Naissance</dt><dd>${fmtDate(p.date_naissance)}</dd></div>
      <div><dt>Téléphone</dt><dd>${esc(p.telephone)}</dd></div>
      <div><dt>Groupe sanguin</dt><dd>${esc(p.groupe_sanguin) || "—"}</dd></div>
      <div><dt>Allergies</dt><dd>${p.allergies ? `<span class="badge b-annul">${esc(p.allergies)}</span>` : "—"}</dd></div>
      <div><dt>Contact d'urgence</dt><dd>${esc(p.contact_urgence) || "—"}</dd></div>
    </dl>
    <div class="row-btns" style="margin-top:24px">
      <a class="btn btn-primary" href="#/patients/${encodeURIComponent(p.cin)}/edit">Modifier</a>
      <button class="btn btn-danger" id="del">Supprimer</button>
      ${isMedecin() ? `<a class="btn" href="#/dossier/${encodeURIComponent(p.cin)}" style="margin-left:auto">🩺 Ouvrir Dossier Médical</a>` : ""}
    </div>
  `;

  $("del").onclick = () => {
    const ov = document.createElement("div");
    ov.className = "overlay";
    ov.innerHTML = `
      <div class="modal">
        <h2>Supprimer ce patient ?</h2>
        <p>Voulez-vous vraiment supprimer <b>${esc(p.prenom)} ${esc(p.nom)}</b> (CIN ${esc(p.cin)}) du système ? Cette action est irréversible.</p>
        <div class="row-btns">
          <button class="btn" id="mback">Annuler</button>
          <button class="btn btn-danger" id="mok">Supprimer</button>
        </div>
      </div>
    `;
    document.body.appendChild(ov);
    ov.querySelector("#mback").onclick = () => ov.remove();
    ov.querySelector("#mok").onclick = async () => {
      try {
        await api(`/api/patients/${encodeURIComponent(p.cin)}/`, { method: "DELETE" });
        ov.remove();
        state.flash = `Patient ${p.prenom} ${p.nom} supprimé.`;
        location.hash = "#/patients";
      } catch (e) {
        alert(e.message);
      }
    };
  };
}

async function pagePatientEdit(cin) {
  const my = ++routeId;
  shell("patients", `<div class="card" id="box">Chargement…</div>`);
  let p;
  try { p = await api(`/api/patients/${encodeURIComponent(cin)}/`); }
  catch (e) {
    if (my === routeId) $("box").innerHTML = `<div class="alert">${esc(e.message)}</div><a class="btn" href="#/patients">← Patients</a>`;
    return;
  }
  if (my !== routeId) return;

  $("box").innerHTML = `
    <div class="page-head">
      <h1>Modifier le patient</h1>
      <a class="btn" href="#/patients/${encodeURIComponent(cin)}">Annuler</a>
    </div>
    <div id="err"></div>
    <div class="grid">
      <div><label for="cin">CIN *</label><input id="cin" value="${esc(p.cin)}" disabled style="background:#f3f4f6"></div>
      <div><label for="nom">Nom *</label><input id="nom" value="${esc(p.nom)}"></div>
      <div><label for="prenom">Prénom *</label><input id="prenom" value="${esc(p.prenom)}"></div>
      <div><label for="dn">Date de naissance *</label><input type="date" id="dn" value="${esc(p.date_naissance)}"></div>
      <div><label for="tel">Téléphone *</label><input id="tel" value="${esc(p.telephone)}"></div>
      <div>
        <label for="gs">Groupe sanguin</label>
        <select id="gs">
          <option value="" ${!p.groupe_sanguin ? "selected" : ""}>—</option>
          ${["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"].map((g) => `<option value="${g}" ${p.groupe_sanguin === g ? "selected" : ""}>${g}</option>`).join("")}
        </select>
      </div>
      <div class="full"><label for="alg">Allergies (séparées par des virgules)</label><input id="alg" value="${esc(p.allergies)}"></div>
      <div class="full"><label for="cu">Contact d'urgence</label><input id="cu" value="${esc(p.contact_urgence)}"></div>
    </div>
    <div class="row-btns">
      <button class="btn btn-primary" id="save">Enregistrer</button>
      <a class="btn" href="#/patients/${encodeURIComponent(cin)}">Annuler</a>
    </div>
  `;

  $("save").onclick = async () => {
    $("err").innerHTML = "";
    const payload = {
      nom: $("nom").value.trim(),
      prenom: $("prenom").value.trim(),
      date_naissance: $("dn").value,
      telephone: $("tel").value.trim(),
      groupe_sanguin: $("gs").value,
      allergies: $("alg").value.trim(),
      contact_urgence: $("cu").value.trim(),
    };
    $("save").disabled = true;
    try {
      await api(`/api/patients/${encodeURIComponent(cin)}/`, { method: "PATCH", body: payload });
      state.flash = "Patient mis à jour.";
      location.hash = `#/patients/${encodeURIComponent(cin)}`;
    } catch (e) {
      $("save").disabled = false;
      $("err").innerHTML = `<div class="alert">${esc(e.message)}</div>`;
    }
  };
}

/* ══════════════════════════════════════════════════════════════════════════
   F003 — Agenda & Rendez-vous (Figures 7 à 11)
   ══════════════════════════════════════════════════════════════════════════ */
function openCancelModal(rdv, onDone) {
  const ov = document.createElement("div");
  ov.className = "overlay";
  ov.innerHTML = `
    <div class="modal">
      <h2>Annuler le rendez-vous</h2>
      <p>Patient : ${esc(rdv.patient_nom)} (CIN : ${esc(rdv.patient)}) · Créneau : ${fmtDate(rdv.date)} à ${esc(rdv.heure)} · ${esc(rdv.medecin_nom)}</p>
      <label for="mo">Motif d'annulation *</label>
      <textarea id="mo" rows="3">Patient indisponible</textarea>
      <div class="field-err" id="moerr"></div>
      <p style="margin-top:10px; font-style:italic">Le rendez-vous restera consultable dans l'agenda avec le statut Annulé.</p>
      <div class="row-btns">
        <button class="btn" id="mback">Retour</button>
        <button class="btn btn-danger" id="mok">Confirmer l'annulation</button>
      </div>
    </div>
  `;
  document.body.appendChild(ov);
  ov.querySelector("#mback").onclick = () => ov.remove();
  ov.querySelector("#mok").onclick = async () => {
    const motif = ov.querySelector("#mo").value.trim();
    if (!motif) { ov.querySelector("#moerr").textContent = "Le motif d'annulation est obligatoire."; return; }
    try {
      await api(`/api/agenda/rdv/${rdv.id}/annuler/`, { method: "POST", body: { motif_annulation: motif } });
      ov.remove();
      state.flash = "Rendez-vous annulé.";
      onDone();
    } catch (e) {
      ov.querySelector("#moerr").textContent = e.message;
    }
  };
}

function agendaRows(list) {
  if (!list.length) return `<tr><td colspan="6" class="empty">Aucun rendez-vous pour cette date.</td></tr>`;
  return list.map((r) => {
    let btns = "";
    if (r.statut === "Planifié") btns += `<button class="btn btn-primary btn-sm" data-act="avancer" data-id="${r.id}">Enregistrer l'arrivée</button>`;
    if (r.statut === "Consultation") btns += `<button class="btn btn-primary btn-sm" data-act="avancer" data-id="${r.id}">Terminer</button>`;
    if (["Planifié", "Salle d'attente", "Consultation"].includes(r.statut)) btns += `<button class="btn btn-sm" data-act="annuler" data-id="${r.id}">Annuler</button>`;
    return `
      <tr>
        <td><a href="#/rdv/${r.id}"><b>${esc(r.heure)}</b></a></td>
        <td>${esc(r.patient_nom)}</td>
        <td>${esc(r.medecin_nom)}</td>
        <td>${esc(r.motif)}</td>
        <td>${badge(r.statut)}${r.statut === "Annulé" && r.motif_annulation ? `<div class="sub">${esc(r.motif_annulation)}</div>` : ""}</td>
        <td class="act">${btns}</td>
      </tr>
    `;
  }).join("");
}

async function pageAgenda() {
  const my = ++routeId;
  const date = state.date || (state.date = "2026-11-13");
  shell("agenda", `
    <div class="page-head">
      <h1>Agenda</h1>
      <div class="actions">
        <input type="date" id="d" value="${esc(date)}">
        <a class="btn btn-primary" href="#/rdv/new">+ Nouveau rendez-vous</a>
      </div>
    </div>
    <div id="msg"></div>
    <div class="card">
      <table>
        <thead>
          <tr><th>HEURE</th><th>PATIENT</th><th>MÉDECIN</th><th>MOTIF</th><th>STATUT</th><th></th></tr>
        </thead>
        <tbody id="rows"><tr><td colspan="6" class="empty">Chargement…</td></tr></tbody>
      </table>
    </div>
  `);

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
    try {
      await api(`/api/agenda/rdv/${rdv.id}/avancer/`, { method: "POST" });
      pageAgenda();
    } catch (err) {
      b.disabled = false;
      $("msg").innerHTML = `<div class="alert">${esc(err.message)}</div>`;
    }
  };
}

async function pageRdvNew() {
  const my = ++routeId;
  shell("agenda", `
    <div class="page-head">
      <h1>Nouveau rendez-vous</h1>
      <a class="btn" href="#/agenda">← Retour à l'agenda</a>
    </div>
    <div id="box" class="card">Chargement…</div>
  `);

  let patients, medecins;
  try { [patients, medecins] = await Promise.all([api("/api/patients/"), api("/api/agenda/medecins/")]); }
  catch (e) { if (my === routeId) $("box").innerHTML = `<div class="alert">${esc(e.message)}</div>`; return; }
  if (my !== routeId) return;

  $("box").innerHTML = `
    <div id="err"></div>
    <div class="grid">
      <div>
        <label for="pt">Patient *</label>
        <select id="pt"><option value="">— choisir —</option>${patients.map((p) => `<option value="${esc(p.cin)}">${esc(p.cin)} — ${esc(p.prenom)} ${esc(p.nom)}</option>`).join("")}</select>
      </div>
      <div>
        <label for="md">Médecin *</label>
        <select id="md"><option value="">— choisir —</option>${medecins.map((m) => `<option value="${m.id}">${esc(m.nom)}</option>`).join("")}</select>
      </div>
      <div>
        <label for="dh">Date et heure *</label>
        <input type="datetime-local" id="dh" value="2026-11-13T10:00" step="60">
        <div class="field-err" id="dherr"></div>
      </div>
      <div class="full">
        <label for="mt">Motif</label>
        <input id="mt" maxlength="255" placeholder="ex : Contrôle annuel, Toux persistante…">
      </div>
    </div>
    <div class="row-btns">
      <button class="btn btn-primary" id="save">Planifier</button>
      <a class="btn" href="#/agenda">Annuler</a>
    </div>
  `;

  $("save").onclick = async () => {
    $("err").innerHTML = ""; $("dherr").textContent = ""; $("dh").classList.remove("invalid");
    const patient = $("pt").value, medecin = $("md").value, dh = $("dh").value;
    if (!patient || !medecin || !dh) {
      $("err").innerHTML = `<div class="alert">Patient, médecin, date et heure sont obligatoires.</div>`;
      return;
    }
    $("save").disabled = true;
    try {
      const r = await api("/api/agenda/rdv/", {
        method: "POST",
        body: { patient, medecin: Number(medecin), date_heure: dh, motif: $("mt").value.trim() }
      });
      state.date = r.date;
      state.flash = `Rendez-vous planifié le ${fmtDate(r.date)} à ${r.heure}.`;
      location.hash = "#/agenda";
    } catch (e) {
      $("save").disabled = false;
      const d = e.data && e.data.date_heure;
      if (d) {
        $("err").innerHTML = `<div class="alert"><b>⚠ Conflit de disponibilité</b>Ce médecin a déjà un rendez-vous à cette date et heure.</div>`;
        $("dh").classList.add("invalid");
        $("dherr").textContent = [].concat(d).join(" ");
      } else {
        $("err").innerHTML = `<div class="alert">${esc(e.message)}</div>`;
      }
    }
  };
}

async function pageRdvDetail(id) {
  const my = ++routeId;
  shell("agenda", `<div class="card" id="box">Chargement…</div>`);
  let r;
  try { r = await api(`/api/agenda/rdv/${encodeURIComponent(id)}/`); }
  catch (e) {
    if (my === routeId) $("box").innerHTML = `<div class="alert">${esc(e.message)}</div><a class="btn" href="#/agenda">← Agenda</a>`;
    return;
  }
  if (my !== routeId) return;

  const ORDER = ["Planifié", "Salle d'attente", "Consultation", "Terminé"], idx = ORDER.indexOf(r.statut);
  const steps = ORDER.map((s, i) => `
    <div class="step ${i < idx || r.statut === "Terminé" ? "done" : i === idx ? "cur" : ""}">
      <div class="dot">${i < idx || r.statut === "Terminé" ? "✓" : i + 1}</div>
      ${esc(s)}
    </div>
  `).join("");
  const open = ["Planifié", "Salle d'attente", "Consultation"].includes(r.statut);

  $("box").innerHTML = `
    <div class="page-head">
      <h1>Rendez-vous du ${fmtDate(r.date)} – ${esc(r.heure)} ${badge(r.statut)}</h1>
      <a class="btn" href="#/agenda">← Agenda</a>
    </div>
    <div id="err"></div>
    <dl>
      <div><dt>Patient</dt><dd><b>${esc(r.patient_nom)}</b></dd></div>
      <div><dt>CIN</dt><dd>${esc(r.patient)}</dd></div>
      <div><dt>Médecin</dt><dd>${esc(r.medecin_nom)}</dd></div>
      <div><dt>Date et heure</dt><dd>${fmtDate(r.date)} à ${esc(r.heure)}</dd></div>
      <div><dt>Motif de consultation</dt><dd>${esc(r.motif) || "—"}</dd></div>
      <div><dt>Statut actuel</dt><dd>${badge(r.statut)}${r.arrivee_heure ? ` <small>(Arrivée à ${esc(r.arrivee_heure)})</small>` : ""}</dd></div>
      ${r.statut === "Annulé" ? `<div class="full" style="grid-column:1/-1"><dt>Motif d'annulation</dt><dd style="color:var(--red)">${esc(r.motif_annulation)}</dd></div>` : ""}
    </dl>
    ${r.statut !== "Annulé" ? `<div class="sec-title">Progression du rendez-vous</div><div class="steps">${steps}</div>` : ""}
    ${open ? `
      <div class="row-btns" style="justify-content:space-between">
        <button class="btn" id="cancel">✕ Annuler le rendez-vous</button>
        ${r.statut !== "Terminé" ? `<button class="btn btn-primary" id="next">→ Avancer le statut</button>` : ""}
      </div>
    ` : ""}
  `;

  if (open) {
    $("cancel").onclick = () => openCancelModal(r, () => pageRdvDetail(id));
    if ($("next")) $("next").onclick = async () => {
      $("next").disabled = true;
      try {
        await api(`/api/agenda/rdv/${r.id}/avancer/`, { method: "POST" });
        pageRdvDetail(id);
      } catch (e) {
        $("next").disabled = false;
        $("err").innerHTML = `<div class="alert">${esc(e.message)}</div>`;
      }
    };
  }
}

/* ══════════════════════════════════════════════════════════════════════════
   F004 — Salle d'attente temps réel (Figure 12)
   ══════════════════════════════════════════════════════════════════════════ */
async function pageSalle() {
  const my = ++routeId;
  shell("salle", `
    <div class="page-head">
      <div>
        <h1>Salle d'attente</h1>
        <span class="live">Mise à jour automatique</span>
      </div>
      <a href="#/agenda" class="btn btn-sm">📅 Voir l'Agenda</a>
    </div>
    <div id="msg"></div>
    <div class="card">
      <div style="padding:14px 18px;border-bottom:1px solid var(--border,#e2e8f0);display:flex;justify-content:space-between;align-items:center">
        <h3 style="margin:0;font-size:15px;color:var(--text,#1e293b)">👥 Patients actuellement en attente</h3>
        <span id="count-attente" class="badge b-salle">0 en attente</span>
      </div>
      <table>
        <thead><tr><th>HEURE</th><th>PATIENT</th><th>MÉDECIN</th><th>STATUT</th><th>ACTION</th></tr></thead>
        <tbody id="rows"></tbody>
      </table>
    </div>

    <div class="card" style="margin-top:24px">
      <div style="padding:14px 18px;border-bottom:1px solid var(--border,#e2e8f0);display:flex;justify-content:space-between;align-items:center">
        <div>
          <h3 style="margin:0;font-size:15px;color:var(--text,#1e293b)">📋 Rendez-vous du jour attendus (Enregistrer l'arrivée)</h3>
          <p style="margin:4px 0 0;font-size:12px;color:var(--muted,#64748b)">Tableau 10 du SFD : Enregistrer l'arrivée fait passer le rendez-vous de <i>Planifié</i> à <i>Salle d'attente</i>.</p>
        </div>
        <span id="count-planifie" class="badge b-plan">0 attendu(s)</span>
      </div>
      <table>
        <thead><tr><th>HEURE</th><th>PATIENT</th><th>MÉDECIN</th><th>MOTIF</th><th>ACTION</th></tr></thead>
        <tbody id="rows-planifies"></tbody>
      </table>
    </div>
  `);

  const load = async () => {
    try {
      const [listAttente, tousRdvJour] = await Promise.all([
        api("/api/agenda/rdv/salle-attente/"),
        api(`/api/agenda/rdv/?date=${today()}`)
      ]);
      if (my !== routeId) return;
      $("msg").innerHTML = "";

      // 1. Patients en salle d'attente
      $("count-attente").textContent = `${listAttente.length} en attente`;
      $("rows").innerHTML = listAttente.length ? listAttente.map((r) => `
        <tr>
          <td><b>${esc(r.heure)}</b></td>
          <td><a href="#/rdv/${r.id}"><b>${esc(r.patient_nom)}</b></a></td>
          <td>${esc(r.medecin_nom)}</td>
          <td>${badge(r.statut)}</td>
          <td class="act"><button class="btn btn-primary btn-sm" data-id="${r.id}">🩺 Appeler le patient</button></td>
        </tr>
      `).join("") : `<tr><td colspan="5" class="empty">Aucun patient en salle d'attente pour le moment.<br><small style="color:var(--muted)">Pour faire entrer un patient, enregistrez son arrivée ci-dessous ou depuis l'Agenda.</small></td></tr>`;

      // 2. Rendez-vous du jour au statut Planifié
      const listPlanifies = (tousRdvJour || []).filter((r) => r.statut === "Planifié");
      $("count-planifie").textContent = `${listPlanifies.length} attendu(s)`;
      $("rows-planifies").innerHTML = listPlanifies.length ? listPlanifies.map((r) => `
        <tr>
          <td><b>${esc(r.heure)}</b></td>
          <td><a href="#/rdv/${r.id}"><b>${esc(r.patient_nom)}</b></a></td>
          <td>${esc(r.medecin_nom)}</td>
          <td>${esc(r.motif || "—")}</td>
          <td class="act"><button class="btn btn-sm" data-id="${r.id}" style="background:#0d9488;color:#fff">✅ Enregistrer l'arrivée</button></td>
        </tr>
      `).join("") : `<tr><td colspan="5" class="empty">Aucun autre rendez-vous planifié en attente d'arrivée aujourd'hui.</td></tr>`;

    } catch (e) {
      if (my === routeId) $("msg").innerHTML = `<div class="alert">${esc(e.message)}</div>`;
    }
  };

  const handleAction = async (e) => {
    const b = e.target.closest("button[data-id]");
    if (!b) return;
    b.disabled = true;
    try {
      await api(`/api/agenda/rdv/${b.dataset.id}/avancer/`, { method: "POST" });
    } catch (err) {
      $("msg").innerHTML = `<div class="alert">${esc(err.message)}</div>`;
    }
    load();
  };

  $("rows").onclick = handleAction;
  $("rows-planifies").onclick = handleAction;

  await load();
  timer = setInterval(load, 5000);
}

/* ══════════════════════════════════════════════════════════════════════════
   F005 — Dossier Médical & Consultations (Figures 13 à 17)
   ══════════════════════════════════════════════════════════════════════════ */
const isMedecin = () => { const s = loadSession(); return !!(s && s.user && s.user.role === "Medecin"); };

/* Le dossier médical est confidentiel : l'API refuse la secrétaire (403), l'interface l'explique. */
function dossierRefuse() {
  if (isMedecin()) return false;
  routeId++;
  shell("dossier", `
    <div class="card">
      <div class="alert">Accès réservé aux médecins : le dossier médical est confidentiel.</div>
      <a class="btn" href="#/patients">← Patients</a>
    </div>`);
  return true;
}

const constantes = (c) => [
  c.tension && `TA ${c.tension}`,
  c.poids != null && `${c.poids} kg`,
  c.temperature != null && `${c.temperature} °C`,
  c.pouls != null && `${c.pouls} bpm`
].filter(Boolean).map(esc).join(" · ") || "—";

async function pageDossierIndex() {
  if (dossierRefuse()) return;
  const my = ++routeId;
  shell("dossier", `
    <div class="page-head">
      <h1>Dossiers Médicaux</h1>
      <span style="color:var(--muted); font-size:12px">Sélectionnez un patient pour ouvrir son dossier</span>
    </div>
    <div class="card">
      <table>
        <thead><tr><th>CIN</th><th>NOM</th><th>PRÉNOM</th><th>ALLERGIES</th><th></th></tr></thead>
        <tbody id="rows"><tr><td colspan="5" class="empty">Chargement…</td></tr></tbody>
      </table>
    </div>
  `);
  let patients = [];
  try { patients = await api("/api/patients/"); } catch (e) { return; }
  if (my !== routeId) return;
  $("rows").innerHTML = patients.map((p) => `
    <tr>
      <td><b>${esc(p.cin)}</b></td>
      <td>${esc(p.nom)}</td>
      <td>${esc(p.prenom)}</td>
      <td>${p.allergies ? `<span class="badge b-annul">${esc(p.allergies)}</span>` : "—"}</td>
      <td class="act"><a class="btn btn-primary btn-sm" href="#/dossier/${encodeURIComponent(p.cin)}">Ouvrir le dossier ➔</a></td>
    </tr>
  `).join("");
}

async function pageDossierPatient(cin) {
  if (dossierRefuse()) return;
  const my = ++routeId;
  shell("dossier", `<div class="card" id="box">Chargement…</div>`);
  let p, consultations, ordonnances;
  try {
    [p, consultations, ordonnances] = await Promise.all([
      api(`/api/patients/${encodeURIComponent(cin)}/`),
      api(`/api/consultations/?patient=${encodeURIComponent(cin)}`),
      // Module Ordonnances (autre membre) : son absence ne doit pas bloquer le dossier.
      api(`/api/ordonnances/?patient=${encodeURIComponent(cin)}`).catch(() => null)
    ]);
  } catch (e) {
    if (my === routeId) $("box").innerHTML = `<div class="alert">${esc(e.message)}</div><a class="btn" href="#/dossier">← Retour</a>`;
    return;
  }
  if (my !== routeId) return;

  $("box").innerHTML = `
    <div class="page-head">
      <h1>${esc(p.prenom)} ${esc(p.nom)}</h1>
      <a class="btn" href="#/dossier">← Autre patient</a>
    </div>
    <dl style="margin-bottom:24px">
      <div><dt>CIN</dt><dd>${esc(p.cin)}</dd></div>
      <div><dt>Naissance</dt><dd>${fmtDate(p.date_naissance)}</dd></div>
      <div><dt>Groupe sanguin</dt><dd>${esc(p.groupe_sanguin) || "—"}</dd></div>
      <div><dt>Allergies</dt><dd>${p.allergies ? `<span class="badge b-annul">${esc(p.allergies)}</span>` : "—"}</dd></div>
    </dl>

    <!-- Consultations -->
    <div class="page-head" style="margin-top:24px">
      <h2 style="font-size:16px; margin:0">Consultations</h2>
      <a class="btn btn-primary btn-sm" href="#/dossier/${encodeURIComponent(p.cin)}/consultation/new">+ Nouvelle consultation</a>
    </div>
    <table>
      <thead><tr><th>DATE</th><th>MOTIF</th><th>DIAGNOSTIC</th><th>CONSTANTES</th><th>MÉDECIN</th><th></th></tr></thead>
      <tbody>
        ${consultations.length ? consultations.map((c) => `
          <tr>
            <td>${fmtDate(c.date)}</td>
            <td><b>${esc(c.motif)}</b></td>
            <td>${esc(c.diagnostic) || "—"}</td>
            <td style="font-size:12px">${constantes(c)}</td>
            <td>${esc(c.medecin_nom)}</td>
            <td class="act">
              <a class="btn btn-sm" href="#/consultation/${c.id}/edit">Modifier</a>
              <button class="btn btn-danger btn-sm" data-delcons="${c.id}">Supprimer</button>
            </td>
          </tr>
        `).join("") : `<tr><td colspan="6" class="empty">Aucune consultation enregistrée.</td></tr>`}
      </tbody>
    </table>

    <!-- Ordonnances -->
    <div class="page-head" style="margin-top:32px">
      <h2 style="font-size:16px; margin:0">Ordonnances</h2>
      ${ordonnances ? `<a class="btn btn-primary btn-sm" href="#/dossier/${encodeURIComponent(p.cin)}/ordonnance/new">+ Nouvelle ordonnance</a>` : ""}
    </div>
    ${ordonnances ? `
    <table>
      <thead><tr><th>N°</th><th>DATE</th><th>LIGNES</th><th>STATUT</th><th></th></tr></thead>
      <tbody>
        ${ordonnances.length ? ordonnances.map((o) => `
          <tr>
            <td><b>N° ${o.id}</b></td>
            <td>${fmtDate(o.date)}</td>
            <td>${o.nb_lignes} ligne(s)</td>
            <td>${o.est_validee ? `<span class="badge b-cons">Validée</span>` : `<span class="badge b-term">Brouillon</span>`}</td>
            <td class="act"><a class="btn btn-sm" href="#/ordonnances/${o.id}">Ouvrir</a></td>
          </tr>
        `).join("") : `<tr><td colspan="5" class="empty">Aucune ordonnance émise.</td></tr>`}
      </tbody>
    </table>` : `<p style="color:var(--muted); font-size:13px">Le module Ordonnances n'est pas encore disponible sur ce serveur.</p>`}
  `;

  // Suppression consultation avec confirmation modale (Figure 17)
  $("box").onclick = (e) => {
    const b = e.target.closest("button[data-delcons]");
    if (!b) return;
    const cid = b.dataset.delcons;
    const c = consultations.find((x) => String(x.id) === cid);
    const ov = document.createElement("div");
    ov.className = "overlay";
    ov.innerHTML = `
      <div class="modal">
        <h2>Supprimer cette consultation ?</h2>
        <p>Voulez-vous vraiment supprimer la consultation du <b>${fmtDate(c.date)}</b> (${esc(c.motif)}) du dossier de <b>${esc(p.prenom)} ${esc(p.nom)}</b> ? Cette action est irréversible.</p>
        <div class="row-btns">
          <button class="btn" id="mback">Annuler</button>
          <button class="btn btn-danger" id="mok">Supprimer</button>
        </div>
      </div>
    `;
    document.body.appendChild(ov);
    ov.querySelector("#mback").onclick = () => ov.remove();
    ov.querySelector("#mok").onclick = async () => {
      try {
        await api(`/api/consultations/${cid}/`, { method: "DELETE" });
        ov.remove();
        state.flash = "Consultation supprimée.";
        pageDossierPatient(cin);
      } catch (err) {
        alert(err.message);
      }
    };
  };
}

/* Formulaire de consultation partagé par « nouvelle » et « modifier ». */
function consultationFields(cin, medecinNom, c = {}) {
  const v = (x) => (x == null ? "" : esc(x));
  return `
    <div id="err"></div>
    <div class="grid">
      <div><label>Patient (CIN)</label><input value="${esc(cin)}" disabled style="background:#f3f4f6"></div>
      <div><label>Médecin</label><input value="${esc(medecinNom)}" disabled style="background:#f3f4f6"></div>
      <div><label for="cd">Date *</label><input type="date" id="cd" value="${esc(c.date || today())}" max="${today()}"></div>
      <div class="full"><label for="cm">Motif *</label><input id="cm" maxlength="255" value="${v(c.motif)}" placeholder="ex : Fièvre et toux, Contrôle annuel…"></div>
      <div><label for="ct">Tension</label><input id="ct" value="${v(c.tension)}" placeholder="ex : 12/8 ou 120/80"></div>
      <div><label for="cpo">Poids (kg)</label><input id="cpo" type="number" step="0.1" min="0" value="${v(c.poids)}"></div>
      <div><label for="cte">Température (°C)</label><input id="cte" type="number" step="0.1" min="0" value="${v(c.temperature)}"></div>
      <div><label for="cpu">Pouls (bpm)</label><input id="cpu" type="number" step="1" min="0" value="${v(c.pouls)}"></div>
      <div class="full"><label for="cdiag">Diagnostic</label><textarea id="cdiag" rows="3" placeholder="Observations cliniques…">${v(c.diagnostic)}</textarea></div>
    </div>`;
}

/* Lit le formulaire ; renvoie null (et affiche l'erreur) si le motif manque. Champ numérique vide → null. */
function readConsultation() {
  const num = (id) => { const t = $(id).value.trim().replace(",", "."); return t === "" ? null : Number(t); };
  const motif = $("cm").value.trim();
  if (!motif) {
    $("err").innerHTML = `<div class="alert">Le motif de la consultation est obligatoire.</div>`;
    return null;
  }
  return {
    date: $("cd").value, motif, tension: $("ct").value.trim(),
    poids: num("cpo"), temperature: num("cte"), pouls: num("cpu"),
    diagnostic: $("cdiag").value.trim()
  };
}

async function pageConsultationNew(cin) {
  if (dossierRefuse()) return;
  const s = loadSession();
  shell("dossier", `
    <div class="page-head">
      <h1>Nouvelle consultation</h1>
      <a class="btn" href="#/dossier/${encodeURIComponent(cin)}">← Retour</a>
    </div>
    <div class="card">
      ${consultationFields(cin, s.user.nom || s.user.username)}
      <div class="row-btns">
        <button class="btn btn-primary" id="save">Enregistrer</button>
        <a class="btn" href="#/dossier/${encodeURIComponent(cin)}">Annuler</a>
      </div>
    </div>
  `);

  $("save").onclick = async () => {
    $("err").innerHTML = "";
    const body = readConsultation();
    if (!body) return;
    $("save").disabled = true;
    try {
      await api("/api/consultations/", { method: "POST", body: { patient_cin: cin, ...body } });
      state.flash = "Consultation ajoutée au dossier.";
      location.hash = `#/dossier/${encodeURIComponent(cin)}`;
    } catch (e) {
      $("save").disabled = false;
      $("err").innerHTML = `<div class="alert">${esc(e.message)}</div>`;
    }
  };
}

async function pageConsultationEdit(id) {
  if (dossierRefuse()) return;
  const my = ++routeId;
  shell("dossier", `<div class="card" id="box">Chargement…</div>`);
  let c;
  try { c = await api(`/api/consultations/${id}/`); }
  catch (e) {
    if (my === routeId) $("box").innerHTML = `<div class="alert">${esc(e.message)}</div><a class="btn" href="#/dossier">← Retour</a>`;
    return;
  }
  if (my !== routeId) return;

  const retour = `#/dossier/${encodeURIComponent(c.patient_cin)}`;
  $("box").innerHTML = `
    <div class="page-head">
      <h1>Modifier la consultation du ${fmtDate(c.date)}</h1>
      <a class="btn" href="${retour}">← Retour</a>
    </div>
    ${consultationFields(c.patient_cin, c.medecin_nom, c)}
    <div class="row-btns">
      <button class="btn btn-primary" id="save">Enregistrer</button>
      <a class="btn" href="${retour}">Annuler</a>
    </div>
  `;

  $("save").onclick = async () => {
    $("err").innerHTML = "";
    const body = readConsultation();
    if (!body) return;
    $("save").disabled = true;
    try {
      await api(`/api/consultations/${id}/`, { method: "PATCH", body });
      state.flash = "Consultation modifiée.";
      location.hash = retour;
    } catch (e) {
      $("save").disabled = false;
      $("err").innerHTML = `<div class="alert">${esc(e.message)}</div>`;
    }
  };
}

/* ══════════════════════════════════════════════════════════════════════════
   F006 & F007 — Gestion des Ordonnances & PDF (Figures 18 à 24)
   ══════════════════════════════════════════════════════════════════════════ */
async function pageOrdonnanceNew(cin) {
  shell("dossier", `
    <div class="page-head">
      <h1>Nouvelle ordonnance</h1>
      <a class="btn" href="#/dossier/${encodeURIComponent(cin)}">← Retour</a>
    </div>
    <div class="card">
      <div class="grid">
        <div><label>Patient (CIN)</label><input value="${esc(cin)}" disabled style="background:#f3f4f6"></div>
        <div><label>Médecin</label><input value="Dr. Demo" disabled style="background:#f3f4f6"></div>
        <div><label for="od">Date *</label><input type="date" id="od" value="2026-11-13"></div>
      </div>
      <p style="color:var(--muted); font-size:12px; margin:16px 0; font-style:italic">
        L'ordonnance est créée vide et non validée ; les médicaments s'ajoutent à l'étape suivante.
      </p>
      <div class="row-btns">
        <button class="btn btn-primary" id="save">Créer l'ordonnance</button>
        <a class="btn" href="#/dossier/${encodeURIComponent(cin)}">Annuler</a>
      </div>
    </div>
  `);

  $("save").onclick = async () => {
    $("save").disabled = true;
    try {
      const o = await api("/api/ordonnances/", {
        method: "POST",
        body: { patient_cin: cin, date: $("od").value }
      });
      location.hash = `#/ordonnances/${o.id}`;
    } catch (e) {
      $("save").disabled = false;
      alert(e.message);
    }
  };
}

async function pageOrdonnanceDetail(id) {
  const my = ++routeId;
  shell("dossier", `<div class="card" id="box">Chargement…</div>`);
  let o;
  try { o = await api(`/api/ordonnances/${id}/`); }
  catch (e) {
    if (my === routeId) $("box").innerHTML = `<div class="alert">${esc(e.message)}</div><a class="btn" href="#/dossier">← Retour</a>`;
    return;
  }
  if (my !== routeId) return;

  $("box").innerHTML = `
    <div class="page-head">
      <h1>Ordonnance n° ${o.id} ${o.est_validee ? `<span class="badge b-cons">Validée</span>` : `<span style="font-weight:normal; color:var(--muted)">— brouillon</span>`}</h1>
      <a class="btn" href="#/dossier/${encodeURIComponent(o.patient_cin || o.patient)}">← Dossier</a>
    </div>
    <div style="font-size:13px; color:var(--muted); margin-bottom:16px">
      Allergies du patient : ${o.patient_allergies ? `<span class="badge b-annul">${esc(o.patient_allergies)}</span>` : "<i>Aucune allergie déclarée</i>"}
    </div>
    <div id="alertbox"></div>

    <table>
      <thead><tr><th>MÉDICAMENT</th><th>DOSAGE</th><th>POSOLOGIE</th><th>DURÉE (J)</th></tr></thead>
      <tbody id="lrows">
        ${o.lignes.length ? o.lignes.map((l) => `
          <tr><td><b>${esc(l.medicament)}</b></td><td>${esc(l.dosage)}</td><td>${esc(l.posologie)}</td><td>${l.duree_jours}</td></tr>
        `).join("") : `<tr><td colspan="4" class="empty">Aucun médicament ajouté.</td></tr>`}
      </tbody>
    </table>

    ${!o.est_validee ? `
      <div style="margin-top:24px; padding-top:16px; border-top:1px solid var(--line)">
        <h3 style="font-size:14px; margin:0 0 12px">Ajouter un médicament</h3>
        <div class="grid">
          <div><label for="med">Médicament *</label><input id="med" placeholder="ex : Paracétamol, Ibuprofène…"></div>
          <div><label for="dos">Dosage *</label><input id="dos" placeholder="ex : 1000 mg, 400 mg"></div>
          <div><label for="pos">Posologie *</label><input id="pos" placeholder="ex : 3 fois par jour"></div>
          <div><label for="dur">Durée (jours) *</label><input type="number" id="dur" value="5" min="1"></div>
        </div>
        <div class="row-btns" style="margin-top:12px">
          <button class="btn btn-primary btn-sm" id="addmed">Ajouter le médicament</button>
        </div>
        <div class="row-btns" style="margin-top:24px; border-top:1px solid var(--line); padding-top:16px">
          <button class="btn btn-primary" id="btnval">Valider l'ordonnance</button>
          <a class="btn" href="#/dossier/${encodeURIComponent(o.patient_cin || o.patient)}">Enregistrer</a>
        </div>
      </div>
    ` : `
      <div class="ok" style="margin-top:20px">
        🔒 <b>Ordonnance verrouillée :</b> aucun ajout ni aucune modification n'est possible.
      </div>
      <div class="row-btns">
        <a class="btn btn-primary" href="#/ordonnances/${o.id}/pdf">📄 Générer le PDF / Imprimer</a>
        <button class="btn" disabled>Modifier</button>
        <button class="btn" disabled>Ajouter un médicament</button>
      </div>
    `}
  `;

  if (!o.est_validee) {
    $("addmed").onclick = async () => {
      $("alertbox").innerHTML = "";
      const medicament = $("med").value.trim(), dosage = $("dos").value.trim(), posologie = $("pos").value.trim(), duree_jours = $("dur").value;
      if (!medicament || !dosage || !posologie) {
        $("alertbox").innerHTML = `<div class="alert">Veuillez renseigner le médicament, son dosage et sa posologie.</div>`;
        return;
      }
      try {
        await api(`/api/ordonnances/${o.id}/ajouter-ligne/`, {
          method: "POST",
          body: { medicament, dosage, posologie, duree_jours: Number(duree_jours) }
        });
        state.flash = `Médicament ajouté : ${medicament} ${dosage}.`;
        pageOrdonnanceDetail(id);
      } catch (err) {
        $("alertbox").innerHTML = `<div class="alert">${esc(err.message)}</div>`;
      }
    };

    $("btnval").onclick = () => {
      const ov = document.createElement("div");
      ov.className = "overlay";
      ov.innerHTML = `
        <div class="modal">
          <h2>Valider cette ordonnance ?</h2>
          <p>L'ordonnance n° ${o.id} comporte ${o.lignes.length} ligne(s). Une fois validée, elle sera <b>verrouillée définitivement</b> : plus aucun ajout ni aucune modification. Cette action est irréversible.</p>
          <div class="row-btns">
            <button class="btn" id="mback">Annuler</button>
            <button class="btn btn-primary" id="mok">Valider</button>
          </div>
        </div>
      `;
      document.body.appendChild(ov);
      ov.querySelector("#mback").onclick = () => ov.remove();
      ov.querySelector("#mok").onclick = async () => {
        try {
          await api(`/api/ordonnances/${o.id}/valider/`, { method: "POST" });
          ov.remove();
          state.flash = "Ordonnance validée et verrouillée.";
          pageOrdonnanceDetail(id);
        } catch (err) {
          alert(err.message);
        }
      };
    };
  }
}

async function pageOrdonnancePdf(id) {
  const my = ++routeId;
  let o;
  try { o = await api(`/api/ordonnances/${id}/`); } catch (e) { return; }
  if (my !== routeId) return;

  $app.innerHTML = `
    <div style="max-width:800px; margin:20px auto; padding:0 20px" class="no-print">
      <a class="btn" href="#/ordonnances/${o.id}">← Dossier</a>
      <button class="btn btn-primary" onclick="window.print()" style="float:right">Télécharger le PDF / Imprimer</button>
    </div>
    <div class="card" style="max-width:800px; margin:20px auto 60px; padding:40px; font-family:Georgia,serif">
      <div style="display:flex; justify-content:space-between; border-bottom:2px solid #111; padding-bottom:16px; margin-bottom:20px">
        <div>
          <h2 style="margin:0; font-size:18px">Dr. Demo</h2>
          <p style="margin:2px 0; color:var(--muted); font-size:12px">Médecine Générale · Cabinet MedConnect Agadir</p>
        </div>
        <div style="text-align:right; font-size:12px">
          <div>Agadir, le : <b>${fmtDate(o.date)}</b></div>
          <div>Ordonnance N° : ORD-${String(o.id).padStart(4, "0")}</div>
        </div>
      </div>
      <div style="background:#f9fafb; padding:10px 14px; border-radius:6px; margin-bottom:24px; font-size:13px">
        <div><b>Patient :</b> ${esc(o.patient_prenom)} ${esc(o.patient_nom)} (CIN : ${esc(o.patient_cin || o.patient)})</div>
      </div>
      <h3 style="text-align:center; text-decoration:underline; letter-spacing:2px; margin-bottom:24px">ORDONNANCE</h3>
      <div style="min-height:220px">
        ${o.lignes.map((l, i) => `
          <div style="margin-bottom:16px">
            <div style="font-weight:700">${i + 1}. ${esc(l.medicament)} ${esc(l.dosage)}</div>
            <div style="margin-left:16px; color:#4b5563">${esc(l.posologie)} — pendant ${l.duree_jours} jours.</div>
          </div>
        `).join("")}
      </div>
      <div style="display:flex; justify-content:flex-end; margin-top:30px">
        <div style="border:2px dashed #9ca3af; padding:12px 24px; text-align:center; width:180px">
          <div style="font-weight:700; font-size:12px">Dr. Demo</div>
          <div style="font-size:10px; color:var(--muted)">Signature & Cachet</div>
          <div style="font-size:20px; color:var(--teal)">✓</div>
        </div>
      </div>
    </div>
  `;
}

/* ══════════════════════════════════════════════════════════════════════════
   Routeur d'application SPA
   ══════════════════════════════════════════════════════════════════════════ */
/* ══════════════════════════════════════════════════════════════════════════
   Accueil — tableau de bord (adapté au rôle ; l'API ne renvoie les données
   médicales qu'au médecin)
   ══════════════════════════════════════════════════════════════════════════ */
const fmtLong = (iso) => new Date(iso + "T12:00:00").toLocaleDateString("fr-FR",
  { weekday: "long", day: "numeric", month: "long", year: "numeric" });
const JOURS_COURTS = ["dim.", "lun.", "mar.", "mer.", "jeu.", "ven.", "sam."];

function accueilKpis(d) {
  const k = d.kpis, med = d.role === "Medecin";
  const pl = (n, un, plur) => `${n} ${n > 1 ? plur : un}`;
  const cards = [
    ["Rendez-vous aujourd'hui", k.rdv_total,
      `${k.termines} terminé(s) · ${k.restants} restant(s) · ${pl(k.annules, "annulé", "annulés")}`],
    ["En salle d'attente", k.en_attente,
      k.attente_moyenne_min == null ? "personne n'attend" : `attente moyenne : ${k.attente_moyenne_min} min`],
    ["Patients", k.patients_total, "enregistrés au cabinet"],
    ["Annulations (semaine)", k.annulations_semaine, med ? "parmi vos rendez-vous" : "tous médecins"]
  ];
  return `<div class="kpis">${cards.map(([l, v, n]) =>
    `<div class="kpi"><div class="l">${esc(l)}</div><div class="v">${esc(v)}</div><div class="n">${esc(n)}</div></div>`
  ).join("")}</div>`;
}

function accueilPlanning(d) {
  const med = d.role === "Medecin";
  const rows = d.rdvs.length ? d.rdvs.map((r) => `
    <tr>
      <td><a href="#/rdv/${r.id}"><b>${esc(r.heure)}</b></a></td>
      <td>${esc(r.patient_nom)}${r.motif ? `<div class="s" style="font-size:12.5px;color:var(--muted)">${esc(r.motif)}</div>` : ""}</td>
      ${med ? "" : `<td>${esc(r.medecin_nom)}</td>`}
      <td>${badge(r.statut)}${r.statut === "Annulé" && r.motif_annulation ? `<div class="sub">${esc(r.motif_annulation)}</div>` : ""}</td>
      <td class="act">${med
        ? `<a class="btn btn-sm" href="#/dossier/${encodeURIComponent(r.patient_cin)}">Dossier</a>`
        : `<a class="btn btn-sm" href="#/rdv/${r.id}">Détail</a>`}</td>
    </tr>`).join("")
    : `<tr><td colspan="${med ? 4 : 5}" class="empty">Aucun rendez-vous aujourd'hui.</td></tr>`;
  return `
    <section class="card flush">
      <div class="head"><h2>${med ? "Ma journée" : "Planning du jour"}</h2><a href="#/agenda" style="color:var(--teal);font-weight:600">Voir l'agenda</a></div>
      <table>
        <thead><tr><th>HEURE</th><th>PATIENT</th>${med ? "" : "<th>MÉDECIN</th>"}<th>STATUT</th><th></th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </section>`;
}

function accueilSalle(d) {
  const med = d.role === "Medecin";
  const rows = d.salle_attente.length ? d.salle_attente.map((a) => `
    <div class="list-row">
      <div>
        <div class="t"><a href="#/rdv/${a.id}">${esc(a.patient_nom)}</a></div>
        <div class="s">${a.arrivee_heure ? `Arrivé à ${esc(a.arrivee_heure)} · ` : ""}RDV ${esc(a.heure)}${med ? "" : ` · ${esc(a.medecin_nom)}`}</div>
      </div>
      <div class="w">${a.attente_min == null ? "" : esc(a.attente_min) + " min"}</div>
    </div>`).join("")
    : `<div class="list-empty">Aucun patient en salle d'attente.</div>`;
  return `
    <section class="card flush">
      <div class="head"><h2>Salle d'attente</h2><a href="#/salle" style="color:var(--teal);font-weight:600">Gérer</a></div>
      ${rows}
    </section>`;
}

function accueilCote(d) {
  if (d.role === "Medecin") {
    const rows = d.consultations_recentes.length ? d.consultations_recentes.map((c) => `
      <div class="list-row">
        <div style="min-width:0">
          <div class="t">${esc(c.patient_nom)}</div>
          <div class="s">${esc(c.motif)} · ${esc(fmtDate(c.date))}</div>
        </div>
        <a class="btn btn-sm" href="#/dossier/${encodeURIComponent(c.patient_cin)}">Ouvrir</a>
      </div>`).join("")
      : `<div class="list-empty">Aucune consultation enregistrée.</div>`;
    return `<section class="card flush"><div class="head"><h2>Dernières consultations</h2><a href="#/dossier" style="color:var(--teal);font-weight:600">Dossiers</a></div>${rows}</section>`;
  }
  const dem = d.demain;
  const rows = dem.par_medecin.length ? dem.par_medecin.map((m) => `
    <div class="list-row"><div class="t">${esc(m.medecin_nom)}</div><div class="s">${esc(m.n)} rendez-vous</div></div>`).join("")
    : `<div class="list-empty">Aucun rendez-vous demain.</div>`;
  return `<section class="card flush"><div class="head"><h2>Demain · ${esc(fmtDate(dem.date))}</h2><span class="s" style="font-size:12.5px;color:var(--muted)">${esc(dem.total)} au total</span></div>${rows}</section>`;
}

function accueilActivite(d) {
  if (d.role !== "Medecin") return "";
  const max = Math.max(1, ...d.activite.map((j) => j.n)), total = d.activite.reduce((s, j) => s + j.n, 0);
  const bars = d.activite.map((j, i) => `
    <div class="bar ${i === d.activite.length - 1 ? "today" : ""}">
      <b>${esc(j.n)}</b><i style="height:${j.n ? Math.round((j.n / max) * 90) : 3}px"></i>
    </div>`).join("");
  const labels = d.activite.map((j, i) => `<span>${i === d.activite.length - 1 ? "auj." : JOURS_COURTS[new Date(j.date + "T12:00:00").getDay()]}</span>`).join("");
  return `
    <section class="card" style="margin-top:20px">
      <div style="display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:8px;margin-bottom:16px">
        <h2 style="margin:0;font-size:15px">Consultations des 7 derniers jours</h2>
        <span style="font-size:12.5px;color:var(--muted)">${esc(total)} au total</span>
      </div>
      <div class="bars">${bars}</div><div class="bar-labels">${labels}</div>
    </section>`;
}

async function pageAccueil() {
  const my = ++routeId;
  shell("accueil", `
    <div class="page-head">
      <div id="hd"><h1>Accueil</h1></div>
      <div class="actions" style="flex-wrap:wrap">
        <form id="qs" class="actions" role="search">
          <input type="text" id="qq" placeholder="Rechercher un patient (CIN, nom)…" aria-label="Rechercher un patient" style="width:230px">
          <button class="btn" type="submit">Rechercher</button>
        </form>
        <a class="btn" href="#/patients/new">Nouveau patient</a>
        <a class="btn btn-primary" href="#/rdv/new">+ Nouveau rendez-vous</a>
      </div>
    </div>
    <div id="msg"></div>
    <div id="dyn"><div class="card">Chargement…</div></div>
  `);

  $("qs").onsubmit = (e) => {
    e.preventDefault();
    state.searchQ = $("qq").value.trim();
    location.hash = "#/patients";
  };

  const load = async () => {
    let d;
    try { d = await api("/api/dashboard/"); }
    catch (e) {
      if (my === routeId) $("msg").innerHTML = `<div class="alert">${esc(e.message)}</div>`;
      return;
    }
    if (my !== routeId) return;
    const med = d.role === "Medecin";
    $("msg").innerHTML = "";
    $("hd").innerHTML = `<h1>Bonjour, ${esc(d.nom)}</h1>
      <span style="color:var(--muted);font-size:13.5px">${esc(fmtLong(d.date))}${med
        ? ` · ${d.kpis.restants} patient(s) restant(s) aujourd'hui` : ""}</span>`;
    $("dyn").innerHTML = `
      ${accueilKpis(d)}
      <div class="cols">
        <div class="main">${accueilPlanning(d)}</div>
        <div class="side">${accueilSalle(d)}${accueilCote(d)}</div>
      </div>
      ${accueilActivite(d)}`;
  };

  await load();
  timer = setInterval(load, 30000);
}

function route() {
  clearInterval(timer);
  timer = null;
  const h = location.hash || "#/", s = loadSession();
  if (h === "#/login") {
    routeId++;
    return s ? (location.hash = "#/") : pageLogin();
  }
  if (!s) {
    location.hash = "#/login";
    return;
  }

  // Accueil (tableau de bord)
  if (h === "#/") return pageAccueil();

  // Routes Patients (F002)
  if (h === "#/patients") return pagePatients();
  if (h === "#/patients/new") return pagePatientNew();
  let m = h.match(/^#\/patients\/([^/]+)\/edit$/);
  if (m) return pagePatientEdit(decodeURIComponent(m[1]));
  m = h.match(/^#\/patients\/([^/]+)$/);
  if (m) return pagePatientDetail(decodeURIComponent(m[1]));

  // Routes Agenda (F003) & Salle d'attente (F004)
  if (h === "#/agenda") return pageAgenda();
  if (h === "#/rdv/new") return pageRdvNew();
  m = h.match(/^#\/rdv\/([^/]+)$/);
  if (m) return pageRdvDetail(m[1]);
  if (h === "#/salle") return pageSalle();

  // Routes Dossier médical (F005)
  if (h === "#/dossier") return pageDossierIndex();
  m = h.match(/^#\/dossier\/([^/]+)\/consultation\/new$/);
  if (m) return pageConsultationNew(decodeURIComponent(m[1]));
  m = h.match(/^#\/consultation\/(\d+)\/edit$/);
  if (m) return pageConsultationEdit(m[1]);
  m = h.match(/^#\/dossier\/([^/]+)\/ordonnance\/new$/);
  if (m) return pageOrdonnanceNew(decodeURIComponent(m[1]));
  m = h.match(/^#\/dossier\/([^/]+)$/);
  if (m) return pageDossierPatient(decodeURIComponent(m[1]));

  // Routes Ordonnances (F006 & F007)
  m = h.match(/^#\/ordonnances\/(\d+)\/pdf$/);
  if (m) return pageOrdonnancePdf(m[1]);
  m = h.match(/^#\/ordonnances\/(\d+)$/);
  if (m) return pageOrdonnanceDetail(m[1]);

  return pageAccueil();
}

window.addEventListener("hashchange", route);
route();
