from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional
import models, io, pytesseract, security
from PIL import Image
import pdfplumber
from parsers import extrair_os_dados
from database import get_db

router = APIRouter(prefix="/upload-pix", tags=["Upload"])

@router.post("/")
async def upload_pix(
    file: UploadFile = File(...), 
    valor_sessao_manual: Optional[float] = Form(None),
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(security.get_current_user) # 🔒 Segurança ativada
):
    content = await file.read()
    texto_extraido = ""
    
    if file.filename.lower().endswith('.pdf') or file.content_type == 'application/pdf':
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            for page in pdf.pages:
                texto_pagina = page.extract_text()
                if texto_pagina: texto_extraido += texto_pagina + "\n"
    else:
        img = Image.open(io.BytesIO(content))
        texto_extraido = pytesseract.image_to_string(img, lang='por')
    
    dados_extraidos = extrair_os_dados(texto_extraido)
    
    dados_extraidos["paciente_id"] = None
    dados_extraidos["sessoes_pagas"] = 1
    dados_extraidos["match_status"] = "Paciente não encontrado"
    dados_extraidos["valor_sessao_sugerido"] = valor_sessao_manual 
    
    valor_texto = dados_extraidos.get("valor", "0").replace(".", "").replace(",", ".")
    valor_pix = float(valor_texto) if valor_texto else 0.0
    nome_lido = dados_extraidos.get("pagador", "").strip().upper()
    
    paciente_encontrado = None

    if nome_lido and nome_lido != "NÃO IDENTIFICADO":
        # 🔒 O Motor de Match só procura nos pacientes desta psicóloga
        pacientes_cadastrados = db.query(models.Paciente).filter(models.Paciente.usuario_id == current_user.id).all()
        for p in pacientes_cadastrados:
            nome_db = p.nome.strip().upper()
            if " ".join(nome_lido.split()[:2]) == " ".join(nome_db.split()[:2]):
                paciente_encontrado = p
                break 

    if paciente_encontrado:
        dados_extraidos["paciente_id"] = paciente_encontrado.id
        dados_extraidos["match_status"] = "Vínculo Automático"
        valor_para_calculo = paciente_encontrado.valor_sessao
        dados_extraidos["valor_sessao_sugerido"] = valor_para_calculo
    else:
        valor_para_calculo = valor_sessao_manual

    if valor_para_calculo and valor_para_calculo > 0:
        sessoes_calculadas = round(valor_pix / valor_para_calculo)
        dados_extraidos["sessoes_pagas"] = max(1, sessoes_calculadas)

    return dados_extraidos