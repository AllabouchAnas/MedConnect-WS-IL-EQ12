"""
MedConnect — Lanceur universel & tout-en-un
===========================================
Usage direct :
  python exe.py           → Menu interactif
  python exe.py --web     → Lance l'application web Django (architecture distribuee SFD V4)
  python exe.py --tests   → Execute les tests Django (27 tests) et pytest (23 tests)
  python exe.py --init-db → Reinitialise la base SQLite avec les donnees de demo (seed_demo)
  python exe.py --flask   → Lance le prototype Flask (port 5000)

Groupe 12 | Master Excellence Ingenierie Logicielle — FSA Agadir | 2026–2027
"""

import sys
import os
import subprocess
import webbrowser
import threading
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(ROOT, "backend")
MANAGE_PY = os.path.join(BACKEND, "manage.py")
PYTHON = os.path.join(ROOT, "venv", "Scripts", "python.exe")

if not os.path.isfile(PYTHON):
    PYTHON = sys.executable


def banner():
    print()
    print("=" * 68)
    print("  🏥  MedConnect — Architecture Distribuee & Web SPA (SFD V4)")
    print("      Groupe 12 | Master Excellence IL — FSA Agadir")
    print("      Modules : patients_api | agenda_api | dossier_medical_api | ordonnances_api")
    print("=" * 68)
    print()


def run_django(port=8000):
    """Lance le serveur Django REST Framework + SPA et ouvre le navigateur."""
    print("▶  Verification de la base SQLite et des migrations...")
    subprocess.run([PYTHON, MANAGE_PY, "migrate"], cwd=BACKEND)

    url = f"http://127.0.0.1:{port}/"
    print(f"\n▶  Demarrage du serveur Django sur {url}")
    print(f"   Ouverture automatique : {url}")
    print("   Identifiants de demonstration :")
    print("     - Medecin    : dr.demo  / DemoPass123!")
    print("     - Secretaire : sec.demo / DemoPass123!")
    print("   (Appuyez sur Ctrl+C pour arreter le serveur)\n")

    def open_browser():
        time.sleep(1.5)
        webbrowser.open(url)

    threading.Thread(target=open_browser, daemon=True).start()
    subprocess.run([PYTHON, MANAGE_PY, "runserver", str(port)], cwd=BACKEND)


def run_flask():
    """Lance le prototype Flask."""
    sys.path.insert(0, ROOT)
    from app import init_db, app
    init_db(seed_demo=True)
    url = "http://127.0.0.1:5000/patients"
    print(f"▶  Demarrage prototype Flask sur {url}")
    threading.Thread(target=lambda: (time.sleep(1.2), webbrowser.open(url)), daemon=True).start()
    app.run(debug=False, port=5000, use_reloader=False)


def run_django_tests():
    candidate_apps = ["patients_api", "agenda_api", "dossier_medical_api", "ordonnances_api"]
    apps_to_test = [app for app in candidate_apps if os.path.isdir(os.path.join(BACKEND, app))]
    print(f"▶  Execution des tests Django REST API ({', '.join(apps_to_test)})...")
    res = subprocess.run([PYTHON, MANAGE_PY, "test"] + apps_to_test, cwd=BACKEND)
    return res.returncode


def run_pytest(html=False):
    if html:
        report_file = os.path.join(ROOT, "rapport_tests.html")
        print(f"▶  Generation du rapport HTML complet : {report_file}")
        res = subprocess.run([PYTHON, "-m", "pytest", f"--html={report_file}", "--self-contained-html"], cwd=ROOT)
        if res.returncode == 0:
            print(f"✅  Rapport HTML pret : {report_file}")
            threading.Thread(target=lambda: (time.sleep(0.5), webbrowser.open(f"file://{report_file}")), daemon=True).start()
        return res.returncode

    print("▶  Execution des tests unitaires pytest...")
    res = subprocess.run([PYTHON, "-m", "pytest", "-v", "--tb=short"], cwd=ROOT)
    return res.returncode


def reset_db_cmd():
    print("▶  Alimentation de la base de donnees de demonstration...")
    res = subprocess.run([PYTHON, MANAGE_PY, "seed_demo"], cwd=BACKEND)
    seed_dossier_py = os.path.join(BACKEND, "dossier_medical_api", "management", "commands", "seed_dossier.py")
    if os.path.isfile(seed_dossier_py):
        subprocess.run([PYTHON, MANAGE_PY, "seed_dossier"], cwd=BACKEND)
    if res.returncode == 0:
        print("✅  Base SQLite MedConnect alimentee avec succes.")
    else:
        print("❌  Erreur lors du seeding.")


def menu():
    banner()
    choices = {
        "1": ("🚀 Lancer MedConnect (Django REST API + SPA Web - Port 8000)", lambda: run_django(8000)),
        "2": ("🧪 Lancer la suite de tests Django REST (45 tests)",          run_django_tests),
        "3": ("🧪 Lancer la suite de tests pytest (23 tests)",              lambda: run_pytest(html=False)),
        "4": ("📄 Generer le rapport HTML interactif des tests",            lambda: run_pytest(html=True)),
        "5": ("🗄️  Reinitialiser la base SQLite de demo (seed_demo)",        reset_db_cmd),
        "6": ("🌐 Lancer le prototype Flask historique (Port 5000)",        run_flask),
        "0": ("Quitter",                                                    lambda: sys.exit(0)),
    }

    for k, (label, _) in choices.items():
        print(f"  [{k}]  {label}")
    print()

    choix = input("Votre choix [0-6] : ").strip()
    if choix in choices:
        print()
        choices[choix][1]()
    else:
        print("❌ Choix invalide.")


if __name__ == "__main__":
    os.chdir(ROOT)
    args = sys.argv[1:]

    if "--web" in args or "-w" in args:
        run_django(8000)
    elif "--flask" in args:
        run_flask()
    elif "--html" in args:
        sys.exit(run_pytest(html=True))
    elif "--tests" in args or "-t" in args:
        code1 = run_django_tests()
        code2 = run_pytest()
        sys.exit(code1 if code1 != 0 else code2)
    elif "--init-db" in args:
        reset_db_cmd()
    else:
        try:
            while True:
                menu()
                print()
                resp = input("Retour au menu principal ? [o/n] : ").strip().lower()
                if resp not in ("o", "oui", "y", "yes"):
                    break
                print()
        except KeyboardInterrupt:
            print("\n\nFermeture de MedConnect. A bientot !")
