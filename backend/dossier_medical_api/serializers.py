from rest_framework import serializers
from .models import Consultation
from patients_api.models import Patient


class ConsultationSerializer(serializers.ModelSerializer):
    patient_cin = serializers.CharField(write_only=True)
    patient_nom = serializers.CharField(source="patient.nom", read_only=True)
    patient_prenom = serializers.CharField(source="patient.prenom", read_only=True)
    medecin_nom = serializers.CharField(source="medecin.get_full_name", read_only=True)

    class Meta:
        model = Consultation
        fields = [
            "id", "patient", "patient_cin", "patient_nom", "patient_prenom",
            "medecin", "medecin_nom", "date", "motif", "diagnostic", "cree_a"
        ]
        read_only_fields = ["id", "patient", "medecin", "cree_a"]

    def validate_motif(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Le motif de la consultation est obligatoire.")
        return value.strip()

    def create(self, validated_data):
        cin = validated_data.pop("patient_cin")
        try:
            patient = Patient.objects.get(cin__iexact=cin)
        except Patient.DoesNotExist:
            raise serializers.ValidationError({"patient_cin": f"Patient avec CIN '{cin}' introuvable."})

        request = self.context.get("request")
        medecin = request.user if request and request.user.is_authenticated else None
        return Consultation.objects.create(patient=patient, medecin=medecin, **validated_data)
