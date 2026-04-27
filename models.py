from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class Usuario(Base):
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String)
    email = Column(String, unique=True, index=True)
    senha_hash = Column(String)
    
    pacientes = relationship("Paciente", back_populates="usuario")
    pagamentos = relationship("Pagamento", back_populates="usuario")


class Paciente(Base):
    __tablename__ = "pacientes"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    cpf = Column(String, unique=False, nullable=True)
    valor_sessao = Column(Float)
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
    valor = Column(Float)
    data_hora = Column(String)
    status = Column(String, default="Pago")
    id_transacao = Column(String, unique=True, index=True, nullable=True) 
    sessoes_pagas = Column(Integer, default=1)
    
    paciente_id = Column(Integer, ForeignKey("pacientes.id"), nullable=True) 
    paciente = relationship("Paciente", back_populates="pagamentos")
    
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    usuario = relationship("Usuario", back_populates="pagamentos")