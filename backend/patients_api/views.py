from django.db.models import Q
from rest_framework import serializers, viewsets

from config.permissions import HasCabinetRole
from .models import Patient


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = [
            "id", "cin", "nom", "prenom", "date_naissance", "telephone",
            "groupe_sanguin", "allergies", "contact_urgence"
        ]

    def validate_cin(self, value):
        val = value.strip().upper()
        qs = Patient.objects.filter(cin__iexact=val)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Un patient avec ce CIN existe déjà.")
        return val

    def validate_telephone(self, value):
        val = value.strip()
        qs = Patient.objects.filter(telephone=val)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Un patient avec ce numéro de téléphone existe déjà.")
        return val


class PatientViewSet(viewsets.ModelViewSet):
    """CRUD complet pour les patients : accessible Médecin et Secrétaire."""
    queryset = Patient.objects.all().order_by("nom", "prenom")
    serializer_class = PatientSerializer
    permission_classes = [HasCabinetRole]
    lookup_field = "cin"

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.query_params.get("search") or self.request.query_params.get("q")
        if q:
            qs = qs.filter(Q(cin__icontains=q) | Q(nom__icontains=q) | Q(prenom__icontains=q))
        return qs
