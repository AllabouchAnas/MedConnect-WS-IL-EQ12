import datetime

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.utils import timezone
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from config.permissions import HasCabinetRole, ROLE_MEDECIN
from .models import RendezVous, Statut
from .serializers import RendezVousSerializer, nom_utilisateur

User = get_user_model()


class RendezVousViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin,
                        mixins.ListModelMixin, viewsets.GenericViewSet):
    """Planifier (POST), rechercher (GET /{id}/), lister, avancer, annuler. Pas de suppression."""
    serializer_class = RendezVousSerializer
    permission_classes = [HasCabinetRole]

    def get_queryset(self):
        qs = RendezVous.objects.select_related("patient", "medecin", "arrivee_par")
        p = self.request.query_params
        if p.get("date"):
            try:
                qs = qs.filter(date_heure__date=datetime.date.fromisoformat(p["date"]))
            except ValueError:
                raise ValidationError({"date": "Format de date invalide (AAAA-MM-JJ)."})
        if p.get("medecin", "").isdigit():
            qs = qs.filter(medecin_id=int(p["medecin"]))
        if p.get("statut"):
            qs = qs.filter(statut=p["statut"])
        return qs

    def perform_create(self, serializer):
        try:
            serializer.save()
        except IntegrityError:  # course critique : deux créations simultanées du même créneau
            raise ValidationError({"date_heure": "Ce médecin a déjà un rendez-vous à cette date et heure."})

    def _transition(self, request, fn):
        rdv = self.get_object()
        try:
            fn(rdv)
        except ValueError as e:
            return Response({"detail": str(e)}, status=400)
        return Response(self.get_serializer(rdv).data)

    @action(detail=True, methods=["post"])
    def avancer(self, request, pk=None):
        return self._transition(request, lambda r: r.avancer(request.user))

    @action(detail=True, methods=["post"])
    def annuler(self, request, pk=None):
        motif = request.data.get("motif_annulation", "")
        return self._transition(request, lambda r: r.annuler(motif))

    @action(detail=False, methods=["get"], url_path="salle-attente")
    def salle_attente(self, request):
        qs = (RendezVous.objects.select_related("patient", "medecin", "arrivee_par")
              .filter(date_heure__date=timezone.localdate(), statut=Statut.SALLE_ATTENTE))
        return Response(self.get_serializer(qs, many=True).data)


class MedecinListView(APIView):
    permission_classes = [HasCabinetRole]

    def get(self, request):
        users = User.objects.filter(groups__name=ROLE_MEDECIN).order_by("username")
        return Response([{"id": u.id, "username": u.username, "nom": nom_utilisateur(u)} for u in users])
