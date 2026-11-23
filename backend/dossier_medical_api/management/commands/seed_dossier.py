import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from dossier_medical_api.models import Consultation
from patients_api.models import Patient

User = get_user_model()

# (cin, jours avant aujourd'hui, motif, tension, poids, température, pouls, diagnostic)
DEMO = [
    ("AB123", 120, "Contrôle annuel", "12/8", "61.5", "36.8", 72, "RAS. Bilan sanguin à refaire dans un an."),
    ("AB123", 14, "Toux persistante", "11/7", "61.0", "37.6", 84, "Bronchite virale, repos et hydratation."),
    ("CD456", 30, "Douleurs lombaires", "13/8", "82.0", "36.9", 76, "Lombalgie commune, antalgiques."),
    # Récentes : alimentent le graphique « 7 derniers jours » de la page d'accueil.
    ("AB123", 1, "Contrôle tension", "12/8", "61.0", "36.7", 70, "Tension normale, traitement inchangé."),
    ("CD456", 3, "Suivi lombalgie", "13/8", "81.5", "36.8", 74, "Amélioration, poursuite de la kinésithérapie."),
]


class Command(BaseCommand):
    help = "Ajoute des consultations de démonstration (à lancer après seed_demo)."

    def handle(self, *args, **opts):
        dr = User.objects.filter(username="dr.demo").first()
        if dr is None:
            raise CommandError("Utilisateur dr.demo introuvable : lancez d'abord « python manage.py seed_demo ».")
        today, crees = timezone.localdate(), 0
        deja_renseignes = set(Consultation.objects.values_list("patient__cin", flat=True))  # état initial
        for cin, jours, motif, ta, poids, temp, pouls, diag in DEMO:
            patient = Patient.objects.filter(cin=cin).first()
            if patient is None or cin in deja_renseignes:
                continue  # idempotent : on n'ajoute rien au dossier d'un patient déjà renseigné
            Consultation.objects.create(
                patient=patient, medecin=dr, date=today - datetime.timedelta(days=jours), motif=motif,
                tension=ta, poids=Decimal(poids), temperature=Decimal(temp), pouls=pouls, diagnostic=diag)
            crees += 1
        self.stdout.write(self.style.SUCCESS(f"{crees} consultation(s) de démonstration ajoutée(s)."))
