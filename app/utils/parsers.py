import re 

MESES_ABREVIADOS = {
    "JAN": "01", "FEV": "02", "MAR": "03", "ABR": "04",
    "MAI": "05", "JUN": "06", "JUL": "07", "AGO": "08",
    "SET": "09", "OUT": "10", "NOV": "11", "DEZ": "12"
}

def extrair_os_dados(arquivo):
    texto = " ".join(arquivo.split()) 
    
    banco = "Desconhecido"
    texto_lower = texto.lower()
    
    # Adicione esta linha mágica aqui:
    print(f"👀 TEXTO LIDO PELO OCR: {texto_lower}")
    
    if "alô caixa" in texto_lower or "sac caixa" in texto_lower:
        banco = "Caixa"
    elif "santander" in texto_lower or "4004-3535" in texto_lower:
        banco = "Santander"
    elif "nubank" in texto_lower or "nu pagamentos s.a" in texto_lower:
        banco = "Nubank"
    elif "bradesco" in texto_lower:
        banco = "Bradesco"
    elif "itaú unibanco" in texto_lower or "4004 4828" in texto_lower:
        banco = "Itaú"
    elif "banco do brasil" in texto_lower or "sisbb" in texto_lower or "comprovante bb" in texto_lower:
        banco = "Banco do Brasil"
    elif "inter" in texto_lower:
        banco = "Inter"
    elif "picpay" in texto_lower:
        banco = "PicPay"

    dados = {
        "pagador": "Não identificado",
        "valor": "0,00",
        "data": "Data não encontrada",
        "banco": banco,
        "id_transacao": ""  
    }

    id_m = re.search(r'(E[a-zA-Z0-9]{31,32})', texto)
    if id_m:
        dados["id_transacao"] = id_m.group(1)

    if banco == "Bradesco":
        if "fez a transação" in arquivo.lower():
            bloco = arquivo.lower().split("fez a transação")[-1]
            nome_m = re.search(r'nome:\s*([A-Za-zÀ-ÿ\s]+)', bloco, re.IGNORECASE)
            if nome_m: dados["pagador"] = nome_m.group(1).strip().upper().split('\n')[0]
        
        valor_m = re.search(r'R\$\s?([\d\.,]+)', texto)
        if valor_m: dados["valor"] = valor_m.group(1)
        
        data_m = re.search(r'(\d{2}/\d{2}/\d{4})', texto)
        if data_m: dados["data"] = data_m.group(1)

    elif banco == "Inter":
        valor_m = re.search(r'VALOR\s*R\$\s*([\d\.,]+)', texto, re.IGNORECASE)
        nome_m = re.search(r'DE\s*([A-Za-zÀ-ÿ\s]+)', texto, re.IGNORECASE)
        if valor_m: dados["valor"] = valor_m.group(1)
        if nome_m: dados["pagador"] = nome_m.group(1).strip().upper()

    elif banco == "Nubank":
        # 1. Extração de Valor (Blindado para "valor r$" ou "r$")
        valor_m = re.search(r'(?:valor\s+r\$|r\$|rs|r\s\$)\s*([\d\.,]+)', texto_lower)
        if valor_m: 
            dados["valor"] = valor_m.group(1)
            
        # 2. Extração da Data (Plano A: Leitura Normal / Plano B: Hackear ID do Pix)
        data_m = re.search(r'(\d{2})\s+([a-zA-Z]{3})\s+(\d{4})', texto)
        if data_m: 
            dia, mes_texto, ano = data_m.groups()
            mes_numero = MESES_ABREVIADOS.get(mes_texto.upper(), mes_texto.upper())
            dados["data"] = f"{dia}/{mes_numero}/{ano}"
        elif dados["id_transacao"]:
            match_data_id = re.search(r'(20[2-3]\d)(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])', dados["id_transacao"])
            if match_data_id:
                ano, mes, dia = match_data_id.groups()
                dados["data"] = f"{dia}/{mes}/{ano}"
                
        # 3. Extração do Nome (Plano A: Completo / Plano B: Fatiamento a Laser)
        if "origem" in texto_lower:
            bloco_origem = texto_lower.split("origem")[-1]
            # O Regex ignora a palavra "nome" e captura até bater em "instituição" ou afins
            nome_m = re.search(r'^[\s:]*(?:nome\s+)?([a-zà-ÿ\s]+?)(?:\s+institui|\s+cpf|\s+cnpj|\]|\-|\d|$)', bloco_origem)
            if nome_m:
                dados["pagador"] = nome_m.group(1).replace(':', '').strip().upper()
        else:
            # Fallback apenas para layouts muito antigos do Nubank
            nome_fallback = re.search(r'(?:conta corrente|conta poupan[çc]a|conta de pagamento)\s+([A-Za-zÀ-ÿ\s]+?)\s+nu\s+pagamentos', texto, re.IGNORECASE)
            if nome_fallback:
                dados["pagador"] = nome_fallback.group(1).strip().upper()

    elif banco == "Banco do Brasil":
        valor_m = re.search(r'R\$\s*([\d\.,]+)', texto, re.IGNORECASE)
        if valor_m: 
            dados["valor"] = valor_m.group(1)
            
        data_m = re.search(r'(\d{2}/\d{2}/\d{4})', texto)
        if data_m: 
            dados["data"] = data_m.group(1)
            
        # ✨ Novo Regex Flexível do BB - Para ao ver números ou a palavra CPF/CNPJ
        nome_m = re.search(r'(?:pagador|nome)[:\s]+(.*?)(?:\s+cpf|\s+cnpj|\d|$)', texto, re.IGNORECASE)
        if nome_m:
            nome_limpo = nome_m.group(1).replace(':', '').replace('-', '').strip().upper()
            dados["pagador"] = nome_limpo
    
    elif banco == "Caixa":
        valor_m = re.search(r'R\$\s*([\d\.,]+)', texto, re.IGNORECASE)
        if valor_m: 
            dados["valor"] = valor_m.group(1)
            
        data_m = re.search(r'(\d{2}/\d{2}/\d{4})', texto)
        if data_m: 
            dados["data"] = data_m.group(1)
            
        # ✨ Limpeza da exigência de CPF na Caixa
        nome_m = re.search(r'dados do pagador\s+nome\s+(.*?)(?:\s+cpf|\s+cnpj|\d|$)', texto, re.IGNORECASE)
        if nome_m:
            dados["pagador"] = nome_m.group(1).replace(':', '').strip().upper()

    elif banco == "Santander":
        # 1. Extração de Valor e Data
        valor_m = re.search(r'R\$\s*([\d\.,]+)', texto, re.IGNORECASE)
        if valor_m: 
            dados["valor"] = valor_m.group(1)
            
        data_m = re.search(r'(\d{2}/\d{2}/\d{4})', texto)
        if data_m: 
            dados["data"] = data_m.group(1)
            
        # ✨ 2. Extração do Nome (Fatiamento a Laser)
        bloco_pagador = ""
        # Procuramos o bloco exato e cortamos tudo o que vem antes!
        if "pagador" in texto_lower:
            bloco_pagador = texto_lower.split("pagador")[-1]
        elif "origem" in texto_lower:
            bloco_pagador = texto_lower.split("origem")[-1]
            
        if bloco_pagador:
            # O símbolo ^ garante que a leitura comece imediatamente após o corte
            nome_m = re.search(r'^[\s:]+(?:nome\s+|de\s+)?([a-zà-ÿ\s]+?)(?:\s+cpf|\s+cnpj|\s+institui|\s+banco|\s+ag[êe]ncia|\d|$)', bloco_pagador)
            if nome_m:
                dados["pagador"] = nome_m.group(1).replace(':', '').strip().upper()
    
    elif banco == "Itaú":
        valor_m = re.search(r'R\$\s*([\d\.,]+)', texto, re.IGNORECASE)
        if valor_m: 
            dados["valor"] = valor_m.group(1)
            
        data_m = re.search(r'(\d{2}/\d{2}/\d{4})', texto)
        if data_m: 
            dados["data"] = data_m.group(1)
            
        # ✨ Limpeza da exigência de CPF no Itaú
        nome_m = re.search(r'realizado em.*?de\s+(.*?)(?:\s+cpf|\s+cnpj|\d|$)', texto, re.IGNORECASE)
        if nome_m:
            dados["pagador"] = nome_m.group(1).replace(':', '').strip().upper()

    elif banco == "PicPay":
        valor_m = re.search(r'VALOR\s*R\$\s*([\d\.,]+)', texto, re.IGNORECASE)
        nome_m = re.search(r'DE\s*([A-Za-zÀ-ÿ\s]+)', texto, re.IGNORECASE)
        if valor_m: dados["valor"] = valor_m.group(1)
        if nome_m: dados["pagador"] = nome_m.group(1).strip().upper()
    
    return dados