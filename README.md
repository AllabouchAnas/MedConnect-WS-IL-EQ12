# MedConnect — Dossier de Tests Unitaires
**Projet :** MedConnect — Gestion Intelligente d'un Cabinet Médical  
**Groupe :** 12 | Master Excellence Ingénierie Logicielle | FSA Agadir | 2026–2027

---

## 👥 Équipe & Répartition des Modules

| Membre | Rôle | Module |
|--------|------|--------|
| **ALLABOUCH ANASS** | Chef de Projet | `patients/` — Gestion des Patients ✅ |
| **Ahmed LAHMAINE** | Product Owner / BA | `agenda/` — Gestion des Rendez-vous |
| **Achraf AIT DAMNAT** | Lead Tech / Architecte | `dossier_medical/` — Dossier Médical |
| **ABDELLAH RAHEL** | Responsable QA | `ordonnances/` — Gestion des Ordonnances |

---

## 📁 Structure du Projet

```
MedConnect-WS-IL-EQ12/
│
├── patients/                        ← Module ALLABOUCH ANASS ✅
│   ├── __init__.py
│   ├── patient.py                   # Modèle Patient
│   ├── patient_service.py           # Service métier (CRUD + règles)
│   └── test_patient_service.py      # 8 tests unitaires — tous PASSED
│
├── agenda/                          ← Module Ahmed LAHMAINE
│   ├── __init__.py
│   ├── rendez_vous.py               # Modèle RendezVous ✅ (fourni)
│   ├── agenda_service.py            # Stub — À IMPLÉMENTER
│   └── test_agenda_service.py       # 5 tests — À faire passer
│
├── dossier_medical/                 ← Module Achraf AIT DAMNAT
│   ├── __init__.py
│   ├── consultation.py              # Modèle Consultation ✅ (fourni)
│   ├── dossier_service.py           # Stub — À IMPLÉMENTER
│   └── test_dossier_service.py      # 5 tests — À faire passer
│
├── ordonnances/                     ← Module ABDELLAH RAHEL
│   ├── __init__.py
│   ├── ordonnance.py                # Modèles Ordonnance + Ligne ✅ (fourni)
│   ├── ordonnance_service.py        # Stub — À IMPLÉMENTER
│   └── test_ordonnance_service.py   # 5 tests — À faire passer
│
├── venv/                            # Environnement virtuel Python (ne pas commit)
├── requirements.txt                 # Dépendances : pytest, pytest-html
├── pytest.ini                       # Configuration pytest
└── README.md                        # Ce fichier
```

---

## ⚙️ Installation & Lancement (commun à tous)

### Étape 1 — Cloner le repo

```bash
git clone https://github.com/AllabouchAnas/MedConnect-WS-IL-EQ12.git
cd MedConnect-WS-IL-EQ12
```

### Étape 2 — Créer et activer l'environnement virtuel

**Windows (PowerShell) :**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux / macOS :**
```bash
python3 -m venv venv
source venv/bin/activate
```

> ✅ Vous verrez `(venv)` apparaître au début de la ligne — l'environnement est actif.

### Étape 3 — Installer les dépendances

```bash
pip install -r requirements.txt
```

### Étape 4 — Lancer les tests de son module

```bash
# Remplacer par votre dossier : patients / agenda / dossier_medical / ordonnances
python -m pytest patients/test_patient_service.py -v
```

### Étape 5 — Générer le rapport HTML

```bash
python -m pytest patients/test_patient_service.py -v --html=rapport_tests_patients.html --self-contained-html
```

> Ouvrir `rapport_tests_patients.html` dans le navigateur — à joindre au dossier de tests.

---

## ✅ Module Patients — ALLABOUCH ANASS (Terminé)

### Règles métier implémentées

| # | Règle |
|---|-------|
| R1 | CIN unique — doublon refusé avec message clair |
| R2 | Téléphone unique — doublon refusé avec message clair |
| R3 | Champs obligatoires : CIN, Nom, Prénom, Date de naissance, Téléphone |
| R4 | Recherche par CIN — retourne le patient ou lève une erreur |
| R5 | Modification de n'importe quel champ d'un patient existant |
| R6 | Suppression — retire le patient du service |

### Résultats des tests

```
8 passed in 0.18s
```

| ID | Scénario | Résultat |
|----|----------|----------|
| UT-PAT-01 | Ajout d'un patient valide | ✅ PASSED |
| UT-PAT-02 | Refus si CIN déjà existant | ✅ PASSED |
| UT-PAT-03 | Refus si téléphone déjà existant | ✅ PASSED |
| UT-PAT-04 | Refus si champ obligatoire vide | ✅ PASSED |
| UT-PAT-05 | Recherche d'un patient existant | ✅ PASSED |
| UT-PAT-06 | Recherche d'un patient inexistant | ✅ PASSED |
| UT-PAT-07 | Modification des données | ✅ PASSED |
| UT-PAT-08 | Suppression d'un patient | ✅ PASSED |

**Lancer :**
```bash
python -m pytest patients/test_patient_service.py -v --html=rapport_tests_patients.html --self-contained-html
```

---

## 🗓️ Module Agenda — Ahmed LAHMAINE (À faire)

### Ce que tu dois implémenter

**Fichier : `agenda/agenda_service.py`**  
Le squelette est déjà là avec les méthodes vides. Tu dois remplir chaque méthode.

| Méthode | Ce qu'elle doit faire |
|---------|----------------------|
| `planifier_rdv(patient_cin, medecin_id, date_heure, motif)` | Créer un RDV — lever `ValueError` si ce médecin a déjà un RDV à cette heure |
| `avancer_statut(rdv_id)` | Passer au statut suivant : `Planifié → Salle d'attente → Consultation → Terminé` |
| `annuler_rdv(rdv_id, motif_annulation)` | Mettre statut à `"Annulé"` sans supprimer le RDV |
| `rechercher_rdv(rdv_id)` | Retourner le RDV ou lever `ValueError` si introuvable |

### Tests à faire passer

| ID | Scénario |
|----|----------|
| UT-AGE-01 | Planifier un RDV valide → succès |
| UT-AGE-02 | Même médecin, même créneau → `ValueError` |
| UT-AGE-03 | Avancer le statut dans l'ordre → succès |
| UT-AGE-04 | Annuler → statut `"Annulé"`, toujours présent dans le service |
| UT-AGE-05 | Rechercher ID inexistant → `ValueError` |

**Lancer :**
```bash
python -m pytest agenda/test_agenda_service.py -v --html=rapport_tests_agenda.html --self-contained-html
```

---

## 🩺 Module Dossier Médical — Achraf AIT DAMNAT (À faire)

### Ce que tu dois implémenter

**Fichier : `dossier_medical/dossier_service.py`**

| Méthode | Ce qu'elle doit faire |
|---------|----------------------|
| `ajouter_consultation(patient_cin, medecin_id, date, motif, ...)` | Enregistrer la consultation — lever `ValueError` si motif vide |
| `get_historique(patient_cin)` | Retourner la liste des consultations du patient (liste vide si aucune) |
| `modifier_consultation(consult_id, **modifications)` | Mettre à jour les champs — lever `ValueError` si ID inexistant |
| `supprimer_consultation(consult_id)` | Supprimer — lever `ValueError` si ID inexistant |

### Tests à faire passer

| ID | Scénario |
|----|----------|
| UT-DOS-01 | Ajouter une consultation valide → succès |
| UT-DOS-02 | Motif vide → `ValueError` |
| UT-DOS-03 | Historique patient avec consultations → liste non vide |
| UT-DOS-04 | Historique patient sans consultations → liste vide |
| UT-DOS-05 | Modifier le diagnostic → changement persisté |

**Lancer :**
```bash
python -m pytest dossier_medical/test_dossier_service.py -v --html=rapport_tests_dossier.html --self-contained-html
```

---

## 💊 Module Ordonnances — ABDELLAH RAHEL (À faire)

### Ce que tu dois implémenter

**Fichier : `ordonnances/ordonnance_service.py`**

| Méthode | Ce qu'elle doit faire |
|---------|----------------------|
| `creer_ordonnance(patient_cin, medecin_id, date)` | Créer une ordonnance vide |
| `ajouter_ligne(ordonnance_id, medicament, dosage, posologie, duree_jours, allergies_patient)` | Ajouter un médicament — lever `ValueError` si allergie détectée ou ordonnance validée |
| `valider_ordonnance(ordonnance_id)` | Passer `est_validee = True` (verrouillage définitif) |
| `modifier_ordonnance(ordonnance_id, **modifications)` | Modifier — lever `ValueError` si déjà validée |
| `rechercher_ordonnance(ordonnance_id)` | Retourner l'ordonnance ou lever `ValueError` |

### Tests à faire passer

| ID | Scénario |
|----|----------|
| UT-ORD-01 | Créer une ordonnance → succès, `est_validee = False` |
| UT-ORD-02 | Ajouter médicament sans allergie → succès |
| UT-ORD-03 | Médicament dans les allergies → `ValueError` avec "allergie" dans le message |
| UT-ORD-04 | Valider → `est_validee = True` |
| UT-ORD-05 | Modifier après validation → `ValueError` avec "validée" dans le message |

**Lancer :**
```bash
python -m pytest ordonnances/test_ordonnance_service.py -v --html=rapport_tests_ordonnances.html --self-contained-html
```

---

## 🗄️ Base de Données

### Phase actuelle — Pas de base de données

Pour cette phase de tests unitaires, **aucune base de données n'est nécessaire**.  
Chaque service stocke les données **en mémoire** (dans un dictionnaire Python) pendant l'exécution des tests.

```
Tests → PatientService → dict Python { "CIN": Patient }
```

C'est suffisant pour vérifier que les règles métier fonctionnent correctement.  
Les données disparaissent après chaque test — c'est voulu (chaque test repart de zéro grâce aux `fixtures`).

### Phase suivante — PostgreSQL + Django

Quand on passera à l'application web complète, on remplacera les dictionnaires par une vraie base de données :

| Élément | Technologie |
|---------|-------------|
| Base de données | **PostgreSQL** |
| ORM (interface Python ↔ DB) | **Django ORM** |
| API REST | **Django REST Framework** |

Chaque classe Python deviendra un **modèle Django** (une table dans la DB) :

```python
# Exemple : patient.py deviendra un modèle Django
from django.db import models

class Patient(models.Model):
    cin           = models.CharField(max_length=20, unique=True)
    nom           = models.CharField(max_length=100)
    prenom        = models.CharField(max_length=100)
    date_naissance = models.DateField()
    telephone     = models.CharField(max_length=20, unique=True)
    groupe_sanguin = models.CharField(max_length=5, blank=True)
    allergies     = models.TextField(blank=True)
    contact_urgence = models.CharField(max_length=20, blank=True)
```

Et les commandes pour créer les tables :
```bash
python manage.py makemigrations
python manage.py migrate
```

---

## 📌 Règles communes pour tous

1. **Pas de base de données** dans cette phase — tout est en mémoire (dictionnaire Python).
2. **Pas de Django, pas de Flask** — classes Python simples uniquement.
3. **Chaque test est indépendant** — la `fixture` repart d'un service vide à chaque fois.
4. **Ne déclarer un test comme PASSÉ qu'après l'avoir exécuté et vérifié.**
5. **Nommer les tests clairement** : `test_UT_XXX_YY_description`
6. **Minimum requis** : 1 cas nominal + 1 cas limite par règle métier importante.

---

## 🔮 Améliorations Futures

Cette phase couvre les tests unitaires en mémoire. La prochaine étape du projet :

### Backend — Django REST Framework
- [ ] Remplacer les dictionnaires par des **modèles Django + PostgreSQL**
- [ ] Exposer chaque service via des **endpoints REST** (GET, POST, PUT, DELETE)
- [ ] Mettre en place l'**authentification JWT** (djangorestframework-simplejwt)
- [ ] Implémenter le **contrôle d'accès par rôle** (RBAC) : Médecin vs Secrétaire
- [ ] Générer des **ordonnances PDF** avec WeasyPrint (non falsifiables)
- [ ] Upload de fichiers pour les pièces jointes (radios, bilans) au format PDF/JPG

### Frontend — Next.js + Tailwind CSS
- [ ] Interface de **gestion des patients** (liste, création, fiche détail)
- [ ] **Calendrier / agenda** avec vue journalière et détection de chevauchements
- [ ] **Dossier médical informatisé** (accès réservé médecin)
- [ ] **Formulaire d'ordonnance** avec alerte allergie en temps réel
- [ ] **Salle d'attente** (vue en temps réel pour la secrétaire)
- [ ] Tableau de bord différencié par rôle (Médecin / Secrétaire)

### Sécurité & Déploiement
- [ ] HTTPS sur tous les échanges
- [ ] Séparation stricte médecin / secrétaire appliquée côté API
- [ ] Déploiement backend (Railway / Render / VPS Nginx + Gunicorn)
- [ ] Déploiement frontend (Vercel / Netlify)
- [ ] Tests d'intégration Postman sur tous les endpoints

---

## 🚀 Guide d'intégration sur `main` pour les équipiers (Academic Attribution)

Afin que l'historique Git et les contributions individuelles reflètent fidèlement le travail de chaque membre pour l'évaluation académique, chaque équipier pousse son module depuis sa machine avec son propre identifiant Git :

| Équipier | Rôle | Module | Commande de test | Statut sur `main` |
| :--- | :--- | :--- | :--- | :--- |
| **Ahmed LAHMAINE** | Product Owner / BA | `agenda_api` | `python backend/manage.py test agenda_api` | ✅ Fusionné via `feature/agenda-api` |
| **Allabouch ANASS** | Chef de Projet | `patients_api` | `python backend/manage.py test patients_api` | ✅ Poussé sur `main` |
| **Achraf AIT DAMNAT** | Lead Tech / Architecte | `dossier_medical_api` | `python backend/manage.py test dossier_medical_api` | ⏳ Prêt sur `develop` |
| **Abdellah RAHEL** | Responsable QA | `ordonnances_api` | `python backend/manage.py test ordonnances_api` | ⏳ Prêt sur `develop` |

### Instructions pas-à-pas pour Achraf et Abdellah :
Consultez le guide complet dans [backend/README.md](file:///c:/Users/Dell%205520/Desktop/Projects/MedConnect-WS-IL-EQ12/backend/README.md) pour les commandes exactes permettant d'extraire votre module depuis `develop`, de le tester et de le pousser sur `main` sous votre propre identifiant Git sans aucun conflit de fusion.

---

*MedConnect — Groupe 12 | Master Excellence IL | Ibn Zohr FSA Agadir | 2026–2027*
