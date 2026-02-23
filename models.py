from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base

class MatrixAuditLog(Base):
    """
    Modèle pour la traçabilité complète des calculs de la Settlement Matrix.
    """
    __tablename__ = "matrix_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    matrix_id = Column(String, index=True, nullable=False) # L'ID de la matrice suivie
    version = Column(Integer, nullable=False) # Numéro de version (v1, v2, etc.)
    
    # Critère : Consignation de la version de l'algorithme
    algorithm_version = Column(String, nullable=False, default="v1.0.0")
    
    # Critère : Enregistrement des données sources (IDs transactions, plages, etc.)
    # Stocké au format JSON pour plus de flexibilité
    source_data = Column(JSON, nullable=False)
    
    # Critère : État initial du solde et autres détails métier
    initial_state = Column(JSON, nullable=True)
    
    # Critère : Lien vers la version précédente
    previous_version_id = Column(Integer, ForeignKey("matrix_audit_logs.id"), nullable=True)
    
    # Critère : Horodatage synchronisé (ISO 8601 géré par Python)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Informations sur l'auteur de l'action
    triggered_by = Column(String, nullable=True)
    comment = Column(String, nullable=True) # Ex: "Correction suite à erreur transaction ID 45"

    # Relation pour naviguer dans l'historique
    previous_entry = relationship("MatrixAuditLog", remote_side=[id])

    def __repr__(self):
        return f"<MatrixAuditLog matrix={self.matrix_id} version={self.version}>"
