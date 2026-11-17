"""Application Dossier médical MedConnect.

Lancer depuis la racine du projet :

    python app.py

Puis ouvrir http://127.0.0.1:8765
"""

import html
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from dossier_medical.store import DossierStore

HOST = "127.0.0.1"
PORT = 8765
ROOT = Path(__file__).resolve().parent
STORE = DossierStore(ROOT / "data" / "dossier.json")


def esc(value):
    if value is None:
        return ""
    return html.escape(str(value))


def optional_number(raw):
    text = (raw or "").strip().replace(",", ".")
    if text == "":
        return None
    return float(text)


def form_values(body):
    parsed = parse_qs(body.decode("utf-8"), keep_blank_values=True)
    return {key: values[0] if values else "" for key, values in parsed.items()}


def page(title, body, notice=""):
    alert = ""
    if notice:
        alert = f'<p class="notice">{esc(notice)}</p>'
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)} — MedConnect</title>
  <style>
    :root {{
      --ink: #1c2430;
      --muted: #5c6b7a;
      --line: #d7e0e7;
      --paper: #f4f7f8;
      --card: #ffffff;
      --teal: #0f6e6b;
      --teal-dark: #0b524f;
      --danger: #9d2c2c;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Segoe UI", Calibri, sans-serif;
      color: var(--ink);
      background: var(--paper);
    }}
    header {{
      background: var(--teal-dark);
      color: white;
      padding: 18px 28px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 16px;
    }}
    header a {{ color: white; text-decoration: none; }}
    header p {{ margin: 4px 0 0; color: #c9e4e2; font-size: 14px; }}
    main {{ max-width: 980px; margin: 0 auto; padding: 28px 20px 64px; }}
    h1 {{ font-size: 28px; margin: 0 0 8px; }}
    h2 {{ font-size: 18px; margin: 0 0 12px; }}
    .lead {{ color: var(--muted); margin: 0 0 22px; }}
    .notice {{
      background: #fff4f2;
      border: 1px solid #f0c2bc;
      color: var(--danger);
      padding: 12px 14px;
      border-radius: 8px;
    }}
    .toolbar, .card, form.card {{
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 18px;
      margin-bottom: 16px;
    }}
    .toolbar {{ display: flex; gap: 10px; align-items: end; flex-wrap: wrap; }}
    label {{ display: block; font-size: 13px; color: var(--muted); margin-bottom: 6px; }}
    input, textarea {{
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px 12px;
      font: inherit;
      color: var(--ink);
      background: white;
    }}
    textarea {{ min-height: 90px; resize: vertical; }}
    .grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }}
    .span-2 {{ grid-column: span 2; }}
    button, .button {{
      display: inline-block;
      background: var(--teal);
      color: white;
      border: 0;
      border-radius: 8px;
      padding: 10px 16px;
      font: inherit;
      text-decoration: none;
      cursor: pointer;
    }}
    button.secondary, .button.secondary {{
      background: white;
      color: var(--teal-dark);
      border: 1px solid var(--line);
    }}
    button.danger {{ background: var(--danger); }}
    .actions {{ display: flex; gap: 10px; flex-wrap: wrap; margin-top: 8px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ text-align: left; padding: 12px 10px; border-bottom: 1px solid var(--line); vertical-align: top; }}
    th {{ font-size: 12px; letter-spacing: 0.04em; text-transform: uppercase; color: var(--muted); }}
    .meta {{ color: var(--muted); font-size: 13px; }}
    .empty {{ color: var(--muted); padding: 8px 0 0; }}
    @media (max-width: 720px) {{
      .grid, .span-2 {{ grid-template-columns: 1fr; }}
      .span-2 {{ grid-column: auto; }}
      header {{ align-items: flex-start; flex-direction: column; }}
    }}
  </style>
</head>
<body>
  <header>
    <div>
      <a href="/"><strong>MedConnect</strong></a>
      <p>Dossier médical informatisé</p>
    </div>
    <a class="button" href="/consultations/nouvelle">Nouvelle consultation</a>
  </header>
  <main>
    {alert}
    {body}
  </main>
</body>
</html>"""


def consultation_fields(values, error=""):
    def val(name):
        return esc(values.get(name, ""))

    return f"""
    <div class="grid">
      <div>
        <label for="patient_cin">CIN du patient</label>
        <input id="patient_cin" name="patient_cin" required value="{val("patient_cin")}">
      </div>
      <div>
        <label for="medecin_id">Identifiant médecin</label>
        <input id="medecin_id" name="medecin_id" required value="{val("medecin_id")}">
      </div>
      <div>
        <label for="date">Date</label>
        <input id="date" name="date" type="date" required value="{val("date")}">
      </div>
      <div>
        <label for="tension">Tension</label>
        <input id="tension" name="tension" placeholder="12/8" value="{val("tension")}">
      </div>
      <div>
        <label for="poids">Poids (kg)</label>
        <input id="poids" name="poids" inputmode="decimal" value="{val("poids")}">
      </div>
      <div>
        <label for="temperature">Température (°C)</label>
        <input id="temperature" name="temperature" inputmode="decimal" value="{val("temperature")}">
      </div>
      <div>
        <label for="pouls">Pouls (bpm)</label>
        <input id="pouls" name="pouls" inputmode="decimal" value="{val("pouls")}">
      </div>
      <div class="span-2">
        <label for="motif">Motif</label>
        <input id="motif" name="motif" required value="{val("motif")}">
      </div>
      <div class="span-2">
        <label for="diagnostic">Diagnostic</label>
        <textarea id="diagnostic" name="diagnostic">{val("diagnostic")}</textarea>
      </div>
    </div>
    """


def home_page(notice=""):
    rows = STORE.patients()
    if not rows:
        listing = '<p class="empty">Aucune consultation enregistrée. Créez la première fiche.</p>'
    else:
        body_rows = []
        for row in rows:
            last = row["derniere"]
            body_rows.append(
                "<tr>"
                f'<td><a href="/patients/{esc(row["cin"])}">{esc(row["cin"])}</a></td>'
                f"<td>{len(row['consultations'])}</td>"
                f"<td>{esc(last.date)}</td>"
                f"<td>{esc(last.motif)}</td>"
                "</tr>"
            )
        listing = (
            "<table><thead><tr><th>Patient</th><th>Consultations</th>"
            "<th>Dernière date</th><th>Dernier motif</th></tr></thead><tbody>"
            + "".join(body_rows)
            + "</tbody></table>"
        )
    body = f"""
    <h1>Patients</h1>
    <p class="lead">Recherchez un dossier par CIN, ou ouvrez un patient déjà suivi.</p>
    <form class="toolbar" method="get" action="/patients">
      <div style="flex:1; min-width:220px;">
        <label for="cin">CIN</label>
        <input id="cin" name="cin" required placeholder="AB123456">
      </div>
      <button type="submit">Ouvrir le dossier</button>
    </form>
    <section class="card">
      <h2>Dossiers ouverts</h2>
      {listing}
    </section>
    """
    return page("Patients", body, notice)


def patient_page(cin, notice=""):
    history = STORE.historique(cin)
    if not history:
        listing = "<p class=\"empty\">Ce patient n'a aucune consultation.</p>"
    else:
        cards = []
        for item in history:
            vitals = " · ".join(
                part for part in [
                    f"Tension {item.tension}" if item.tension else "",
                    f"Poids {item.poids} kg" if item.poids is not None else "",
                    f"Température {item.temperature} °C" if item.temperature is not None else "",
                    f"Pouls {item.pouls}" if item.pouls is not None else "",
                ] if part
            )
            cards.append(f"""
            <article class="card">
              <h2>{esc(item.date)} — {esc(item.motif)}</h2>
              <p class="meta">Consultation #{item.id} · Médecin {esc(item.medecin_id)}</p>
              <p>{esc(item.diagnostic) or "Diagnostic non renseigné."}</p>
              <p class="meta">{esc(vitals)}</p>
              <div class="actions">
                <a class="button secondary" href="/consultations/{item.id}">Modifier</a>
                <form method="post" action="/consultations/{item.id}/supprimer">
                  <button class="danger" type="submit">Supprimer</button>
                </form>
              </div>
            </article>
            """)
        listing = "".join(cards)
    body = f"""
    <h1>Dossier {esc(cin)}</h1>
    <p class="lead">{len(history)} consultation(s) enregistrée(s).</p>
    <p><a class="button" href="/consultations/nouvelle?patient_cin={esc(cin)}">Ajouter une consultation</a></p>
    {listing}
    """
    return page(f"Dossier {cin}", body, notice)


def new_page(values=None, notice=""):
    values = values or {}
    body = f"""
    <h1>Nouvelle consultation</h1>
    <p class="lead">Le motif est obligatoire. Les constantes sont facultatives.</p>
    <form class="card" method="post" action="/consultations">
      {consultation_fields(values)}
      <div class="actions"><button type="submit">Enregistrer</button></div>
    </form>
    """
    return page("Nouvelle consultation", body, notice)


def edit_page(consultation, notice=""):
    values = {
        "patient_cin": consultation.patient_cin,
        "medecin_id": consultation.medecin_id,
        "date": consultation.date,
        "tension": consultation.tension,
        "poids": "" if consultation.poids is None else consultation.poids,
        "temperature": "" if consultation.temperature is None else consultation.temperature,
        "pouls": "" if consultation.pouls is None else consultation.pouls,
        "motif": consultation.motif,
        "diagnostic": consultation.diagnostic,
    }
    body = f"""
    <h1>Modifier la consultation #{consultation.id}</h1>
    <p class="lead">Patient {esc(consultation.patient_cin)}</p>
    <form class="card" method="post" action="/consultations/{consultation.id}">
      {consultation_fields(values)}
      <div class="actions">
        <button type="submit">Enregistrer les modifications</button>
        <a class="button secondary" href="/patients/{esc(consultation.patient_cin)}">Retour au dossier</a>
      </div>
    </form>
    """
    return page(f"Consultation {consultation.id}", body, notice)


def read_consultation_form(values):
    try:
        poids = optional_number(values.get("poids"))
        temperature = optional_number(values.get("temperature"))
        pouls = optional_number(values.get("pouls"))
    except ValueError:
        raise ValueError("Poids, température et pouls doivent être des nombres.")
    return {
        "patient_cin": values.get("patient_cin", "").strip(),
        "medecin_id": values.get("medecin_id", "").strip(),
        "date": values.get("date", "").strip(),
        "motif": values.get("motif", "").strip(),
        "tension": values.get("tension", "").strip(),
        "poids": poids,
        "temperature": temperature,
        "pouls": int(pouls) if pouls is not None and float(pouls).is_integer() else pouls,
        "diagnostic": values.get("diagnostic", "").strip(),
    }


class AppHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        print("[%s] %s" % (self.log_date_time_string(), fmt % args))

    def send_html(self, content, status=200):
        data = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def redirect(self, location):
        self.send_response(303)
        self.send_header("Location", location)
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        query = parse_qs(parsed.query)
        notice = query.get("erreur", [""])[0]

        if path == "/":
            self.send_html(home_page(notice))
            return

        if path == "/patients":
            cin = query.get("cin", [""])[0].strip()
            if not cin:
                self.redirect("/?erreur=Indiquez+un+CIN.")
                return
            self.redirect(f"/patients/{cin}")
            return

        if path.startswith("/patients/"):
            cin = path.split("/", 2)[2]
            self.send_html(patient_page(cin, notice))
            return

        if path == "/consultations/nouvelle":
            values = {"patient_cin": query.get("patient_cin", [""])[0]}
            self.send_html(new_page(values, notice))
            return

        if path.startswith("/consultations/"):
            consult_id = path.split("/", 2)[2]
            try:
                consultation = STORE.obtenir(consult_id)
            except ValueError as error:
                self.send_html(home_page(str(error)), status=404)
                return
            self.send_html(edit_page(consultation, notice))
            return

        self.send_html(home_page("Page introuvable."), status=404)

    def read_body(self):
        length = int(self.headers.get("Content-Length", "0"))
        return form_values(self.rfile.read(length))

    def do_POST(self):
        path = urlparse(self.path).path.rstrip("/") or "/"
        values = self.read_body()

        if path == "/consultations":
            try:
                fields = read_consultation_form(values)
                if not fields["patient_cin"] or not fields["medecin_id"] or not fields["date"]:
                    raise ValueError("CIN, médecin et date sont obligatoires.")
                consultation = STORE.service.ajouter_consultation(**fields)
                STORE.save()
            except ValueError as error:
                self.send_html(new_page(values, str(error)), status=400)
                return
            self.redirect(f"/patients/{consultation.patient_cin}")
            return

        if path.startswith("/consultations/") and path.endswith("/supprimer"):
            consult_id = path.split("/")[2]
            try:
                consultation = STORE.service.supprimer_consultation(int(consult_id))
                STORE.save()
            except ValueError as error:
                self.send_html(home_page(str(error)), status=404)
                return
            self.redirect(f"/patients/{consultation.patient_cin}")
            return

        if path.startswith("/consultations/"):
            consult_id = path.split("/", 2)[2]
            try:
                fields = read_consultation_form(values)
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
                self.send_html(edit_page(current, str(error)), status=400)
                return
            self.redirect(f"/patients/{consultation.patient_cin}")
            return

        self.send_html(home_page("Action introuvable."), status=404)


def main():
    server = ThreadingHTTPServer((HOST, PORT), AppHandler)
    print(f"MedConnect dossier médical : http://{HOST}:{PORT}")
    print("Arrêt : Ctrl+C")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nArrêt du serveur.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
