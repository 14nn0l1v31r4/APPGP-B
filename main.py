import os
import pytesseract
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importa a conexão do banco e os modelos (Eles mudaram de lugar!)
from app.core.database import engine
from app import models

# Importa as Novas Rotas (Controllers)
from app.controllers import (
    auth_controller,
    pacientes_controller,
    pagamentos_controller,
    dashboard_controller,
    upload_controller
)

# 🛠️ Correção Tesseract (Windows / Docker)
tesseract_cmd = os.getenv('TESSERACT_CMD', '/usr/bin/tesseract')
pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

tessdata_prefix = os.getenv('TESSDATA_PREFIX')
if tessdata_prefix:
    os.environ['TESSDATA_PREFIX'] = tessdata_prefix

# Cria as tabelas na base de dados
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="APPGP - API", description="Sistema de Gestão Pix para Psicólogas com Arquitetura Profissional")

# Configuração de Segurança (CORS)
app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"], 
    allow_methods=["*"], 
    allow_headers=["*"]
)

# 🌟 Registar os Controllers (Antigas Rotas)
app.include_router(auth_controller.router)
app.include_router(pacientes_controller.router)
app.include_router(pagamentos_controller.router)
app.include_router(dashboard_controller.router)
app.include_router(upload_controller.router)

@app.get("/")
def home():
    return {"message": "Backend APPGP - Cérebro MVC Ativado! 🧠✨ "}