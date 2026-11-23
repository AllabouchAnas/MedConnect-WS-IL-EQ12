from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import MedecinListView, RendezVousViewSet

router = DefaultRouter()
router.register("agenda/rdv", RendezVousViewSet, basename="rdv")

urlpatterns = [path("agenda/medecins/", MedecinListView.as_view())] + router.urls
