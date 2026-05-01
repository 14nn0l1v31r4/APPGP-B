from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app import models
from app.core import security
from app.core.database import get_db
from app.services import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/")
def get_dashboard(mes: str = "Abril", db: Session = Depends(get_db), current_user: models.Usuario = Depends(security.get_current_user)):
    return dashboard_service.gerar_relatorio_dashboard(db, mes, current_user.id)