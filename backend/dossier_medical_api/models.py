from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models

from patients_api.models import Patient

# Tension artérielle : « 12/8 » (cmHg) ou « 120/80 » (mmHg).
validateur_tension = RegexValidator(r"^\d{2,3}/\d{1,3}$", "Format attendu : 12/8 ou 120/80.")


class Consultation(models.Model):
    """Une consultation médicale dans le dossier d'un patient (module Dossier Médical, F005)."""

    # PROTECT : on ne supprime jamais l'historique clinique en cascade.
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name="consultations")
    medecin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                                related_name="consultations_medecin")
    date = models.DateField()
    motif = models.CharField(max_length=255)  # obligatoire
    tension = models.CharField(max_length=7, blank=True, validators=[validateur_tension])
    poids = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,  # kg
                                validators=[MinValueValidator(Decimal("0.5")), MaxValueValidator(Decimal("500"))])
    temperature = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True,  # °C
                                      validators=[MinValueValidator(Decimal("30")),
                                                  MaxValueValidator(Decimal("45"))])
    pouls = models.PositiveSmallIntegerField(null=True, blank=True,  # bpm
                                             validators=[MinValueValidator(20), MaxValueValidator(300)])
    diagnostic = models.TextField(blank=True)
    cree_a = models.DateTimeField(auto_now_add=True)
    modifie_a = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-id"]  # historique : le plus récent d'abord

    def __str__(self):
        return f"Consultation {self.pk} - {self.patient.cin} - {self.date:%d/%m/%Y}"
