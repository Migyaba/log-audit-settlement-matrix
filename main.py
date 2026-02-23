import os
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import SessionLocal, engine, Base
from models import MatrixAuditLog

# Initialisation de la base de données
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Mojaloop Log Audit Settlement Matrix",
    description="Un système de journalisation pour assurer la traçabilité des calculs et des modifications apportées à la Settlement Matrix.",
    version="1.0.0"
)

# Dépendance pour la base de données
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Schéma pour la réception des logs d'audit
class AuditLogCreate(BaseModel):
    matrix_id: str
    source_data: dict # IDs transactions, dates, etc.
    algorithm_version: Optional[str] = "v1.0.0"
    initial_state: Optional[dict] = None
    triggered_by: Optional[str] = None
    comment: Optional[str] = None

@app.post("/audit/log", response_model=dict)
def create_audit_log(audit_in: AuditLogCreate, db: Session = Depends(get_db)):
    """
    Enregistre une nouvelle version de calcul pour une Settlement Matrix.
    Gère automatiquement le versionnement et le lien avec la version précédente.
    """
    # 1. Rechercher la dernière version existante pour cette matrice
    last_entry = db.query(MatrixAuditLog).filter(
        MatrixAuditLog.matrix_id == audit_in.matrix_id
    ).order_by(MatrixAuditLog.version.desc()).first()

    # 2. Déterminer le nouveau numéro de version et le lien précédent
    new_version = 1
    previous_id = None
    
    if last_entry:
        new_version = last_entry.version + 1
        previous_id = last_entry.id

    # 3. Créer l'entrée d'audit
    new_log = MatrixAuditLog(
        matrix_id=audit_in.matrix_id,
        version=new_version,
        algorithm_version=audit_in.algorithm_version,
        source_data=audit_in.source_data,
        initial_state=audit_in.initial_state,
        previous_version_id=previous_id,
        triggered_by=audit_in.triggered_by,
        comment=audit_in.comment
    )

    db.add(new_log)
    db.commit()
    db.refresh(new_log)

    return {
        "message": "Log d'audit enregistré avec succès",
        "id": new_log.id,
        "matrixId": new_log.matrix_id,
        "version": f"v{new_log.version}",
        "timestamp": new_log.created_at
    }

@app.get("/audit/matrix/{matrix_id}", response_model=List[dict])
def get_matrix_history(matrix_id: str, db: Session = Depends(get_db)):
    """
    Récupère l'historique complet des calculs pour une matrice spécifique.
    Permet de voir l'évolution de v1 à la version actuelle.
    """
    logs = db.query(MatrixAuditLog).filter(
        MatrixAuditLog.matrix_id == matrix_id
    ).order_by(MatrixAuditLog.version.asc()).all()
    
    if not logs:
        raise HTTPException(status_code=404, detail="Aucun historique trouvé pour cette matrice")
        
    return [
        {
            "version": f"v{log.version}",
            "timestamp": log.created_at,
            "algorithm": log.algorithm_version,
            "triggeredBy": log.triggered_by,
            "comment": log.comment,
            "hasPrevious": log.previous_version_id is not None
        } for log in logs
    ]

@app.get("/audit/report/{matrix_id}")
def generate_audit_report(matrix_id: str, db: Session = Depends(get_db)):
    """
    Génère un rapport d'audit détaillé (Piste d'audit) pour une matrice.
    Inclut les données sources pour chaque étape.
    """
    logs = db.query(MatrixAuditLog).filter(
        MatrixAuditLog.matrix_id == matrix_id
    ).order_by(MatrixAuditLog.version.asc()).all()
    
    if not logs:
        raise HTTPException(status_code=404, detail="Matrice inconnue")

    report = {
        "reportId": f"AUDIT-{matrix_id}-{datetime.utcnow().strftime('%Y%3m%d')}",
        "matrixId": matrix_id,
        "generatedAt": datetime.utcnow(),
        "totalVersions": len(logs),
        "auditTrail": [
            {
                "step": log.version,
                "date": log.created_at,
                "actionBy": log.triggered_by,
                "changes": log.comment,
                "technicalDetails": {
                    "algo": log.algorithm_version,
                    "transactionsCount": len(log.source_data.get("transactionIds", [])) if isinstance(log.source_data, dict) else "N/A"
                }
            } for log in logs
        ]
    }
    
    return report

@app.get("/health")
def health_check():
    """Vérification de l'état de santé du service."""
    return {"status": "OK", "timestamp": datetime.utcnow()}

