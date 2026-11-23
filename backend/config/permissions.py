from rest_framework.permissions import BasePermission

ROLE_MEDECIN = "Medecin"
ROLE_SECRETAIRE = "Secretaire"


def role_of(user):
    names = set(user.groups.values_list("name", flat=True))
    if ROLE_MEDECIN in names:
        return ROLE_MEDECIN
    if ROLE_SECRETAIRE in names:
        return ROLE_SECRETAIRE
    return None


class IsMedecin(BasePermission):
    """Dossier médical : réservé aux médecins (la secrétaire n'y a pas accès, côté API)."""
    message = "Accès réservé aux médecins : le dossier médical est confidentiel."

    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and (u.is_superuser or role_of(u) == ROLE_MEDECIN))


class HasCabinetRole(BasePermission):
    """Agenda / patients / salle d'attente : Médecin ou Secrétaire (contrôle côté API)."""
    message = "Accès refusé : rôle Médecin ou Secrétaire requis."

    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and (u.is_superuser or role_of(u)))
