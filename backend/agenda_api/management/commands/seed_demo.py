import datetime

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.utils import timezone

from agenda_api.models import RendezVous, Statut
from patients_api.models import Patient

User = get_user_model()
MDP = "Demo@1234"


class Command(BaseCommand):
    help = "Crée les rôles, utilisateurs, patients et rendez-vous de démonstration."

    def handle(self, *args, **opts):
        med, _ = Group.objects.get_or_create(name="Medecin")
        sec, _ = Group.objects.get_or_create(name="Secretaire")
        for username, first, last, group in [("dr.demo", "Dr.", "Demo", med), ("dr.alami", "Dr.", "Alami", med),
                                             ("sec.demo", "Secrétaire", "Demo", sec)]:
            u, created = User.objects.get_or_create(username=username,
                                                    defaults={"first_name": first, "last_name": last})
            if created:
                u.set_password(MDP)
                u.save()
            u.groups.add(group)

        data = [("AB123", "Benali", "Sara", "1990-05-01", "0600000001", "O+", "Pénicilline", "0600000009"),
                ("CD456", "Alaoui", "Omar", "1985-01-02", "0600000002", "A+", "", "0600000008"),
                ("EF789", "Tazi", "Leila", "1978-11-23", "0600000003", "B+", "", "0600000007")]
        for cin, nom, prenom, nais, tel, gs, all_, urg in data:
            Patient.objects.get_or_create(cin=cin, defaults=dict(
                nom=nom, prenom=prenom, date_naissance=nais, telephone=tel,
                groupe_sanguin=gs, allergies=all_, contact_urgence=urg))

        today = timezone.localdate()
        if not RendezVous.objects.filter(date_heure__date=today).exists():
            dr = User.objects.get(username="dr.demo")
            s = User.objects.get(username="sec.demo")
            tz = timezone.get_current_timezone()
            rows = [("AB123", 9, 0, "Contrôle annuel", Statut.SALLE_ATTENTE),
                    ("CD456", 9, 30, "Toux persistante", Statut.CONSULTATION),
                    ("EF789", 10, 0, "Renouvellement", Statut.PLANIFIE),
                    ("AB123", 10, 30, "Suivi", Statut.ANNULE)]
            for cin, h, m, motif, statut in rows:
                dt = datetime.datetime.combine(today, datetime.time(h, m), tzinfo=tz)
                r = RendezVous(patient=Patient.objects.get(cin=cin), medecin=dr, date_heure=dt,
                               motif=motif, statut=statut)
                if statut in (Statut.SALLE_ATTENTE, Statut.CONSULTATION):
                    r.arrivee_a, r.arrivee_par = dt - datetime.timedelta(minutes=8), s
                if statut == Statut.ANNULE:
                    r.motif_annulation = "Patient indisponible"
                r.save()
        self.stdout.write(self.style.SUCCESS(
            f"Données de démo prêtes. Comptes : dr.demo / sec.demo (mot de passe {MDP})"))
