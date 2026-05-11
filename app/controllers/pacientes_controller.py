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


@router.get("/desmarcadas")
def listar_sessoes_desmarcadas(
    db: Session = Depends(get_db), 
    current_user: models.Usuario = Depends(security.get_current_user)
):
    desmarcadas = (
        db.query(models.SessaoDesmarcada)
        .join(models.Paciente)
        .filter(models.Paciente.usuario_id == current_user.id)
        .order_by(models.SessaoDesmarcada.data_sessao.desc())
        .all()
    )
    resultado = []
    for d in desmarcadas:
        resultado.append({
            "id": d.id,
            "paciente_id": d.paciente_id,
            "paciente_nome": d.paciente.nome,
            "data_sessao": d.data_sessao
        })
        
    return resultado