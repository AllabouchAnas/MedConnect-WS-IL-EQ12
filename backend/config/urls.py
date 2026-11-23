from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView
from rest_framework_simplejwt.views import TokenRefreshView

from agenda_api.auth_views import LoginView, LogoutView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/login/", LoginView.as_view()),
    path("api/auth/refresh/", TokenRefreshView.as_view()),
    path("api/auth/logout/", LogoutView.as_view()),
    path("api/", include("agenda_api.urls")),
    path("api/", include("patients_api.urls")),
    path("api/", include("dossier_medical_api.urls")),
    path("", TemplateView.as_view(template_name="index.html")),
]
