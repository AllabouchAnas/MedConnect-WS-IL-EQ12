import datetime

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from patients_api.models import Patient
from .models import RendezVous, Statut

User = get_user_model()
URL = "/api/agenda/rdv/"


class AgendaApiTests(TestCase):
    def setUp(self):
        cache.clear()
        med, _ = Group.objects.get_or_create(name="Medecin")
        sec, _ = Group.objects.get_or_create(name="Secretaire")
        self.dr = User.objects.create_user("dr.test", password="Demo@1234")
        self.dr2 = User.objects.create_user("dr.deux", password="Demo@1234")
        self.sec = User.objects.create_user("sec.test", password="Demo@1234")
        self.dr.groups.add(med); self.dr2.groups.add(med); self.sec.groups.add(sec)
        self.p1 = Patient.objects.create(cin="AB123", nom="Benali", prenom="Sara", date_naissance="1990-05-01",
                                         telephone="0600000001")
        self.p2 = Patient.objects.create(cin="CD456", nom="Alaoui", prenom="Omar", date_naissance="1985-01-02",
                                         telephone="0600000002")
        self.c = APIClient()
        self.c.force_authenticate(self.sec)

    def create(self, cin="AB123", medecin=None, dt="2026-11-13T10:00", motif="Contrôle"):
        return self.c.post(URL, {"patient": cin, "medecin": (medecin or self.dr).id,
                                 "date_heure": dt, "motif": motif}, format="json")

    # UT-AGE-01
    def test_planifier_rdv_valide(self):
        r = self.create()
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["statut"], "Planifié")
        self.assertEqual(r.data["heure"], "10:00")

    # UT-AGE-02
    def test_refus_chevauchement_meme_medecin(self):
        self.create()
        r = self.create(cin="CD456")
        self.assertEqual(r.status_code, 400)
        self.assertIn("date_heure", r.data)
        self.assertEqual(RendezVous.objects.count(), 1)

    def test_meme_creneau_autre_medecin_ok(self):
        self.create()
        self.assertEqual(self.create(medecin=self.dr2).status_code, 201)

    def test_creneau_libere_apres_annulation(self):
        rid = self.create().data["id"]
        self.c.post(f"{URL}{rid}/annuler/", {"motif_annulation": "Indisponible"}, format="json")
        self.assertEqual(self.create(cin="CD456").status_code, 201)

    def test_patient_inexistant_refuse(self):
        self.assertEqual(self.create(cin="ZZ999").status_code, 400)

    # UT-AGE-03
    def test_avancer_statut_dans_lordre(self):
        rid = self.create().data["id"]
        seq = [self.c.post(f"{URL}{rid}/avancer/").data["statut"] for _ in range(3)]
        self.assertEqual(seq, ["Salle d'attente", "Consultation", "Terminé"])
        rdv = RendezVous.objects.get(pk=rid)
        self.assertIsNotNone(rdv.arrivee_a)
        self.assertEqual(rdv.arrivee_par, self.sec)
        self.assertEqual(self.c.post(f"{URL}{rid}/avancer/").status_code, 400)

    def test_avancer_annule_refuse(self):
        rid = self.create().data["id"]
        self.c.post(f"{URL}{rid}/annuler/", {"motif_annulation": "x"}, format="json")
        self.assertEqual(self.c.post(f"{URL}{rid}/avancer/").status_code, 400)

    # UT-AGE-04
    def test_annuler_conserve_le_rdv(self):
        rid = self.create().data["id"]
        r = self.c.post(f"{URL}{rid}/annuler/", {"motif_annulation": "Patient indisponible"}, format="json")
        self.assertEqual(r.data["statut"], "Annulé")
        self.assertEqual(r.data["motif_annulation"], "Patient indisponible")
        self.assertTrue(RendezVous.objects.filter(pk=rid).exists())

    def test_annuler_sans_motif_refuse(self):
        rid = self.create().data["id"]
        self.assertEqual(self.c.post(f"{URL}{rid}/annuler/", {}, format="json").status_code, 400)

    # UT-AGE-05
    def test_recherche_rdv_inexistant(self):
        self.assertEqual(self.c.get(f"{URL}9999/").status_code, 404)

    def test_liste_filtree_par_date(self):
        self.create(dt="2026-11-13T10:00"); self.create(dt="2026-11-14T10:00")
        self.assertEqual(len(self.c.get(URL, {"date": "2026-11-13"}).data), 1)
        self.assertEqual(self.c.get(URL, {"date": "pas-une-date"}).status_code, 400)

    def test_salle_attente_du_jour_uniquement(self):
        now = timezone.localtime().replace(second=0, microsecond=0)
        today = RendezVous.objects.create(patient=self.p1, medecin=self.dr, date_heure=now,
                                          statut=Statut.SALLE_ATTENTE)
        RendezVous.objects.create(patient=self.p2, medecin=self.dr, date_heure=now + datetime.timedelta(days=1),
                                  statut=Statut.SALLE_ATTENTE)
        RendezVous.objects.create(patient=self.p2, medecin=self.dr2, date_heure=now)  # Planifié
        data = self.c.get(URL + "salle-attente/").data
        self.assertEqual([d["id"] for d in data], [today.id])

    # Sécurité F001
    def test_acces_sans_jeton_refuse(self):
        self.assertEqual(APIClient().get(URL).status_code, 401)

    def test_utilisateur_sans_role_refuse(self):
        u = User.objects.create_user("intrus", password="Demo@1234")
        c = APIClient(); c.force_authenticate(u)
        self.assertEqual(c.get(URL).status_code, 403)

    def test_login_jwt_et_blocage_apres_5_echecs(self):
        c = APIClient()
        ok = c.post("/api/auth/login/", {"username": "sec.test", "password": "Demo@1234"}, format="json")
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(ok.data["user"]["role"], "Secretaire")
        c.credentials(HTTP_AUTHORIZATION="Bearer " + ok.data["access"])
        self.assertEqual(c.get(URL).status_code, 200)
        c = APIClient()
        for _ in range(5):
            self.assertEqual(c.post("/api/auth/login/", {"username": "dr.test", "password": "mauvais"},
                                    format="json").status_code, 401)
        r = c.post("/api/auth/login/", {"username": "dr.test", "password": "Demo@1234"}, format="json")
        self.assertEqual(r.status_code, 429)

    def test_logout_invalide_le_refresh(self):
        c = APIClient()
        t = c.post("/api/auth/login/", {"username": "sec.test", "password": "Demo@1234"}, format="json").data
        c.post("/api/auth/logout/", {"refresh": t["refresh"]}, format="json")
        self.assertEqual(c.post("/api/auth/refresh/", {"refresh": t["refresh"]}, format="json").status_code, 401)
