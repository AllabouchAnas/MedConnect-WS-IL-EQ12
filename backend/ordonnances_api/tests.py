from datetime import date
from django.contrib.auth.models import Group, User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from config.permissions import ROLE_MEDECIN, ROLE_SECRETAIRE
from patients_api.models import Patient
from ordonnances_api.models import Ordonnance


class OrdonnancesApiTests(TestCase):
    def setUp(self):
        self.grp_med, _ = Group.objects.get_or_create(name=ROLE_MEDECIN)
        self.grp_sec, _ = Group.objects.get_or_create(name=ROLE_SECRETAIRE)

        self.dr = User.objects.create_user("dr.test", password="password123")
        self.dr.groups.add(self.grp_med)

        self.sec = User.objects.create_user("sec.test", password="password123")
        self.sec.groups.add(self.grp_sec)

        self.patient = Patient.objects.create(
            cin="AB123", nom="Benali", prenom="Sara",
            date_naissance=date(1990, 5, 1), telephone="0600000001",
            allergies="Pénicilline"
        )

        self.client_dr = APIClient()
        self.client_dr.force_authenticate(user=self.dr)

        self.ord = Ordonnance.objects.create(
            patient=self.patient, medecin=self.dr, date=date(2026, 11, 13)
        )

    def test_alerte_et_refus_allergie_temps_reel(self):
        # Règle F006 (Figure 18) : Refus si médicament allergène
        resp = self.client_dr.post(f"/api/ordonnances/{self.ord.id}/ajouter-ligne/", {
            "medicament": "Pénicilline",
            "dosage": "500 mg",
            "posologie": "2 fois par jour",
            "duree_jours": 7
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("allergique", resp.data.get("detail", ""))

    def test_ajout_medicament_valide(self):
        resp = self.client_dr.post(f"/api/ordonnances/{self.ord.id}/ajouter-ligne/", {
            "medicament": "Ibuprofène",
            "dosage": "400 mg",
            "posologie": "2 fois par jour",
            "duree_jours": 3
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.ord.lignes.count(), 1)

    def test_validation_et_verrouillage_ordonnance(self):
        # Règle F006 (Figures 21, 22, 23) : Immutabilité post-validation
        resp_val = self.client_dr.post(f"/api/ordonnances/{self.ord.id}/valider/")
        self.assertEqual(resp_val.status_code, status.HTTP_200_OK)
        self.ord.refresh_from_db()
        self.assertTrue(self.ord.est_validee)

        # Tentative d'ajout après validation -> Refus 400
        resp_add = self.client_dr.post(f"/api/ordonnances/{self.ord.id}/ajouter-ligne/", {
            "medicament": "Paracétamol",
            "dosage": "1000 mg",
            "posologie": "1/j",
            "duree_jours": 1
        })
        self.assertEqual(resp_add.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("validée", resp_add.data.get("detail", ""))
