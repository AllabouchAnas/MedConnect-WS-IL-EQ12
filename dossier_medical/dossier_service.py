"""
Service Dossier Médical — MedConnect
Module : Dossier Médical Informatisé
Auteur : Achraf AIT DAMNAT (Lead Tech / Architecte)

Règles métier à respecter :
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
        # TODO : valider le motif
        # TODO : créer et stocker la Consultation
        # TODO : retourner la Consultation créée
        raise NotImplementedError("À implémenter par Achraf AIT DAMNAT")

    # ------------------------------------------------------------------
    # Historique
    # ------------------------------------------------------------------

    def get_historique(self, patient_cin):
        """
        Retourne la liste des consultations d'un patient (peut être vide).
        """
        # TODO : filtrer self._consultations par patient_cin
        raise NotImplementedError("À implémenter par Achraf AIT DAMNAT")

    # ------------------------------------------------------------------
    # Modifier
    # ------------------------------------------------------------------

    def modifier_consultation(self, consult_id, **modifications):
        """
        Met à jour les champs d'une consultation existante.
        Lève ValueError si la consultation n'existe pas.
        """
        # TODO : récupérer, valider les champs, appliquer les modifications
        raise NotImplementedError("À implémenter par Achraf AIT DAMNAT")

    # ------------------------------------------------------------------
    # Supprimer
    # ------------------------------------------------------------------

    def supprimer_consultation(self, consult_id):
        """
        Supprime une consultation.
        Lève ValueError si elle n'existe pas.
        """
        # TODO : vérifier existence, supprimer de self._consultations
        raise NotImplementedError("À implémenter par Achraf AIT DAMNAT")

    # ------------------------------------------------------------------
    # Utilitaires
    # ------------------------------------------------------------------

    def nombre_consultations(self):
        """Retourne le nombre total de consultations enregistrées."""
        return len(self._consultations)
