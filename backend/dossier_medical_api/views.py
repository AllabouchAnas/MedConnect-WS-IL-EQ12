import datetime

from django.db.models import Q
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError

from config.permissions import IsMedecin
from .models import Consultation
from .serializers import ConsultationSerializer


def _date_param(params, name):
    if not params.get(name):
        return None
    try:
        return datetime.date.fromisoformat(params[name])
    except ValueError:
        raise ValidationError({name: "Format de date invalide (AAAA-MM-JJ)."})


class ConsultationViewSet(viewsets.ModelViewSet):
    """Dossier médical : consultations (accès réservé aux médecins).

    GET    /api/consultations/?patient=CIN   historique d'un patient (liste vide si aucune)
    POST   /api/consultations/               ajouter (motif obligatoire, médecin = utilisateur connecté)
    GET    /api/consultations/{id}/          consulter
    PATCH  /api/consultations/{id}/          modifier (le patient ne change pas)
    DELETE /api/consultations/{id}/          supprimer
    Filtres optionnels : medecin, date_debut, date_fin, search (motif / diagnostic).
    """
    serializer_class = ConsultationSerializer
    permission_classes = [IsMedecin]

    def get_queryset(self):
        qs = Consultation.objects.select_related("patient", "medecin")
        p = self.request.query_params
        if p.get("patient"):
            qs = qs.filter(patient__cin__iexact=p["patient"].strip())
        if p.get("medecin", "").isdigit():
            qs = qs.filter(medecin_id=int(p["medecin"]))
        debut, fin = _date_param(p, "date_debut"), _date_param(p, "date_fin")
        if debut:
            qs = qs.filter(date__gte=debut)
        if fin:
            qs = qs.filter(date__lte=fin)
        if p.get("search"):
            qs = qs.filter(Q(motif__icontains=p["search"]) | Q(diagnostic__icontains=p["search"]))
        return qs

    def perform_create(self, serializer):
        serializer.save(medecin=self.request.user)
