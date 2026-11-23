"""
MedConnect — Application Web de Gestion Intelligente d'un Cabinet Médical
Couvre l'intégralité du Dossier des Spécifications Fonctionnelles (F001 à F007) :
  F001 — Authentification utilisateur (Figure 1)
  F002 — Gestion des patients (Figures 2 à 6)
  F003 — Gestion des rendez-vous / Agenda (Figures 7 à 11)
  F004 — Salle d'attente temps réel (Figure 12)
  F005 — Dossier médical & consultations (Figures 13 à 17)
  F006 — Gestion des ordonnances & alertes allergies (Figures 18 à 23)
  F007 — Ordonnance au format PDF & impression (Figure 24)

Groupe 12 | Master Excellence Ingénierie Logicielle — FSA Agadir | 2026–2027
"""

import os
import sqlite3
from datetime import datetime, date
from flask import (Flask, render_template, request, redirect,
                   url_for, flash, g, session, jsonify)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "medconnect.db")

app = Flask(__name__)
app.secret_key = "medconnect-eq12-master-key-2026"


# ─── Connexion SQLite ─────────────────────────────────────────────────────────
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA journal_mode=WAL")
        g.db.execute("PRAGMA foreign_keys=ON")
    return g.db


@app.teardown_appcontext
def close_db(exc=None):
    db = g.pop("db", None)
    if db:
        db.close()


# ─── Schéma complet de la base de données ─────────────────────────────────────
SCHEMA = """
CREATE TABLE IF NOT EXISTS patients (
    cin             TEXT PRIMARY KEY,
    nom             TEXT NOT NULL,
    prenom          TEXT NOT NULL,
    date_naissance  TEXT NOT NULL,
    telephone       TEXT NOT NULL UNIQUE,
    groupe_sanguin  TEXT DEFAULT '',
    allergies       TEXT DEFAULT '',
    contact_urgence TEXT DEFAULT '',
    created_at      TEXT DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS medecins (
    id              TEXT PRIMARY KEY,
    nom             TEXT NOT NULL,
    specialite      TEXT NOT NULL,
    email           TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS rendez_vous (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_cin       TEXT NOT NULL,
    medecin_id        TEXT NOT NULL,
    date_heure        TEXT NOT NULL,
    motif             TEXT DEFAULT '',
    statut            TEXT NOT NULL DEFAULT 'Planifié',
    motif_annulation  TEXT DEFAULT NULL,
    heure_arrivee     TEXT DEFAULT NULL,
    created_at        TEXT DEFAULT (datetime('now','localtime')),
    FOREIGN KEY(patient_cin) REFERENCES patients(cin) ON DELETE CASCADE,
    FOREIGN KEY(medecin_id) REFERENCES medecins(id)
);

CREATE TABLE IF NOT EXISTS consultations (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_cin       TEXT NOT NULL,
    medecin_id        TEXT NOT NULL,
    date              TEXT NOT NULL,
    motif             TEXT NOT NULL,
    diagnostic        TEXT DEFAULT '',
    created_at        TEXT DEFAULT (datetime('now','localtime')),
    FOREIGN KEY(patient_cin) REFERENCES patients(cin) ON DELETE CASCADE,
    FOREIGN KEY(medecin_id) REFERENCES medecins(id)
);

CREATE TABLE IF NOT EXISTS ordonnances (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_cin       TEXT NOT NULL,
    medecin_id        TEXT NOT NULL,
    date              TEXT NOT NULL,
    est_validee       INTEGER NOT NULL DEFAULT 0,
    created_at        TEXT DEFAULT (datetime('now','localtime')),
    FOREIGN KEY(patient_cin) REFERENCES patients(cin) ON DELETE CASCADE,
    FOREIGN KEY(medecin_id) REFERENCES medecins(id)
);

CREATE TABLE IF NOT EXISTS lignes_ordonnance (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    ordonnance_id     INTEGER NOT NULL,
    medicament        TEXT NOT NULL,
    dosage            TEXT NOT NULL,
    posologie         TEXT NOT NULL,
    duree_jours       INTEGER NOT NULL,
    FOREIGN KEY(ordonnance_id) REFERENCES ordonnances(id) ON DELETE CASCADE
);
"""

STATUTS_CYCLE = ["Planifié", "Salle d'attente", "Consultation", "Terminé"]


# ─── Initialisation & Données de démonstration (Issues du SFD V4) ─────────────
def init_db(seed_demo=True):
    with sqlite3.connect(DATABASE) as db:
        db.executescript(SCHEMA)

        # Vérifier si déjà initialisé
        cnt = db.execute("SELECT COUNT(*) FROM medecins").fetchone()[0]
        if cnt == 0 and seed_demo:
            # Médecins
            db.execute("""
                INSERT INTO medecins (id, nom, specialite, email)
                VALUES ('dr.demo', 'Dr. Demo', 'Médecine générale', 'dr.demo@medconnect.ma')
            """)

            # Patients (Figure 2 & 5)
            patients_demo = [
                ("CD456", "Alaoui", "Omar", "1985-01-02", "0600000002", "", "", ""),
                ("AB123", "Benali", "Sara", "1990-05-01", "0600000001", "O+", "Pénicilline", "0600000009"),
                ("EF789", "Tazi", "Leila", "1978-11-23", "0600000003", "", "", ""),
            ]
            db.executemany("""
                INSERT INTO patients (cin, nom, prenom, date_naissance, telephone, groupe_sanguin, allergies, contact_urgence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, patients_demo)

            # Rendez-vous du 13/11/2026 (Figures 7, 10, 11)
            rdv_demo = [
                ("AB123", "dr.demo", "2026-11-13 09:00", "Contrôle annuel", "Salle d'attente", None, "09:22"),
                ("CD456", "dr.demo", "2026-11-13 09:30", "Toux persistante", "Consultation", None, "09:25"),
                ("EF789", "dr.demo", "2026-11-13 10:00", "Renouvellement", "Planifié", None, None),
                ("AB123", "dr.demo", "2026-11-13 10:30", "Suivi", "Annulé", "Patient indisponible", None),
            ]
            db.executemany("""
                INSERT INTO rendez_vous (patient_cin, medecin_id, date_heure, motif, statut, motif_annulation, heure_arrivee)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, rdv_demo)

            # Consultations (Figure 13)
            consultations_demo = [
                ("AB123", "dr.demo", "2026-10-14", "Fièvre et toux", "Bronchite virale — repos et hydratation, contrôle dans 7 jours."),
                ("AB123", "dr.demo", "2025-10-09", "Contrôle annuel", "RAS"),
            ]
            db.executemany("""
                INSERT INTO consultations (patient_cin, medecin_id, date, motif, diagnostic)
                VALUES (?, ?, ?, ?, ?)
            """, consultations_demo)

            # Ordonnances (Figure 13, 18, 20, 22)
            # Ordonnance n° 1 (Validée)
            c1 = db.execute("INSERT INTO ordonnances (patient_cin, medecin_id, date, est_validee) VALUES ('AB123', 'dr.demo', '2026-11-13', 1)")
            ord1_id = c1.lastrowid
            db.execute("INSERT INTO lignes_ordonnance (ordonnance_id, medicament, dosage, posologie, duree_jours) VALUES (?, 'Paracétamol', '1000 mg', '3 fois par jour', 5)", (ord1_id,))
            db.execute("INSERT INTO lignes_ordonnance (ordonnance_id, medicament, dosage, posologie, duree_jours) VALUES (?, 'Ibuprofène', '400 mg', '2 fois par jour', 3)", (ord1_id,))

            # Ordonnance n° 2 (Brouillon)
            c2 = db.execute("INSERT INTO ordonnances (patient_cin, medecin_id, date, est_validee) VALUES ('AB123', 'dr.demo', '2026-11-13', 0)")
            ord2_id = c2.lastrowid
            db.execute("INSERT INTO lignes_ordonnance (ordonnance_id, medicament, dosage, posologie, duree_jours) VALUES (?, 'Paracétamol', '1000 mg', '3 fois par jour', 5)", (ord2_id,))

            db.commit()


# ─── Filtres Jinja ────────────────────────────────────────────────────────────
@app.template_filter("format_date_fr")
def format_date_fr(val):
    if not val:
        return ""
    try:
        parts = val.split("-")
        if len(parts) == 3:
            return f"{parts[2]}/{parts[1]}/{parts[0]}"
    except Exception:
        pass
    return val


@app.template_filter("format_heure")
def format_heure(date_heure_str):
    if not date_heure_str:
        return ""
    try:
        if " " in date_heure_str:
            return date_heure_str.split(" ")[1]
        elif "T" in date_heure_str:
            return date_heure_str.split("T")[1]
    except Exception:
        pass
    return date_heure_str


@app.template_filter("format_date_only")
def format_date_only(date_heure_str):
    if not date_heure_str:
        return ""
    try:
        d = date_heure_str.split(" ")[0].split("T")[0]
        parts = d.split("-")
        return f"{parts[2]}/{parts[1]}/{parts[0]}"
    except Exception:
        return date_heure_str


# ─── Contexte global templates ────────────────────────────────────────────────
@app.context_processor
def inject_global_data():
    role = session.get("role", "Secrétaire")
    user = session.get("user", "sec.demo" if role == "Secrétaire" else "dr.demo")
    return {
        "current_role": role,
        "current_user": user,
    }


# ─── F001 : Authentification & Changement de rôle ─────────────────────────────
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        ident = request.form.get("identifiant", "sec.demo").strip()
        if "dr" in ident.lower() or "med" in ident.lower():
            session["user"] = "dr.demo"
            session["role"] = "Médecin"
            return redirect(url_for("dossier_medical_index"))
        else:
            session["user"] = "sec.demo"
            session["role"] = "Secrétaire"
            return redirect(url_for("patients_list"))
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/switch-role/<role>")
def switch_role(role):
    if role.lower() == "medecin":
        session["user"] = "dr.demo"
        session["role"] = "Médecin"
        return redirect(url_for("dossier_medical_index"))
    else:
        session["user"] = "sec.demo"
        session["role"] = "Secrétaire"
        return redirect(url_for("patients_list"))


@app.route("/")
def index():
    if session.get("role") == "Médecin":
        return redirect(url_for("dossier_medical_index"))
    return redirect(url_for("patients_list"))


# ─── F002 : Gestion des patients (Figures 2 à 6) ──────────────────────────────
@app.route("/patients")
def patients_list():
    q = request.args.get("q", "").strip()
    db = get_db()
    if q:
        patients = db.execute("SELECT * FROM patients WHERE UPPER(cin) LIKE UPPER(?) ORDER BY cin", (f"%{q}%",)).fetchall()
    else:
        patients = db.execute("SELECT * FROM patients ORDER BY cin").fetchall()
    return render_template("patients/list.html", patients=patients, q=q)


@app.route("/patients/nouveau", methods=["GET", "POST"])
def patients_add():
    error_msg = None
    data = {"cin": "", "nom": "", "prenom": "", "date_naissance": "", "telephone": "", "groupe_sanguin": "", "allergies": "", "contact_urgence": ""}

    if request.method == "POST":
        data = {k: request.form.get(k, "").strip() for k in data}
        required = [("cin", "CIN"), ("nom", "Nom"), ("prenom", "Prénom"), ("date_naissance", "Date de naissance"), ("telephone", "Téléphone")]
        missing = [lbl for k, lbl in required if not data[k]]

        if missing:
            error_msg = f"Champs obligatoires manquants : {', '.join(missing)}."
        else:
            db = get_db()
            if db.execute("SELECT 1 FROM patients WHERE UPPER(cin) = UPPER(?)", (data["cin"],)).fetchone():
                error_msg = "Un patient avec ce CIN existe déjà."
            elif db.execute("SELECT 1 FROM patients WHERE telephone = ?", (data["telephone"],)).fetchone():
                error_msg = "Un patient avec ce numéro de téléphone existe déjà."
            else:
                db.execute("""
                    INSERT INTO patients (cin, nom, prenom, date_naissance, telephone, groupe_sanguin, allergies, contact_urgence)
                    VALUES (:cin, :nom, :prenom, :date_naissance, :telephone, :groupe_sanguin, :allergies, :contact_urgence)
                """, data)
                db.commit()
                return redirect(url_for("patient_detail", cin=data["cin"]))

    return render_template("patients/form.html", title="Nouveau patient", action=url_for("patients_add"), data=data, error_msg=error_msg, edit=False)


@app.route("/patients/<cin>")
def patient_detail(cin):
    db = get_db()
    patient = db.execute("SELECT * FROM patients WHERE UPPER(cin) = UPPER(?)", (cin.strip(),)).fetchone()
    if not patient:
        return redirect(url_for("patients_list"))
    show_modal = request.args.get("action") == "delete"
    return render_template("patients/detail.html", patient=patient, show_modal=show_modal)


@app.route("/patients/<cin>/modifier", methods=["GET", "POST"])
def patients_edit(cin):
    db = get_db()
    patient = db.execute("SELECT * FROM patients WHERE UPPER(cin) = UPPER(?)", (cin.strip(),)).fetchone()
    if not patient:
        return redirect(url_for("patients_list"))

    error_msg = None
    data = dict(patient)

    if request.method == "POST":
        data = {k: request.form.get(k, "").strip() for k in ["nom", "prenom", "date_naissance", "telephone", "groupe_sanguin", "allergies", "contact_urgence"]}
        required = [("nom", "Nom"), ("prenom", "Prénom"), ("date_naissance", "Date de naissance"), ("telephone", "Téléphone")]
        missing = [lbl for k, lbl in required if not data[k]]

        if missing:
            error_msg = f"Champs obligatoires manquants : {', '.join(missing)}."
        else:
            if db.execute("SELECT 1 FROM patients WHERE telephone = ? AND UPPER(cin) != UPPER(?)", (data["telephone"], cin.strip())).fetchone():
                error_msg = "Ce numéro de téléphone est déjà utilisé par un autre patient."
            else:
                db.execute("""
                    UPDATE patients
                    SET nom = :nom, prenom = :prenom, date_naissance = :date_naissance,
                        telephone = :telephone, groupe_sanguin = :groupe_sanguin,
                        allergies = :allergies, contact_urgence = :contact_urgence
                    WHERE UPPER(cin) = UPPER(:cin)
                """, {**data, "cin": cin.strip()})
                db.commit()
                return redirect(url_for("patient_detail", cin=cin))

    return render_template("patients/form.html", title="Modifier le patient", action=url_for("patients_edit", cin=cin), data=data, cin=cin, error_msg=error_msg, edit=True)


@app.route("/patients/<cin>/supprimer", methods=["POST"])
def patients_delete(cin):
    db = get_db()
    db.execute("DELETE FROM patients WHERE UPPER(cin) = UPPER(?)", (cin.strip(),))
    db.commit()
    return redirect(url_for("patients_list"))


# ─── F003 : Gestion des Rendez-vous / Agenda (Figures 7 à 11) ─────────────────
@app.route("/agenda")
def agenda_list():
    date_filter = request.args.get("date", "2026-11-13").strip()
    db = get_db()
    rdvs = db.execute("""
        SELECT r.*, p.nom as patient_nom, p.prenom as patient_prenom, m.nom as medecin_nom
        FROM rendez_vous r
        JOIN patients p ON UPPER(r.patient_cin) = UPPER(p.cin)
        JOIN medecins m ON r.medecin_id = m.id
        WHERE date(r.date_heure) = date(?)
        ORDER BY r.date_heure ASC
    """, (date_filter,)).fetchall()

    return render_template("agenda/list.html", rdvs=rdvs, date_filter=date_filter)


@app.route("/agenda/nouveau", methods=["GET", "POST"])
def agenda_add():
    db = get_db()
    patients = db.execute("SELECT cin, nom, prenom FROM patients ORDER BY nom, prenom").fetchall()
    medecins = db.execute("SELECT id, nom, specialite FROM medecins").fetchall()

    error_msg = None
    conflict_detail = None
    data = {"patient_cin": "", "medecin_id": "dr.demo", "date_heure": "2026-11-13T10:00", "motif": ""}

    if request.method == "POST":
        data = {
            "patient_cin": request.form.get("patient_cin", "").strip(),
            "medecin_id": request.form.get("medecin_id", "dr.demo").strip(),
            "date_heure": request.form.get("date_heure", "").replace("T", " ").strip(),
            "motif": request.form.get("motif", "").strip(),
        }

        # Vérification chevauchement (Règle Agenda — Figure 9)
        existing = db.execute("""
            SELECT r.*, p.nom, p.prenom
            FROM rendez_vous r
            JOIN patients p ON UPPER(r.patient_cin) = UPPER(p.cin)
            WHERE r.medecin_id = ? AND r.date_heure = ? AND r.statut != 'Annulé'
        """, (data["medecin_id"], data["date_heure"])).fetchone()

        if existing:
            error_msg = "Ce médecin a déjà un rendez-vous à cette date et heure."
            time_part = existing["date_heure"].split(" ")[1] if " " in existing["date_heure"] else ""
            conflict_detail = f"Créneau {time_part} indisponible : consultation déjà enregistrée avec {existing['prenom']} {existing['nom']}."
        else:
            db.execute("""
                INSERT INTO rendez_vous (patient_cin, medecin_id, date_heure, motif, statut)
                VALUES (?, ?, ?, ?, 'Planifié')
            """, (data["patient_cin"], data["medecin_id"], data["date_heure"], data["motif"]))
            db.commit()
            date_only = data["date_heure"].split(" ")[0]
            return redirect(url_for("agenda_list", date=date_only))

    return render_template("agenda/form.html", patients=patients, medecins=medecins, data=data, error_msg=error_msg, conflict_detail=conflict_detail)


@app.route("/agenda/<int:rdv_id>")
def agenda_detail(rdv_id):
    db = get_db()
    rdv = db.execute("""
        SELECT r.*, p.nom as patient_nom, p.prenom as patient_prenom, p.telephone, p.cin,
               m.nom as medecin_nom, m.specialite as medecin_specialite
        FROM rendez_vous r
        JOIN patients p ON UPPER(r.patient_cin) = UPPER(p.cin)
        JOIN medecins m ON r.medecin_id = m.id
        WHERE r.id = ?
    """, (rdv_id,)).fetchone()

    if not rdv:
        return redirect(url_for("agenda_list"))

    show_cancel_modal = request.args.get("action") == "cancel"
    return render_template("agenda/detail.html", rdv=rdv, statuts_cycle=STATUTS_CYCLE, show_modal=show_cancel_modal)


@app.route("/agenda/<int:rdv_id>/avancer", methods=["POST"])
def agenda_avancer_statut(rdv_id):
    db = get_db()
    rdv = db.execute("SELECT * FROM rendez_vous WHERE id = ?", (rdv_id,)).fetchone()
    if rdv and rdv["statut"] in STATUTS_CYCLE:
        idx = STATUTS_CYCLE.index(rdv["statut"])
        if idx < len(STATUTS_CYCLE) - 1:
            next_statut = STATUTS_CYCLE[idx + 1]
            now_time = datetime.now().strftime("%H:%M")
            if next_statut == "Salle d'attente":
                db.execute("UPDATE rendez_vous SET statut = ?, heure_arrivee = ? WHERE id = ?", (next_statut, now_time, rdv_id))
            else:
                db.execute("UPDATE rendez_vous SET statut = ? WHERE id = ?", (next_statut, rdv_id))
            db.commit()

    ref = request.referrer
    if ref and "salle-d-attente" in ref:
        return redirect(url_for("salle_attente"))
    return redirect(url_for("agenda_detail", rdv_id=rdv_id))


@app.route("/agenda/<int:rdv_id>/annuler", methods=["POST"])
def agenda_annuler_rdv(rdv_id):
    motif_annulation = request.form.get("motif_annulation", "Annulé").strip()
    db = get_db()
    db.execute("UPDATE rendez_vous SET statut = 'Annulé', motif_annulation = ? WHERE id = ?", (motif_annulation, rdv_id))
    db.commit()
    return redirect(url_for("agenda_detail", rdv_id=rdv_id))


# ─── F004 : Salle d'attente (Figure 12) ───────────────────────────────────────
@app.route("/salle-d-attente")
def salle_attente():
    db = get_db()
    # Affiche les RDV du jour au statut 'Salle d'attente'
    patients_attente = db.execute("""
        SELECT r.*, p.nom as patient_nom, p.prenom as patient_prenom, m.nom as medecin_nom
        FROM rendez_vous r
        JOIN patients p ON UPPER(r.patient_cin) = UPPER(p.cin)
        JOIN medecins m ON r.medecin_id = m.id
        WHERE r.statut = 'Salle d''attente'
        ORDER BY r.date_heure ASC
    """).fetchall()

    return render_template("salle_attente/list.html", patients_attente=patients_attente)


# ─── F005 : Dossier Médical & Consultations (Figures 13 à 17) ──────────────────
@app.route("/dossier-medical")
def dossier_medical_index():
    # Liste de sélection des patients pour le médecin
    q = request.args.get("q", "").strip()
    db = get_db()
    if q:
        patients = db.execute("SELECT * FROM patients WHERE UPPER(cin) LIKE UPPER(?) OR UPPER(nom) LIKE UPPER(?) ORDER BY nom", (f"%{q}%", f"%{q}%")).fetchall()
    else:
        patients = db.execute("SELECT * FROM patients ORDER BY nom, prenom").fetchall()
    return render_template("dossier_medical/index.html", patients=patients, q=q)


@app.route("/dossier-medical/<cin>")
def dossier_medical_patient(cin):
    db = get_db()
    patient = db.execute("SELECT * FROM patients WHERE UPPER(cin) = UPPER(?)", (cin.strip(),)).fetchone()
    if not patient:
        return redirect(url_for("dossier_medical_index"))

    consultations = db.execute("""
        SELECT * FROM consultations WHERE UPPER(patient_cin) = UPPER(?) ORDER BY date DESC, id DESC
    """, (cin.strip(),)).fetchall()

    ordonnances = db.execute("""
        SELECT o.*, COUNT(l.id) as nb_lignes
        FROM ordonnances o
        LEFT JOIN lignes_ordonnance l ON o.id = l.ordonnance_id
        WHERE UPPER(o.patient_cin) = UPPER(?)
        GROUP BY o.id
        ORDER BY o.id DESC
    """, (cin.strip(),)).fetchall()

    return render_template("dossier_medical/patient.html", patient=patient, consultations=consultations, ordonnances=ordonnances)


@app.route("/dossier-medical/<cin>/consultations/nouvelle", methods=["GET", "POST"])
def consultation_add(cin):
    db = get_db()
    patient = db.execute("SELECT * FROM patients WHERE UPPER(cin) = UPPER(?)", (cin.strip(),)).fetchone()
    if not patient:
        return redirect(url_for("dossier_medical_index"))

    error_msg = None
    data = {"date": "2026-11-13", "motif": "", "diagnostic": "", "medecin_id": "dr.demo"}

    if request.method == "POST":
        data["date"] = request.form.get("date", "").strip()
        data["motif"] = request.form.get("motif", "").strip()
        data["diagnostic"] = request.form.get("diagnostic", "").strip()

        # Règle F005 — Motif obligatoire (Figure 15)
        if not data["motif"]:
            error_msg = "Le motif de la consultation est obligatoire."
        else:
            db.execute("""
                INSERT INTO consultations (patient_cin, medecin_id, date, motif, diagnostic)
                VALUES (?, ?, ?, ?, ?)
            """, (cin.strip(), data["medecin_id"], data["date"], data["motif"], data["diagnostic"]))
            db.commit()
            return redirect(url_for("dossier_medical_patient", cin=cin))

    return render_template("dossier_medical/consultation_form.html", patient=patient, data=data, error_msg=error_msg, edit=False)


@app.route("/consultations/<int:cons_id>/modifier", methods=["GET", "POST"])
def consultation_edit(cons_id):
    db = get_db()
    cons = db.execute("SELECT * FROM consultations WHERE id = ?", (cons_id,)).fetchone()
    if not cons:
        return redirect(url_for("dossier_medical_index"))

    patient = db.execute("SELECT * FROM patients WHERE UPPER(cin) = UPPER(?)", (cons["patient_cin"],)).fetchone()
    error_msg = None
    data = dict(cons)

    if request.method == "POST":
        motif = request.form.get("motif", "").strip()
        diagnostic = request.form.get("diagnostic", "").strip()
        cons_date = request.form.get("date", "").strip()

        if not motif:
            error_msg = "Le motif de la consultation est obligatoire."
        else:
            db.execute("""
                UPDATE consultations
                SET motif = ?, diagnostic = ?, date = ?
                WHERE id = ?
            """, (motif, diagnostic, cons_date, cons_id))
            db.commit()
            return redirect(url_for("dossier_medical_patient", cin=cons["patient_cin"]))

    return render_template("dossier_medical/consultation_form.html", patient=patient, data=data, error_msg=error_msg, edit=True, cons_id=cons_id)


@app.route("/consultations/<int:cons_id>/supprimer", methods=["GET", "POST"])
def consultation_delete(cons_id):
    db = get_db()
    cons = db.execute("SELECT * FROM consultations WHERE id = ?", (cons_id,)).fetchone()
    if not cons:
        return redirect(url_for("dossier_medical_index"))

    patient = db.execute("SELECT * FROM patients WHERE UPPER(cin) = UPPER(?)", (cons["patient_cin"],)).fetchone()

    if request.method == "POST":
        db.execute("DELETE FROM consultations WHERE id = ?", (cons_id,))
        db.commit()
        return redirect(url_for("dossier_medical_patient", cin=cons["patient_cin"]))

    # Modal suppression (Figure 17)
    return render_template("dossier_medical/consultation_delete.html", patient=patient, cons=cons)


# ─── F006 : Gestion des Ordonnances & Contrôle Allergies (Figures 18 à 23) ───
@app.route("/dossier-medical/<cin>/ordonnances/nouvelle", methods=["GET", "POST"])
def ordonnance_add(cin):
    db = get_db()
    patient = db.execute("SELECT * FROM patients WHERE UPPER(cin) = UPPER(?)", (cin.strip(),)).fetchone()
    if not patient:
        return redirect(url_for("dossier_medical_index"))

    if request.method == "POST":
        ord_date = request.form.get("date", "2026-11-13").strip()
        medecin_id = "dr.demo"
        cur = db.execute("INSERT INTO ordonnances (patient_cin, medecin_id, date, est_validee) VALUES (?, ?, ?, 0)", (cin.strip(), medecin_id, ord_date))
        db.commit()
        return redirect(url_for("ordonnance_detail", ord_id=cur.lastrowid))

    return render_template("ordonnances/form_new.html", patient=patient, default_date="2026-11-13")


@app.route("/ordonnances/<int:ord_id>")
def ordonnance_detail(ord_id):
    db = get_db()
    ordonnance = db.execute("""
        SELECT o.*, p.nom as patient_nom, p.prenom as patient_prenom, p.allergies, m.nom as medecin_nom
        FROM ordonnances o
        JOIN patients p ON UPPER(o.patient_cin) = UPPER(p.cin)
        JOIN medecins m ON o.medecin_id = m.id
        WHERE o.id = ?
    """, (ord_id,)).fetchone()

    if not ordonnance:
        return redirect(url_for("dossier_medical_index"))

    lignes = db.execute("SELECT * FROM lignes_ordonnance WHERE ordonnance_id = ? ORDER BY id ASC", (ord_id,)).fetchall()
    show_validate_modal = request.args.get("action") == "validate"
    allergy_error = request.args.get("allergy_error")
    success_msg = request.args.get("success_msg")
    error_msg = request.args.get("error_msg")

    return render_template("ordonnances/detail.html",
                           ordonnance=ordonnance,
                           lignes=lignes,
                           show_validate_modal=show_validate_modal,
                           allergy_error=allergy_error,
                           success_msg=success_msg,
                           error_msg=error_msg)


@app.route("/ordonnances/<int:ord_id>/ajouter-ligne", methods=["POST"])
def ordonnance_add_line(ord_id):
    db = get_db()
    ord_row = db.execute("""
        SELECT o.*, p.allergies
        FROM ordonnances o
        JOIN patients p ON UPPER(o.patient_cin) = UPPER(p.cin)
        WHERE o.id = ?
    """, (ord_id,)).fetchone()

    if not ord_row:
        return redirect(url_for("dossier_medical_index"))

    if ord_row["est_validee"] == 1:
        return redirect(url_for("ordonnance_detail", ord_id=ord_id, error_msg="Modification refusée : l'ordonnance est validée."))

    medicament = request.form.get("medicament", "").strip()
    dosage = request.form.get("dosage", "").strip()
    posologie = request.form.get("posologie", "").strip()
    duree = request.form.get("duree", "5").strip()

    # Règle F006 : Alerte d'allergie en temps réel (Figure 18)
    patient_allergies = [a.strip().lower() for a in (ord_row["allergies"] or "").split(",") if a.strip()]
    if medicament.lower() in patient_allergies or any(a in medicament.lower() for a in patient_allergies):
        err = f"Médicament refusé : le patient est allergique à {ord_row['allergies']}."
        return redirect(url_for("ordonnance_detail", ord_id=ord_id, allergy_error=err))

    try:
        duree_int = int(duree)
    except ValueError:
        duree_int = 1

    db.execute("""
        INSERT INTO lignes_ordonnance (ordonnance_id, medicament, dosage, posologie, duree_jours)
        VALUES (?, ?, ?, ?, ?)
    """, (ord_id, medicament, dosage, posologie, duree_int))
    db.commit()

    msg = f"Médicament ajouté : {medicament} {dosage}."
    return redirect(url_for("ordonnance_detail", ord_id=ord_id, success_msg=msg))


@app.route("/ordonnances/<int:ord_id>/valider", methods=["POST"])
def ordonnance_valider(ord_id):
    db = get_db()
    db.execute("UPDATE ordonnances SET est_validee = 1 WHERE id = ?", (ord_id,))
    db.commit()
    return redirect(url_for("ordonnance_detail", ord_id=ord_id))


# ─── F007 : Ordonnance PDF & Imprimable (Figure 24) ───────────────────────────
@app.route("/ordonnances/<int:ord_id>/pdf")
def ordonnance_pdf(ord_id):
    db = get_db()
    ordonnance = db.execute("""
        SELECT o.*, p.nom as patient_nom, p.prenom as patient_prenom, p.date_naissance, p.cin,
               m.nom as medecin_nom, m.specialite as medecin_specialite, m.email as medecin_email
        FROM ordonnances o
        JOIN patients p ON UPPER(o.patient_cin) = UPPER(p.cin)
        JOIN medecins m ON o.medecin_id = m.id
        WHERE o.id = ?
    """, (ord_id,)).fetchone()

    if not ordonnance:
        return redirect(url_for("dossier_medical_index"))

    lignes = db.execute("SELECT * FROM lignes_ordonnance WHERE ordonnance_id = ? ORDER BY id ASC", (ord_id,)).fetchall()
    return render_template("ordonnances/pdf.html", ordonnance=ordonnance, lignes=lignes)


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
