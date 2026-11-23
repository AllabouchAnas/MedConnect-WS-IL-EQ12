from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from patients_api.models import Patient


class Statut(models.TextChoices):
    PLANIFIE = "Planifié", "Planifié"
    SALLE_ATTENTE = "Salle d'attente", "Salle d'attente"
    CONSULTATION = "Consultation", "Consultation"
    TERMINE = "Terminé", "Terminé"
    ANNULE = "Annulé", "Annulé"


STATUTS_ORDONNES = [Statut.PLANIFIE, Statut.SALLE_ATTENTE, Statut.CONSULTATION, Statut.TERMINE]


class RendezVous(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name="rendez_vous")
    medecin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                                related_name="rendez_vous_medecin")
    date_heure = models.DateTimeField()
    motif = models.CharField(max_length=255, blank=True)
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.PLANIFIE)
    motif_annulation = models.CharField(max_length=255, blank=True)
    arrivee_a = models.DateTimeField(null=True, blank=True)
    arrivee_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                    on_delete=models.SET_NULL, related_name="+")
    cree_a = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date_heure"]
        verbose_name_plural = "rendez-vous"
        constraints = [
            # Un médecin ne peut avoir qu'un RDV actif par créneau (garde-fou au niveau base).
            models.UniqueConstraint(
                fields=["medecin", "date_heure"],
                condition=~Q(statut="Annulé"),
                name="uniq_creneau_medecin_actif",
            )
        ]

    def __str__(self):
        return f"RDV {self.pk} - {self.patient.cin} - {self.date_heure:%d/%m/%Y %H:%M}"

    def avancer(self, user=None):
        """Planifié → Salle d'attente → Consultation → Terminé."""
        if self.statut == Statut.ANNULE:
            raise ValueError("Impossible d'avancer le statut d'un rendez-vous annulé.")
        if self.statut == Statut.TERMINE:
            raise ValueError("Le rendez-vous est déjà terminé.")
        if self.statut == Statut.PLANIFIE:
            self.arrivee_a = timezone.now()
            self.arrivee_par = user
        self.statut = STATUTS_ORDONNES[STATUTS_ORDONNES.index(self.statut) + 1]
        self.save()

    def annuler(self, motif):
        """Passe à « Annulé » sans supprimer le rendez-vous."""
        if self.statut == Statut.ANNULE:
            raise ValueError("Ce rendez-vous est déjà annulé.")
        if self.statut == Statut.TERMINE:
            raise ValueError("Impossible d'annuler un rendez-vous terminé.")
        if not motif or not motif.strip():
            raise ValueError("Le motif d'annulation est obligatoire.")
        self.statut = Statut.ANNULE
        self.motif_annulation = motif.strip()
        self.save()
