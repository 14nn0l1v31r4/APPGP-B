from fastapi import HTTPException
from sqlalchemy.orm import Session
from app import schemas
from app.repositories import pagamentos_repository

def processar_pagamento(db: Session, pg: schemas.PagamentoCreate, usuario_id: int):
    id_final = pg.paciente_id

    if not id_final and pg.novo_paciente_nome:
        dados_novo_paciente = {
            "nome": pg.novo_paciente_nome,
            "valor_sessao": pg.valor_sessao_manual,
            "data_inicio": pg.data_inicio_manual,
            "usuario_id": usuario_id,
            "status": "Ativo"
        }
        novo_paciente = pagamentos_repository.criar_paciente_via_pagamento(db, dados_novo_paciente)
        id_final = novo_paciente.id

    dados_pagamento = {
        "paciente_id": id_final,
        "valor": pg.valor,
        "data_hora": pg.data_hora,
        "sessoes_pagas": pg.sessoes_pagas,
        "pagador": pg.pagador,
        "status": "Pago",
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