from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional

class PacienteCreate(BaseModel):
    nome: str
    valor_sessao: Decimal = Field(..., gt=0)
    data_inicio: str

class PacienteUpdate(BaseModel):
    valor_sessao: Decimal = Field(..., gt=0)

class StatusUpdate(BaseModel):
    status: str
    data_inativo: Optional[str] = None
    
class DesmarcarSessao(BaseModel):
    data_sessao: str

class PagamentoCreate(BaseModel):
    sessoes_pagas: int = Field(default=1, ge=1)
    pagador: str = Field(..., min_length=1)
    valor: Decimal = Field(..., gt=0)
    data_hora: str | datetime = Field(...)
    paciente_id: Optional[int] = None    
    id_transacao: Optional[str] = None
    idempotencia_chave: Optional[str] = None
    novo_paciente_nome: Optional[str] = None
    valor_sessao_manual: Optional[Decimal] = Field(default=None, gt=0)
    data_inicio_manual: Optional[str] = None

class PagamentoRapidoCreate(BaseModel):
    paciente_id: int
    sessoes_pagas: int = Field(default=1, ge=1)
    data_hora: Optional[str | datetime] = None
    idempotencia_chave: Optional[str] = None

class UsuarioCreate(BaseModel):
    nome: str
    email: str
    senha: str = Field(..., max_length=50)

class UsuarioResponse(BaseModel):
    id: int
    nome: str
    email: str

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str

class SessaoDesmarcadaUpdate(BaseModel):
    data_sessao: str
