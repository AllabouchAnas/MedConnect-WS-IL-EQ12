"""
Modèle RendezVous — MedConnect
Module : Gestion de l'Agenda
Auteur : Ahmed LAHMAINE (Product Owner / BA)
"""

# Cycle de statuts autorisé (dans l'ordre)
STATUTS_ORDONNES = [
    "Planifié",
    "Salle d'attente",
    "Consultation",
    "Terminé",
]


class RendezVous:
    """Représente un rendez-vous médical."""

    _compteur = 1  # Générateur d'ID auto-incrémenté

    def __init__(self, patient_cin, medecin_id, date_heure, motif=""):
        self.id = RendezVous._compteur
        RendezVous._compteur += 1

        self.patient_cin = patient_cin
        self.medecin_id = medecin_id
        self.date_heure = date_heure   # Format attendu : "YYYY-MM-DD HH:MM"
        self.motif = motif
        self.statut = "Planifié"       # Statut initial
        self.motif_annulation = None

    def __repr__(self):
        return (f"RendezVous(id={self.id}, patient={self.patient_cin}, "
                f"medecin={self.medecin_id}, date={self.date_heure}, "
                f"statut={self.statut})")

