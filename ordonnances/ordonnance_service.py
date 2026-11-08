"""
Service Ordonnances — MedConnect
Module : Gestion des Ordonnances
Auteur : ABDELLAH RAHEL (Responsable QA)

Règles métier implémentées :
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
        ordonnance = Ordonnance(patient_cin, medecin_id, date)
        self._ordonnances[ordonnance.id] = ordonnance
        return ordonnance

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
        ordonnance = self.rechercher_ordonnance(ordonnance_id)

        if ordonnance.est_validee:
            raise ValueError(
                "Impossible d'ajouter un médicament à une ordonnance déjà validée."
            )

        # Vérification allergie — comparaison insensible à la casse
        if allergies_patient:
            allergies_lower = [a.lower() for a in allergies_patient]
            if medicament.lower() in allergies_lower:
                raise ValueError(
                    f"Alerte allergie : le patient est allergique à '{medicament}'."
                )

        ligne = LigneOrdonnance(medicament, dosage, posologie, duree_jours)
        ordonnance.lignes.append(ligne)
        return ligne

    # ------------------------------------------------------------------
    # Valider
    # ------------------------------------------------------------------

    def valider_ordonnance(self, ordonnance_id):
        """
        Valide l'ordonnance — la rend non modifiable.
        Lève ValueError si l'ordonnance n'existe pas.
        """
        ordonnance = self.rechercher_ordonnance(ordonnance_id)
        ordonnance.est_validee = True
        return ordonnance

    # ------------------------------------------------------------------
    # Modifier
    # ------------------------------------------------------------------

    def modifier_ordonnance(self, ordonnance_id, **modifications):
        """
        Modifie les champs d'une ordonnance.
        Lève ValueError si l'ordonnance est déjà validée.
        """
        ordonnance = self.rechercher_ordonnance(ordonnance_id)

        if ordonnance.est_validee:
            raise ValueError(
                "Impossible de modifier une ordonnance déjà validée."
            )

        champs_autorisés = {"date", "patient_cin", "medecin_id"}
        for champ, valeur in modifications.items():
            if champ not in champs_autorisés:
                raise ValueError(f"Champ inconnu : '{champ}'.")
            setattr(ordonnance, champ, valeur)

        return ordonnance

    # ------------------------------------------------------------------
    # Utilitaires
    # ------------------------------------------------------------------

    def rechercher_ordonnance(self, ordonnance_id):
        """
        Retourne l'ordonnance ou lève ValueError si introuvable.
        """
        if ordonnance_id not in self._ordonnances:
            raise ValueError(
                f"Aucune ordonnance trouvée avec l'ID '{ordonnance_id}'."
            )
        return self._ordonnances[ordonnance_id]

    def nombre_ordonnances(self):
        """Retourne le nombre total d'ordonnances."""
        return len(self._ordonnances)
