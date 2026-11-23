import datetime

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from patients_api.models import Patient
from .models import Consultation

User = get_user_model()
URL = "/api/consultations/"


def jours(n):
    """Date ISO située n jours avant aujourd'hui."""
    return (timezone.localdate() - datetime.timedelta(days=n)).isoformat()


class DossierMedicalApiTests(TestCase):
    def setUp(self):
        med, _ = Group.objects.get_or_create(name="Medecin")
        sec, _ = Group.objects.get_or_create(name="Secretaire")
        self.dr = User.objects.create_user("dr.test", password="Demo@1234", first_name="Dr.", last_name="Test")
        self.dr2 = User.objects.create_user("dr.deux", password="Demo@1234")
        self.sec = User.objects.create_user("sec.test", password="Demo@1234")
        self.dr.groups.add(med); self.dr2.groups.add(med); self.sec.groups.add(sec)
        self.p1 = Patient.objects.create(cin="AB123", nom="Benali", prenom="Sara",
                                         date_naissance="1990-05-01", telephone="0600000001")
        self.p2 = Patient.objects.create(cin="CD456", nom="Alaoui", prenom="Omar",
                                         date_naissance="1985-01-02", telephone="0600000002")
        self.c = APIClient()
        self.c.force_authenticate(self.dr)

    def payload(self, **kw):
        data = {"patient_cin": "AB123", "date": jours(0), "motif": "Douleurs abdominales"}
        data.update(kw)
        return data

    def create(self, **kw):
        return self.c.post(URL, self.payload(**kw), format="json")

    # UT-DOS-01 — ajout d'une consultation valide
    def test_ajout_consultation_valide(self):
        r = self.create(tension="13/8", poids=72.5, temperature=37.2, pouls=80, diagnostic="Gastrite légère")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["patient_cin"], "AB123")
        self.assertEqual(r.data["patient_nom"], "Sara Benali")
        self.assertEqual(r.data["medecin"], self.dr.id)       # médecin = utilisateur connecté
        self.assertEqual(r.data["medecin_nom"], "Dr. Test")
        corps = r.json()                                      # JSON réellement reçu par le navigateur
        self.assertEqual(corps["poids"], 72.5)                # nombre, pas chaîne
        self.assertEqual(corps["temperature"], 37.2)
        self.assertIsInstance(corps["temperature"], float)
        self.assertEqual(Consultation.objects.count(), 1)

    def test_constantes_facultatives(self):
        r = self.create()
        self.assertEqual(r.status_code, 201)
        self.assertIsNone(r.data["poids"])
        self.assertEqual(r.data["tension"], "")

    def test_medecin_non_falsifiable(self):
        r = self.create(medecin=self.dr2.id)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["medecin"], self.dr.id)

    # UT-DOS-02 — motif obligatoire
    def test_refus_motif_vide(self):
        for motif in ("", "   "):
            r = self.create(motif=motif)
            self.assertEqual(r.status_code, 400)
            self.assertIn("motif", r.data)
        self.assertEqual(Consultation.objects.count(), 0)

    def test_refus_motif_absent(self):
        data = self.payload(); del data["motif"]
        r = self.c.post(URL, data, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("motif", r.data)

    def test_refus_patient_inconnu_ou_absent(self):
        r = self.create(patient_cin="ZZZ")
        self.assertEqual(r.status_code, 400)
        self.assertIn("patient_cin", r.data)
        data = self.payload(); del data["patient_cin"]
        self.assertEqual(self.c.post(URL, data, format="json").status_code, 400)

    def test_refus_date_future_ou_invalide(self):
        demain = (timezone.localdate() + datetime.timedelta(days=1)).isoformat()
        self.assertIn("date", self.create(date=demain).data)
        self.assertEqual(self.create(date="pas-une-date").status_code, 400)

    def test_refus_constantes_aberrantes(self):
        for champ, valeur in [("temperature", 99), ("temperature", 10), ("pouls", 5), ("pouls", 400),
                              ("poids", -3), ("poids", 900), ("tension", "abc"), ("tension", "12-8")]:
            r = self.create(**{champ: valeur})
            self.assertEqual(r.status_code, 400, f"{champ}={valeur}")
            self.assertIn(champ, r.data)

    # UT-DOS-03 — historique d'un patient avec consultations
    def test_historique_patient(self):
        self.create(date=jours(10), motif="Ancienne")
        self.create(date=jours(1), motif="Récente")
        self.create(patient_cin="CD456", motif="Autre patient")
        r = self.c.get(URL, {"patient": "AB123"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual([x["motif"] for x in r.data], ["Récente", "Ancienne"])  # plus récent d'abord

    def test_filtre_patient_insensible_a_la_casse(self):
        self.create()
        self.assertEqual(len(self.c.get(URL, {"patient": "ab123"}).data), 1)

    # UT-DOS-04 — historique vide
    def test_historique_vide(self):
        self.create()
        r = self.c.get(URL, {"patient": "CD456"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data, [])

    def test_filtres_dates_et_recherche(self):
        self.create(date=jours(30), motif="Toux", diagnostic="Bronchite")
        self.create(date=jours(2), motif="Fièvre")
        self.assertEqual(len(self.c.get(URL, {"date_debut": jours(5)}).data), 1)
        self.assertEqual(len(self.c.get(URL, {"date_fin": jours(5)}).data), 1)
        self.assertEqual(len(self.c.get(URL, {"search": "bronch"}).data), 1)
        self.assertEqual(self.c.get(URL, {"date_debut": "xx"}).status_code, 400)

    # UT-DOS-05 — modification du diagnostic
    def test_modifier_diagnostic(self):
        cid = self.create(diagnostic="Initial").data["id"]
        r = self.c.patch(f"{URL}{cid}/", {"diagnostic": "Gastrite confirmée"}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Consultation.objects.get(pk=cid).diagnostic, "Gastrite confirmée")

    def test_modification_ne_peut_pas_vider_le_motif(self):
        cid = self.create().data["id"]
        r = self.c.patch(f"{URL}{cid}/", {"motif": " "}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertEqual(Consultation.objects.get(pk=cid).motif, "Douleurs abdominales")

    def test_patient_non_modifiable(self):
        cid = self.create().data["id"]
        self.assertEqual(self.c.patch(f"{URL}{cid}/", {"patient_cin": "AB123"}, format="json").status_code, 200)
        r = self.c.patch(f"{URL}{cid}/", {"patient_cin": "CD456"}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertEqual(Consultation.objects.get(pk=cid).patient, self.p1)

    # Suppression / identifiants inexistants
    def test_suppression(self):
        cid = self.create().data["id"]
        self.assertEqual(self.c.delete(f"{URL}{cid}/").status_code, 204)
        self.assertEqual(Consultation.objects.count(), 0)
        self.assertEqual(self.c.delete(f"{URL}{cid}/").status_code, 404)

    def test_id_inexistant(self):
        self.assertEqual(self.c.get(f"{URL}9999/").status_code, 404)
        self.assertEqual(self.c.patch(f"{URL}9999/", {"motif": "x"}, format="json").status_code, 404)
        self.assertEqual(self.c.delete(f"{URL}9999/").status_code, 404)

    def test_dossier_partage_entre_medecins(self):
        cid = self.create().data["id"]
        self.c.force_authenticate(self.dr2)
        self.assertEqual(self.c.get(f"{URL}{cid}/").status_code, 200)

    # Sécurité : accès réservé aux médecins
    def test_secretaire_refusee_partout(self):
        cid = self.create().data["id"]
        self.c.force_authenticate(self.sec)
        self.assertEqual(self.c.get(URL).status_code, 403)
        self.assertEqual(self.c.get(f"{URL}{cid}/").status_code, 403)
        self.assertEqual(self.create().status_code, 403)
        self.assertEqual(self.c.patch(f"{URL}{cid}/", {"diagnostic": "x"}, format="json").status_code, 403)
        self.assertEqual(self.c.delete(f"{URL}{cid}/").status_code, 403)
        self.assertEqual(Consultation.objects.count(), 1)

    def test_utilisateur_sans_role_refuse(self):
        self.c.force_authenticate(User.objects.create_user("intrus", password="Demo@1234"))
        self.assertEqual(self.c.get(URL).status_code, 403)

    def test_non_authentifie_refuse(self):
        self.assertEqual(APIClient().get(URL).status_code, 401)
        self.assertEqual(APIClient().post(URL, self.payload(), format="json").status_code, 401)
