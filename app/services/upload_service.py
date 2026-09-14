import io, pytesseract, pdfplumber
from decimal import Decimal
from PIL import Image
from sqlalchemy.orm import Session
from app.repositories import upload_repository
from app.utils.parsers import extrair_os_dados

def processar_arquivo_pix(db: Session, content: bytes, filename: str, content_type: str, valor_sessao_manual: float, usuario_id: int):
    texto_extraido = ""
    
    if filename.lower().endswith('.pdf') or content_type == 'application/pdf':
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            for page in pdf.pages:
                texto_pagina = page.extract_text()
                if texto_pagina: texto_extraido += texto_pagina + "\n"
    else:
        img = Image.open(io.BytesIO(content))
        texto_extraido = pytesseract.image_to_string(img, lang='por')
    
    dados_extraidos = extrair_os_dados(texto_extraido)
    
    dados_extraidos.update({
        "paciente_id": None,
        "sessoes_pagas": 1,
        "match_status": "Paciente não encontrado",
        "valor_sessao_sugerido": valor_sessao_manual
    })
    
    valor_texto = dados_extraidos.get("valor", "0").replace(".", "").replace(",", ".")
    valor_pix = Decimal(valor_texto) if valor_texto else Decimal("0")
    nome_lido = dados_extraidos.get("pagador", "").strip().upper()
    
    paciente_encontrado = None
    if nome_lido and nome_lido != "NÃO IDENTIFICADO":
        pacientes_cadastrados = upload_repository.buscar_pacientes_por_usuario(db, usuario_id)
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
        sessoes_calculadas = round(
            valor_pix / Decimal(str(valor_para_calculo))
        )
        dados_extraidos["sessoes_pagas"] = max(1, sessoes_calculadas)

    return dados_extraidos
