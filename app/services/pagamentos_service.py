from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app import schemas
from app.repositories import pagamentos_repository
from app.repositories import pagamentos_repository, pacientes_repository

def registrar_pagamento_rapido(db: Session, dados: schemas.PagamentoRapidoCreate, usuario_id: int):
    paciente = pacientes_repository.buscar_por_id(db, dados.paciente_id, usuario_id)
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente não encontrado")

    sessoes = dados.sessoes_pagas if dados.sessoes_pagas > 0 else 1
    valor_calculado = paciente.valor_sessao * sessoes
    data_hora_final = dados.data_hora if dados.data_hora else datetime.now().strftime("%d/%m/%Y %H:%M")

    dados_pagamento = {
        "paciente_id": paciente.id,
        "valor": valor_calculado,
        "data_hora": data_hora_final,
        "sessoes_pagas": sessoes,
        "pagador": paciente.nome,
        "status": "Pago",
        "id_transacao": "MANUAL",
        "usuario_id": usuario_id
    }

    pagamentos_repository.criar_pagamento(db, dados_pagamento)
    return {
        "status": "sucesso", 
        "paciente_id": paciente.id,
        "valor": valor_calculado,
        "sessoes_pagas": sessoes
    }

def processar_pagamento(db: Session, pg: schemas.PagamentoCreate, usuario_id: int):
    id_final = pg.paciente_id

    if not id_final and pg.novo_paciente_nome:
        data_inicio = pg.data_inicio_manual or datetime.now().strftime("%Y-%m-%d")
        valor_sessao = pg.valor_sessao_manual if pg.valor_sessao_manual is not None else pg.valor
        dados_novo_paciente = {
            "nome": pg.novo_paciente_nome,
            "valor_sessao": pg.valor_sessao_manual,
            "data_inicio": pg.data_inicio_manual,
            "valor_sessao": valor_sessao,
            "data_inicio": data_inicio,
            "usuario_id": usuario_id,
            "status": "Ativo"
        }
        novo_paciente = pagamentos_repository.criar_paciente_via_pagamento(db, dados_novo_paciente)
        id_final = novo_paciente.id

    data_hora_final = pg.data_hora if pg.data_hora else datetime.now().strftime("%d/%m/%Y %H:%M")

    dados_pagamento = {
        "paciente_id": id_final,
        "valor": pg.valor,
        "data_hora": pg.data_hora,
        "sessoes_pagas": pg.sessoes_pagas,
        "data_hora": data_hora_final,
        "sessoes_pagas": pg.sessoes_pagas if pg.sessoes_pagas > 0 else 1,
        "pagador": pg.pagador,
        "status": "Pago",
        "id_transacao": pg.id_transacao or "MANUAL",
        "usuario_id": usuario_id
    }
    
    pagamentos_repository.criar_pagamento(db, dados_pagamento)
    return {"status": "sucesso", "paciente_id": id_final}

def remover_pagamento(db: Session, pagamento_id: int, usuario_id: int):
    pg = pagamentos_repository.buscar_por_id(db, pagamento_id, usuario_id)
    if not pg:
        raise HTTPException(status_code=404, detail="Lançamento não encontrado")
    
    pagamentos_repository.deletar(db, pg)
    return {"status": "excluído"}

