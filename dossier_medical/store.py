"""Persistance fichier du dossier médical.

Les tests unitaires continuent d'utiliser un DossierService vide en mémoire.
L'application charge et enregistre les consultations dans un fichier JSON.
"""

import json
from pathlib import Path

from dossier_medical.consultation import Consultation
from dossier_medical.dossier_service import DossierService


class DossierStore:
    """Enveloppe DossierService avec sauvegarde sur disque."""

    def __init__(self, path):
        self.path = Path(path)
        self.service = DossierService()
        self.load()

    def load(self):
        self.service = DossierService()
        Consultation._compteur = 1
        if not self.path.exists():
            return

        data = json.loads(self.path.read_text(encoding="utf-8"))
        max_id = 0
        for item in data.get("consultations", []):
            consultation = Consultation(
                item["patient_cin"],
                item["medecin_id"],
                item["date"],
                item["motif"],
                item.get("tension") or "",
                item.get("poids"),
                item.get("temperature"),
                item.get("pouls"),
                item.get("diagnostic") or "",
            )
            consultation.id = int(item["id"])
            self.service._consultations[consultation.id] = consultation
            max_id = max(max_id, consultation.id)
        Consultation._compteur = max_id + 1

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        consultations = []
        for consultation in self.service._consultations.values():
            consultations.append({
                "id": consultation.id,
                "patient_cin": consultation.patient_cin,
                "medecin_id": consultation.medecin_id,
                "date": consultation.date,
                "motif": consultation.motif,
                "tension": consultation.tension,
                "poids": consultation.poids,
                "temperature": consultation.temperature,
                "pouls": consultation.pouls,
                "diagnostic": consultation.diagnostic,
            })
        consultations.sort(key=lambda item: item["id"])
        payload = json.dumps(
            {"consultations": consultations},
            ensure_ascii=False,
            indent=2,
        )
        self.path.write_text(payload + "\n", encoding="utf-8")

    def patients(self):
        """Patients ayant au moins une consultation, du plus récent au plus ancien."""
        grouped = {}
        for consultation in self.service._consultations.values():
            grouped.setdefault(consultation.patient_cin, []).append(consultation)
        rows = []
        for cin, consultations in grouped.items():
            consultations.sort(key=lambda item: (item.date, item.id), reverse=True)
            rows.append({
                "cin": cin,
                "consultations": consultations,
                "derniere": consultations[0],
            })
        rows.sort(key=lambda row: (row["derniere"].date, row["cin"]), reverse=True)
        return rows

    def historique(self, patient_cin):
        consultations = self.service.get_historique(patient_cin)
        return sorted(consultations, key=lambda item: (item.date, item.id), reverse=True)

    def obtenir(self, consult_id):
        consultation = self.service._consultations.get(int(consult_id))
        if consultation is None:
            raise ValueError(
                f"Aucune consultation trouvée avec l'ID '{consult_id}'."
            )
        return consultation
