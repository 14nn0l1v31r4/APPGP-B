# Usa uma imagem oficial do Python, versão slim (mais leve e rápida)
FROM python:3.11-slim

# Define o diretório de trabalho dentro do contêiner
WORKDIR /app

# 🛠️ Instala as dependências do sistema operacional
# O Tesseract precisa do pacote 'por' para ler português
# O poppler-utils é necessário para o pdfplumber funcionar bem
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-por \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copia apenas o arquivo de dependências primeiro (aproveita o cache do Docker)
COPY requirements.txt .

# Instala as bibliotecas do Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o resto do projeto (a nova pasta app/, main.py, etc) para dentro do contêiner
COPY . .

# Expõe a porta 8000 para podermos acessar a API
EXPOSE 8000

# Comando para iniciar o servidor diretamente pelo Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]