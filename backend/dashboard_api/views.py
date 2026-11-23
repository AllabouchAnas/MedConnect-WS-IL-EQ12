import datetime

from django.db.models import Count
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from agenda_api.models import RendezVous, Statut
from agenda_api.serializers import nom_utilisateur
from config.permissions import HasCabinetRole, ROLE_MEDECIN, ROLE_SECRETAIRE, role_of
from dossier_medical_api.models import Consultation
from patients_api.models import Patient

RESTANTS = (Statut.PLANIFIE, Statut.SALLE_ATTENTE, Statut.CONSULTATION)


def _rdv(r):
    return {"id": r.id, "heure": timezone.localtime(r.date_heure).strftime("%H:%M"),
            "patient_cin": r.patient.cin, "patient_nom": r.patient.nom_complet,
            "medecin_nom": nom_utilisateur(r.medecin), "motif": r.motif, "statut": r.statut,
            "motif_annulation": r.motif_annulation}


def _attente(r, maintenant):
    minutes = None
    if r.arrivee_a:
        minutes = max(0, int((maintenant - r.arrivee_a).total_seconds() // 60))
    return {"id": r.id, "patient_nom": r.patient.nom_complet, "medecin_nom": nom_utilisateur(r.medecin),
            "heure": timezone.localtime(r.date_heure).strftime("%H:%M"),
            "arrivee_heure": timezone.localtime(r.arrivee_a).strftime("%H:%M") if r.arrivee_a else None,
            "attente_min": minutes}


class DashboardView(APIView):
    """Page d'accueil : indicateurs et listes courtes du jour, adaptés au rôle.

    Médecin   : ses propres rendez-vous + ses consultations (données médicales).
    Secrétaire: les rendez-vous de tous les médecins, AUCUNE donnée médicale dans la réponse.
    """
    permission_classes = [HasCabinetRole]

    def get(self, request):
        user = request.user
        est_medecin = role_of(user) == ROLE_MEDECIN
        maintenant = timezone.now()
        aujourdhui = timezone.localdate()

        rdv_qs = RendezVous.objects.select_related("patient", "medecin")
        if est_medecin:
            rdv_qs = rdv_qs.filter(medecin=user)
        jour = list(rdv_qs.filter(date_heure__date=aujourdhui))
        en_attente = [r for r in jour if r.statut == Statut.SALLE_ATTENTE]
        attentes = [a for a in (_attente(r, maintenant) for r in en_attente)]
        durees = [a["attente_min"] for a in attentes if a["attente_min"] is not None]

        lundi = aujourdhui - datetime.timedelta(days=aujourdhui.weekday())
        annulations_semaine = rdv_qs.filter(
            statut=Statut.ANNULE, date_heure__date__gte=lundi,
            date_heure__date__lte=lundi + datetime.timedelta(days=6)).count()

        data = {
            "role": ROLE_MEDECIN if est_medecin else ROLE_SECRETAIRE,
            "nom": nom_utilisateur(user),
            "date": aujourdhui.isoformat(),
            "kpis": {
                "rdv_total": len(jour),
                "termines": sum(r.statut == Statut.TERMINE for r in jour),
                "restants": sum(r.statut in RESTANTS for r in jour),
                "annules": sum(r.statut == Statut.ANNULE for r in jour),
                "en_attente": len(en_attente),
                "attente_moyenne_min": round(sum(durees) / len(durees)) if durees else None,
                "patients_total": Patient.objects.count(),
                "annulations_semaine": annulations_semaine,
            },
            "rdvs": [_rdv(r) for r in jour],
            "salle_attente": attentes,
        }

        if est_medecin:
            # Données médicales : uniquement dans la réponse destinée au médecin.
            recentes = Consultation.objects.filter(medecin=user).select_related("patient")[:5]
            data["consultations_recentes"] = [
                {"id": c.id, "patient_cin": c.patient.cin, "patient_nom": c.patient.nom_complet,
                 "date": c.date.isoformat(), "motif": c.motif} for c in recentes]
            debut = aujourdhui - datetime.timedelta(days=6)
            par_jour = dict(Consultation.objects.filter(medecin=user, date__gte=debut, date__lte=aujourdhui)
                            .values_list("date").annotate(n=Count("id")))
            data["activite"] = [{"date": (debut + datetime.timedelta(days=i)).isoformat(),
                                 "n": par_jour.get(debut + datetime.timedelta(days=i), 0)} for i in range(7)]
        else:
            demain = aujourdhui + datetime.timedelta(days=1)
            rdvs_demain = (RendezVous.objects.select_related("medecin").filter(date_heure__date=demain)
                           .exclude(statut=Statut.ANNULE))
            par_medecin = {}
            for r in rdvs_demain:
                nom = nom_utilisateur(r.medecin)
                par_medecin[nom] = par_medecin.get(nom, 0) + 1
            data["demain"] = {"date": demain.isoformat(), "total": sum(par_medecin.values()),
                              "par_medecin": [{"medecin_nom": k, "n": v} for k, v in sorted(par_medecin.items())]}
        return Response(data)
