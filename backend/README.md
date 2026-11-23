# MedConnect – Module Agenda (rendez-vous) : backend + frontend

## Lancer (depuis la racine du projet cloné)
    cd backend
    python -m venv venv
    venv\Scripts\activate          (Windows)  |  source venv/bin/activate (Linux/Mac)
    pip install -r requirements.txt
    python manage.py migrate
    python manage.py seed_demo
    python manage.py runserver
Ouvrir http://127.0.0.1:8000/ - comptes : sec.demo ou dr.demo, mot de passe Demo@1234

## Tests
    python manage.py test        (16 tests API : règles métier + sécurité)

## API
POST /api/auth/login/ | /refresh/ | /logout/
GET, POST /api/agenda/rdv/ (?date=AAAA-MM-JJ&medecin=&statut=) ; GET /api/agenda/rdv/{id}/
POST /api/agenda/rdv/{id}/avancer/ ; POST /api/agenda/rdv/{id}/annuler/ {motif_annulation}
GET /api/agenda/rdv/salle-attente/ ; GET /api/agenda/medecins/ ; GET /api/patients/

## PostgreSQL (optionnel)
pip install psycopg2-binary ; variables : DB_ENGINE=postgres DB_NAME DB_USER DB_PASSWORD DB_HOST DB_PORT
