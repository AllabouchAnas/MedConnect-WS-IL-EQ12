"""
Modèle Consultation — MedConnect
Module : Dossier Médical
Auteur : Achraf AIT DAMNAT (Lead Tech / Architecte)
"""


class Consultation:
    """Représente une consultation médicale."""

    _compteur = 1

    def __init__(self, patient_cin, medecin_id, date, motif,
                 tension="", poids=None, temperature=None,
                 pouls=None, diagnostic=""):
        self.id = Consultation._compteur
        Consultation._compteur += 1

        self.patient_cin = patient_cin
        self.medecin_id = medecin_id
        self.date = date               # Format : "YYYY-MM-DD"
        self.motif = motif             # Obligatoire
        self.tension = tension         # Ex: "12/8"
        self.poids = poids             # En kg
        self.temperature = temperature # En °C
        self.pouls = pouls             # En bpm
        self.diagnostic = diagnostic

    def __repr__(self):
        return (f"Consultation(id={self.id}, patient={self.patient_cin}, "
                f"date={self.date}, motif={self.motif})")

