"""
Dossier de Tests Unitaires — Gestion des Patients
Projet   : MedConnect
Module   : Gestion des Patients
Auteur   : ALLABOUCH ANASS (Chef de Projet)
Version  : 1.0
Date     : 2026-11-07
Framework: pytest

Scénarios testés :
  UT-PAT-01 — Ajout d'un patient valide
  UT-PAT-02 — Refus si CIN déjà existant
  UT-PAT-03 — Refus si téléphone déjà existant
  UT-PAT-04 — Refus si champ obligatoire vide
  UT-PAT-05 — Recherche d'un patient existant
  UT-PAT-06 — Recherche d'un patient inexistant
  UT-PAT-07 — Modification des données d'un patient
  UT-PAT-08 — Suppression d'un patient existant
"""

import pytest
from patients.patient_service import PatientService


# ---------------------------------------------------------------------------
# Fixture : un service vide remis à zéro pour chaque test
# ---------------------------------------------------------------------------

@pytest.fixture
def service():
    """Fournit un PatientService vide pour chaque test."""
    return PatientService()


@pytest.fixture
def service_avec_patient(service):
    """Fournit un service avec un patient déjà enregistré."""
    service.ajouter_patient(
        cin="AB123456",
        nom="Alami",
        prenom="Youssef",
        date_naissance="1990-05-15",
        telephone="0601234567",
        groupe_sanguin="A+",
        allergies="Pénicilline",
        contact_urgence="0699999999",
    )
    return service


# ---------------------------------------------------------------------------
# UT-PAT-01 — Ajout d'un patient valide
# ---------------------------------------------------------------------------

def test_UT_PAT_01_ajout_patient_valide(service):
    """UT-PAT-01 : L'ajout d'un patient avec tous les champs valides doit réussir."""
    patient = service.ajouter_patient(
        cin="AB123456",
        nom="Alami",
        prenom="Youssef",
        date_naissance="1990-05-15",
        telephone="0601234567",
    )

    assert patient is not None
    assert patient.cin == "AB123456"
    assert patient.nom == "Alami"
    assert patient.prenom == "Youssef"
    assert service.nombre_patients() == 1


# ---------------------------------------------------------------------------
# UT-PAT-02 — Refus si CIN déjà existant
# ---------------------------------------------------------------------------

def test_UT_PAT_02_refus_cin_duplique(service):
    """UT-PAT-02 : L'ajout d'un patient avec un CIN déjà enregistré doit être refusé."""
    service.ajouter_patient(
        cin="AB123456",
        nom="Alami",
        prenom="Youssef",
        date_naissance="1990-05-15",
        telephone="0601234567",
    )

    with pytest.raises(ValueError, match="CIN"):
        service.ajouter_patient(
            cin="AB123456",        # Même CIN
            nom="Benali",
            prenom="Hassan",
            date_naissance="1985-03-20",
            telephone="0612345678",  # Téléphone différent
        )

    # Le service ne doit toujours avoir qu'un seul patient
    assert service.nombre_patients() == 1


# ---------------------------------------------------------------------------
# UT-PAT-03 — Refus si téléphone déjà existant
# ---------------------------------------------------------------------------

def test_UT_PAT_03_refus_telephone_duplique(service):
    """UT-PAT-03 : L'ajout d'un patient avec un téléphone déjà utilisé doit être refusé."""
    service.ajouter_patient(
        cin="AB123456",
        nom="Alami",
        prenom="Youssef",
        date_naissance="1990-05-15",
        telephone="0601234567",
    )

    with pytest.raises(ValueError, match="téléphone"):
        service.ajouter_patient(
            cin="CD789012",          # CIN différent
            nom="Benali",
            prenom="Hassan",
            date_naissance="1985-03-20",
            telephone="0601234567",  # Même téléphone
        )

    assert service.nombre_patients() == 1


# ---------------------------------------------------------------------------
# UT-PAT-04 — Refus si champ obligatoire vide
# ---------------------------------------------------------------------------

def test_UT_PAT_04_refus_champ_obligatoire_vide(service):
    """UT-PAT-04 : L'ajout d'un patient avec un champ obligatoire vide doit être refusé."""
    with pytest.raises(ValueError, match="obligatoire"):
        service.ajouter_patient(
            cin="AB123456",
            nom="",             # Nom vide — champ obligatoire
            prenom="Youssef",
            date_naissance="1990-05-15",
            telephone="0601234567",
        )

    assert service.nombre_patients() == 0


# ---------------------------------------------------------------------------
# UT-PAT-05 — Recherche d'un patient existant
# ---------------------------------------------------------------------------

def test_UT_PAT_05_recherche_patient_existant(service_avec_patient):
    """UT-PAT-05 : La recherche d'un patient existant par CIN doit retourner ses données."""
    patient = service_avec_patient.rechercher_patient("AB123456")

    assert patient is not None
    assert patient.nom == "Alami"
    assert patient.prenom == "Youssef"
    assert patient.telephone == "0601234567"


# ---------------------------------------------------------------------------
# UT-PAT-06 — Recherche d'un patient inexistant
# ---------------------------------------------------------------------------

def test_UT_PAT_06_recherche_patient_inexistant(service):
    """UT-PAT-06 : La recherche d'un CIN inexistant doit lever une erreur."""
    with pytest.raises(ValueError, match="Aucun patient"):
        service.rechercher_patient("CINQUINAEXISTEPAS")


# ---------------------------------------------------------------------------
# UT-PAT-07 — Modification des données d'un patient
# ---------------------------------------------------------------------------

def test_UT_PAT_07_modification_patient(service_avec_patient):
    """UT-PAT-07 : La modification du téléphone d'un patient existant doit être persistée."""
    service_avec_patient.modifier_patient("AB123456", telephone="0699999999")
    patient = service_avec_patient.rechercher_patient("AB123456")

    assert patient.telephone == "0699999999"


# ---------------------------------------------------------------------------
# UT-PAT-08 — Suppression d'un patient existant
# ---------------------------------------------------------------------------

def test_UT_PAT_08_suppression_patient(service_avec_patient):
    """UT-PAT-08 : La suppression d'un patient existant doit le retirer du service."""
    assert service_avec_patient.nombre_patients() == 1

    service_avec_patient.supprimer_patient("AB123456")

    assert service_avec_patient.nombre_patients() == 0
    with pytest.raises(ValueError):
        service_avec_patient.rechercher_patient("AB123456")

