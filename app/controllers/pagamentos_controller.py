from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app import schemas
from app import models
from app.core import security
from app.core.database import get_db
from app.services import pagamentos_service

router = APIRouter(prefix="/pagamentos", tags=["Pagamentos"])

@router.post("/")
def registrar_pagamento(pg: schemas.PagamentoCreate, db: Session = Depends(get_db), current_user: models.Usuario = Depends(security.get_current_user)):
    return pagamentos_service.processar_pagamento(db, pg, current_user.id)

@router.delete("/{pagamento_id}")
def deletar_pagamento(pagamento_id: int, db: Session = Depends(get_db), current_user: models.Usuario = Depends(security.get_current_user)):
    return pagamentos_service.remover_pagamento(db, pagamento_id, current_user.id)