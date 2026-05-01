from sqlalchemy.orm import Session
from app import models
from app.repositories import upload_repository
from app.utils.parsers import extrair_os_dados

def buscar_pacientes_por_usuario(db: Session, usuario_id: int):
    # O motor de match precisa da lista de pacientes para procurar
    return db.query(models.Paciente).filter(models.Paciente.usuario_id == usuario_id).all()