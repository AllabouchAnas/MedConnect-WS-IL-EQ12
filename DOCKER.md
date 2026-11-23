# MedConnect avec Docker

Application Django (gunicorn) + PostgreSQL, lancées ensemble par une seule commande.

## Lancer

```bash
docker compose up --build
```

Puis ouvrir http://localhost:8000 — comptes de démo `dr.demo` / `sec.demo`, mot de passe `Demo@1234`.
Au démarrage, le conteneur applique les migrations, prépare les fichiers statiques et crée les données de démo.

## Commandes utiles

| Action | Commande |
|---|---|
| Lancer en arrière-plan | `docker compose up -d --build` |
| Voir les journaux | `docker compose logs -f web` |
| Arrêter (les données restent) | `docker compose down` |
| Tout effacer, base comprise | `docker compose down -v` |
| Lancer les tests dans le conteneur | `docker compose run --rm -e SEED_DEMO=0 web python manage.py test` |
| Créer un administrateur | `docker compose exec web python manage.py createsuperuser` |

## Variables (facultatives)

À définir dans l'environnement ou dans un fichier `.env` placé à côté de `docker-compose.yml` (ne pas le commiter).

| Variable | Valeur par défaut | Rôle |
|---|---|---|
| `DJANGO_SECRET_KEY` | clé de développement du compose | **À changer** hors démonstration |
| `DB_PASSWORD` | `medconnect-dev` | mot de passe PostgreSQL |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | noms de domaine acceptés |
| `SEED_DEMO` | `1` | `0` = ne pas créer les comptes et données de démo |

## Fichiers

- `docker-compose.yml` : services `web` et `db` (+ volume `pgdata`)
- `backend/Dockerfile`, `backend/docker-entrypoint.sh`, `backend/.dockerignore`
- `backend/config/settings_docker.py` : réglages du conteneur (WhiteNoise pour `/static`, refus de la clé secrète publique du dépôt). `config/settings.py` n'est pas modifié.
