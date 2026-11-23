FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_SETTINGS_MODULE=config.settings_docker

WORKDIR /app

# Dépendances d'abord : cette couche est mise en cache tant que requirements.txt ne change pas.
COPY requirements.txt .
RUN pip install -r requirements.txt gunicorn whitenoise psycopg2-binary

COPY . .
# sed : sous Windows, git peut convertir le script en fins de ligne CRLF, ce que Linux ne sait pas exécuter.
RUN sed -i 's/\r$//' docker-entrypoint.sh \
    && chmod +x docker-entrypoint.sh \
    && useradd --create-home --uid 1000 app \
    && chown -R app:app /app
USER app

EXPOSE 8000
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--access-logfile", "-"]
