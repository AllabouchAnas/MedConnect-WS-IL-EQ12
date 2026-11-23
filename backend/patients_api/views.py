from django.db.models import Q
from rest_framework import serializers, viewsets

from config.permissions import HasCabinetRole
from .models import Patient


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ["cin", "nom", "prenom", "date_naissance", "telephone",
                  "groupe_sanguin", "allergies", "contact_urgence"]


class PatientViewSet(viewsets.ReadOnlyModelViewSet):
    """Lecture seule : sert à choisir le patient lors de la planification d'un RDV."""
    serializer_class = PatientSerializer
    permission_classes = [HasCabinetRole]
    lookup_field = "cin"

    def get_queryset(self):
        qs = Patient.objects.all()
        q = self.request.query_params.get("search")
        if q:
            qs = qs.filter(Q(cin__icontains=q) | Q(nom__icontains=q) | Q(prenom__icontains=q))
        return qs
