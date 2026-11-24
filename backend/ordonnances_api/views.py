from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from config.permissions import IsMedecin, HasCabinetRole
from .models import Ordonnance, LigneOrdonnance
from .serializers import OrdonnanceSerializer, LigneOrdonnanceSerializer


class OrdonnanceViewSet(viewsets.ModelViewSet):
    """
    Gestion des ordonnances :
    Création, ajout de lignes avec contrôle d'allergie, validation et export.
    """
    queryset = Ordonnance.objects.all().prefetch_related("lignes", "patient", "medecin")
    serializer_class = OrdonnanceSerializer

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy", "ajouter_ligne", "valider"]:
            return [IsMedecin()]
        return [HasCabinetRole()]

    def get_queryset(self):
        qs = super().get_queryset()
        cin = self.request.query_params.get("patient") or self.request.query_params.get("cin")
        if cin:
            qs = qs.filter(patient__cin__iexact=cin.strip())
        return qs

    @action(detail=True, methods=["post"], url_path="ajouter-ligne")
    def ajouter_ligne(self, request, pk=None):
        ordonnance = self.get_object()

        # Règle d'immutabilité : refus si validée
        if ordonnance.est_validee:
            return Response(
                {"detail": "Modification refusée : l'ordonnance est validée."},
                status=status.HTTP_400_BAD_REQUEST
            )

        medicament = (request.data.get("medicament") or "").strip()
        dosage = (request.data.get("dosage") or "").strip()
        posologie = (request.data.get("posologie") or "").strip()
        duree = request.data.get("duree_jours") or request.data.get("duree") or 1

        if not medicament:
            return Response({"medicament": "Le nom du médicament est obligatoire."}, status=status.HTTP_400_BAD_REQUEST)

        # Règle F006 : Alerte d'allergie en temps réel (Figure 18)
        patient_allergies = [a.strip().lower() for a in (ordonnance.patient.allergies or "").split(",") if a.strip()]
        if medicament.lower() in patient_allergies or any(a in medicament.lower() for a in patient_allergies):
            return Response(
                {"detail": f"Médicament refusé : le patient est allergique à {ordonnance.patient.allergies}."},
                status=status.HTTP_400_BAD_REQUEST
            )

        ligne = LigneOrdonnance.objects.create(
            ordonnance=ordonnance,
            medicament=medicament,
            dosage=dosage,
            posologie=posologie,
            duree_jours=int(duree)
        )
        return Response(LigneOrdonnanceSerializer(ligne).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="valider")
    def valider(self, request, pk=None):
        ordonnance = self.get_object()
        ordonnance.valider()
        return Response(OrdonnanceSerializer(ordonnance).data, status=status.HTTP_200_OK)
