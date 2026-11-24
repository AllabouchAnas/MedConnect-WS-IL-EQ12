# DOSSIER D'ANALYSE ET DE TESTS

**MedConnect -- Plateforme distribuée de gestion de cabinet médical**

Référence : DAT-MC-001 | Version : 1.0 | Date : 24 novembre 2026

## 1. Fiche d'identification

| Champ | Valeur |
|---|---|
| Nom du projet | MedConnect |
| Référence | DAT-MC-001 |
| Responsable des tests | Allabouch Anass |
| Statut | Validé |
| Périmètre | 23 unitaires + 45 API = 68 cas |

## 2. Historique des versions

| Version | Date | Intervenant | Action |
|---|---|---|---|
| 0.1 | 23/11/2026 | Groupe 12 | Création et périmètre |
| 0.2 | 24/11/2026 | Équipe QA | Exécution des campagnes |
| 0.3 | 24/11/2026 | Responsable qualité | Couverture, Ruff, pip-audit |
| 1.0 | 24/11/2026 | Chef de projet | Validation finale |

## 3. Objectifs

- Vérifier les règles métier des 4 modules.

- Conserver une trace des scénarios, résultats et anomalies.

- Fournir les preuves des outils qualité demandés.


## 4. Périmètre et stratégie

| Niveau | Outil | Nombre | Objectif |
|---|---|---|---|
| Unitaire | Pytest | 23 | Règles métier isolées |
| API | Django TestCase | 45 | Endpoints, JWT, persistance |
| API outillée | Newman | 16 requêtes / 26 assertions | Campagne reproductible |
| E2E | Selenium | 4 | Parcours navigateur |
| Charge | JMeter | 250 échantillons | 25 VUs, 0 erreur |

## 5. Cas unitaires (23)

| ID | Module | Scénario / attendu | Résultat |
|---|---|---|---|
| UT-AGE-01 | agenda | Planifier un RDV avec un créneau libre doit réussir. | PASS |
| UT-AGE-02 | agenda | Deux RDV au même créneau pour le même médecin doivent être refusés. | PASS |
| UT-AGE-03 | agenda | Avancer le statut doit suivre le cycle défini. | PASS |
| UT-AGE-04 | agenda | Annuler un RDV doit changer son statut sans le supprimer. | PASS |
| UT-AGE-05 | agenda | Rechercher un ID inexistant doit lever une erreur. | PASS |
| UT-DOS-01 | dossier_medical | Ajouter une consultation avec tous les champs valides doit réussir. | PASS |
| UT-DOS-02 | dossier_medical | Ajouter une consultation sans motif doit être refusé. | PASS |
| UT-DOS-03 | dossier_medical | L'historique d'un patient avec consultations doit retourner une liste non vide. | PASS |
| UT-DOS-04 | dossier_medical | L'historique d'un patient sans consultations doit retourner une liste vide. | PASS |
| UT-DOS-05 | dossier_medical | Modifier le diagnostic d'une consultation existante doit être persisté. | PASS |
| UT-ORD-01 | ordonnances | Créer une ordonnance doit réussir et retourner l'objet. | PASS |
| UT-ORD-02 | ordonnances | Ajouter un médicament non allergène doit réussir. | PASS |
| UT-ORD-03 | ordonnances | Prescrire un médicament allergène doit lever une ValueError. | PASS |
| UT-ORD-04 | ordonnances | Valider une ordonnance doit passer est_validee à True. | PASS |
| UT-ORD-05 | ordonnances | Modifier une ordonnance validée doit être refusé. | PASS |
| UT-PAT-01 | patients | L'ajout d'un patient avec tous les champs valides doit réussir. | PASS |
| UT-PAT-02 | patients | L'ajout d'un patient avec un CIN déjà enregistré doit être refusé. | PASS |
| UT-PAT-03 | patients | L'ajout d'un patient avec un téléphone déjà utilisé doit être refusé. | PASS |
| UT-PAT-04 | patients | L'ajout d'un patient avec un champ obligatoire vide doit être refusé. | PASS |
| UT-PAT-05 | patients | La recherche d'un patient existant par CIN doit retourner ses données. | PASS |
| UT-PAT-06 | patients | La recherche d'un CIN inexistant doit lever une erreur. | PASS |
| UT-PAT-07 | patients | La modification du téléphone d'un patient existant doit être persistée. | PASS |
| UT-PAT-08 | patients | La suppression d'un patient existant doit le retirer du service. | PASS |

## 6. Cas API (45)

| ID | Module | Scénario / attendu | Résultat |
|---|---|---|---|
| API-PAT-01 | patients_api | POST /api/patients/ crée un patient valide et retourne 201 avec les données persistées. | PASS |
| API-PAT-02 | patients_api | Un CIN déjà enregistré est refusé (400) sans créer de doublon. | PASS |
| API-PAT-03 | patients_api | Un téléphone déjà utilisé est refusé (400). | PASS |
| API-PAT-04 | patients_api | La recherche par CIN et la modification subsequente sont persistées (200). | PASS |
| API-PAT-05 | patients_api | DELETE /api/patients/{id}/ supprime le patient et retourne 204. | PASS |
| API-AGE-01 | agenda_api | POST /api/agenda/rdv/ crée un RDV sur un créneau libre (201, statut=Planifié). | PASS |
| API-AGE-02 | agenda_api | Deux RDV sur le même créneau pour le même médecin sont refusés (400). | PASS |
| API-AGE-03 | agenda_api | Le même créneau est accepté pour un autre médecin (201). | PASS |
| API-AGE-04 | agenda_api | Un RDV annulé libère son créneau pour une nouvelle réservation. | PASS |
| API-AGE-05 | agenda_api | Un RDV pour un patient inexistant est refusé (400). | PASS |
| API-AGE-06 | agenda_api | Le cycle Planifié → Salle d'attente → Consultation → Terminé est respecté. | PASS |
| API-AGE-07 | agenda_api | Un RDV annulé ne peut plus avancer dans le cycle (400). | PASS |
| API-AGE-08 | agenda_api | L'annulation conserve l'enregistrement avec statut=Annulé. | PASS |
| API-AGE-09 | agenda_api | Une annulation sans motif est refusée (400). | PASS |
| API-AGE-10 | agenda_api | La recherche d'un RDV inexistant retourne 404. | PASS |
| API-AGE-11 | agenda_api | GET /api/agenda/rdv/ filtre correctement les RDV par date. | PASS |
| API-AGE-12 | agenda_api | La salle d'attente ne contient que les RDV du jour. | PASS |
| API-AGE-13 | agenda_api | Un appel sans jeton JWT est refusé (401). | PASS |
| API-AGE-14 | agenda_api | Un utilisateur sans rôle est refusé (403). | PASS |
| API-AGE-15 | agenda_api | Le login retourne un JWT valide et verrouille le compte après 5 échecs. | PASS |
| API-AGE-16 | agenda_api | Le logout révoque le token de refresh (401 sur rafraîchissement). | PASS |
| API-DOS-01 | dossier_medical_api | POST /api/consultations/ crée une consultation valide (201). | PASS |
| API-DOS-02 | dossier_medical_api | Les constantes médicales facultatives peuvent être omises. | PASS |
| API-DOS-03 | dossier_medical_api | Le médecin est forcé à l'utilisateur connecté, même si un autre est envoyé. | PASS |
| API-DOS-04 | dossier_medical_api | Un motif vide est refusé (400). | PASS |
| API-DOS-05 | dossier_medical_api | Un motif absent est refusé (400). | PASS |
| API-DOS-06 | dossier_medical_api | Un patient inconnu ou manquant est refusé (400). | PASS |
| API-DOS-07 | dossier_medical_api | Une date future ou invalide est refusée (400). | PASS |
| API-DOS-08 | dossier_medical_api | Des constantes aberrantes sont refusées (400). | PASS |
| API-DOS-09 | dossier_medical_api | GET /api/consultations/?patient=... retourne l'historique complet du patient. | PASS |
| API-DOS-10 | dossier_medical_api | Le filtre patient est insensible à la casse. | PASS |
| API-DOS-11 | dossier_medical_api | Un patient sans consultation retourne une liste vide (200). | PASS |
| API-DOS-12 | dossier_medical_api | Les filtres combinés dates + recherche retournent uniquement les consultations correspondantes. | PASS |
| API-DOS-13 | dossier_medical_api | PATCH /api/consultations/{id}/ met à jour le diagnostic (200). | PASS |
| API-DOS-14 | dossier_medical_api | Une modification ne peut pas vider le motif (400). | PASS |
| API-DOS-15 | dossier_medical_api | Le patient d'une consultation ne peut pas être changé (400). | PASS |
| API-DOS-16 | dossier_medical_api | DELETE /api/consultations/{id}/ supprime la consultation (204). | PASS |
| API-DOS-17 | dossier_medical_api | Un identifiant inexistant retourne 404. | PASS |
| API-DOS-18 | dossier_medical_api | Un dossier est partagé entre médecins autorisés (200). | PASS |
| API-DOS-19 | dossier_medical_api | La secrétaire est refusée sur toutes les ressources médicales (403). | PASS |
| API-DOS-20 | dossier_medical_api | Un utilisateur sans rôle est refusé (403). | PASS |
| API-DOS-21 | dossier_medical_api | Un appel non authentifié est refusé (401). | PASS |
| API-ORD-01 | ordonnances_api | Un médicament allergène déclenche une alerte et est refusé en temps réel. | PASS |
| API-ORD-02 | ordonnances_api | Ajout d'une ligne de médicament non allergène accepté (201). | PASS |
| API-ORD-03 | ordonnances_api | La validation passe est_validee=True et verrouille l'ordonnance. | PASS |

## 7. Synthèse des résultats

| Outil | Résultat | Preuve | Observation |
|---|---|---|---|
| Pytest (unitaires) | 23/23 | reports/pytest.txt | Tous les cas métier passent |
| Django TestCase (API) | 45/45 | reports/django_api.txt | dashboard_api exclu du périmètre retenu |
| Postman / Newman | 16 requêtes, 26 assertions, 0 échec | reports/newman/newman.html | Scénarios API bout en bout |
| Selenium | 4/4 parcours | reports/e2e.html | Chrome headless, parcours patient |
| JMeter | 250 échantillons, 0 erreur | reports/jmeter/dashboard/index.html | 25 VUs, 13,47 req/s |
| Coverage.py | 88 % métier / 93 % API | reports/coverage/ | Seuil de couverture validé |
| Ruff | 0 erreur bloquante | reports/ruff.txt | 5 F401 corrigés |
| pip-audit | 0 vulnérabilité connue | reports/pip_audit.txt | backend + racine |

## 8. Anomalies et décisions

| ID | Constats | Statut | Traitement |
|---|---|---|---|
| A-01 | 5 imports inutilisés (F401) détectés par Ruff | Corrigé | Suppression des imports dans 4 fichiers backend |
| A-02 | Newman PATCH refusé (téléphone figé) | Corrigé | Capture du téléphone créé dans la variable `tel` |
| A-03 | Selenium attendait `#/ login` au lieu de `#/` exact | Corrigé | Attente explicite de `#/` et de `switch-role` |
| A-04 | Daemon Docker indisponible et pull ZAP en `unexpected EOF` | Contourné | Rapports HTML de repli dans `reports/qa_summary/` |
| A-05 | Snyk : erreur 500 / absence de jeton | Contourné | Remplacé par pip-audit (0 vulnérabilité) |

## 9. Conclusion

68/68 cas exécutés avec succès. Couverture 88 % métier / 93 % API. Newman, Selenium et JMeter confirment le comportement fonctionnel et la stabilité. Dossier validé.
