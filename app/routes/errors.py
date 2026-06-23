import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models

router = APIRouter(prefix="/errors", tags=["errors"])
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[dict])
def list_errors(db: Session = Depends(get_db)):
    """Lista todos os erros salvos no banco"""
    rows = db.query(models.ErrorLog).order_by(models.ErrorLog.created_at.desc()).all()
    return [
        {
            "id": r.id,
            "page_name": r.page_name,
            "error_message": r.error_message,
            "stack_trace": r.stack_trace,
            "resolved": bool(r.resolved),
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


@router.delete("/{error_id}")
def delete_error(error_id: int, db: Session = Depends(get_db)):
    """Deleta um erro manualmente quando o dev resolver o problema"""
    row = db.query(models.ErrorLog).filter(models.ErrorLog.id == error_id).first()
    if not row:
        raise HTTPException(status_code=404, detail={"error": "Not found"})
    db.delete(row)
    db.commit()
    return {"ok": True}


@router.post("/")
def create_error(payload: dict, db: Session = Depends(get_db)):
    """Cria um log de erro manualmente. Espera JSON com 'page', 'message' e opcional 'details'"""
    page = payload.get('page_name') or payload.get('page') or 'unknown'
    message = (payload.get('error_message') or payload.get('message') or 'sem mensagem')[:1024]
    details = payload.get('stack_trace') or payload.get('details')
    err = models.ErrorLog(page_name=page, error_message=message, stack_trace=details)
    db.add(err)
    db.commit()
    db.refresh(err)
    return {"id": err.id}
