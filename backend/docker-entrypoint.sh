#!/bin/sh
# Démarrage du conteneur : migrations, fichiers statiques, données de démo (facultatif), puis le serveur.
set -e

python manage.py migrate --noinput
python manage.py collectstatic --noinput

if [ "${SEED_DEMO:-0}" = "1" ]; then
    # Idempotent : ne recrée rien si les données existent déjà.
    python manage.py seed_demo
    python manage.py seed_dossier
fi

exec "$@"
