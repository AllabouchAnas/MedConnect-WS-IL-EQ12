from django.contrib import admin
from .models import Consultation


@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "medecin", "date", "motif")
    list_filter = ("medecin", "date")
    search_fields = ("patient__cin", "patient__nom", "motif", "diagnostic")
