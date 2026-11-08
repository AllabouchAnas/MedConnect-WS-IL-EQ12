"""
Service Dossier Médical — MedConnect
Module : Dossier Médical Informatisé
Auteur : Achraf AIT DAMNAT (Lead Tech / Architecte)

Règles métier implémentées :
  - Le motif est obligatoire pour toute consultation
  - L'historique par patient retourne toutes ses consultations
  - Modification uniquement si la consultation existe
  - Suppression uniquement si la consultation existe
"""

from dossier_medical.consultation import Consultation


class DossierService:
    """Service de gestion des consultations — stockage en mémoire."""

    def __init__(self):
        # Dictionnaire interne : id -> Consultation
        self._consultations = {}

    # ------------------------------------------------------------------
    # Ajouter une consultation
    # ------------------------------------------------------------------

    def ajouter_consultation(self, patient_cin, medecin_id, date, motif,
                             tension="", poids=None, temperature=None,
                             pouls=None, diagnostic=""):
        """
        Enregistre une nouvelle consultation.

        Lève ValueError si :
          - Le motif est vide
        """
        if not motif or str(motif).strip() == "":
            raise ValueError("Le champ 'motif' est obligatoire.")

        consultation = Consultation(
            patient_cin, medecin_id, date, motif,
            tension, poids, temperature, pouls, diagnostic
        )
        self._consultations[consultation.id] = consultation
        return consultation

    # ------------------------------------------------------------------
    # Historique
    # ------------------------------------------------------------------

    def get_historique(self, patient_cin):
        """
        Retourne la liste des consultations d'un patient (peut être vide).
        """
        return [
            c for c in self._consultations.values()
            if c.patient_cin == patient_cin
        ]

    # ------------------------------------------------------------------
    # Modifier
    # ------------------------------------------------------------------

    def modifier_consultation(self, consult_id, **modifications):
        """
        Met à jour les champs d'une consultation existante.
        Lève ValueError si la consultation n'existe pas.
        """
        if consult_id not in self._consultations:
            raise ValueError(
                f"Aucune consultation trouvée avec l'ID '{consult_id}'."
            )
        consultation = self._consultations[consult_id]

        champs_autorisés = {
            "motif", "tension", "poids", "temperature",
            "pouls", "diagnostic", "date"
        }
        for champ, valeur in modifications.items():
            if champ not in champs_autorisés:
                raise ValueError(f"Champ inconnu : '{champ}'.")
            setattr(consultation, champ, valeur)

        return consultation

    # ------------------------------------------------------------------
    # Supprimer
    # ------------------------------------------------------------------

    def supprimer_consultation(self, consult_id):
        """
        Supprime une consultation.
        Lève ValueError si elle n'existe pas.
        """
        if consult_id not in self._consultations:
            raise ValueError(
                f"Aucune consultation trouvée avec l'ID '{consult_id}'."
            )
        consultation = self._consultations.pop(consult_id)
        return consultation

    # ------------------------------------------------------------------
    # Utilitaires
    # ------------------------------------------------------------------

    def nombre_consultations(self):
        """Retourne le nombre total de consultations enregistrées."""
        return len(self._consultations)
