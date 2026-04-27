from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import models, database, os, pytesseract

# Importamos os nossos Controllers (Routers)
from routers import pacientes, pagamentos, dashboard, upload, auth

# Configuração Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
os.environ['TESSDATA_PREFIX'] = r'C:\Program Files\Tesseract-OCR\tessdata'

# Cria as tabelas na base de dados
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="APPGP - API", description="Sistema de Gestão Pix para Psicólogas")

# Configuração de Segurança (CORS)
app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"], 
    allow_methods=["*"], 
    allow_headers=["*"]
)

# 🌟 Registar as Rotas (Ficheiros isolados)
app.include_router(auth.router)
app.include_router(pacientes.router)
app.include_router(pagamentos.router)
app.include_router(dashboard.router)
app.include_router(upload.router)

@app.get("/")
def home():
    return {"message": "Backend APPGP - Cérebro Ativado com Arquitetura Limpa! 🧠✨ "}