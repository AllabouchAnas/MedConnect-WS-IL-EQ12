# MedConnect – Architecture Distribuée Django REST & SPA (SFD V4)

## 👥 Répartition des Modules & État sur `main`

| Membre | Rôle | Module Backend | Statut sur `main` |
| :--- | :--- | :--- | :--- |
| **Ahmed LAHMAINE** | Product Owner / BA | `agenda_api` | ✅ Fusionné via `feature/agenda-api` |
| **Allabouch ANASS** | Chef de Projet | `patients_api` | ✅ Poussé sur `main` |
| **Achraf AIT DAMNAT** | Lead Tech / Architecte | `dossier_medical_api` | ⏳ Prêt sur `develop` (à pousser sous son nom) |
| **Abdellah RAHEL** | Responsable QA | `ordonnances_api` | ⏳ Prêt sur `develop` (à pousser sous son nom) |

---

## 🚀 Instructions pour les équipiers : Comment pousser votre module sur `main` sous votre propre nom

Afin que l'historique Git et les contributions individuelles reflètent fidèlement le travail de chaque membre pour l'évaluation académique, les modules `dossier_medical_api` et `ordonnances_api` sont entièrement finalisés et testés sur la branche `develop`.

Voici la procédure pas-à-pas à exécuter depuis votre machine locale :

### 1. Pour Achraf AIT DAMNAT (`dossier_medical_api`)

```bash
# 1. Configurer votre identité Git
git config user.name "Achraf Ait Damnat"
git config user.email "votre-email@etudiant.uiz.ac.ma"

# 2. Récupérer la dernière version de main
git checkout main
git pull origin main

# 3. Créer votre branche de travail
git checkout -b feature/dossier-medical-api

# 4. Extraire votre module depuis develop
git checkout origin/develop -- backend/dossier_medical_api/

# 5. Activer le module dans settings.py et urls.py :
# Dans backend/config/settings.py, ajouter "dossier_medical_api" dans INSTALLED_APPS
# Dans backend/config/urls.py, ajouter : path("api/", include("dossier_medical_api.urls")),

# 6. Exécuter les tests du module
python backend/manage.py test dossier_medical_api

# 7. Commiter et pousser sous votre nom
git add backend/dossier_medical_api backend/config/settings.py backend/config/urls.py
git commit -m "feat(dossier-medical): API REST Consultations & Dossier Medical conforme SFD V4"
git push origin feature/dossier-medical-api

# 8. Fusionner dans main (ou ouvrir une Pull Request)
git checkout main
git merge feature/dossier-medical-api
git push origin main
```

---

### 2. Pour Abdellah RAHEL (`ordonnances_api`)

```bash
# 1. Configurer votre identité Git
git config user.name "Abdellah Rahel"
git config user.email "votre-email@etudiant.uiz.ac.ma"

# 2. Récupérer la dernière version de main
git checkout main
git pull origin main

# 3. Créer votre branche de travail
git checkout -b feature/ordonnances-api

# 4. Extraire votre module depuis develop
git checkout origin/develop -- backend/ordonnances_api/

# 5. Activer le module dans settings.py et urls.py :
# Dans backend/config/settings.py, ajouter "ordonnances_api" dans INSTALLED_APPS
# Dans backend/config/urls.py, ajouter : path("api/", include("ordonnances_api.urls")),

# 6. Exécuter les tests du module
python backend/manage.py test ordonnances_api

# 7. Commiter et pousser sous votre nom
git add backend/ordonnances_api backend/config/settings.py backend/config/urls.py
git commit -m "feat(ordonnances): API REST Ordonnances, alertes allergies et verrouillage SFD V4"
git push origin feature/ordonnances-api

# 8. Fusionner dans main (ou ouvrir une Pull Request)
git checkout main
git merge feature/ordonnances-api
git push origin main
```

---

## 💻 Lancer l'application unifiée (Branche `develop`)

La branche `develop` intègre déjà l'ensemble des 4 modules avec **27 tests réussis sur 27**.

```bash
# Lancement direct via le script universel à la racine :
python exe.py --web

# Ou manuellement :
cd backend
python manage.py migrate
python manage.py seed_demo
python manage.py runserver 8000
```
Ouvrir http://127.0.0.1:8000/ — Identifiants : `dr.demo` ou `sec.demo` / `DemoPass123!`.

## 🧪 Tests complets sur `develop`
```bash
python manage.py test patients_api agenda_api dossier_medical_api ordonnances_api
# Résultat : 27 tests PASSED
```
