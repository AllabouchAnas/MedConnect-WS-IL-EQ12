"""MedConnect web application entry point and central router.

Run from the project root with ``python app.py``, then open
http://127.0.0.1:8765.
"""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse

from dossier_medical import views as dossier_views
from dossier_medical.store import DossierStore
from web.layout import page

HOST = "127.0.0.1"
PORT = 8765
ROOT = Path(__file__).resolve().parent
STORE = DossierStore(ROOT / "data" / "dossier.json")
STYLESHEET = ROOT / "web" / "static" / "styles.css"


def home_page(notice=""):
    patients_count = len(STORE.patients())
    consultations_count = STORE.service.nombre_consultations()
    body = f"""
    <h1>Bienvenue sur MedConnect</h1>
    <p class="lead">Votre espace de gestion pour le cabinet médical.</p>

    <section class="stat-grid" aria-label="Activité du dossier médical">
      <article class="card stat-card">
        <strong>{patients_count}</strong>
        <span>Patients suivis</span>
      </article>
      <article class="card stat-card">
        <strong>{consultations_count}</strong>
        <span>Consultations enregistrées</span>
      </article>
    </section>

    <h2>Modules</h2>
    <section class="module-grid" aria-label="Modules MedConnect">
      <article class="card module-card">
        <h2 class="card-title">Patients</h2>
        <p>Consultez les dossiers patients.</p>
        <span class="module-status">Interface en preparation</span>
      </article>
      <article class="card module-card">
        <h2 class="card-title">Agenda</h2>
        <p>Gérez les rendez-vous du cabinet.</p>
        <span class="module-status">Interface en preparation</span>
      </article>
      <article class="card module-card">
        <h2 class="card-title">Dossier médical</h2>
        <p>Consultez les historiques et les consultations.</p>
        <a class="button secondary" href="/dossier-medical">Ouvrir les dossiers</a>
      </article>
      <article class="card module-card">
        <h2 class="card-title">Ordonnances</h2>
        <p>Gérez les prescriptions médicales.</p>
        <span class="module-status">Interface en preparation</span>
      </article>
    </section>
    """
    return page("Accueil", body, notice)


class AppHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        print("[%s] %s" % (self.log_date_time_string(), fmt % args))

    def send_content(self, content, content_type, status=200):
        data = content if isinstance(content, bytes) else content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def send_html(self, content, status=200):
        self.send_content(content, "text/html; charset=utf-8", status)

    def redirect(self, location):
        self.send_response(303)
        self.send_header("Location", location)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def read_body(self):
        length = int(self.headers.get("Content-Length", "0"))
        parsed = parse_qs(self.rfile.read(length).decode("utf-8"), keep_blank_values=True)
        return {key: values[0] if values else "" for key, values in parsed.items()}

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        query = parse_qs(parsed.query)
        notice = query.get("erreur", [""])[0]

        if path == "/static/styles.css":
            try:
                stylesheet = STYLESHEET.read_bytes()
            except OSError:
                self.send_html(home_page("La feuille de style est indisponible."), status=500)
                return
            self.send_content(stylesheet, "text/css; charset=utf-8")
            return

        if path == "/":
            self.send_html(home_page(notice))
            return

        if path == "/dossier-medical":
            self.send_html(dossier_views.records_page(STORE, notice))
            return

        if path == "/patients":
            cin = query.get("cin", [""])[0].strip()
            if not cin:
                self.redirect("/?erreur=Indiquez+un+CIN.")
                return
            self.redirect(f"/patients/{quote(cin, safe='')}")
            return

        if path.startswith("/patients/"):
            cin = unquote(path.split("/", 2)[2])
            self.send_html(dossier_views.patient_page(STORE, cin, notice))
            return

        if path == "/consultations/nouvelle":
            values = {"patient_cin": query.get("patient_cin", [""])[0]}
            self.send_html(dossier_views.new_page(values, notice))
            return

        if path.startswith("/consultations/"):
            consult_id = path.split("/", 2)[2]
            try:
                consultation = STORE.obtenir(consult_id)
            except (TypeError, ValueError) as error:
                self.send_html(home_page(str(error)), status=404)
                return
            self.send_html(dossier_views.edit_page(consultation, notice))
            return

        self.send_html(home_page("Page introuvable."), status=404)

    def do_POST(self):
        path = urlparse(self.path).path.rstrip("/") or "/"
        values = self.read_body()

        if path == "/consultations":
            try:
                fields = dossier_views.read_consultation_form(values)
                if not fields["patient_cin"] or not fields["medecin_id"] or not fields["date"]:
                    raise ValueError("CIN, médecin et date sont obligatoires.")
                consultation = STORE.service.ajouter_consultation(**fields)
                STORE.save()
            except ValueError as error:
                self.send_html(dossier_views.new_page(values, str(error)), status=400)
                return
            self.redirect(f"/patients/{quote(consultation.patient_cin, safe='')}")
            return

        if path.startswith("/consultations/") and path.endswith("/supprimer"):
            consult_id = path.split("/")[2]
            try:
                consultation = STORE.service.supprimer_consultation(int(consult_id))
                STORE.save()
            except ValueError as error:
                self.send_html(home_page(str(error)), status=404)
                return
            self.redirect(f"/patients/{quote(consultation.patient_cin, safe='')}")
            return

        if path.startswith("/consultations/"):
            consult_id = path.split("/", 2)[2]
            try:
                fields = dossier_views.read_consultation_form(values)
                if not fields["patient_cin"] or not fields["medecin_id"] or not fields["date"]:
                    raise ValueError("CIN, médecin et date sont obligatoires.")
                consultation = STORE.service.modifier_consultation(int(consult_id), **fields)
                STORE.save()
            except ValueError as error:
                try:
                    current = STORE.obtenir(consult_id)
                except ValueError:
                    self.send_html(home_page(str(error)), status=404)
                    return
                self.send_html(dossier_views.edit_page(current, str(error)), status=400)
                return
            self.redirect(f"/patients/{quote(consultation.patient_cin, safe='')}")
            return

        self.send_html(home_page("Action introuvable."), status=404)


def main():
    server = ThreadingHTTPServer((HOST, PORT), AppHandler)
    print(f"MedConnect : http://{HOST}:{PORT}")
    print("Arrêt : Ctrl+C")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nArrêt du serveur.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
