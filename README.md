# Mojaloop Log Audit Settlement Matrix

Ce microservice est le module de **traçabilité et d'audit** pour la génération de la Settlement Matrix au sein de l'écosystème Mojaloop. Il assure que chaque calcul de solde est enregistré, versionné et immuable.

## Objectifs du Projet
Ce système garantit la transparence et la fiabilité des calculs financiers en :
- Enregistrant les données sources pour chaque génération (ID transactions, plages horaires, état initial).
- Consignant la version de l'algorithme ou des règles métier utilisée.
- Empêchant l'écrasement des anciennes versions (Système immuable).
- Sauvegardant chaque version avec un numéro (v1, v2...) et un lien vers la précédente (Linéage).

## Stack Technique
- **Framework** : FastAPI (Python 3.12+)
- **Base de données** : SQLite (via SQLAlchemy)
- **Validation** : Pydantic
- **Standard Temps** : ISO 8601 avec synchronisation **UTC** (`timezone.utc`).

## Fonctionnalités Clés
- **Append-Only** : L'accès est restreint à l'ajout. Aucune route de modification (`UPDATE`) ou de suppression (`DELETE`) n'est exposée.
- **Auto-Versioning** : Le service détecte automatiquement la progression des versions pour une matrice donnée.
- **Multi-Format Export** : Génération de rapports d'audit en formats **JSON** et **CSV** pour les auditeurs.
- **Lecture Seule** : Les endpoints de consultation garantissent l'intégrité des données pour les utilisateurs finaux.

## Installation

1. **Environnement Virtuel** :
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Dépendances** :
   ```bash
   pip install fastapi[standard] sqlalchemy pydantic
   ```

3. **Lancement** :
   ```bash
   uvicorn main:app --reload --port 8001
   ```

## Utilisation de l'API

### 1. Enregistrer un Audit (POST)
**Endpoint** : `/audit/log`  
**Description** : Enregistre un nouveau calcul immuable.
```json
{
  "matrix_id": "SETTLEMENT-32",
  "source_data": {
    "transactionIds": [101, 102, 103],
    "period": "2026-02-23 AM"
  },
  "algorithm_version": "v1.2.0",
  "comment": "Calcul initial après correction"
}
```

### 2. Consulter l'Historique (GET)
**Endpoint** : `/audit/matrix/{matrix_id}`  
**Description** : Affiche la chronologie complète des calculs incluant les liens de version.

### 3. Extraire le Rapport Auditeur (GET)
**Endpoint** : `/audit/report/{matrix_id}`  
**Format JSON (défaut)** : `GET /audit/report/M-101`  
**Format CSV** : `GET /audit/report/M-101?format=csv`  
**Description** : Génère une piste d'audit complète incluant le nombre de transactions traitées et les détails techniques.

## Sécurité et Audit
Toutes les dates sont enregistrées selon la norme **ISO 8601** en utilisant `datetime.now(timezone.utc)`. La structure de données utilise une contrainte de clé étrangère `previous_version_id` pour assurer l'intégrité de la chaîne de calculs. Le service est conçu pour être "Read-Only" pour tous les clients de consultation.

---
*Settlement Matrix - Mojaloop Hub.*
