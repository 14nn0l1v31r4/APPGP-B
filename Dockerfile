# 1. Usa uma imagem leve do Python
FROM python:3.11-slim

# 2. Instala o Tesseract OCR, o suporte para Português e bibliotecas de imagem
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-por \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*
    
# 3. Define a pasta de trabalho dentro do container
WORKDIR /app

# 4. Copia o arquivo de dependências e instala as bibliotecas Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copia todo o código do seu backend para dentro do container
COPY . .

# 6. Comando para iniciar o servidor FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]