from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app import schemas
from app.core import security
from app.repositories import auth_repository

def registrar_novo_usuario(db: Session, usuario: schemas.UsuarioCreate):
    if auth_repository.buscar_por_email(db, usuario.email):
        raise HTTPException(status_code=400, detail="Este email já está registado.")

    senha_criptografada = security.gerar_hash_senha(usuario.senha)
    dados_usuario = {
        "nome": usuario.nome,
        "email": usuario.email,
        "senha_hash": senha_criptografada
    }
    return auth_repository.criar_usuario(db, dados_usuario)

def autenticar_usuario(db: Session, email: str, senha: str):
    usuario = auth_repository.buscar_por_email(db, email)

    if not usuario or not security.verificar_senha(senha, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_acesso = security.criar_token_acesso(dados={"sub": usuario.email})
    return {"access_token": token_acesso, "token_type": "bearer"}