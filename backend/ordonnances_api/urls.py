from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import OrdonnanceViewSet

router = DefaultRouter()
router.register(r"ordonnances", OrdonnanceViewSet, basename="ordonnance")

urlpatterns = [
    path("", include(router.urls)),
]
