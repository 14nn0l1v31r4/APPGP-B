from sqlalchemy.orm import Session
from app import models


def listar_todos(db: Session, usuario_id: int):
    return db.query(models.Paciente).filter(models.Paciente.usuario_id == usuario_id).all()

def buscar_por_nome(db: Session, nome: str, usuario_id: int):
    return db.query(models.Paciente).filter(
        models.Paciente.nome == nome, 
        models.Paciente.usuario_id == usuario_id
    ).first()

def buscar_por_id(db: Session, paciente_id: int, usuario_id: int):
    return db.query(models.Paciente).filter(
        models.Paciente.id == paciente_id, 
        models.Paciente.usuario_id == usuario_id
    ).first()

def criar(db: Session, dados_paciente: dict):
    novo_paciente = models.Paciente(**dados_paciente)
    db.add(novo_paciente)
    db.commit()
    db.refresh(novo_paciente)
    return novo_paciente

def salvar_alteracoes(db: Session):
    db.commit()

def registrar_sessao_desmarcada(db: Session, dados_desmarcada: dict):
    nova_desmarcada = models.SessaoDesmarcada(**dados_desmarcada)
    db.add(nova_desmarcada)
    db.commit()
    return nova_desmarcada