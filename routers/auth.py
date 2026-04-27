from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import models, schemas, security
from database import get_db

router = APIRouter(prefix="/auth", tags=["Autenticação"])

@router.post("/registrar", response_model=schemas.UsuarioResponse)
def registrar_usuario(usuario: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    # 1. Verifica se o email já está em uso
    db_usuario = db.query(models.Usuario).filter(models.Usuario.email == usuario.email).first()
    if db_usuario:
        raise HTTPException(status_code=400, detail="Este email já está registado.")

    # 2. Criptografa a senha e guarda no banco
    senha_criptografada = security.gerar_hash_senha(usuario.senha)
    novo_usuario = models.Usuario(
        nome=usuario.nome,
        email=usuario.email,
        senha_hash=senha_criptografada
    )
    
    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)
    
    return novo_usuario

@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # 1. O OAuth2PasswordRequestForm usa o campo 'username', nós mapeamos para o 'email'
    usuario = db.query(models.Usuario).filter(models.Usuario.email == form_data.username).first()

    # 2. Se o usuário não existir ou a senha estiver errada, barra o acesso!
    if not usuario or not security.verificar_senha(form_data.password, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Tudo certo! Gera o crachá (Token JWT)
    token_acesso = security.criar_token_acesso(dados={"sub": usuario.email})
    
    return {"access_token": token_acesso, "token_type": "bearer"}