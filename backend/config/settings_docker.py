"""Réglages utilisés dans le conteneur Docker (DJANGO_SETTINGS_MODULE=config.settings_docker).

Reprend config/settings.py sans le modifier, et ajoute ce qu'il faut pour un serveur réel :
fichiers statiques servis par WhiteNoise (gunicorn ne sert pas /static) et refus de démarrer
avec la clé secrète de développement qui est écrite dans le dépôt.
"""
from django.core.exceptions import ImproperlyConfigured

from .settings import *  # noqa: F401,F403
from .settings import BASE_DIR, DEBUG, MIDDLEWARE, SECRET_KEY

if not DEBUG and SECRET_KEY.startswith("medconnect-dev-secret-key"):
    raise ImproperlyConfigured(
        "DJANGO_SECRET_KEY doit être défini (la clé de développement du dépôt est publique).")

MIDDLEWARE = list(MIDDLEWARE)
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")  # juste après SecurityMiddleware

STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}
