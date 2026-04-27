from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import models, schemas, security
from database import get_db

router = APIRouter(prefix="/pacientes", tags=["Pacientes"])

@router.get("/")
def listar_pacientes(db: Session = Depends(get_db), current_user: models.Usuario = Depends(security.get_current_user)):
    # 🔒 Só devolve os pacientes DA psicóloga logada
    return db.query(models.Paciente).filter(models.Paciente.usuario_id == current_user.id).all()

@router.post("/")
def criar_paciente(paciente: schemas.PacienteCreate, db: Session = Depends(get_db), current_user: models.Usuario = Depends(security.get_current_user)):
    existente = db.query(models.Paciente).filter(
        models.Paciente.nome == paciente.nome, 
        models.Paciente.usuario_id == current_user.id
    ).first()
    
    if existente: return existente
    
    # 🔒 Associa o novo paciente à psicóloga logada
    novo = models.Paciente(**paciente.dict(), usuario_id=current_user.id)
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo

@router.put("/{paciente_id}")
def atualizar_paciente(paciente_id: int, paciente: schemas.PacienteUpdate, db: Session = Depends(get_db), current_user: models.Usuario = Depends(security.get_current_user)):
    db_paciente = db.query(models.Paciente).filter(models.Paciente.id == paciente_id, models.Paciente.usuario_id == current_user.id).first()
    if not db_paciente: raise HTTPException(status_code=404, detail="Paciente não encontrado")
    
    db_paciente.valor_sessao = paciente.valor_sessao
    db.commit()
    db.refresh(db_paciente)
    return db_paciente

@router.patch("/{paciente_id}/status")
def alternar_status_paciente(paciente_id: int, status_data: schemas.StatusUpdate, db: Session = Depends(get_db), current_user: models.Usuario = Depends(security.get_current_user)):
    p = db.query(models.Paciente).filter(models.Paciente.id == paciente_id, models.Paciente.usuario_id == current_user.id).first()
    if not p: raise HTTPException(status_code=404, detail="Paciente não encontrado")
    
    p.status = status_data.status
    p.data_inativo = status_data.data_inativo if p.status == "Inativo" else None
    db.commit()
    return {"status": p.status}

@router.post("/{paciente_id}/desmarcar")
def registrar_sessao_desmarcada(paciente_id: int, info: schemas.DesmarcarSessao, db: Session = Depends(get_db), current_user: models.Usuario = Depends(security.get_current_user)):
    p = db.query(models.Paciente).filter(models.Paciente.id == paciente_id, models.Paciente.usuario_id == current_user.id).first()
    if not p: raise HTTPException(status_code=404, detail="Acesso negado")
    
    nova_desmarcada = models.SessaoDesmarcada(data_sessao=info.data_sessao, paciente_id=paciente_id)
    db.add(nova_desmarcada)
    db.commit()
    return {"status": "sucesso"}