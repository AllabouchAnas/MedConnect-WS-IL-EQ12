from django.conf import settings
from django.db import models
from patients_api.models import Patient


class Consultation(models.Model):
    """Représente un acte médical dans le dossier d'un patient."""
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="consultations")
    medecin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="consultations")
    date = models.DateField()
    motif = models.CharField(max_length=255)
    diagnostic = models.TextField(blank=True)
    cree_a = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-id"]
        verbose_name = "Consultation"
        verbose_name_plural = "Consultations"

    def __str__(self):
        return f"Consultation {self.id} - {self.patient.cin} ({self.date})"
