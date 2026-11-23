from datetime import date
from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand
from django.utils import timezone

from agenda_api.models import RendezVous, Statut
from config.permissions import ROLE_MEDECIN, ROLE_SECRETAIRE
from patients_api.models import Patient
from dossier_medical_api.models import Consultation
from ordonnances_api.models import Ordonnance, LigneOrdonnance


class Command(BaseCommand):
    help = "Initialise les données de démonstration conformes au SFD V4 (F001 à F007)."

    def handle(self, *args, **options):
        # 1. Groupes et rôles
        grp_med, _ = Group.objects.get_or_create(name=ROLE_MEDECIN)
        grp_sec, _ = Group.objects.get_or_create(name=ROLE_SECRETAIRE)

        # 2. Utilisateurs
        dr, _ = User.objects.get_or_create(username="dr.demo", defaults={
            "first_name": "Dr.", "last_name": "Demo", "email": "dr.demo@medconnect.ma",
            "is_staff": True
        })
        dr.set_password("Demo@1234")
        dr.save()
        dr.groups.set([grp_med])

        sec, _ = User.objects.get_or_create(username="sec.demo", defaults={
            "first_name": "Secrétaire", "last_name": "Démo", "email": "sec.demo@medconnect.ma",
            "is_staff": True
        })
        sec.set_password("Demo@1234")
        sec.save()
        sec.groups.set([grp_sec])

        # 3. Patients (Figures 2 & 5)
        patients_data = [
            {"cin": "CD456", "nom": "Alaoui", "prenom": "Omar", "date_naissance": date(1985, 1, 2), "telephone": "0600000002"},
            {"cin": "AB123", "nom": "Benali", "prenom": "Sara", "date_naissance": date(1990, 5, 1), "telephone": "0600000001",
             "groupe_sanguin": "O+", "allergies": "Pénicilline", "contact_urgence": "0600000009"},
            {"cin": "EF789", "nom": "Tazi", "prenom": "Leila", "date_naissance": date(1978, 11, 23), "telephone": "0600000003"},
        ]
        patients = {}
        for p in patients_data:
            obj, _ = Patient.objects.update_or_create(cin=p["cin"], defaults=p)
            patients[p["cin"]] = obj

        # 4. Rendez-vous (Figures 7 à 11)
        tz = timezone.get_current_timezone()
        rdv_data = [
            {"patient": patients["AB123"], "medecin": dr, "date_heure": timezone.datetime(2026, 11, 13, 9, 0, tzinfo=tz),
             "motif": "Contrôle annuel", "statut": Statut.SALLE_ATTENTE},
            {"patient": patients["CD456"], "medecin": dr, "date_heure": timezone.datetime(2026, 11, 13, 9, 30, tzinfo=tz),
             "motif": "Toux persistante", "statut": Statut.CONSULTATION},
            {"patient": patients["EF789"], "medecin": dr, "date_heure": timezone.datetime(2026, 11, 13, 10, 0, tzinfo=tz),
             "motif": "Renouvellement", "statut": Statut.PLANIFIE},
            {"patient": patients["AB123"], "medecin": dr, "date_heure": timezone.datetime(2026, 11, 13, 10, 30, tzinfo=tz),
             "motif": "Suivi", "statut": Statut.ANNULE, "motif_annulation": "Patient indisponible"},
        ]
        for r in rdv_data:
            RendezVous.objects.update_or_create(patient=r["patient"], medecin=r["medecin"], date_heure=r["date_heure"], defaults=r)

        # 5. Consultations (Figure 13)
        c1, _ = Consultation.objects.update_or_create(
            patient=patients["AB123"], medecin=dr, date=date(2026, 10, 14),
            defaults={"motif": "Fièvre et toux", "diagnostic": "Bronchite virale — repos et hydratation, contrôle dans 7 jours."}
        )
        c2, _ = Consultation.objects.update_or_create(
            patient=patients["AB123"], medecin=dr, date=date(2025, 10, 9),
            defaults={"motif": "Contrôle annuel", "diagnostic": "RAS"}
        )

        # 6. Ordonnances (Figures 13, 18, 20, 22)
        # Ordonnance N° 1 (Validée)
        o1, _ = Ordonnance.objects.update_or_create(
            patient=patients["AB123"], medecin=dr, date=date(2026, 11, 13), est_validee=True,
            defaults={"consultation": c1}
        )
        LigneOrdonnance.objects.get_or_create(ordonnance=o1, medicament="Paracétamol", dosage="1000 mg", posologie="3 fois par jour", duree_jours=5)
        LigneOrdonnance.objects.get_or_create(ordonnance=o1, medicament="Ibuprofène", dosage="400 mg", posologie="2 fois par jour", duree_jours=3)

        # Ordonnance N° 2 (Brouillon)
        o2, _ = Ordonnance.objects.update_or_create(
            patient=patients["AB123"], medecin=dr, date=date(2026, 11, 13), est_validee=False
        )
        LigneOrdonnance.objects.get_or_create(ordonnance=o2, medicament="Paracétamol", dosage="1000 mg", posologie="3 fois par jour", duree_jours=5)

        self.stdout.write(self.style.SUCCESS("✅ Données de démonstration initialisées avec succès !"))
        self.stdout.write(self.style.SUCCESS("   Comptes : dr.demo / sec.demo  |  Mot de passe : Demo@1234"))
