# Mojaloop Log Audit Settlement Matrix

Ce microservice est le module de **traçabilité et d'audit** pour la génération de la Settlement Matrix au sein de l'écosystème Mojaloop. Il assure que chaque calcul de solde est enregistré, versionné et immuable.

## Objectifs du Projet
Ce système garantit la transparence et la fiabilité des calculs financiers en :
- Enregistrant les données sources (Transactions, snapshots de solde).
- Versionnant automatiquement chaque recalcul (v1, v2, etc.).
- Créant une "piste d'audit" (Audit Trail) infalsifiable.

## Stack Technique
- **Framework** : FastAPI (Python)
- **Base de données** : SQLite (via SQLAlchemy)
- **Validation** : Pydantic
- **Standard Temps** : ISO 8601 (UTC)

## Fonctionnalités Clés
- **Append-Only** : Aucune suppression ou modification possible des logs.
- **Auto-Versioning** : Le service détecte automatiquement la version précédente pour lier les calculs entre eux.
- **Extraction de Rapport** : Génération d'un rapport complet pour les auditeurs externes au format JSON.

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
   uvicorn main:app --reload
   ```

## Utilisation de l'API

### 1. Enregistrer un Audit (POST)
**Endpoint** : `/audit/log`  
**Description** : Appelé par le moteur de calcul après chaque génération de matrice.
```json
{
  "matrix_id": "SETTLEMENT-32",
  "source_data": {
    "transactionIds": [101, 102, 103],
    "period": "2026-02-23 AM"
  },
  "algorithm_version": "v1.2.0",
  "comment": "Calcul initial"
}
```

### 2. Consulter l'Historique (GET)
**Endpoint** : `/audit/matrix/{matrix_id}`  
**Description** : Affiche toutes les étapes de calcul pour une matrice spécifique.

### 3. Extraire le Rapport Auditeur (GET)
**Endpoint** : `/audit/report/{matrix_id}`  
**Description** : Génère une preuve de calcul structurée incluant les données techniques de chaque version.

## Sécurité et Audit
Toutes les dates sont enregistrées en **UTC** selon la norme ISO 8601. Le système utilise un mécanisme de **previous_version_id** pour garantir qu'aucune version de l'historique n'a été supprimée ou altérée.

---
*Settlement Matrix - Mojaloop Hub.*
