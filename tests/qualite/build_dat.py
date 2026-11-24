"""Build the MedConnect DAT (Dossier d'Analyse et de Tests).

Outputs:
  - report/MedConnect_DAT.docx  (main deliverable, Word format)
  - report/MedConnect_DAT.md    (editable mirror / diff-friendly source)

The script collects the exact 68 retained test cases from the source code:
  - 23 Pytest unit tests (docstrings give the expected behaviour)
  - 45 Django API tests (dashboard_api is intentionally excluded)
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[2]
OUT_DOCX = ROOT / "report" / "MedConnect_DAT.docx"
OUT_MD = ROOT / "report" / "MedConnect_DAT.md"

DATE = "24 novembre 2026"
REF = "DAT-MC-001"
TITLE = "DOSSIER D'ANALYSE ET DE TESTS"
SUBTITLE = "MedConnect -- Plateforme distribuée de gestion de cabinet médical"

# ---------------------------------------------------------------------------
# Expected behaviour for the 45 Django API tests (no docstrings in source)
# ---------------------------------------------------------------------------
API_EXPECT: dict[str, str] = {
    # patients_api
    "test_ajout_patient_valide": "POST /api/patients/ crée un patient valide et retourne 201 avec les données persistées.",
    "test_refus_cin_duplique": "Un CIN déjà enregistré est refusé (400) sans créer de doublon.",
    "test_refus_telephone_duplique": "Un téléphone déjà utilisé est refusé (400).",
    "test_recherche_et_modification": "La recherche par CIN et la modification subsequente sont persistées (200).",
    "test_suppression_patient": "DELETE /api/patients/{id}/ supprime le patient et retourne 204.",
    # agenda_api
    "test_planifier_rdv_valide": "POST /api/agenda/rdv/ crée un RDV sur un créneau libre (201, statut=Planifié).",
    "test_refus_chevauchement_meme_medecin": "Deux RDV sur le même créneau pour le même médecin sont refusés (400).",
    "test_meme_creneau_autre_medecin_ok": "Le même créneau est accepté pour un autre médecin (201).",
    "test_creneau_libere_apres_annulation": "Un RDV annulé libère son créneau pour une nouvelle réservation.",
    "test_patient_inexistant_refuse": "Un RDV pour un patient inexistant est refusé (400).",
    "test_avancer_statut_dans_lordre": "Le cycle Planifié → Salle d'attente → Consultation → Terminé est respecté.",
    "test_avancer_annule_refuse": "Un RDV annulé ne peut plus avancer dans le cycle (400).",
    "test_annuler_conserve_le_rdv": "L'annulation conserve l'enregistrement avec statut=Annulé.",
    "test_annuler_sans_motif_refuse": "Une annulation sans motif est refusée (400).",
    "test_recherche_rdv_inexistant": "La recherche d'un RDV inexistant retourne 404.",
    "test_liste_filtree_par_date": "GET /api/agenda/rdv/ filtre correctement les RDV par date.",
    "test_salle_attente_du_jour_uniquement": "La salle d'attente ne contient que les RDV du jour.",
    "test_acces_sans_jeton_refuse": "Un appel sans jeton JWT est refusé (401).",
    "test_utilisateur_sans_role_refuse": "Un utilisateur authentifié sans rôle métier est refusé (403).",
    "test_login_jwt_et_blocage_apres_5_echecs": "Le login retourne un JWT valide et verrouille le compte après 5 échecs.",
    "test_logout_invalide_le_refresh": "Le logout révoque le token de refresh (401 sur rafraîchissement).",
    # dossier_medical_api
    "test_ajout_consultation_valide": "POST /api/consultations/ crée une consultation valide (201).",
    "test_constantes_facultatives": "Les constantes médicales facultatives peuvent être omises.",
    "test_medecin_non_falsifiable": "Le médecin est forcé à l'utilisateur connecté, même si un autre est envoyé.",
    "test_refus_motif_vide": "Un motif vide est refusé (400).",
    "test_refus_motif_absent": "Un motif absent est refusé (400).",
    "test_refus_patient_inconnu_ou_absent": "Un patient inconnu ou manquant est refusé (400).",
    "test_refus_date_future_ou_invalide": "Une date future ou invalide est refusée (400).",
    "test_refus_constantes_aberrantes": "Des constantes aberrantes sont refusées (400).",
    "test_historique_patient": "GET /api/consultations/?patient=... retourne l'historique complet du patient.",
    "test_filtre_patient_insensible_a_la_casse": "Le filtre patient est insensible à la casse.",
    "test_historique_vide": "Un patient sans consultation retourne une liste vide (200).",
    "test_filtres_dates_et_recherche": "Les filtres combinés dates + recherche retournent uniquement les consultations correspondantes.",
    "test_modifier_diagnostic": "PATCH /api/consultations/{id}/ met à jour le diagnostic (200).",
    "test_modification_ne_peut_pas_vider_le_motif": "Une modification ne peut pas vider le motif (400).",
    "test_patient_non_modifiable": "Le patient d'une consultation ne peut pas être changé (400).",
    "test_suppression": "DELETE /api/consultations/{id}/ supprime la consultation (204).",
    "test_id_inexistant": "Un identifiant inexistant retourne 404.",
    "test_dossier_partage_entre_medecins": "Un dossier est partagé entre médecins autorisés (200).",
    "test_secretaire_refusee_partout": "La secrétaire est refusée sur toutes les ressources médicales (403).",
    "test_utilisateur_sans_role_refuse": "Un utilisateur sans rôle est refusé (403).",
    "test_non_authentifie_refuse": "Un appel non authentifié est refusé (401).",
    # ordonnances_api
    "test_alerte_et_refus_allergie_temps_reel": "Un médicament allergène déclenche une alerte et est refusé en temps réel.",
    "test_ajout_medicament_valide": "Ajout d'une ligne de médicament non allergène accepté (201).",
    "test_validation_et_verrouillage_ordonnance": "La validation passe est_validee=True et verrouille l'ordonnance.",
}

API_MODULES = [
    ("patients_api", "PAT"),
    ("agenda_api", "AGE"),
    ("dossier_medical_api", "DOS"),
    ("ordonnances_api", "ORD"),
]


def collect_unit_cases() -> list[tuple[str, str, str]]:
    cases: list[tuple[str, str, str]] = []
    for path in sorted(ROOT.glob("*/test_*.py")):
        module = path.parent.name
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not node.name.startswith("test_"):
                continue
            doc = (ast.get_docstring(node) or "").splitlines()
            first = doc[0].strip() if doc else node.name.replace("_", " ")
            match = re.match(r"(UT-[A-Z]+-\d+)\s*:\s*(.*)", first)
            if match:
                tid, expected = match.group(1), match.group(2).strip()
            else:
                tid, expected = node.name.upper(), first
            cases.append((tid, module, expected))
    return cases


def collect_api_cases() -> list[tuple[str, str, str]]:
    cases: list[tuple[str, str, str]] = []
    for module, prefix in API_MODULES:
        path = ROOT / "backend" / module / "tests.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        functions = [
            n
            for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            and n.name.startswith("test_")
        ]
        for index, node in enumerate(functions, start=1):
            if node.name not in API_EXPECT:
                raise SystemExit(f"Missing expected-behaviour description for {module}.{node.name}")
            expected = API_EXPECT[node.name]
            cases.append((f"API-{prefix}-{index:02d}", module, expected))
    return cases


UNIT_CASES = collect_unit_cases()
API_CASES = collect_api_cases()

SUMMARY = [
    ("Pytest (unitaires)", "23/23", "reports/pytest.txt", "Tous les cas métier passent"),
    ("Django TestCase (API)", "45/45", "reports/django_api.txt", "dashboard_api exclu du périmètre retenu"),
    ("Postman / Newman", "16 requêtes, 26 assertions, 0 échec", "reports/newman/newman.html", "Scénarios API bout en bout"),
    ("Selenium", "4/4 parcours", "reports/e2e.html", "Chrome headless, parcours patient"),
    ("JMeter", "250 échantillons, 0 erreur", "reports/jmeter/dashboard/index.html", "25 VUs, 13,47 req/s"),
    ("Coverage.py", "88 % métier / 93 % API", "reports/coverage/", "Seuil de couverture validé"),
    ("Ruff", "0 erreur bloquante", "reports/ruff.txt", "5 F401 corrigés"),
    ("pip-audit", "0 vulnérabilité connue", "reports/pip_audit.txt", "backend + racine"),
]

ANOMALIES = [
    ("A-01", "5 imports inutilisés (F401) détectés par Ruff", "Corrigé", "Suppression des imports dans 4 fichiers backend"),
    ("A-02", "Newman PATCH refusé (téléphone figé)", "Corrigé", "Capture du téléphone créé dans la variable `tel`"),
    ("A-03", "Selenium attendait `#/ login` au lieu de `#/` exact", "Corrigé", "Attente explicite de `#/` et de `switch-role`"),
    ("A-04", "Daemon Docker indisponible et pull ZAP en `unexpected EOF`", "Contourné", "Rapports HTML de repli dans `reports/qa_summary/`"),
    ("A-05", "Snyk : erreur 500 / absence de jeton", "Contourné", "Remplacé par pip-audit (0 vulnérabilité)"),
]

SCREENSHOTS = [
    ("Rapport Newman", "qa_postman_newman.png"),
    ("Rapport Selenium", "qa_e2e_report.png"),
    ("Tableau de bord JMeter", "qa_jmeter_dashboard.png"),
    ("Couverture unitaire", "qa_coverage_unitaire.png"),
    ("Couverture API", "qa_coverage_api.png"),
    ("Analyse Ruff", "qa_ruff.png"),
    ("Audit des dépendances", "qa_pip_audit.png"),
    ("Liste des patients (Selenium)", "e2e_01_patients.png"),
    ("Consultation créée (Selenium)", "e2e_04_consultation_creee.png"),
]


# ---------------------------------------------------------------------------
# Word helpers
# ---------------------------------------------------------------------------
def shade(cell, hex_color: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tc_pr.append(shd)


def add_table(doc: Document, headers: list[str], rows: list[list[str]], widths: list[float] | None = None):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.autofit = False
    hdr = table.rows[0].cells
    for i, title in enumerate(headers):
        hdr[i].text = title
        shade(hdr[i], "1F4E5F")
        for paragraph in hdr[i].paragraphs:
            for run in paragraph.runs:
                run.font.bold = True
                run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                run.font.size = Pt(9)
    # Repeat header row on page breaks
    tr_pr = table.rows[0]._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)

    for row in rows:
        cells = table.add_row().cells
        for i, value in enumerate(row):
            cells[i].text = str(value)
            for paragraph in cells[i].paragraphs:
                for run in paragraph.runs:
                    run.font.size = Pt(9)
    if widths:
        for row in table.rows:
            for i, width in enumerate(widths):
                row.cells[i].width = Cm(width)
    doc.add_paragraph()
    return table


def add_bullets(doc: Document, items: list[str]) -> None:
    for item in items:
        doc.add_paragraph(item, style="List Bullet")


def add_caption(doc: Document, text: str) -> None:
    p = doc.add_paragraph(text, style="Caption")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER


def build_docx() -> None:
    doc = Document()

    section = doc.sections[0]
    section.left_margin = Cm(2.2)
    section.right_margin = Cm(2.2)
    section.top_margin = Cm(2.0)
    section.bottom_margin = Cm(2.0)

    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(10)
    for style_name in ("Title", "Heading 1", "Heading 2"):
        style = doc.styles[style_name]
        style.font.color.rgb = RGBColor(0x1F, 0x4E, 0x5F)

    doc.core_properties.title = TITLE
    doc.core_properties.subject = SUBTITLE
    doc.core_properties.author = "Groupe 12 -- MedConnect"
    doc.core_properties.keywords = "DAT, tests, MedConnect, Pytest, Django, Selenium, JMeter"

    # ---- Cover ----
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("ROYAUME DU MAROC\nISIC -- Module Web Services et Applications Distribuées\nAnnée universitaire 2026-2027")
    r.font.size = Pt(11)
    r.font.bold = True

    doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(TITLE)
    r.font.size = Pt(24)
    r.font.bold = True
    r.font.color.rgb = RGBColor(0x1F, 0x4E, 0x5F)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(SUBTITLE)
    r.font.size = Pt(14)

    doc.add_paragraph()
    add_table(
        doc,
        ["Champ", "Valeur"],
        [
            ["Référence du document", REF],
            ["Version", "1.0"],
            ["Date", DATE],
            ["Groupe", "Groupe 12"],
            ["Responsable des tests", "Allabouch Anass (Chef de projet)"],
            ["Statut", "Validé"],
        ],
        [5.0, 11.5],
    )
    doc.add_page_break()

    # ---- 1. Identification ----
    doc.add_heading("1. Fiche d'identification du document", level=1)
    add_table(
        doc,
        ["Élément", "Valeur"],
        [
            ["Nom du projet", "MedConnect -- Plateforme de gestion de cabinet médical"],
            ["Référence du document", REF],
            ["Version du document", "1.0"],
            ["Date de création", DATE],
            ["Responsable des tests", "Allabouch Anass"],
            ["Équipe de développement", "Allabouch Anass, Ahmed Lahmaine, Achraf Ait Damnat, Abdellah Rahel"],
            ["Statut", "Validé"],
            ["Périmètre", "23 tests unitaires + 45 tests API (68 cas retenus)"],
        ],
        [5.2, 11.3],
    )

    # ---- 2. Version history ----
    doc.add_heading("2. Historique des versions et des intervenants", level=1)
    add_table(
        doc,
        ["Version", "Date", "Intervenant", "Rôle", "Nature de l'intervention", "Validation"],
        [
            ["0.1", "23/11/2026", "Groupe 12", "Rédacteurs", "Création du dossier et définition du périmètre (68 cas)", "Validé"],
            ["0.2", "24/11/2026", "Équipe QA", "Testeurs", "Exécution Pytest / Django / Newman / Selenium / JMeter", "Validé"],
            ["0.3", "24/11/2026", "Équipe QA", "Responsable qualité", "Ajout couverture, Ruff, pip-audit et preuves", "Validé"],
            ["1.0", "24/11/2026", "Allabouch Anass", "Chef de projet", "Relecture finale et validation du dossier", "Validé"],
        ],
        [1.6, 2.4, 3.0, 2.6, 5.3, 1.6],
    )

    # ---- 3. Objectifs ----
    doc.add_heading("3. Objet et objectifs", level=1)
    doc.add_paragraph(
        "Ce dossier décrit l'analyse, la conception et l'exécution des tests réalisés sur MedConnect. "
        "Il couvre les règles métier des quatre modules logiciels et les services REST exposés par l'API Django."
    )
    add_bullets(
        doc,
        [
            "Vérifier que chaque règle métier est respectée par le code et par l'API.",
            "Conserver une trace exécutable des scénarios, résultats, couverture et anomalies.",
            "Fournir une preuve d'exécution pour les outils qualité demandés (Newman, Selenium, JMeter, Ruff, pip-audit).",
            "Permettre la relecture et la rejouabilité après toute modification du code.",
        ],
    )

    # ---- 4. Application ----
    doc.add_heading("4. Présentation simplifiée de l'application", level=1)
    doc.add_paragraph(
        "MedConnect est une SPA JavaScript consommant une API REST Django/DRF sécurisée par JWT. "
        "Deux rôles métier sont pris en charge : le médecin et la secrétaire médicale."
    )
    add_table(
        doc,
        ["Module", "Entité principale", "Responsabilité", "Accès"],
        [
            ["patients_api", "Patient", "CRUD patients, unicité CIN/téléphone", "Médecin + Secrétaire"],
            ["agenda_api", "RendezVous", "Créneaux, statuts, salle d'attente, JWT", "Médecin + Secrétaire"],
            ["dossier_medical_api", "Consultation", "Dossier médical, constantes, historique", "Médecin uniquement"],
            ["ordonnances_api", "Ordonnance", "Lignes, allergie, validation immuable", "Médecin uniquement"],
        ],
        [4.0, 3.4, 6.0, 3.1],
    )

    # ---- 5. Périmètre ----
    doc.add_heading("5. Périmètre et stratégie de test", level=1)
    doc.add_paragraph(
        "Le périmètre retenu conserve les 68 tests historiques : 23 tests unitaires Python et 45 tests d'intégration API Django. "
        "Les 15 tests de `dashboard_api` sont volontairement exclus du décompte, conformément au choix validé. "
        "Les outils Java (Checkstyle, JUnit/TestNG, JaCoCo) et JavaScript (Istanbul, Cypress) sont non applicables à cette pile."
    )
    add_table(
        doc,
        ["Niveau", "Outil", "Nombre", "Objectif"],
        [
            ["Unitaire", "Pytest", "23", "Règles métier isolées, sans base de données"],
            ["API", "Django TestCase", "45", "Endpoints, permissions JWT, persistance"],
            ["API outillée", "Postman / Newman", "16 requêtes / 26 assertions", "Campagne reproductible sur serveur réel"],
            ["E2E", "Selenium", "4", "Parcours navigateur avec Chrome headless"],
            ["Charge", "JMeter", "250 échantillons", "25 utilisateurs virtuels, 0 erreur"],
        ],
        [3.2, 4.2, 4.2, 4.9],
    )

    # ---- 6. Environnement ----
    doc.add_heading("6. Environnement et données de test", level=1)
    add_table(
        doc,
        ["Élément", "Valeur"],
        [
            ["URL de l'API", "http://127.0.0.1:8000/"],
            ["Base de données", "SQLite 3 (db.sqlite3, généré par seed_demo)"],
            ["Comptes de démonstration", "dr.demo / sec.demo -- mot de passe Demo@1234"],
            ["Navigateurs", "Chrome headless (Selenium), Firefox/Edge supportés"],
            ["Données de référence", "Patients CD456 / AB123, médecins de démonstration"],
            ["Commande de seed", "python manage.py seed_demo"],
        ],
        [5.0, 11.5],
    )

    # ---- 7. Règles métier ----
    doc.add_heading("7. Règles métier principales vérifiées", level=1)
    add_table(
        doc,
        ["ID règle", "Règle", "Comportement attendu"],
        [
            ["MR-01", "CIN et téléphone uniques", "Refus HTTP 400 / ValueError lors d'un doublon"],
            ["MR-02", "Créneau non chevauchant", "Refus si même médecin + même date/heure"],
            ["MR-03", "Cycle de statut RDV strict", "Planifié → Salle d'attente → Consultation → Terminé / Annulé"],
            ["MR-04", "Motif de consultation obligatoire", "Refus si absent ou vide, y compris en modification"],
            ["MR-05", "Allergie médicamenteuse", "Alerte temps réel et refus de la ligne d'ordonnance"],
            ["MR-06", "Ordonnance validée immuable", "Aucune modification après validation"],
            ["MR-07", "RBAC", "Secrétaire refusée sur consultations/ordonnances (403)"],
            ["MR-08", "JWT et verrouillage", "401 sans jeton, 403 sans rôle, blocage après 5 échecs"],
        ],
        [2.3, 5.5, 8.7],
    )

    # ---- 8. Unit cases ----
    doc.add_heading("8. Cas de tests unitaires (23)", level=1)
    doc.add_paragraph(
        "Chaque test est indépendant : la fixture repart d'un service vide. "
        "Résultats relevés dans `reports/pytest.txt` : 23 passed."
    )
    add_table(
        doc,
        ["ID", "Module", "Scénario / comportement attendu", "Résultat"],
        [[tid, module, expected, "PASS"] for tid, module, expected in UNIT_CASES],
        [2.4, 3.4, 8.8, 1.9],
    )

    # ---- 9. API cases ----
    doc.add_heading("9. Cas de tests d'intégration API (45)", level=1)
    doc.add_paragraph(
        "Les tests Django utilisent une base de test dédiée et valident les codes HTTP, "
        "la persistance et les permissions. Résultats relevés dans `reports/django_api.txt` : Ran 45 tests -- OK."
    )
    add_table(
        doc,
        ["ID", "Module", "Scénario / comportement attendu", "Résultat"],
        [[tid, module, expected, "PASS"] for tid, module, expected in API_CASES],
        [2.6, 3.6, 8.4, 1.9],
    )

    # ---- 10. Résultats ----
    doc.add_heading("10. Synthèse des résultats d'exécution", level=1)
    add_table(
        doc,
        ["Outil", "Résultat", "Preuve", "Observation"],
        [list(row) for row in SUMMARY],
        [3.8, 4.0, 5.2, 3.5],
    )

    # ---- 11. Couverture ----
    doc.add_heading("11. Mesure de couverture", level=1)
    add_table(
        doc,
        ["Périmètre", "Couverture", "Commande", "Preuve"],
        [
            ["Logique métier", "88 %", "coverage run --source=patients,agenda,dossier_medical,ordonnances", "reports/coverage/unit"],
            ["API Django", "93 %", "coverage run --source=patients_api,agenda_api,dossier_medical_api,ordonnances_api", "reports/coverage/api"],
        ],
        [3.5, 2.5, 7.0, 3.5],
    )

    # ---- 12. Complémentaire ----
    doc.add_heading("12. Tests complémentaires et preuves visuelles", level=1)
    doc.add_paragraph(
        "La campagne principale est complétée par une campagne Postman/Newman (16 requêtes, 26 assertions, 0 échec), "
        "quatre parcours Selenium et un test de charge JMeter à 25 utilisateurs virtuels. "
        "JMeter : 250 échantillons, 0 erreur, moyenne 825,72 ms, médiane 35 ms, p95 3970,6 ms, débit 13,47 req/s."
    )
    for caption, filename in SCREENSHOTS:
        path = ROOT / "report" / "screenshots" / filename
        if path.exists():
            doc.add_picture(str(path), width=Cm(15.5))
            add_caption(doc, caption + " -- " + filename)

    # ---- 13. Qualité / sécurité ----
    doc.add_heading("13. Analyse statique et sécurité des dépendances", level=1)
    add_bullets(
        doc,
        [
            "Ruff (règles E9 + F) : 0 erreur bloquante après correction de 5 imports F401.",
            "pip-audit sur `requirements.txt` et `backend/requirements.txt` : aucune vulnérabilité connue.",
            "SonarQube : daemon Docker indisponible ; état et solution de repli consignés dans `reports/qa_summary/`.",
            "OWASP ZAP : échec du téléchargement de l'image (`unexpected EOF`) et daemon indisponible ; contrôles équivalents (JWT, RBAC, validation des entrées) documentés.",
            "Snyk : erreur 500 / absence de jeton ; remplacé par pip-audit.",
        ],
    )

    # ---- 14. Anomalies ----
    doc.add_heading("14. Anomalies, corrections et décisions", level=1)
    add_table(
        doc,
        ["ID", "Constats", "Statut", "Traitement / décision"],
        [list(row) for row in ANOMALIES],
        [1.8, 5.4, 2.4, 6.9],
    )
    doc.add_paragraph(
        "Aucune anomalie bloquante ne subsiste. Les limitations d'environnement (Docker, Snyk) sont documentées "
        "et ne remettent pas en cause les 68 cas exécutés avec succès."
    )

    # ---- 15. Conclusion ----
    doc.add_heading("15. Conclusion", level=1)
    doc.add_paragraph(
        "Les 68 cas de test retenus sont exécutés avec succès : 23 tests unitaires et 45 tests API. "
        "La couverture atteint 88 % sur la logique métier et 93 % sur les API. "
        "Les campagnes Newman, Selenium et JMeter confirment le comportement fonctionnel et la stabilité du service. "
        "Le dossier est considéré comme validé pour la remise."
    )
    add_bullets(
        doc,
        [
            "Poursuivre l'intégration de ces tests dans une pipeline CI (perspective, non livrée).",
            "Étendre la couverture aux scénarios dashboard_api si le périmètre est réouvert.",
            "Réexécuter pip-audit et Ruff à chaque évolution des dépendances.",
        ],
    )

    doc.save(OUT_DOCX)


# ---------------------------------------------------------------------------
# Markdown mirror
# ---------------------------------------------------------------------------
def md_table(headers: list[str], rows: list[list[str]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    out += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return "\n".join(out)


def build_markdown() -> None:
    lines: list[str] = []
    lines += [f"# {TITLE}", "", f"**{SUBTITLE}**", "", f"Référence : {REF} | Version : 1.0 | Date : {DATE}", ""]

    lines += ["## 1. Fiche d'identification", ""]
    lines += [
        md_table(
            ["Champ", "Valeur"],
            [
                ["Nom du projet", "MedConnect"],
                ["Référence", REF],
                ["Responsable des tests", "Allabouch Anass"],
                ["Statut", "Validé"],
                ["Périmètre", "23 unitaires + 45 API = 68 cas"],
            ],
        ),
        "",
    ]

    lines += ["## 2. Historique des versions", ""]
    lines += [
        md_table(
            ["Version", "Date", "Intervenant", "Action"],
            [
                ["0.1", "23/11/2026", "Groupe 12", "Création et périmètre"],
                ["0.2", "24/11/2026", "Équipe QA", "Exécution des campagnes"],
                ["0.3", "24/11/2026", "Responsable qualité", "Couverture, Ruff, pip-audit"],
                ["1.0", "24/11/2026", "Chef de projet", "Validation finale"],
            ],
        ),
        "",
    ]

    lines += ["## 3. Objectifs", ""]
    lines += [
        "- Vérifier les règles métier des 4 modules.\n",
        "- Conserver une trace des scénarios, résultats et anomalies.\n",
        "- Fournir les preuves des outils qualité demandés.\n",
        "",
    ]

    lines += ["## 4. Périmètre et stratégie", ""]
    lines += [
        md_table(
            ["Niveau", "Outil", "Nombre", "Objectif"],
            [
                ["Unitaire", "Pytest", "23", "Règles métier isolées"],
                ["API", "Django TestCase", "45", "Endpoints, JWT, persistance"],
                ["API outillée", "Newman", "16 requêtes / 26 assertions", "Campagne reproductible"],
                ["E2E", "Selenium", "4", "Parcours navigateur"],
                ["Charge", "JMeter", "250 échantillons", "25 VUs, 0 erreur"],
            ],
        ),
        "",
    ]

    lines += ["## 5. Cas unitaires (23)", ""]
    lines += [md_table(["ID", "Module", "Scénario / attendu", "Résultat"], [[a, b, c, "PASS"] for a, b, c in UNIT_CASES]), ""]

    lines += ["## 6. Cas API (45)", ""]
    lines += [md_table(["ID", "Module", "Scénario / attendu", "Résultat"], [[a, b, c, "PASS"] for a, b, c in API_CASES]), ""]

    lines += ["## 7. Synthèse des résultats", ""]
    lines += [md_table(["Outil", "Résultat", "Preuve", "Observation"], [list(r) for r in SUMMARY]), ""]

    lines += ["## 8. Anomalies et décisions", ""]
    lines += [md_table(["ID", "Constats", "Statut", "Traitement"], [list(r) for r in ANOMALIES]), ""]

    lines += ["## 9. Conclusion", ""]
    lines += [
        "68/68 cas exécutés avec succès. Couverture 88 % métier / 93 % API. "
        "Newman, Selenium et JMeter confirment le comportement fonctionnel et la stabilité. Dossier validé.",
        "",
    ]

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    print(f"Unit cases: {len(UNIT_CASES)} | API cases: {len(API_CASES)}")
    if len(UNIT_CASES) != 23 or len(API_CASES) != 45:
        raise SystemExit("Unexpected test count -- refusing to build an inconsistent DAT")
    build_docx()
    build_markdown()
    print(f"Written: {OUT_DOCX}")
    print(f"Written: {OUT_MD}")
