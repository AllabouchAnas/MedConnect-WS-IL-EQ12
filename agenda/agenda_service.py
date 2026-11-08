"""
Service Agenda — MedConnect
Module : Gestion des Rendez-vous
Auteur : Ahmed LAHMAINE (Product Owner / BA)

Règles métier implémentées :
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
        # Vérification chevauchement : même médecin, même créneau, non annulé
        for rdv in self._rendez_vous.values():
            if (rdv.medecin_id == medecin_id
                    and rdv.date_heure == date_heure
                    and rdv.statut != "Annulé"):
                raise ValueError(
                    f"Le médecin '{medecin_id}' a déjà un rendez-vous "
                    f"le {date_heure}."
                )

        rdv = RendezVous(patient_cin, medecin_id, date_heure, motif)
        self._rendez_vous[rdv.id] = rdv
        return rdv

    # ------------------------------------------------------------------
    # Avancer le statut
    # ------------------------------------------------------------------

    def avancer_statut(self, rdv_id):
        """
        Fait avancer le statut du RDV au suivant dans le cycle.
        Lève ValueError si le RDV est déjà Terminé ou Annulé.
        """
        rdv = self.rechercher_rdv(rdv_id)

        if rdv.statut == "Annulé":
            raise ValueError("Impossible d'avancer le statut d'un RDV annulé.")

        if rdv.statut == "Terminé":
            raise ValueError("Le rendez-vous est déjà terminé.")

        index_actuel = STATUTS_ORDONNES.index(rdv.statut)
        rdv.statut = STATUTS_ORDONNES[index_actuel + 1]
        return rdv

    # ------------------------------------------------------------------
    # Annuler
    # ------------------------------------------------------------------

    def annuler_rdv(self, rdv_id, motif_annulation=""):
        """
        Annule un rendez-vous (conserve l'historique, ne supprime pas).
        Lève ValueError si le RDV n'existe pas.
        """
        rdv = self.rechercher_rdv(rdv_id)
        rdv.statut = "Annulé"
        rdv.motif_annulation = motif_annulation
        return rdv

    # ------------------------------------------------------------------
    # Recherche
    # ------------------------------------------------------------------

    def rechercher_rdv(self, rdv_id):
        """
        Retourne le RDV correspondant à l'ID.
        Lève ValueError si introuvable.
        """
        if rdv_id not in self._rendez_vous:
            raise ValueError(f"Aucun rendez-vous trouvé avec l'ID '{rdv_id}'.")
        return self._rendez_vous[rdv_id]

    # ------------------------------------------------------------------
    # Utilitaires
    # ------------------------------------------------------------------

    def nombre_rdv(self):
        """Retourne le nombre total de rendez-vous (y compris annulés)."""
        return len(self._rendez_vous)
