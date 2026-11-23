from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

from config.permissions import ROLE_MEDECIN
from patients_api.models import Patient
from .models import RendezVous, Statut

User = get_user_model()


def nom_utilisateur(u):
    return (u.get_full_name() or u.username) if u else None


class RendezVousSerializer(serializers.ModelSerializer):
    patient = serializers.SlugRelatedField(
        slug_field="cin", queryset=Patient.objects.all(),
        error_messages={"does_not_exist": "Patient introuvable.", "required": "Le patient est obligatoire."})
    medecin = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(groups__name=ROLE_MEDECIN),
        error_messages={"does_not_exist": "Médecin introuvable.", "required": "Le médecin est obligatoire.",
                        "incorrect_type": "Médecin invalide."})
    patient_nom = serializers.CharField(source="patient.nom_complet", read_only=True)
    medecin_nom = serializers.SerializerMethodField()
    arrivee_par_nom = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()
    heure = serializers.SerializerMethodField()
    arrivee_heure = serializers.SerializerMethodField()

    class Meta:
        model = RendezVous
        fields = ["id", "patient", "patient_nom", "medecin", "medecin_nom", "date_heure", "date", "heure",
                  "motif", "statut", "motif_annulation", "arrivee_a", "arrivee_heure", "arrivee_par_nom"]
        read_only_fields = ["statut", "motif_annulation", "arrivee_a"]
        validators = []  # le conflit de créneau est géré dans validate() (RDV annulés exclus)
        extra_kwargs = {"date_heure": {"error_messages": {
            "required": "La date et l'heure sont obligatoires.", "invalid": "Date et heure invalides."}}}

    def get_medecin_nom(self, o):
        return nom_utilisateur(o.medecin)

    def get_arrivee_par_nom(self, o):
        return o.arrivee_par.username if o.arrivee_par else None

    def get_date(self, o):
        return timezone.localtime(o.date_heure).date().isoformat()

    def get_heure(self, o):
        return timezone.localtime(o.date_heure).strftime("%H:%M")

    def get_arrivee_heure(self, o):
        return timezone.localtime(o.arrivee_a).strftime("%H:%M") if o.arrivee_a else None

    def validate_date_heure(self, value):
        return value.replace(second=0, microsecond=0)

    def validate(self, attrs):
        conflit = (RendezVous.objects.filter(medecin=attrs["medecin"], date_heure=attrs["date_heure"])
                   .exclude(statut=Statut.ANNULE).select_related("patient").first())
        if conflit:
            h = timezone.localtime(conflit.date_heure).strftime("%H:%M")
            raise serializers.ValidationError({"date_heure": (
                f"Créneau {h} indisponible : consultation déjà enregistrée avec {conflit.patient.nom_complet}.")})
        return attrs
