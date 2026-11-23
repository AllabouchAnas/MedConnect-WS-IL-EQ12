from rest_framework import viewsets
from config.permissions import IsMedecin, HasCabinetRole
from .models import Consultation
from .serializers import ConsultationSerializer


class ConsultationViewSet(viewsets.ModelViewSet):
    """
    Gestion des consultations du dossier médical.
    Consultation réservée au personnel médical / cabinet, écriture réservée au Médecin.
    """
    queryset = Consultation.objects.all()
    serializer_class = ConsultationSerializer

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsMedecin()]
        return [HasCabinetRole()]

    def get_queryset(self):
        qs = Consultation.objects.select_related("patient", "medecin")
        cin = self.request.query_params.get("patient") or self.request.query_params.get("cin")
        if cin:
            qs = qs.filter(patient__cin__iexact=cin.strip())
        return qs
