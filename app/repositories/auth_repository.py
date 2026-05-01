from sqlalchemy.orm import Session
from app import models

def buscar_por_email(db: Session, email: str):
    return db.query(models.Usuario).filter(models.Usuario.email == email).first()

def criar_usuario(db: Session, dados: dict):
    novo_usuario = models.Usuario(**dados)
    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)
    return novo_usuario