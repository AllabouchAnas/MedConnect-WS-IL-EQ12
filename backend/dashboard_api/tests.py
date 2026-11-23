import datetime

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from agenda_api.models import RendezVous, Statut
from dossier_medical_api.models import Consultation
from patients_api.models import Patient

User = get_user_model()
URL = "/api/dashboard/"


def a(jours=0, h=9, m=0):
    """Datetime locale « aujourd'hui + jours » à h:m."""
    jour = timezone.localdate() + datetime.timedelta(days=jours)
    return datetime.datetime.combine(jour, datetime.time(h, m), tzinfo=timezone.get_current_timezone())


class DashboardApiTests(TestCase):
    def setUp(self):
        med, _ = Group.objects.get_or_create(name="Medecin")
        sec, _ = Group.objects.get_or_create(name="Secretaire")
        self.dr = User.objects.create_user("dr.a", password="x", first_name="Dr.", last_name="A")
        self.dr2 = User.objects.create_user("dr.b", password="x", first_name="Dr.", last_name="B")
        self.sec = User.objects.create_user("sec", password="x")
        self.dr.groups.add(med); self.dr2.groups.add(med); self.sec.groups.add(sec)
        self.p1 = Patient.objects.create(cin="AB1", nom="Benali", prenom="Sara",
                                         date_naissance="1990-01-01", telephone="0600000001")
        self.p2 = Patient.objects.create(cin="CD2", nom="Alaoui", prenom="Omar",
                                         date_naissance="1985-01-01", telephone="0600000002")
        self.c = APIClient()

    def rdv(self, medecin, dt, statut=Statut.PLANIFIE, patient=None, **kw):
        return RendezVous.objects.create(patient=patient or self.p1, medecin=medecin, date_heure=dt,
                                         statut=statut, **kw)

    def get(self, user):
        self.c.force_authenticate(user)
        r = self.c.get(URL)
        self.assertEqual(r.status_code, 200)
        return r.data

    # Accès
    def test_non_authentifie(self):
        self.assertEqual(APIClient().get(URL).status_code, 401)

    def test_utilisateur_sans_role_refuse(self):
        self.c.force_authenticate(User.objects.create_user("intrus", password="x"))
        self.assertEqual(self.c.get(URL).status_code, 403)

    # Base vide
    def test_base_vide(self):
        d = self.get(self.dr)
        self.assertEqual(d["kpis"]["rdv_total"], 0)
        self.assertIsNone(d["kpis"]["attente_moyenne_min"])
        self.assertEqual(d["rdvs"], [])
        self.assertEqual(d["salle_attente"], [])
        self.assertEqual(d["consultations_recentes"], [])
        self.assertEqual([x["n"] for x in d["activite"]], [0] * 7)

    # Indicateurs
    def test_indicateurs_du_jour(self):
        self.rdv(self.dr, a(h=8), Statut.TERMINE)
        self.rdv(self.dr, a(h=9), Statut.CONSULTATION, self.p2)
        self.rdv(self.dr, a(h=10), Statut.SALLE_ATTENTE, arrivee_a=timezone.now() - datetime.timedelta(minutes=12))
        self.rdv(self.dr, a(h=11), Statut.PLANIFIE, self.p2)
        self.rdv(self.dr, a(h=12), Statut.ANNULE, motif_annulation="x")
        k = self.get(self.dr)["kpis"]
        self.assertEqual((k["rdv_total"], k["termines"], k["restants"], k["annules"], k["en_attente"]),
                         (5, 1, 3, 1, 1))
        self.assertEqual(k["attente_moyenne_min"], 12)
        self.assertEqual(k["patients_total"], 2)

    def test_ordre_chronologique_et_champs(self):
        self.rdv(self.dr, a(h=11), motif="B")
        self.rdv(self.dr, a(h=9), motif="A")
        rdvs = self.get(self.dr)["rdvs"]
        self.assertEqual([r["heure"] for r in rdvs], ["09:00", "11:00"])
        self.assertEqual(rdvs[0]["patient_nom"], "Sara Benali")
        self.assertEqual(rdvs[0]["medecin_nom"], "Dr. A")

    def test_hier_et_demain_exclus_du_jour(self):
        self.rdv(self.dr, a(-1)); self.rdv(self.dr, a(1))
        self.assertEqual(self.get(self.dr)["kpis"]["rdv_total"], 0)

    def test_annulations_de_la_semaine(self):
        lundi = -timezone.localdate().weekday()
        self.rdv(self.dr, a(lundi, 9), Statut.ANNULE, motif_annulation="x")             # lundi : compté
        self.rdv(self.dr, a(lundi - 1, 9), Statut.ANNULE, motif_annulation="x")         # dimanche précédent : non
        self.rdv(self.dr, a(lundi + 7, 9), Statut.ANNULE, motif_annulation="x")         # lundi suivant : non
        self.assertEqual(self.get(self.dr)["kpis"]["annulations_semaine"], 1)

    # Périmètre par rôle
    def test_medecin_ne_voit_que_ses_rendez_vous(self):
        self.rdv(self.dr, a(h=9)); self.rdv(self.dr2, a(h=9), patient=self.p2)
        d = self.get(self.dr)
        self.assertEqual([r["medecin_nom"] for r in d["rdvs"]], ["Dr. A"])
        self.assertEqual(d["role"], "Medecin")

    def test_secretaire_voit_tous_les_medecins(self):
        self.rdv(self.dr, a(h=9)); self.rdv(self.dr2, a(h=9), patient=self.p2)
        d = self.get(self.sec)
        self.assertEqual(sorted(r["medecin_nom"] for r in d["rdvs"]), ["Dr. A", "Dr. B"])
        self.assertEqual(d["role"], "Secretaire")

    def test_salle_attente_medecin_filtree_secretaire_complete(self):
        for dr, p, t in [(self.dr, self.p1, 10), (self.dr2, self.p2, 11)]:
            self.rdv(dr, a(h=t), Statut.SALLE_ATTENTE, p, arrivee_a=timezone.now())
        self.assertEqual(len(self.get(self.dr)["salle_attente"]), 1)
        self.assertEqual(len(self.get(self.sec)["salle_attente"]), 2)

    # Confidentialité
    def test_aucune_donnee_medicale_pour_la_secretaire(self):
        Consultation.objects.create(patient=self.p1, medecin=self.dr, date=timezone.localdate(),
                                    motif="SECRET-MOTIF", diagnostic="SECRET-DIAG")
        r = self.c
        r.force_authenticate(self.sec)
        resp = r.get(URL)
        self.assertNotIn("consultations_recentes", resp.data)
        self.assertNotIn("activite", resp.data)
        self.assertNotIn("SECRET", resp.content.decode())
        self.assertIn("demain", resp.data)

    def test_diagnostic_jamais_expose_meme_au_medecin(self):
        Consultation.objects.create(patient=self.p1, medecin=self.dr, date=timezone.localdate(),
                                    motif="Toux", diagnostic="SECRET-DIAG")
        resp = APIClient(); resp.force_authenticate(self.dr)
        self.assertNotIn("SECRET-DIAG", resp.get(URL).content.decode())  # la page d'accueil n'en a pas besoin

    # Données médicales du médecin
    def test_consultations_recentes_limitees_a_5_et_au_medecin(self):
        for i in range(7):
            Consultation.objects.create(patient=self.p1, medecin=self.dr,
                                        date=timezone.localdate() - datetime.timedelta(days=i), motif=f"M{i}")
        Consultation.objects.create(patient=self.p2, medecin=self.dr2, date=timezone.localdate(), motif="Autre")
        rec = self.get(self.dr)["consultations_recentes"]
        self.assertEqual([c["motif"] for c in rec], ["M0", "M1", "M2", "M3", "M4"])
        self.assertEqual(rec[0]["patient_cin"], "AB1")

    def test_activite_sur_7_jours(self):
        t = timezone.localdate()
        for delta, n in [(0, 2), (3, 1), (6, 3), (7, 5)]:   # J-7 hors fenêtre
            for _ in range(n):
                Consultation.objects.create(patient=self.p1, medecin=self.dr,
                                            date=t - datetime.timedelta(days=delta), motif="x")
        act = self.get(self.dr)["activite"]
        self.assertEqual(len(act), 7)
        self.assertEqual(act[-1]["date"], t.isoformat())
        self.assertEqual([x["n"] for x in act], [3, 0, 0, 1, 0, 0, 2])

    # Demain (secrétaire)
    def test_demain_par_medecin_sans_annules(self):
        self.rdv(self.dr, a(1, 9)); self.rdv(self.dr, a(1, 10), patient=self.p2)
        self.rdv(self.dr2, a(1, 9), patient=self.p2)
        self.rdv(self.dr, a(1, 11), Statut.ANNULE, motif_annulation="x")
        dem = self.get(self.sec)["demain"]
        self.assertEqual(dem["total"], 3)
        self.assertEqual(dem["par_medecin"], [{"medecin_nom": "Dr. A", "n": 2}, {"medecin_nom": "Dr. B", "n": 1}])
