import pytest
from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import HTTPException
from app.services import pagamentos_service
from app import schemas, models


TEST_DATE = datetime(2026, 9, 13, 10, 0, tzinfo=ZoneInfo("America/Sao_Paulo"))

def test_pagamento_rapido_calcula_valor_automatico(db_session, test_user):
    # Cria paciente no banco
    paciente = models.Paciente(
        nome="Lucas Fernandes",
        valor_sessao=150.0,
        tipo_contrato="Por Sessão",
        status="Ativo",
        data_inicio="2026-09-01",
        usuario_id=test_user.id
    )
    db_session.add(paciente)
    db_session.commit()
    db_session.refresh(paciente)

    dados_rapido = schemas.PagamentoRapidoCreate(
        paciente_id=paciente.id,
        sessoes_pagas=2
    )

    resultado = pagamentos_service.registrar_pagamento_rapido(
        db=db_session,
        dados=dados_rapido,
        usuario_id=test_user.id
    )

    assert resultado["status"] == "sucesso"
    assert resultado["paciente_id"] == paciente.id

    # Verifica no banco
    pg = db_session.query(models.Pagamento).filter(
        models.Pagamento.paciente_id == paciente.id
    ).first()
    assert pg is not None
    assert pg.valor == 300.0
    assert pg.sessoes_pagas == 2
    assert pg.pagador == "Lucas Fernandes"
    assert pg.id_transacao is None

def test_pagamento_rapido_permite_dois_lancamentos_manuais(db_session, test_user):
    paciente = models.Paciente(
        nome="Paciente Repetido",
        valor_sessao=100.0,
        status="Ativo",
        data_inicio="2026-09-01",
        usuario_id=test_user.id
    )
    db_session.add(paciente)
    db_session.commit()

    dados = schemas.PagamentoRapidoCreate(paciente_id=paciente.id)
    pagamentos_service.registrar_pagamento_rapido(db_session, dados, test_user.id)
    pagamentos_service.registrar_pagamento_rapido(db_session, dados, test_user.id)

    pagamentos = db_session.query(models.Pagamento).filter(
        models.Pagamento.paciente_id == paciente.id
    ).all()
    assert len(pagamentos) == 2
    assert all(pg.id_transacao is None for pg in pagamentos)

def test_pagamento_rapido_paciente_outro_usuario_bloqueado(db_session, test_user, test_user_2):
    # Paciente pertence ao test_user_2
    paciente_outro = models.Paciente(
        nome="Paciente Privado",
        valor_sessao=200.0,
        status="Ativo",
        data_inicio="2026-09-01",
        usuario_id=test_user_2.id
    )
    db_session.add(paciente_outro)
    db_session.commit()

    dados_rapido = schemas.PagamentoRapidoCreate(
        paciente_id=paciente_outro.id,
        sessoes_pagas=1
    )

    # test_user tenta dar baixa
    with pytest.raises(HTTPException) as exc_info:
        pagamentos_service.registrar_pagamento_rapido(
            db=db_session,
            dados=dados_rapido,
            usuario_id=test_user.id
        )
    assert exc_info.value.status_code == 404

def test_pagamento_com_criacao_novo_paciente(db_session, test_user):
    dados = schemas.PagamentoCreate(
        pagador="Camila Rocha",
        valor=180.0,
        data_hora=TEST_DATE,
        sessoes_pagas=1,
        paciente_id=None,
        novo_paciente_nome="Camila Rocha",
        valor_sessao_manual=180.0,
        data_inicio_manual="2026-09-01"
    )

    resultado = pagamentos_service.processar_pagamento(
        db=db_session,
        pg=dados,
        usuario_id=test_user.id
    )

    assert resultado["status"] == "sucesso"
    novo_id = resultado["paciente_id"]
    assert novo_id is not None

    # Verifica se paciente foi criado
    paciente_criado = db_session.query(models.Paciente).filter(models.Paciente.id == novo_id).first()
    assert paciente_criado is not None
    assert paciente_criado.nome == "Camila Rocha"
    assert paciente_criado.valor_sessao == 180.0
    assert paciente_criado.usuario_id == test_user.id

    # Verifica se pagamento foi vinculado
    pg = db_session.query(models.Pagamento).filter(models.Pagamento.paciente_id == novo_id).first()
    assert pg is not None
    assert pg.valor == 180.0
    assert pg.sessoes_pagas == 1

def test_pagamento_existente_de_outro_usuario_e_rejeitado(db_session, test_user, test_user_2):
    paciente = models.Paciente(
        nome="Paciente Protegido",
        valor_sessao=200.0,
        status="Ativo",
        data_inicio="2026-09-01",
        usuario_id=test_user_2.id
    )
    db_session.add(paciente)
    db_session.commit()

    dados = schemas.PagamentoCreate(
        pagador="Tentativa",
        valor=200.0,
        data_hora=TEST_DATE,
        paciente_id=paciente.id
    )

    with pytest.raises(HTTPException) as exc_info:
        pagamentos_service.processar_pagamento(db_session, dados, test_user.id)

    assert exc_info.value.status_code == 404
    assert db_session.query(models.Pagamento).filter(
        models.Pagamento.paciente_id == paciente.id
    ).count() == 0

def test_pagamento_com_falha_nao_deixa_paciente_orfao(db_session, test_user):
    existente = models.Pagamento(
        pagador="Existente",
        valor=100.0,
        data_hora=datetime(2026, 9, 13, 9, tzinfo=ZoneInfo("America/Sao_Paulo")),
        sessoes_pagas=1,
        id_transacao="PIX-EXISTENTE",
        usuario_id=test_user.id
    )
    db_session.add(existente)
    db_session.commit()

    dados = schemas.PagamentoCreate(
        pagador="Novo Paciente",
        valor=150.0,
        data_hora=TEST_DATE,
        paciente_id=None,
        id_transacao="PIX-EXISTENTE",
        novo_paciente_nome="Paciente Órfão",
        valor_sessao_manual=150.0,
        data_inicio_manual="2026-09-01"
    )

    with pytest.raises(HTTPException) as exc_info:
        pagamentos_service.processar_pagamento(db_session, dados, test_user.id)

    assert exc_info.value.status_code == 409
    assert db_session.query(models.Paciente).filter(
        models.Paciente.nome == "Paciente Órfão"
    ).count() == 0

def test_pagamento_rapido_com_chave_e_idempotente(db_session, test_user):
    paciente = models.Paciente(
        nome="Paciente Idempotente",
        valor_sessao=110.0,
        status="Ativo",
        data_inicio="2026-09-01",
        usuario_id=test_user.id
    )
    db_session.add(paciente)
    db_session.commit()

    dados = schemas.PagamentoRapidoCreate(
        paciente_id=paciente.id,
        idempotencia_chave="clique-001"
    )
    primeiro = pagamentos_service.registrar_pagamento_rapido(db_session, dados, test_user.id)
    segundo = pagamentos_service.registrar_pagamento_rapido(db_session, dados, test_user.id)

    assert primeiro["pagamento_id"] == segundo["pagamento_id"]
    assert db_session.query(models.Pagamento).filter(
        models.Pagamento.paciente_id == paciente.id
    ).count() == 1
