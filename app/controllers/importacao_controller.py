from fastapi import APIRouter, Depends, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from typing import Optional, List
from app import models, schemas
from app.core import security
from app.core.database import get_db
from app.services import importacao_service

router = APIRouter(prefix="/upload-pix/lotes", tags=["Importação em Lote"])

@router.post("/", response_model=schemas.LoteImportacaoResponse, status_code=status.HTTP_201_CREATED)
async def criar_lote_importacao(
    files: List[UploadFile] = File(...),
    valor_sessao_manual: Optional[float] = Form(None),
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(security.get_current_user)
):
    arquivos_lidos = []
    for f in files:
        content = await f.read()
        arquivos_lidos.append((content, f.filename, f.content_type))

    return importacao_service.criar_lote_e_processar(
        db=db,
        arquivos=arquivos_lidos,
        valor_sessao_manual=valor_sessao_manual,
        usuario_id=current_user.id
    )

@router.get("/{lote_id}", response_model=schemas.LoteImportacaoResponse)
def obter_detalhes_lote(
    lote_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(security.get_current_user)
):
    return importacao_service.obter_lote(
        db=db,
        lote_id=lote_id,
        usuario_id=current_user.id
    )

@router.patch("/{lote_id}/itens/{item_id}", response_model=schemas.ItemImportacaoResponse)
def editar_item_lote(
    lote_id: int,
    item_id: int,
    dados: schemas.ItemImportacaoUpdate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(security.get_current_user)
):
    return importacao_service.editar_item(
        db=db,
        lote_id=lote_id,
        item_id=item_id,
        dados=dados,
        usuario_id=current_user.id
    )

@router.post("/{lote_id}/itens/{item_id}/rejeitar", response_model=schemas.ItemImportacaoResponse)
def rejeitar_item_lote(
    lote_id: int,
    item_id: int,
    dados: Optional[schemas.RejeitarItemRequest] = None,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(security.get_current_user)
):
    motivo = dados.motivo if dados else None
    return importacao_service.rejeitar_item(
        db=db,
        lote_id=lote_id,
        item_id=item_id,
        motivo=motivo,
        usuario_id=current_user.id
    )

@router.post("/{lote_id}/itens/{item_id}/aprovar", response_model=schemas.ItemImportacaoResponse)
def aprovar_item_lote(
    lote_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(security.get_current_user)
):
    return importacao_service.aprovar_item_individual(
        db=db,
        lote_id=lote_id,
        item_id=item_id,
        usuario_id=current_user.id
    )

@router.post("/{lote_id}/aprovar-selecionados")
def aprovar_selecionados_lote(
    lote_id: int,
    dados: schemas.AprovarSelecionadosRequest,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(security.get_current_user)
):
    return importacao_service.aprovar_selecionados(
        db=db,
        lote_id=lote_id,
        item_ids=dados.item_ids,
        usuario_id=current_user.id
    )
