from sqlalchemy import Column, DateTime, Integer, String, Numeric, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime

class Usuario(Base):
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String)
    email = Column(String, unique=True, index=True)
    senha_hash = Column(String)
    
    pacientes = relationship("Paciente", back_populates="usuario")
    pagamentos = relationship("Pagamento", back_populates="usuario")
    lotes = relationship("LoteImportacao", back_populates="usuario")


class Paciente(Base):
    __tablename__ = "pacientes"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    cpf = Column(String, unique=False, nullable=True)
    valor_sessao = Column(Numeric(12, 2))
    tipo_contrato = Column(String, default="Por Sessão")
    dia_vencimento = Column(Integer, nullable=True)
    status = Column(String, default="Ativo")
    data_inicio = Column(String, default=lambda: datetime.now().strftime("%Y-%m-%d"))
    data_inativo = Column(String, nullable=True) 
    
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    usuario = relationship("Usuario", back_populates="pacientes")
    
    pagamentos = relationship("Pagamento", back_populates="paciente")
    
    # RELAÇÃO: Lista de datas desmarcadas
    desmarcadas = relationship("SessaoDesmarcada", back_populates="paciente", cascade="all, delete-orphan")

# NOVA TABELA: Histórico de Faltas/Desmarcações
class SessaoDesmarcada(Base):
    __tablename__ = "sessoes_desmarcadas"
    
    id = Column(Integer, primary_key=True, index=True)
    data_sessao = Column(String) # A data da falta (YYYY-MM-DD)
    paciente_id = Column(Integer, ForeignKey("pacientes.id"))
    
    paciente = relationship("Paciente", back_populates="desmarcadas")


class Pagamento(Base):
    __tablename__ = "pagamentos"
    
    id = Column(Integer, primary_key=True, index=True)
    pagador = Column(String)
    valor = Column(Numeric(12, 2))
    data_hora = Column(DateTime(timezone=True))
    status = Column(String, default="Pago")
    id_transacao = Column(String, unique=True, index=True, nullable=True) 
    idempotencia_chave = Column(String, unique=True, index=True, nullable=True)
    sessoes_pagas = Column(Integer, default=1)
    
    paciente_id = Column(Integer, ForeignKey("pacientes.id"), nullable=True) 
    paciente = relationship("Paciente", back_populates="pagamentos")
    
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    usuario = relationship("Usuario", back_populates="pagamentos")


class LoteImportacao(Base):
    __tablename__ = "lotes_importacao"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
    status = Column(String, default="PROCESSANDO", index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    usuario = relationship("Usuario", back_populates="lotes")
    itens = relationship("ItemImportacao", back_populates="lote", cascade="all, delete-orphan")


class ItemImportacao(Base):
    __tablename__ = "itens_importacao"

    id = Column(Integer, primary_key=True, index=True)
    lote_id = Column(Integer, ForeignKey("lotes_importacao.id"), nullable=False, index=True)
    nome_arquivo = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    hash_sha256 = Column(String, nullable=True)

    banco = Column(String, nullable=True)
    pagador = Column(String, nullable=True)
    valor = Column(Numeric(12, 2), nullable=True)
    data_hora = Column(String, nullable=True)
    id_transacao = Column(String, nullable=True)

    paciente_id = Column(Integer, ForeignKey("pacientes.id"), nullable=True)
    sessoes_pagas = Column(Integer, default=1)
    valor_sessao_sugerido = Column(Numeric(12, 2), nullable=True)

    dados_extraidos = Column(JSON, nullable=True)

    status = Column(String, default="PROCESSANDO", index=True)
    etapa_erro = Column(String, nullable=True)
    mensagem_erro = Column(String, nullable=True)

    pagamento_id = Column(Integer, ForeignKey("pagamentos.id"), nullable=True, unique=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    lote = relationship("LoteImportacao", back_populates="itens")
    paciente = relationship("Paciente")
    pagamento = relationship("Pagamento")
