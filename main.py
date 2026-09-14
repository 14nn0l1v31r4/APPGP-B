import os
import pytesseract
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import engine
from app import models

from app.controllers import (
    auth_controller,
    pacientes_controller,
    pagamentos_controller,
    dashboard_controller,
    upload_controller,
    importacao_controller
)

tesseract_cmd = os.getenv('TESSERACT_CMD', '/usr/bin/tesseract')
pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

tessdata_prefix = os.getenv('TESSDATA_PREFIX')
if tessdata_prefix:
    os.environ['TESSDATA_PREFIX'] = tessdata_prefix

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="APPGP - API", description="Sistema de Gestão Pix para Psicólogas")

app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"], 
    allow_methods=["*"], 
    allow_headers=["*"]
)

app.include_router(auth_controller.router)
app.include_router(pacientes_controller.router)
app.include_router(pagamentos_controller.router)
app.include_router(dashboard_controller.router)
app.include_router(upload_controller.router)
app.include_router(importacao_controller.router)

@app.get("/")
def home():
    return {"message": "Backend APPGP"}