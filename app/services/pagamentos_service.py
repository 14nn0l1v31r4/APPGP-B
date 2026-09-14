from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import schemas
from app.repositories import pacientes_repository, pagamentos_repository
from app.utils.dates import normalizar_data_hora


def _data_hora_validada(valor):
    try:
        return normalizar_data_hora(valor)
    except ValueError as erro:
        raise HTTPException(
            status_code=422,
            detail="Formato de data/hora inválido"
        ) from erro


def _resultado_pagamento(pagamento, paciente_id: int, valor, sessoes: int):
    return {
        "status": "sucesso",
        "pagamento_id": pagamento.id,
        "paciente_id": paciente_id,
        "valor": valor,
        "sessoes_pagas": sessoes
    }


def _resolver_conflito(
    db: Session,
    erro: IntegrityError,
    idempotencia_chave: str | None,
    usuario_id: int
):
    db.rollback()
    if idempotencia_chave:
        existente = pagamentos_repository.buscar_por_idempotencia(
            db, idempotencia_chave, usuario_id
        )
        if existente:
            return existente
    raise HTTPException(status_code=409, detail="Pagamento duplicado") from erro


def registrar_pagamento_rapido(
    db: Session,
    dados: schemas.PagamentoRapidoCreate,
    usuario_id: int
):
    paciente = pacientes_repository.buscar_por_id(db, dados.paciente_id, usuario_id)
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente não encontrado")

    if dados.idempotencia_chave:
        existente = pagamentos_repository.buscar_por_idempotencia(
            db, dados.idempotencia_chave, usuario_id
        )
        if existente:
            return _resultado_pagamento(
                existente,
                existente.paciente_id,
                existente.valor,
                existente.sessoes_pagas
            )

    sessoes = dados.sessoes_pagas
    valor_calculado = paciente.valor_sessao * sessoes
    data_hora_final = _data_hora_validada(
        dados.data_hora or datetime.now()
    )
    dados_pagamento = {
        "paciente_id": paciente.id,
        "valor": valor_calculado,
        "data_hora": data_hora_final,
        "sessoes_pagas": sessoes,
        "pagador": paciente.nome,
        "status": "Pago",
        "id_transacao": None,
        "idempotencia_chave": dados.idempotencia_chave,
        "usuario_id": usuario_id
    }

    try:
        pagamento = pagamentos_repository.criar_pagamento(db, dados_pagamento)
        db.commit()
    except IntegrityError as erro:
        pagamento = _resolver_conflito(
            db, erro, dados.idempotencia_chave, usuario_id
        )

    return _resultado_pagamento(
        pagamento, paciente.id, pagamento.valor, pagamento.sessoes_pagas
    )


def processar_pagamento(db: Session, pg: schemas.PagamentoCreate, usuario_id: int):
    if pg.idempotencia_chave:
        existente = pagamentos_repository.buscar_por_idempotencia(
            db, pg.idempotencia_chave, usuario_id
        )
        if existente:
            return {
                "status": "sucesso",
                "pagamento_id": existente.id,
                "paciente_id": existente.paciente_id
            }

    id_final = pg.paciente_id
    if id_final:
        paciente = pacientes_repository.buscar_por_id(db, id_final, usuario_id)
        if not paciente:
            raise HTTPException(status_code=404, detail="Paciente não encontrado")

    if not id_final and pg.novo_paciente_nome:
        data_inicio = pg.data_inicio_manual or datetime.now().strftime("%Y-%m-%d")
        valor_sessao = (
            pg.valor_sessao_manual
            if pg.valor_sessao_manual is not None
            else pg.valor
        )
        dados_novo_paciente = {
            "nome": pg.novo_paciente_nome.strip(),
            "valor_sessao": valor_sessao,
            "data_inicio": data_inicio,
            "usuario_id": usuario_id,
            "status": "Ativo"
        }
        novo_paciente = pagamentos_repository.criar_paciente_via_pagamento(
            db, dados_novo_paciente
        )
        id_final = novo_paciente.id

    data_hora_final = _data_hora_validada(pg.data_hora)
    dados_pagamento = {
        "paciente_id": id_final,
        "valor": pg.valor,
        "data_hora": data_hora_final,
        "sessoes_pagas": pg.sessoes_pagas,
        "pagador": pg.pagador.strip(),
        "status": "Pago",
        "id_transacao": pg.id_transacao,
        "idempotencia_chave": pg.idempotencia_chave,
        "usuario_id": usuario_id
    }

    try:
        pagamento = pagamentos_repository.criar_pagamento(db, dados_pagamento)
        db.commit()
    except IntegrityError as erro:
        conflito = _resolver_conflito(
            db, erro, pg.idempotencia_chave, usuario_id
        )
        return {
            "status": "sucesso",
            "pagamento_id": conflito.id,
            "paciente_id": conflito.paciente_id
        }

    return {
        "status": "sucesso",
        "pagamento_id": pagamento.id,
        "paciente_id": id_final
    }


def remover_pagamento(db: Session, pagamento_id: int, usuario_id: int):
    pg = pagamentos_repository.buscar_por_id(db, pagamento_id, usuario_id)
    if not pg:
        raise HTTPException(status_code=404, detail="Lançamento não encontrado")

    pagamentos_repository.deletar(db, pg)
    return {"status": "excluído"}

