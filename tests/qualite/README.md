# Campagne QA — MedConnect (Groupe 12)

Ce dossier centralise la reproductibilité de la campagne de tests qualité décrite au chapitre 9 de `report/main.tex`. Les preuves d'exécution sont versées dans `reports/` et les captures LaTeX dans `report/screenshots/`.

## Commandes (depuis la racine du dépôt)

```bash
# 1. Tests unitaires + couverture logique métier
python -m pytest -v --html=reports/pytest.html --self-contained-html
python -m coverage run --source=patients,agenda,dossier_medical,ordonnances --omit='*/test_*.py' -m pytest -q
python -m coverage report -m
python -m coverage html -d reports/coverage/html_unitaire

# 2. Tests API Django (45) + couverture API
cd backend
python manage.py test patients_api agenda_api dossier_medical_api ordonnances_api -v 1
python -m coverage run --source=patients_api,agenda_api,dossier_medical_api,ordonnances_api --omit='*/tests.py,*/migrations/*,*/management/*' manage.py test patients_api agenda_api dossier_medical_api ordonnances_api -v 0
python -m coverage report -m
cd ..

# 3. Postman / Newman (serveur Django démarré, données seed_demo)
newman run tests/postman/MedConnect.postman_collection.json \
  -e tests/postman/MedConnect.postman_environment.json -r cli,html \
  --reporter-html-export reports/newman/newman.html

# 4. Selenium (Chrome headless, serveur démarré)
python -m pytest tests/e2e/test_parcours_patient.py -v --html=reports/e2e.html --self-contained-html

# 5. JMeter (Docker)
docker run --rm -v "$PWD:/jmeter" -w /jmeter justb4/jmeter:latest \
  -n -t /jmeter/tests/performance/medconnect.jmx \
  -l /jmeter/reports/jmeter/results.jtl -e -o /jmeter/reports/jmeter/dashboard

# 6. Analyse statique et sécurité
python -m ruff check --select E9,F patients agenda dossier_medical ordonnances backend
python -m pip_audit -r backend/requirements.txt
python -m pip_audit -r requirements.txt

# 7. Captures des rapports HTML pour le LaTeX
python tests/qualite/capture_reports.py

# 8. Compilation du rapport (Tectonic, repli si pdflatex/MiKTeX est incomplet)
cd report
tectonic main.tex   # deux passes pour les références croisées
cd ..

# 9. Génération du DAT (Dossier d'Analyse et de Tests)
python tests/qualite/build_dat.py
```

## Résultats enregistrés

| Outil | Résultat | Preuve |
|---|---|---|
| Pytest | 23/23 | `reports/pytest.txt`, `reports/pytest.html` |
| Django TestCase | 45/45 | `reports/django_api.txt` |
| Coverage.py | 88 % métier / 93 % API | `reports/coverage/` |
| Newman | 16 requêtes, 26 assertions, 0 échec | `reports/newman/` |
| Selenium | 4/4 parcours | `reports/e2e.html`, `report/screenshots/e2e_*.png` |
| JMeter | 250 échantillons, 0 erreur | `reports/jmeter/dashboard/` |
| Ruff | 0 erreur bloquante après correction de 5 imports | `reports/ruff.txt` |
| pip-audit | aucune vulnérabilité connue | `reports/pip_audit*.txt` |
| SonarQube / ZAP / Snyk | non finalisés (environnement), solutions de repli documentées | `reports/qa_summary/` |
| DAT | dossier de tests DOCX + miroir Markdown, 68 cas | `report/MedConnect_DAT.docx`, `report/MedConnect_DAT.md` |

Les outils Java (`Checkstyle`, `JUnit/TestNG`, `JaCoCo`) et JavaScript (`Istanbul`, `Cypress`) du référentiel sont non applicables à la pile Python/Django ; leurs objectifs sont couverts par Ruff, Pytest/Django TestCase et coverage.py.
