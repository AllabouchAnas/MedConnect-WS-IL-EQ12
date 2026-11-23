"""HTML views for the medical dossier module."""

from web.layout import esc, page


def consultation_fields(values):
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


def records_page(store, notice=""):
    rows = store.patients()
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
    <h1>Dossiers médicaux</h1>
    <p class="lead">Recherchez un dossier par CIN, ou ouvrez un patient déjà suivi.</p>
    <form class="toolbar" method="get" action="/patients">
      <div class="search-field">
        <label for="cin">CIN</label>
        <input id="cin" name="cin" required placeholder="AB123456">
      </div>
      <button type="submit">Ouvrir le dossier</button>
    </form>
    <section class="card">
      <h2>Dossiers ouverts</h2>
      <div class="table-wrap">{listing}</div>
    </section>
    """
    return page("Dossiers médicaux", body, notice)


def patient_page(store, cin, notice=""):
    history = store.historique(cin)
    if not history:
        listing = '<p class="empty">Ce patient n\'a aucune consultation.</p>'
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
              <h2 class="card-title">{esc(item.date)} — {esc(item.motif)}</h2>
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
    body = f"""
    <h1>Nouvelle consultation</h1>
    <p class="lead">Le motif est obligatoire. Les constantes sont facultatives.</p>
    <form class="card" method="post" action="/consultations">
      {consultation_fields(values or {})}
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
    def optional_number(raw):
        text = (raw or "").strip().replace(",", ".")
        if text == "":
            return None
        return float(text)

    try:
        poids = optional_number(values.get("poids"))
        temperature = optional_number(values.get("temperature"))
        pouls = optional_number(values.get("pouls"))
    except ValueError as error:
        raise ValueError(
            "Poids, température et pouls doivent être des nombres."
        ) from error
    return {
        "patient_cin": values.get("patient_cin", "").strip(),
        "medecin_id": values.get("medecin_id", "").strip(),
        "date": values.get("date", "").strip(),
        "motif": values.get("motif", "").strip(),
        "tension": values.get("tension", "").strip(),
        "poids": poids,
        "temperature": temperature,
        "pouls": int(pouls) if pouls is not None and pouls.is_integer() else pouls,
        "diagnostic": values.get("diagnostic", "").strip(),
    }
