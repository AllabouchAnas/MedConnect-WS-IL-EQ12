"""
Dossier de Tests Unitaires — Gestion de l'Agenda
Projet   : MedConnect
Module   : Agenda (Rendez-vous)
Auteur   : Ahmed LAHMAINE (Product Owner / BA)
Version  : 1.0
Date     : 2026-11-07
Framework: pytest

Scénarios testés :
  UT-AGE-01 — Planifier un RDV valide
  UT-AGE-02 — Refus si créneau déjà pris (même médecin, même heure)
  UT-AGE-03 — Avancer le statut dans l'ordre
  UT-AGE-04 — Annuler un RDV (historique conservé)
  UT-AGE-05 — Rechercher un RDV inexistant

INSTRUCTIONS :
  Implémenter agenda/agenda_service.py pour faire passer tous les tests.
  Lancer : python -m pytest agenda/test_agenda_service.py -v
"""

import pytest
from agenda.agenda_service import AgendaService


@pytest.fixture
def service():
    """Fournit un AgendaService vide pour chaque test."""
    # Réinitialise l'ID auto-incrémenté entre les tests
    from agenda.rendez_vous import RendezVous
    RendezVous._compteur = 1
    return AgendaService()


@pytest.fixture
def service_avec_rdv(service):
    """Fournit un service avec un RDV déjà planifié."""
    service.planifier_rdv(
        patient_cin="AB123456",
        medecin_id="MED001",
        date_heure="2026-11-10 09:00",
        motif="Consultation générale",
    )
    return service


# ---------------------------------------------------------------------------
# UT-AGE-01 — Planifier un RDV valide
# ---------------------------------------------------------------------------

def test_UT_AGE_01_planifier_rdv_valide(service):
    """UT-AGE-01 : Planifier un RDV avec un créneau libre doit réussir."""
    rdv = service.planifier_rdv(
        patient_cin="AB123456",
        medecin_id="MED001",
        date_heure="2026-11-10 09:00",
    )

    assert rdv is not None
    assert rdv.patient_cin == "AB123456"
    assert rdv.statut == "Planifié"
    assert service.nombre_rdv() == 1


# ---------------------------------------------------------------------------
# UT-AGE-02 — Refus si créneau déjà pris
# ---------------------------------------------------------------------------

def test_UT_AGE_02_refus_chevauchement(service):
    """UT-AGE-02 : Deux RDV au même créneau pour le même médecin doivent être refusés."""
    service.planifier_rdv(
        patient_cin="AB123456",
        medecin_id="MED001",
        date_heure="2026-11-10 09:00",
    )

    with pytest.raises(ValueError):
        service.planifier_rdv(
            patient_cin="CD789012",   # Patient différent
            medecin_id="MED001",      # Même médecin
            date_heure="2026-11-10 09:00",  # Même créneau
        )

    assert service.nombre_rdv() == 1


# ---------------------------------------------------------------------------
# UT-AGE-03 — Avancer le statut dans l'ordre
# ---------------------------------------------------------------------------

def test_UT_AGE_03_avancer_statut(service_avec_rdv):
    """UT-AGE-03 : Avancer le statut doit suivre le cycle défini."""
    rdv = service_avec_rdv.rechercher_rdv(1)
    assert rdv.statut == "Planifié"

    service_avec_rdv.avancer_statut(1)
    assert rdv.statut == "Salle d'attente"

    service_avec_rdv.avancer_statut(1)
    assert rdv.statut == "Consultation"

    service_avec_rdv.avancer_statut(1)
    assert rdv.statut == "Terminé"


# ---------------------------------------------------------------------------
# UT-AGE-04 — Annuler un RDV (historique conservé)
# ---------------------------------------------------------------------------

def test_UT_AGE_04_annuler_rdv(service_avec_rdv):
    """UT-AGE-04 : Annuler un RDV doit changer son statut sans le supprimer."""
    service_avec_rdv.annuler_rdv(1, motif_annulation="Patient absent")

    rdv = service_avec_rdv.rechercher_rdv(1)
    assert rdv.statut == "Annulé"
    assert rdv.motif_annulation == "Patient absent"
    assert service_avec_rdv.nombre_rdv() == 1  # Toujours présent


# ---------------------------------------------------------------------------
# UT-AGE-05 — Rechercher un RDV inexistant
# ---------------------------------------------------------------------------

def test_UT_AGE_05_recherche_rdv_inexistant(service):
    """UT-AGE-05 : Rechercher un ID inexistant doit lever une erreur."""
    with pytest.raises(ValueError):
        service.rechercher_rdv(999)
