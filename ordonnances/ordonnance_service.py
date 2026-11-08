"""
Service Ordonnances — MedConnect
Module : Gestion des Ordonnances
Auteur : ABDELLAH RAHEL (Responsable QA)

Règles métier à respecter :
  - Alerte allergie si un médicament est dans la liste des allergies du patient
  - Une ordonnance validée devient non modifiable
  - Chaque ordonnance peut contenir plusieurs lignes (médicaments)
"""

from ordonnances.ordonnance import Ordonnance, LigneOrdonnance


class OrdonnanceService:
    """Service de gestion des ordonnances — stockage en mémoire."""

    def __init__(self):
        # Dictionnaire interne : id -> Ordonnance
        self._ordonnances = {}

    # ------------------------------------------------------------------
    # Créer une ordonnance
    # ------------------------------------------------------------------

    def creer_ordonnance(self, patient_cin, medecin_id, date):
        """
        Crée une nouvelle ordonnance vide (sans lignes).
        Retourne l'ordonnance créée.
        """
        # TODO : créer et stocker l'Ordonnance
        # TODO : retourner l'Ordonnance
        raise NotImplementedError("À implémenter par ABDELLAH RAHEL")

    # ------------------------------------------------------------------
    # Ajouter une ligne (médicament)
    # ------------------------------------------------------------------

    def ajouter_ligne(self, ordonnance_id, medicament, dosage, posologie,
                      duree_jours, allergies_patient=None):
        """
        Ajoute un médicament à une ordonnance.

        Lève ValueError si :
          - L'ordonnance est déjà validée
          - Le médicament figure dans la liste allergies_patient
        """
        # TODO : vérifier que l'ordonnance existe et n'est pas validée
        # TODO : vérifier conflit d'allergie (comparaison insensible à la casse)
        # TODO : créer LigneOrdonnance et l'ajouter à ordonnance.lignes
        raise NotImplementedError("À implémenter par ABDELLAH RAHEL")

    # ------------------------------------------------------------------
    # Valider
    # ------------------------------------------------------------------

    def valider_ordonnance(self, ordonnance_id):
        """
        Valide l'ordonnance — la rend non modifiable.
        Lève ValueError si l'ordonnance n'existe pas.
        """
        # TODO : passer est_validee à True
        raise NotImplementedError("À implémenter par ABDELLAH RAHEL")

    # ------------------------------------------------------------------
    # Modifier
    # ------------------------------------------------------------------

    def modifier_ordonnance(self, ordonnance_id, **modifications):
        """
        Modifie les champs d'une ordonnance.
        Lève ValueError si l'ordonnance est déjà validée.
        """
        # TODO : vérifier est_validee, appliquer modifications
        raise NotImplementedError("À implémenter par ABDELLAH RAHEL")

    # ------------------------------------------------------------------
    # Utilitaires
    # ------------------------------------------------------------------

    def rechercher_ordonnance(self, ordonnance_id):
        """
        Retourne l'ordonnance ou lève ValueError si introuvable.
        """
        # TODO : chercher dans self._ordonnances
        raise NotImplementedError("À implémenter par ABDELLAH RAHEL")

    def nombre_ordonnances(self):
        """Retourne le nombre total d'ordonnances."""
        return len(self._ordonnances)
