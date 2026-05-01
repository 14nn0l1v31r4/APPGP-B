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
    
    if "alô caixa" in texto_lower or "sac caixa" in texto_lower:
        banco = "Caixa"
    elif "atendimento santander" in texto_lower or "4004-3535" in texto_lower:
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
            nome_m = re.search(r'nome:\s*([A-Z\s]+)', bloco, re.IGNORECASE)
            if nome_m: dados["pagador"] = nome_m.group(1).strip().upper().split('\n')[0]
        
        valor_m = re.search(r'R\$\s?([\d\.,]+)', texto)
        if valor_m: dados["valor"] = valor_m.group(1)
        
        data_m = re.search(r'(\d{2}/\d{2}/\d{4})', texto)
        if data_m: dados["data"] = data_m.group(1)

    elif banco == "Inter":
        valor_m = re.search(r'VALOR\s*R\$\s*([\d\.,]+)', texto, re.IGNORECASE)
        nome_m = re.search(r'DE\s*([A-Z\s]+)', texto, re.IGNORECASE)
        # ... e assim por diante
        if valor_m: dados["valor"] = valor_m.group(1)
        if nome_m: dados["pagador"] = nome_m.group(1).strip().upper()

    elif banco == "Nubank":
        valor_m = re.search(r'R\$\s*([\d\.,]+)', texto, re.IGNORECASE)
        if valor_m: 
            dados["valor"] = valor_m.group(1)
            
        data_m = re.search(r'(\d{2})\s+([a-zA-Z]{3})\s+(\d{4})', texto)
        
        if data_m: 
            dia = data_m.group(1)
            mes_texto = data_m.group(2).upper()
            ano = data_m.group(3)
            
            mes_numero = MESES_ABREVIADOS.get(mes_texto, mes_texto)
            
            dados["data"] = f"{dia}/{mes_numero}/{ano}"
            
        nome_m = re.search(r'(?:conta corrente|conta poupan[çc]a|conta de pagamento)\s+([a-zA-ZÀ-ÿ\s]+?)\s+nu\s+pagamentos', texto, re.IGNORECASE)
        if nome_m:
            dados["pagador"] = nome_m.group(1).strip().upper()


    elif banco == "Banco do Brasil":
        valor_m = re.search(r'R\$\s*([\d\.,]+)', texto, re.IGNORECASE)
        if valor_m: 
            dados["valor"] = valor_m.group(1)
            
        data_m = re.search(r'(\d{2}/\d{2}/\d{4})', texto)
        if data_m: 
            dados["data"] = data_m.group(1)
            
        nome_m = re.search(r'pagador\s+(.*?)\s+cpf', texto, re.IGNORECASE)
        if nome_m:
            dados["pagador"] = nome_m.group(1).strip().upper()
    
    elif banco == "Caixa":
        valor_m = re.search(r'R\$\s*([\d\.,]+)', texto, re.IGNORECASE)
        if valor_m: 
            dados["valor"] = valor_m.group(1)
            
        data_m = re.search(r'(\d{2}/\d{2}/\d{4})', texto)
        if data_m: 
            dados["data"] = data_m.group(1)
            
        nome_m = re.search(r'dados do pagador\s+nome\s+(.*?)\s+cpf', texto, re.IGNORECASE)
        if nome_m:
            dados["pagador"] = nome_m.group(1).strip().upper()

    elif banco == "Santander":
        valor_m = re.search(r'R\$\s*([\d\.,]+)', texto, re.IGNORECASE)
        if valor_m: 
            dados["valor"] = valor_m.group(1)
        data_m = re.search(r'(\d{2}/\d{2}/\d{4})', texto)
        if data_m: 
            dados["data"] = data_m.group(1)
            
        nome_m = re.search(r'dados do pagador\s+de\s+(.*?)\s+cpf', texto, re.IGNORECASE)
        if nome_m:
            dados["pagador"] = nome_m.group(1).strip().upper()
    
    elif banco == "Itaú":
        valor_m = re.search(r'R\$\s*([\d\.,]+)', texto, re.IGNORECASE)
        if valor_m: 
            dados["valor"] = valor_m.group(1)
            
        data_m = re.search(r'(\d{2}/\d{2}/\d{4})', texto)
        if data_m: 
            dados["data"] = data_m.group(1)
            
        nome_m = re.search(r'realizado em.*?de\s+(.*?)\s+cpf', texto, re.IGNORECASE)
        if nome_m:
            dados["pagador"] = nome_m.group(1).strip().upper()

    elif banco == "PicPay":
        valor_m = re.search(r'VALOR\s*R\$\s*([\d\.,]+)', texto, re.IGNORECASE)
        nome_m = re.search(r'DE\s*([A-Z\s]+)', texto, re.IGNORECASE)
        if valor_m: dados["valor"] = valor_m.group(1)
        if nome_m: dados["pagador"] = nome_m.group(1).strip().upper()
    
    return dados