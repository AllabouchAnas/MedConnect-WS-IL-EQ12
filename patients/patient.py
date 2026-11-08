"""
Modèle Patient — MedConnect
Module : Gestion des Patients
Auteur : ALLABOUCH ANASS (Chef de Projet)
"""


class Patient:
    """Représente un patient du cabinet médical."""

    def __init__(self, cin, nom, prenom, date_naissance, telephone,
                 groupe_sanguin="", allergies="", contact_urgence=""):
        self.cin = cin
        self.nom = nom
        self.prenom = prenom
        self.date_naissance = date_naissance
        self.telephone = telephone
        self.groupe_sanguin = groupe_sanguin
        self.allergies = allergies
        self.contact_urgence = contact_urgence

    def __repr__(self):
        return f"Patient(cin={self.cin}, nom={self.nom}, prenom={self.prenom})"

