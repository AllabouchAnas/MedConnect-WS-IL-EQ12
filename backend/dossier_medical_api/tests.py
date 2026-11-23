from datetime import date
from django.contrib.auth.models import Group, User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from config.permissions import ROLE_MEDECIN, ROLE_SECRETAIRE
from patients_api.models import Patient
from dossier_medical_api.models import Consultation


class ConsultationApiTests(TestCase):
    def setUp(self):
        self.grp_med, _ = Group.objects.get_or_create(name=ROLE_MEDECIN)
        self.grp_sec, _ = Group.objects.get_or_create(name=ROLE_SECRETAIRE)

        self.dr = User.objects.create_user("dr.test", password="password123")
        self.dr.groups.add(self.grp_med)

        self.sec = User.objects.create_user("sec.test", password="password123")
        self.sec.groups.add(self.grp_sec)

        self.patient = Patient.objects.create(
            cin="AB123", nom="Benali", prenom="Sara",
            date_naissance=date(1990, 5, 1), telephone="0600000001"
        )

        self.client_dr = APIClient()
        self.client_dr.force_authenticate(user=self.dr)

        self.client_sec = APIClient()
        self.client_sec.force_authenticate(user=self.sec)

    def test_medecin_peut_ajouter_consultation_valide(self):
        resp = self.client_dr.post("/api/consultations/", {
            "patient_cin": "AB123",
            "date": "2026-11-13",
            "motif": "Contrôle annuel",
            "diagnostic": "Bonne santé générale"
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Consultation.objects.count(), 1)

    def test_refus_motif_vide(self):
        # Règle F005 — Motif obligatoire (Figure 15)
        resp = self.client_dr.post("/api/consultations/", {
            "patient_cin": "AB123",
            "date": "2026-11-13",
            "motif": "",
            "diagnostic": "Test"
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("motif", resp.data)

    def test_secretaire_interdite_de_creer_consultation(self):
        # Règle RBAC — Secret médical
        resp = self.client_sec.post("/api/consultations/", {
            "patient_cin": "AB123",
            "date": "2026-11-13",
            "motif": "Tentative secrétaire",
        })
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
