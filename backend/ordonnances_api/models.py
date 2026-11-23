from django.conf import settings
from django.db import models
from patients_api.models import Patient
from dossier_medical_api.models import Consultation


class Ordonnance(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="ordonnances")
    medecin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="ordonnances")
    consultation = models.ForeignKey(Consultation, null=True, blank=True, on_delete=models.SET_NULL, related_name="ordonnances")
    date = models.DateField()
    est_validee = models.BooleanField(default=False)
    cree_a = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]
        verbose_name = "Ordonnance"
        verbose_name_plural = "Ordonnances"

    def __str__(self):
        stat = "Validée" if self.est_validee else "Brouillon"
        return f"Ordonnance {self.id} - {self.patient.cin} ({stat})"

    def valider(self):
        self.est_validee = True
        self.save()


class LigneOrdonnance(models.Model):
    ordonnance = models.ForeignKey(Ordonnance, on_delete=models.CASCADE, related_name="lignes")
    medicament = models.CharField(max_length=200)
    dosage = models.CharField(max_length=100)
    posologie = models.CharField(max_length=255)
    duree_jours = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.medicament} {self.dosage} ({self.duree_jours} jours)"
