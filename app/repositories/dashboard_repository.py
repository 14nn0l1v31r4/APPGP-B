from sqlalchemy.orm import Session
from app import models

def buscar_pagamentos_mes(db: Session, usuario_id: int, filtro_mes: str):
    return db.query(models.Pagamento).filter(
        models.Pagamento.usuario_id == usuario_id,
        models.Pagamento.data_hora.contains(f"/{filtro_mes}/")
    ).all()

def buscar_todos_dados_usuario(db: Session, usuario_id: int):
    pacientes = db.query(models.Paciente).filter(models.Paciente.usuario_id == usuario_id).all()
    pagamentos = db.query(models.Pagamento).filter(models.Pagamento.usuario_id == usuario_id).all()
    return pacientes, pagamentos

def contar_desmarcadas_por_paciente(db: Session, paciente_id: int):
    return db.query(models.SessaoDesmarcada).filter(models.SessaoDesmarcada.paciente_id == paciente_id).count()