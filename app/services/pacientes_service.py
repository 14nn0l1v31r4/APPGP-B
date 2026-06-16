from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.repositories import pacientes_repository
from app import schemas
from app.models import Pagamento

def listar_pacientes(db: Session, usuario_id: int):
    return pacientes_repository.listar_todos(db, usuario_id)

def criar_paciente(db: Session, paciente: schemas.PacienteCreate, usuario_id: int):
    existente = pacientes_repository.buscar_por_nome(db, paciente.nome, usuario_id)
    if existente:
        return existente
    
    dados = paciente.dict()
    dados["usuario_id"] = usuario_id
    return pacientes_repository.criar(db, dados)

def atualizar_paciente(db: Session, paciente_id: int, paciente_dados: schemas.PacienteUpdate, usuario_id: int):
    paciente = pacientes_repository.buscar_por_id(db, paciente_id, usuario_id)
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente não encontrado")
    
    paciente.valor_sessao = paciente_dados.valor_sessao
    pacientes_repository.salvar_alteracoes(db)
    return paciente

def alternar_status(db: Session, paciente_id: int, status_data: schemas.StatusUpdate, usuario_id: int):
    p = pacientes_repository.buscar_por_id(db, paciente_id, usuario_id)
    if not p:
        raise HTTPException(status_code=404, detail="Paciente não encontrado")
    
    p.status = status_data.status
    p.data_inativo = status_data.data_inativo if p.status == "Inativo" else None
    pacientes_repository.salvar_alteracoes(db)
    return {"status": p.status}

def registrar_desmarcada(db: Session, paciente_id: int, info: schemas.DesmarcarSessao, usuario_id: int):
    p = pacientes_repository.buscar_por_id(db, paciente_id, usuario_id)
    if not p:
        raise HTTPException(status_code=404, detail="Acesso negado")
    
    dados = {"data_sessao": info.data_sessao, "paciente_id": paciente_id}
    pacientes_repository.registrar_sessao_desmarcada(db, dados)
    return {"status": "sucesso"}

def listar_sessoes_desmarcadas(db: Session, usuario_id: int):
    desmarcadas = pacientes_repository.listar_desmarcadas(db, usuario_id)
    
    resultado = []
    for d in desmarcadas:
        resultado.append({
            "id": d.id,
            "paciente_id": d.paciente_id,
            "paciente_nome": d.paciente.nome,
            "data_sessao": d.data_sessao
        })
    return resultado

def atualizar_sessao_desmarcada(db: Session, desmarcada_id: int, dados: schemas.SessaoDesmarcadaUpdate, usuario_id: int):
    sessao = pacientes_repository.buscar_desmarcada_por_id(db, desmarcada_id, usuario_id)
    if not sessao:
        raise HTTPException(status_code=404, detail="Sessão não encontrada ou acesso negado.")
    
    sessao.data_sessao = dados.data_sessao
    pacientes_repository.salvar_alteracoes(db)
    return {"mensagem": "Data atualizada com sucesso!"}

def excluir_sessao_desmarcada(db: Session, desmarcada_id: int, usuario_id: int):
    sessao = pacientes_repository.buscar_desmarcada_por_id(db, desmarcada_id, usuario_id)
    if not sessao:
        raise HTTPException(status_code=404, detail="Sessão não encontrada ou acesso negado.")
    
    pacientes_repository.excluir_desmarcada(db, sessao)
    return {"mensagem": "Sessão excluída com sucesso!"} 

def resumo_mensal(db: Session, paciente_id: int, usuario_id: int): # Removeu o parâmetro 'mes'
    # 1. Verifica se o paciente existe e pertence a esta psicóloga
    p = pacientes_repository.buscar_por_id(db, paciente_id, usuario_id)
    if not p:
        raise HTTPException(status_code=404, detail="Paciente não encontrado")
    
    # 2. Busca TODOS os pagamentos históricos deste paciente, ordenando pelos mais recentes
    pagamentos = db.query(Pagamento).filter(
        Pagamento.paciente_id == paciente_id
    ).order_by(Pagamento.id.desc()).all()
    
    # 3. Faz a matemática acumulada de todo o histórico
    total_sessoes = sum(pg.sessoes_pagas for pg in pagamentos if pg.sessoes_pagas)
    total_valor = sum(pg.valor for pg in pagamentos)
    
    return {
        "total_sessoes_pagas": total_sessoes,
        "total_valor_pago": total_valor,
        "pagamentos": [{"data": pg.data_hora, "valor": pg.valor, "sessoes": pg.sessoes_pagas} for pg in pagamentos]
    }