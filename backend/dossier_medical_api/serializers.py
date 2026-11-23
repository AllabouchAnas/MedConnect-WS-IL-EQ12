from django.utils import timezone
from rest_framework import serializers

from patients_api.models import Patient
from .models import Consultation


class ConsultationSerializer(serializers.ModelSerializer):
    # Le client désigne le patient par son CIN ; le médecin est toujours l'utilisateur connecté.
    patient_cin = serializers.SlugRelatedField(
        source="patient", slug_field="cin", queryset=Patient.objects.all(),
        error_messages={"does_not_exist": "Patient introuvable.", "required": "Le patient est obligatoire."})
    patient_nom = serializers.CharField(source="patient.nom_complet", read_only=True)
    medecin_nom = serializers.SerializerMethodField()

    class Meta:
        model = Consultation
        fields = ["id", "patient_cin", "patient_nom", "medecin", "medecin_nom", "date", "motif",
                  "tension", "poids", "temperature", "pouls", "diagnostic", "cree_a", "modifie_a"]
        read_only_fields = ["medecin", "cree_a", "modifie_a"]
        extra_kwargs = {
            "date": {"error_messages": {"required": "La date est obligatoire.", "invalid": "Date invalide (AAAA-MM-JJ)."}},
            "motif": {"error_messages": {"required": "Le motif est obligatoire.",
                                         "blank": "Le motif est obligatoire.",
                                         "null": "Le motif est obligatoire."}},
            # Constantes renvoyées comme nombres JSON (72.5) et non comme chaînes ("72.50").
            "poids": {"coerce_to_string": False},
            "temperature": {"coerce_to_string": False},
        }

    def get_medecin_nom(self, o):
        return o.medecin.get_full_name() or o.medecin.username

    def validate_date(self, value):
        if value > timezone.localdate():
            raise serializers.ValidationError("La date de la consultation ne peut pas être dans le futur.")
        return value

    def validate(self, attrs):
        # Une consultation reste attachée au dossier du patient pour lequel elle a été créée.
        if self.instance and "patient" in attrs and attrs["patient"] != self.instance.patient:
            raise serializers.ValidationError(
                {"patient_cin": "Le patient d'une consultation ne peut pas être modifié."})
        return attrs
