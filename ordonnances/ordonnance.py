"""
Modèles Ordonnance & LigneOrdonnance — MedConnect
Module : Gestion des Ordonnances
Auteur : ABDELLAH RAHEL (Responsable QA)
"""


class LigneOrdonnance:
    """Représente une ligne (un médicament) dans une ordonnance."""

    def __init__(self, medicament, dosage, posologie, duree_jours):
        self.medicament = medicament   # DCI (Dénomination Commune Internationale)
        self.dosage = dosage           # Ex: "500mg"
        self.posologie = posologie     # Ex: "2 fois par jour"
        self.duree_jours = duree_jours # Ex: 7

    def __repr__(self):
        return (f"Ligne({self.medicament} {self.dosage} — "
                f"{self.posologie} pendant {self.duree_jours}j)")


class Ordonnance:
    """Représente une ordonnance médicale."""

    _compteur = 1

    def __init__(self, patient_cin, medecin_id, date):
        self.id = Ordonnance._compteur
        Ordonnance._compteur += 1

        self.patient_cin = patient_cin
        self.medecin_id = medecin_id
        self.date = date               # Format : "YYYY-MM-DD"
        self.lignes = []               # Liste de LigneOrdonnance
        self.est_validee = False       # Verrou : True = non modifiable

    def __repr__(self):
        return (f"Ordonnance(id={self.id}, patient={self.patient_cin}, "
                f"validee={self.est_validee}, lignes={len(self.lignes)})")

