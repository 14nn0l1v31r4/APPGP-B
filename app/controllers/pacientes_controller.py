from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app import schemas
from app import models
from app.core import security
from app.core.database import get_db
from app.services import pacientes_service

router = APIRouter(prefix="/pacientes", tags=["Pacientes"])

@router.get("/")
def listar_pacientes(db: Session = Depends(get_db), current_user: models.Usuario = Depends(security.get_current_user)):
    return pacientes_service.listar_pacientes(db, current_user.id)

@router.post("/")
def criar_paciente(paciente: schemas.PacienteCreate, db: Session = Depends(get_db), current_user: models.Usuario = Depends(security.get_current_user)):
    return pacientes_service.criar_paciente(db, paciente, current_user.id)

@router.put("/{paciente_id}")
def atualizar_paciente(paciente_id: int, paciente: schemas.PacienteUpdate, db: Session = Depends(get_db), current_user: models.Usuario = Depends(security.get_current_user)):
    return pacientes_service.atualizar_paciente(db, paciente_id, paciente, current_user.id)

@router.patch("/{paciente_id}/status")
def alternar_status_paciente(paciente_id: int, status_data: schemas.StatusUpdate, db: Session = Depends(get_db), current_user: models.Usuario = Depends(security.get_current_user)):
    return pacientes_service.alternar_status(db, paciente_id, status_data, current_user.id)

@router.post("/{paciente_id}/desmarcar")
def registrar_sessao_desmarcada(paciente_id: int, info: schemas.DesmarcarSessao, db: Session = Depends(get_db), current_user: models.Usuario = Depends(security.get_current_user)):
    return pacientes_service.registrar_desmarcada(db, paciente_id, info, current_user.id)

@router.get("/{paciente_id}/resumo")
def resumo_paciente(
    paciente_id: int, 
    mes: str, 
    db: Session = Depends(get_db), 
    current_user: models.Usuario = Depends(security.get_current_user)
):
    return pacientes_service.resumo_mensal(db, paciente_id, mes, current_user.id)

@router.get("/desmarcadas")
def listar_sessoes_desmarcadas(
    db: Session = Depends(get_db), 
    current_user: models.Usuario = Depends(security.get_current_user)
):
    return pacientes_service.listar_sessoes_desmarcadas(db, current_user.id)

@router.put("/desmarcadas/{desmarcada_id}")
def atualizar_sessao_desmarcada(
    desmarcada_id: int, 
    dados: schemas.SessaoDesmarcadaUpdate, 
    db: Session = Depends(get_db), 
    current_user: models.Usuario = Depends(security.get_current_user)
):
    return pacientes_service.atualizar_sessao_desmarcada(db, desmarcada_id, dados, current_user.id)

@router.delete("/desmarcadas/{desmarcada_id}")
def excluir_sessao_desmarcada(
    desmarcada_id: int, 
    db: Session = Depends(get_db), 
    current_user: models.Usuario = Depends(security.get_current_user)
):
    return pacientes_service.excluir_sessao_desmarcada(db, desmarcada_id, current_user.id)