from datetime import date
from django.contrib.auth.models import Group, User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from config.permissions import ROLE_SECRETAIRE
from .models import Patient


class PatientApiTests(TestCase):
    def setUp(self):
        self.grp_sec, _ = Group.objects.get_or_create(name=ROLE_SECRETAIRE)
        self.sec = User.objects.create_user("sec.test", password="password123")
        self.sec.groups.add(self.grp_sec)

        self.client = APIClient()
        self.client.force_authenticate(user=self.sec)

    def test_ajout_patient_valide(self):
        resp = self.client.post("/api/patients/", {
            "cin": "AB123456",
            "nom": "Alami",
            "prenom": "Youssef",
            "date_naissance": "1990-05-15",
            "telephone": "0601234567"
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Patient.objects.count(), 1)

    def test_refus_cin_duplique(self):
        Patient.objects.create(
            cin="AB123456", nom="Alami", prenom="Youssef",
            date_naissance=date(1990, 5, 15), telephone="0601234567"
        )
        resp = self.client.post("/api/patients/", {
            "cin": "AB123456",
            "nom": "Benali",
            "prenom": "Hassan",
            "date_naissance": "1985-03-20",
            "telephone": "0612345678"
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("cin", resp.data)

    def test_refus_telephone_duplique(self):
        Patient.objects.create(
            cin="AB123456", nom="Alami", prenom="Youssef",
            date_naissance=date(1990, 5, 15), telephone="0601234567"
        )
        resp = self.client.post("/api/patients/", {
            "cin": "CD789012",
            "nom": "Benali",
            "prenom": "Hassan",
            "date_naissance": "1985-03-20",
            "telephone": "0601234567"
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("telephone", resp.data)

    def test_recherche_et_modification(self):
        p = Patient.objects.create(
            cin="AB123456", nom="Alami", prenom="Youssef",
            date_naissance=date(1990, 5, 15), telephone="0601234567"
        )
        resp = self.client.patch(f"/api/patients/{p.cin}/", {"telephone": "0699999999"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        p.refresh_from_db()
        self.assertEqual(p.telephone, "0699999999")

    def test_suppression_patient(self):
        p = Patient.objects.create(
            cin="AB123456", nom="Alami", prenom="Youssef",
            date_naissance=date(1990, 5, 15), telephone="0601234567"
        )
        resp = self.client.delete(f"/api/patients/{p.cin}/")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Patient.objects.count(), 0)
