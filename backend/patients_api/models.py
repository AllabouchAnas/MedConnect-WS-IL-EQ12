from django.db import models


class Patient(models.Model):
    cin = models.CharField(max_length=20, unique=True)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    date_naissance = models.DateField()
    telephone = models.CharField(max_length=20, unique=True)
    groupe_sanguin = models.CharField(max_length=5, blank=True)
    allergies = models.TextField(blank=True)
    contact_urgence = models.CharField(max_length=20, blank=True)

    class Meta:
        ordering = ["nom", "prenom"]

    @property
    def nom_complet(self):
        return f"{self.prenom} {self.nom}"

    def __str__(self):
        return f"{self.cin} - {self.nom_complet}"
