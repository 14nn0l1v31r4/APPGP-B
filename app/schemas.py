from pydantic import BaseModel, Field
from typing import Optional

class PacienteCreate(BaseModel):
    nome: str
    valor_sessao: float
    data_inicio: str

class PacienteUpdate(BaseModel):
    valor_sessao: float

class StatusUpdate(BaseModel):
    status: str
    data_inativo: Optional[str] = None
    
class DesmarcarSessao(BaseModel):
    data_sessao: str

class PagamentoCreate(BaseModel):
    pagador: str
    valor: float
    data_hora: str
    sessoes_pagas: int = 0                
    sessoes_pagas: int = 1                
    paciente_id: Optional[int] = None    
    id_transacao: Optional[str] = None
    novo_paciente_nome: Optional[str] = None
    valor_sessao_manual: Optional[float] = None
    data_inicio_manual: Optional[str] = None

class PagamentoRapidoCreate(BaseModel):
    paciente_id: int
    sessoes_pagas: int = 1
    data_hora: Optional[str] = None

class UsuarioCreate(BaseModel):
    nome: str
    email: str
    senha: str = Field(..., max_length=50)

class UsuarioResponse(BaseModel):
    id: int
    nome: str
    email: str

    class Config:
        from_attributes = True  # Permite ler dados direto do banco SQLAlchemy

class Token(BaseModel):
    access_token: str
    token_type: str

class SessaoDesmarcadaUpdate(BaseModel):
    data_sessao: str