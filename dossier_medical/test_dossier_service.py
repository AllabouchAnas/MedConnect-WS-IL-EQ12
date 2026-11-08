"""
Dossier de Tests Unitaires — Dossier Médical
Projet   : MedConnect
Module   : Dossier Médical (Consultations)
Auteur   : Achraf AIT DAMNAT (Lead Tech / Architecte)
Version  : 1.0
Date     : 2026-11-07
Framework: pytest

Scénarios testés :
  UT-DOS-01 — Ajouter une consultation valide
  UT-DOS-02 — Refus si motif vide
  UT-DOS-03 — Récupérer l'historique d'un patient avec consultations
  UT-DOS-04 — Historique vide pour un patient sans consultations
  UT-DOS-05 — Modifier le diagnostic d'une consultation

INSTRUCTIONS :
  Implémenter dossier_medical/dossier_service.py pour faire passer tous les tests.
  Lancer : python -m pytest dossier_medical/test_dossier_service.py -v
"""

import pytest
from dossier_medical.dossier_service import DossierService


@pytest.fixture
def service():
    """Fournit un DossierService vide pour chaque test."""
    from dossier_medical.consultation import Consultation
    Consultation._compteur = 1
    return DossierService()


@pytest.fixture
def service_avec_consultation(service):
    """Fournit un service avec une consultation déjà enregistrée."""
    service.ajouter_consultation(
        patient_cin="AB123456",
        medecin_id="MED001",
        date="2026-11-07",
        motif="Douleurs abdominales",
        tension="13/8",
        poids=72.5,
        temperature=37.2,
        diagnostic="Gastrite légère",
    )
    return service


# ---------------------------------------------------------------------------
# UT-DOS-01 — Ajouter une consultation valide
# ---------------------------------------------------------------------------

def test_UT_DOS_01_ajout_consultation_valide(service):
    """UT-DOS-01 : Ajouter une consultation avec tous les champs valides doit réussir."""
    consult = service.ajouter_consultation(
        patient_cin="AB123456",
        medecin_id="MED001",
        date="2026-11-07",
        motif="Douleurs abdominales",
    )

    assert consult is not None
    assert consult.patient_cin == "AB123456"
    assert consult.motif == "Douleurs abdominales"
    assert service.nombre_consultations() == 1


# ---------------------------------------------------------------------------
# UT-DOS-02 — Refus si motif vide
# ---------------------------------------------------------------------------

def test_UT_DOS_02_refus_motif_vide(service):
    """UT-DOS-02 : Ajouter une consultation sans motif doit être refusé."""
    with pytest.raises(ValueError, match="motif"):
        service.ajouter_consultation(
            patient_cin="AB123456",
            medecin_id="MED001",
            date="2026-11-07",
            motif="",          # Motif vide — interdit
        )

    assert service.nombre_consultations() == 0


# ---------------------------------------------------------------------------
# UT-DOS-03 — Historique d'un patient avec consultations
# ---------------------------------------------------------------------------

def test_UT_DOS_03_historique_avec_consultations(service_avec_consultation):
    """UT-DOS-03 : L'historique d'un patient avec consultations doit retourner une liste non vide."""
    historique = service_avec_consultation.get_historique("AB123456")

    assert isinstance(historique, list)
    assert len(historique) == 1
    assert historique[0].motif == "Douleurs abdominales"


# ---------------------------------------------------------------------------
# UT-DOS-04 — Historique vide pour un patient sans consultations
# ---------------------------------------------------------------------------

def test_UT_DOS_04_historique_vide(service):
    """UT-DOS-04 : L'historique d'un patient sans consultations doit retourner une liste vide."""
    historique = service.get_historique("PATIENTINCONNU")

    assert isinstance(historique, list)
    assert len(historique) == 0


# ---------------------------------------------------------------------------
# UT-DOS-05 — Modifier le diagnostic
# ---------------------------------------------------------------------------

def test_UT_DOS_05_modifier_diagnostic(service_avec_consultation):
    """UT-DOS-05 : Modifier le diagnostic d'une consultation existante doit être persisté."""
    service_avec_consultation.modifier_consultation(1, diagnostic="Ulcère gastrique")

    historique = service_avec_consultation.get_historique("AB123456")
    assert historique[0].diagnostic == "Ulcère gastrique"

