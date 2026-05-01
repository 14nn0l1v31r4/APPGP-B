from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional
from app import models
from app.core import security
from app.core.database import get_db
from app.services import upload_service

router = APIRouter(prefix="/upload-pix", tags=["Upload"])

@router.post("/")
async def upload_pix(
    file: UploadFile = File(...), 
    valor_sessao_manual: Optional[float] = Form(None),
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(security.get_current_user)
):
    content = await file.read()
    
    return upload_service.processar_arquivo_pix(
        db=db,
        content=content,
        filename=file.filename,
        content_type=file.content_type,
        valor_sessao_manual=valor_sessao_manual,
        usuario_id=current_user.id
    )