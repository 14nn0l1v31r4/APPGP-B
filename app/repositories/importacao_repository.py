from sqlalchemy.orm import Session
from app import models

def criar_lote(db: Session, usuario_id: int) -> models.LoteImportacao:
    lote = models.LoteImportacao(usuario_id=usuario_id, status="PROCESSANDO")
    db.add(lote)
    db.commit()
    db.refresh(lote)
    return lote

def criar_item(db: Session, lote_id: int, dados: dict) -> models.ItemImportacao:
    dados_completos = dados.copy()
    dados_completos["lote_id"] = lote_id
    item = models.ItemImportacao(**dados_completos)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

def buscar_lote(db: Session, lote_id: int, usuario_id: int) -> models.LoteImportacao | None:
    return db.query(models.LoteImportacao).filter(
        models.LoteImportacao.id == lote_id,
        models.LoteImportacao.usuario_id == usuario_id
    ).first()

def buscar_item(db: Session, lote_id: int, item_id: int, usuario_id: int) -> models.ItemImportacao | None:
    return (
        db.query(models.ItemImportacao)
        .join(models.LoteImportacao)
        .filter(
            models.ItemImportacao.id == item_id,
            models.ItemImportacao.lote_id == lote_id,
            models.LoteImportacao.usuario_id == usuario_id
        )
        .first()
    )

def listar_itens(db: Session, lote_id: int, usuario_id: int) -> list[models.ItemImportacao]:
    return (
        db.query(models.ItemImportacao)
        .join(models.LoteImportacao)
        .filter(
            models.ItemImportacao.lote_id == lote_id,
            models.LoteImportacao.usuario_id == usuario_id
        )
        .order_by(models.ItemImportacao.id.asc())
        .all()
    )

def salvar(db: Session, entidade) -> None:
    db.commit()
    db.refresh(entidade)

