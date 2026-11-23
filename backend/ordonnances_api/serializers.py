from rest_framework import serializers
from .models import Ordonnance, LigneOrdonnance
from patients_api.models import Patient
from dossier_medical_api.models import Consultation


class LigneOrdonnanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = LigneOrdonnance
        fields = ["id", "medicament", "dosage", "posologie", "duree_jours"]


class OrdonnanceSerializer(serializers.ModelSerializer):
    patient_cin = serializers.CharField(write_only=True)
    patient_nom = serializers.CharField(source="patient.nom", read_only=True)
    patient_prenom = serializers.CharField(source="patient.prenom", read_only=True)
    patient_allergies = serializers.CharField(source="patient.allergies", read_only=True)
    medecin_nom = serializers.CharField(source="medecin.get_full_name", read_only=True)
    lignes = LigneOrdonnanceSerializer(many=True, read_only=True)
    nb_lignes = serializers.IntegerField(source="lignes.count", read_only=True)

    class Meta:
        model = Ordonnance
        fields = [
            "id", "patient", "patient_cin", "patient_nom", "patient_prenom", "patient_allergies",
            "medecin", "medecin_nom", "consultation", "date", "est_validee", "lignes", "nb_lignes", "cree_a"
        ]
        read_only_fields = ["id", "patient", "medecin", "est_validee", "cree_a"]

    def create(self, validated_data):
        cin = validated_data.pop("patient_cin")
        try:
            patient = Patient.objects.get(cin__iexact=cin)
        except Patient.DoesNotExist:
            raise serializers.ValidationError({"patient_cin": f"Patient avec CIN '{cin}' introuvable."})

        request = self.context.get("request")
        medecin = request.user if request and request.user.is_authenticated else None
        return Ordonnance.objects.create(patient=patient, medecin=medecin, **validated_data)
