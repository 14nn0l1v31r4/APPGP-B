import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do ficheiro .env
load_dotenv()

# Vai buscar o URL da base de dados ao .env. Se não encontrar, usa o SQLite local como plano B.
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./appgp.db")

# O argumento 'check_same_thread' é obrigatório apenas para o SQLite.
# Se no futuro mudarmos o URL do .env para um PostgreSQL, o Python desativa isso automaticamente.
connect_args = {"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args=connect_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()