import os
import csv
import io
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import SessionLocal, engine, Base
from models import MatrixAuditLog

# Initialisation de la base de données
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Mojaloop Log Audit Settlement Matrix",
    description="""
    Système de journalisation immuable.
    CONTRÔLE D'ACCÈS : Les utilisateurs ont un accès en LECTURE SEULE. 
    L'application ne propose aucune route DELETE ou UPDATE.
    """,
    version="1.1.0"
)

# Dépendance pour la base de données
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Schémas de données
class AuditLogCreate(BaseModel):
    matrix_id: str
    source_data: dict
    algorithm_version: Optional[str] = "v1.0.0"
    initial_state: Optional[dict] = None
    triggered_by: Optional[str] = None
    comment: Optional[str] = None

@app.post("/audit/log", response_model=dict)
def create_audit_log(audit_in: AuditLogCreate, db: Session = Depends(get_db)):
    """
    Action APPEND-ONLY. Enregistre une nouvelle version immuable.
    """
    last_entry = db.query(MatrixAuditLog).filter(
        MatrixAuditLog.matrix_id == audit_in.matrix_id
    ).order_by(MatrixAuditLog.version.desc()).first()

    new_version = 1
    previous_id = None
    
    if last_entry:
        new_version = last_entry.version + 1
        previous_id = last_entry.id

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
        "version": f"v{new_log.version}",
        "timestamp": new_log.created_at
    }

@app.get("/audit/matrix/{matrix_id}")
def get_matrix_history(matrix_id: str, db: Session = Depends(get_db)):
    """Lecture seule de l'historique."""
    logs = db.query(MatrixAuditLog).filter(
        MatrixAuditLog.matrix_id == matrix_id
    ).order_by(MatrixAuditLog.version.asc()).all()
    
    if not logs:
        raise HTTPException(status_code=404, detail="Matrice inconnue")
        
    return [
    {
        "version": f"v{log.version}",
        "timestamp": log.created_at,
        "algorithm": log.algorithm_version,
        "triggeredBy": log.triggered_by,
        "comment": log.comment,
        "previousVersionId": log.previous_version_id
    } for log in logs
    ]

@app.get("/audit/report/{matrix_id}")
def generate_audit_report(
    matrix_id: str, 
    format: str = "json", 
    db: Session = Depends(get_db)
):
    """
    Génère la piste d'audit complète au format JSON ou CSV.
    """
    logs = db.query(MatrixAuditLog).filter(
        MatrixAuditLog.matrix_id == matrix_id
    ).order_by(MatrixAuditLog.version.asc()).all()
    
    if not logs:
        raise HTTPException(status_code=404, detail="Matrice inconnue")

    if format.lower() == "csv":
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=["v", "date", "admin", "comment", "algo", "tx_count"])
        writer.writeheader()
        
        for log in logs:
            tx_count = len(log.source_data.get("transactionIds", [])) if isinstance(log.source_data, dict) else 0
            writer.writerow({
                "v": f"v{log.version}",
                "date": log.created_at.isoformat() if log.created_at else "",
                "admin": log.triggered_by or "N/A",
                "comment": log.comment or "",
                "algo": log.algorithm_version,
                "tx_count": tx_count
            })
        
        output.seek(0)
        return StreamingResponse(
            output, 
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=audit_{matrix_id}.csv"}
        )

    # Format JSON par défaut
    return {
        "reportId": f"AUDIT-{matrix_id}-{datetime.now(timezone.utc).strftime('%Y%m%d')}",
        "matrixId": matrix_id,
        "generatedAt": datetime.now(timezone.utc),
        "auditTrail": [
            {
                "version": log.version,
                "timestamp": log.created_at,
                "triggeredBy": log.triggered_by,
                "details": log.comment,
                "technical": {
                    "algo": log.algorithm_version,
                    "txCount": len(log.source_data.get("transactionIds", [])) if isinstance(log.source_data, dict) else 0
                }
            } for log in logs
        ]
    }

@app.get("/health")
def health_check():
    return {"status": "OK", "timestamp": datetime.now(timezone.utc)}

