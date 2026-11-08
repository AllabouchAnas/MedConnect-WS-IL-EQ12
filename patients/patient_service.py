"""
Service Gestion des Patients — MedConnect
Module : Gestion des Patients
Auteur : ALLABOUCH ANASS (Chef de Projet)

Règles métier implémentées :
  - CIN unique (doublons refusés)
  - Téléphone unique (doublons refusés)
  - Champs obligatoires : cin, nom, prenom, date_naissance, telephone
  - Recherche par CIN
  - Modification des données d'un patient existant
  - Suppression d'un patient
"""

from patients.patient import Patient


class PatientService:
    """
    Service de gestion des patients — stockage en mémoire.
    Simule les opérations CRUD avec validation des règles métier.
    """

    def __init__(self):
        # Dictionnaire interne : cin -> Patient
        self._patients = {}

    # ------------------------------------------------------------------
    # Ajout
    # ------------------------------------------------------------------

    def ajouter_patient(self, cin, nom, prenom, date_naissance, telephone,
                        groupe_sanguin="", allergies="", contact_urgence=""):
        """
        Ajoute un nouveau patient.

        Lève ValueError si :
          - Un champ obligatoire est vide / None
          - Le CIN existe déjà
          - Le téléphone existe déjà
        """
        # Validation des champs obligatoires
        for champ, valeur in [("CIN", cin), ("Nom", nom), ("Prénom", prenom),
                               ("Date de naissance", date_naissance),
                               ("Téléphone", telephone)]:
            if not valeur or str(valeur).strip() == "":
                raise ValueError(f"Le champ '{champ}' est obligatoire.")

        # Vérification doublons CIN
        if cin in self._patients:
            raise ValueError(f"Un patient avec le CIN '{cin}' existe déjà.")

        # Vérification doublons téléphone
        for p in self._patients.values():
            if p.telephone == telephone:
                raise ValueError(
                    f"Un patient avec le téléphone '{telephone}' existe déjà."
                )

        patient = Patient(cin, nom, prenom, date_naissance, telephone,
                          groupe_sanguin, allergies, contact_urgence)
        self._patients[cin] = patient
        return patient

    # ------------------------------------------------------------------
    # Recherche
    # ------------------------------------------------------------------

    def rechercher_patient(self, cin):
        """
        Retourne le patient correspondant au CIN.
        Lève ValueError si aucun patient trouvé.
        """
        if cin not in self._patients:
            raise ValueError(f"Aucun patient trouvé avec le CIN '{cin}'.")
        return self._patients[cin]

    # ------------------------------------------------------------------
    # Modification
    # ------------------------------------------------------------------

    def modifier_patient(self, cin, **modifications):
        """
        Modifie les données d'un patient existant.
        Seuls les champs fournis sont mis à jour.
        Lève ValueError si le patient n'existe pas.
        """
        patient = self.rechercher_patient(cin)

        champs_autorisés = {
            "nom", "prenom", "date_naissance",
            "telephone", "groupe_sanguin", "allergies", "contact_urgence"
        }

        for champ, valeur in modifications.items():
            if champ not in champs_autorisés:
                raise ValueError(f"Champ inconnu : '{champ}'.")
            setattr(patient, champ, valeur)

        return patient

    # ------------------------------------------------------------------
    # Suppression
    # ------------------------------------------------------------------

    def supprimer_patient(self, cin):
        """
        Supprime le patient identifié par son CIN.
        Lève ValueError si le patient n'existe pas.
        """
        patient = self.rechercher_patient(cin)
        del self._patients[cin]
        return patient

    # ------------------------------------------------------------------
    # Utilitaires
    # ------------------------------------------------------------------

    def nombre_patients(self):
        """Retourne le nombre de patients enregistrés."""
        return len(self._patients)

    def lister_patients(self):
        """Retourne la liste de tous les patients."""
        return list(self._patients.values())

