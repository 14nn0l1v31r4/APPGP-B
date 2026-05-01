from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app import schemas
from app.core import security
from app import models
from app.core.database import get_db
from app.services import auth_service


router = APIRouter(prefix="/auth", tags=["Autenticação"])

@router.post("/registrar", response_model=schemas.UsuarioResponse)
def registrar_usuario(usuario: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    return auth_service.registrar_novo_usuario(db, usuario)

@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # O form_data.username mapeia para o nosso email
    return auth_service.autenticar_usuario(db, form_data.username, form_data.password)