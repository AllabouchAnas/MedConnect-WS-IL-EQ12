"""
Service Agenda — MedConnect
Module : Gestion des Rendez-vous
Auteur : Ahmed LAHMAINE (Product Owner / BA)

Règles métier à respecter :
  - Pas de chevauchement pour le même médecin au même créneau
  - Cycle de statuts : Planifié → Salle d'attente → Consultation → Terminé
  - Annulation possible à tout moment (conserve l'historique)
  - Recherche par ID
"""

from agenda.rendez_vous import RendezVous, STATUTS_ORDONNES


class AgendaService:
    """Service de gestion des rendez-vous — stockage en mémoire."""

    def __init__(self):
        # Dictionnaire interne : id -> RendezVous
        self._rendez_vous = {}

    # ------------------------------------------------------------------
    # Planifier
    # ------------------------------------------------------------------

    def planifier_rdv(self, patient_cin, medecin_id, date_heure, motif=""):
        """
        Planifie un nouveau rendez-vous.

        Lève ValueError si :
          - Un RDV non annulé existe déjà pour ce médecin à cette date/heure
        """
        # TODO : vérifier les chevauchements pour ce médecin à cette date_heure
        # TODO : créer et stocker le RendezVous
        # TODO : retourner le RendezVous créé
        raise NotImplementedError("À implémenter par Ahmed LAHMAINE")

    # ------------------------------------------------------------------
    # Avancer le statut
    # ------------------------------------------------------------------

    def avancer_statut(self, rdv_id):
        """
        Fait avancer le statut du RDV au suivant dans le cycle.
        Lève ValueError si le RDV est déjà Terminé ou Annulé.
        """
        # TODO : récupérer le RDV, trouver le prochain statut, l'appliquer
        raise NotImplementedError("À implémenter par Ahmed LAHMAINE")

    # ------------------------------------------------------------------
    # Annuler
    # ------------------------------------------------------------------

    def annuler_rdv(self, rdv_id, motif_annulation=""):
        """
        Annule un rendez-vous (conserve l'historique, ne supprime pas).
        Lève ValueError si le RDV n'existe pas.
        """
        # TODO : passer statut à "Annulé", enregistrer motif_annulation
        raise NotImplementedError("À implémenter par Ahmed LAHMAINE")

    # ------------------------------------------------------------------
    # Recherche
    # ------------------------------------------------------------------

    def rechercher_rdv(self, rdv_id):
        """
        Retourne le RDV correspondant à l'ID.
        Lève ValueError si introuvable.
        """
        # TODO : chercher dans self._rendez_vous
        raise NotImplementedError("À implémenter par Ahmed LAHMAINE")

    # ------------------------------------------------------------------
    # Utilitaires
    # ------------------------------------------------------------------

    def nombre_rdv(self):
        """Retourne le nombre total de rendez-vous (y compris annulés)."""
        return len(self._rendez_vous)
