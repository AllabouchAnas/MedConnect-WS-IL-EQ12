"""
Dossier de Tests Unitaires — Gestion des Ordonnances
Projet   : MedConnect
Module   : Ordonnances
Auteur   : ABDELLAH RAHEL (Responsable QA)
Version  : 1.0
Date     : 2026-11-07
Framework: pytest

Scénarios testés :
  UT-ORD-01 — Créer une ordonnance valide
  UT-ORD-02 — Ajouter un médicament sans conflit d'allergie
  UT-ORD-03 — Alerte si médicament dans les allergies du patient
  UT-ORD-04 — Valider une ordonnance
  UT-ORD-05 — Refus de modification après validation

INSTRUCTIONS :
  Implémenter ordonnances/ordonnance_service.py pour faire passer tous les tests.
  Lancer : python -m pytest ordonnances/test_ordonnance_service.py -v
"""

import pytest
from ordonnances.ordonnance_service import OrdonnanceService


@pytest.fixture
def service():
    """Fournit un OrdonnanceService vide pour chaque test."""
    from ordonnances.ordonnance import Ordonnance
    Ordonnance._compteur = 1
    return OrdonnanceService()


@pytest.fixture
def service_avec_ordonnance(service):
    """Fournit un service avec une ordonnance déjà créée."""
    service.creer_ordonnance(
        patient_cin="AB123456",
        medecin_id="MED001",
        date="2026-11-07",
    )
    return service


# ---------------------------------------------------------------------------
# UT-ORD-01 — Créer une ordonnance valide
# ---------------------------------------------------------------------------

def test_UT_ORD_01_creer_ordonnance_valide(service):
    """UT-ORD-01 : Créer une ordonnance doit réussir et retourner l'objet."""
    ordonnance = service.creer_ordonnance(
        patient_cin="AB123456",
        medecin_id="MED001",
        date="2026-11-07",
    )

    assert ordonnance is not None
    assert ordonnance.patient_cin == "AB123456"
    assert ordonnance.est_validee is False
    assert len(ordonnance.lignes) == 0
    assert service.nombre_ordonnances() == 1


# ---------------------------------------------------------------------------
# UT-ORD-02 — Ajouter un médicament sans conflit d'allergie
# ---------------------------------------------------------------------------

def test_UT_ORD_02_ajout_ligne_sans_allergie(service_avec_ordonnance):
    """UT-ORD-02 : Ajouter un médicament non allergène doit réussir."""
    service_avec_ordonnance.ajouter_ligne(
        ordonnance_id=1,
        medicament="Paracétamol",
        dosage="500mg",
        posologie="3 fois par jour",
        duree_jours=5,
        allergies_patient=["Pénicilline"],  # Pas de conflit
    )

    ordonnance = service_avec_ordonnance.rechercher_ordonnance(1)
    assert len(ordonnance.lignes) == 1
    assert ordonnance.lignes[0].medicament == "Paracétamol"


# ---------------------------------------------------------------------------
# UT-ORD-03 — Alerte si médicament dans les allergies
# ---------------------------------------------------------------------------

def test_UT_ORD_03_alerte_allergie(service_avec_ordonnance):
    """UT-ORD-03 : Prescrire un médicament allergène doit lever une ValueError."""
    with pytest.raises(ValueError, match="allergie"):
        service_avec_ordonnance.ajouter_ligne(
            ordonnance_id=1,
            medicament="Pénicilline",   # Dans la liste des allergies !
            dosage="500mg",
            posologie="2 fois par jour",
            duree_jours=7,
            allergies_patient=["Pénicilline", "Aspirine"],
        )

    ordonnance = service_avec_ordonnance.rechercher_ordonnance(1)
    assert len(ordonnance.lignes) == 0  # Aucune ligne ajoutée


# ---------------------------------------------------------------------------
# UT-ORD-04 — Valider une ordonnance
# ---------------------------------------------------------------------------

def test_UT_ORD_04_valider_ordonnance(service_avec_ordonnance):
    """UT-ORD-04 : Valider une ordonnance doit passer est_validee à True."""
    service_avec_ordonnance.valider_ordonnance(1)

    ordonnance = service_avec_ordonnance.rechercher_ordonnance(1)
    assert ordonnance.est_validee is True


# ---------------------------------------------------------------------------
# UT-ORD-05 — Refus de modification après validation
# ---------------------------------------------------------------------------

def test_UT_ORD_05_refus_modification_apres_validation(service_avec_ordonnance):
    """UT-ORD-05 : Modifier une ordonnance validée doit être refusé."""
    service_avec_ordonnance.valider_ordonnance(1)

    with pytest.raises(ValueError, match="validée"):
        service_avec_ordonnance.modifier_ordonnance(1, date="2026-12-01")

