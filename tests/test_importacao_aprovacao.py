from decimal import Decimal
from app import models
from app.repositories import importacao_repository

def test_aprovar_item_individual_cria_pagamento(client, db_session, test_user):
    paciente = models.Paciente(
        nome="Mariana Lima",
        valor_sessao=160.0,
        status="Ativo",
        data_inicio="2026-09-01",
        usuario_id=test_user.id
    )
    db_session.add(paciente)
    db_session.commit()

    lote = importacao_repository.criar_lote(db_session, test_user.id)
    item = importacao_repository.criar_item(db_session, lote.id, {
        "nome_arquivo": "recibo.pdf",
        "content_type": "application/pdf",
        "pagador": "Mariana Lima",
        "valor": Decimal("160.00"),
        "data_hora": "13/09/2026 14:00",
        "paciente_id": paciente.id,
        "sessoes_pagas": 1,
        "id_transacao": "E12345678901234567890123456789012",
        "status": "PENDENTE_REVISAO"
    })

    # Aprova o item
    resp = client.post(f"/upload-pix/lotes/{lote.id}/itens/{item.id}/aprovar")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "APROVADO"
    assert data["pagamento_id"] is not None

    # Verifica se pagamento foi criado no banco
    pagamento = db_session.query(models.Pagamento).filter(
        models.Pagamento.id == data["pagamento_id"]
    ).first()
    assert pagamento is not None
    assert pagamento.valor == Decimal("160.00")
    assert pagamento.paciente_id == paciente.id
    assert pagamento.id_transacao == "E12345678901234567890123456789012"
    assert pagamento.idempotencia_chave == f"lote-{lote.id}-item-{item.id}"

def test_aprovar_item_repetido_e_idempotente(client, db_session, test_user):
    paciente = models.Paciente(
        nome="Mariana Lima",
        valor_sessao=160.0,
        status="Ativo",
        data_inicio="2026-09-01",
        usuario_id=test_user.id
    )
    db_session.add(paciente)
    db_session.commit()

    lote = importacao_repository.criar_lote(db_session, test_user.id)
    item = importacao_repository.criar_item(db_session, lote.id, {
        "nome_arquivo": "recibo.pdf",
        "content_type": "application/pdf",
        "pagador": "Mariana Lima",
        "valor": Decimal("160.00"),
        "data_hora": "13/09/2026 14:00",
        "paciente_id": paciente.id,
        "sessoes_pagas": 1,
        "status": "PENDENTE_REVISAO"
    })

    # Primeira aprovação
    resp1 = client.post(f"/upload-pix/lotes/{lote.id}/itens/{item.id}/aprovar")
    assert resp1.status_code == 200
    pag_id_1 = resp1.json()["pagamento_id"]

    # Segunda aprovação (repetida)
    resp2 = client.post(f"/upload-pix/lotes/{lote.id}/itens/{item.id}/aprovar")
    assert resp2.status_code == 200
    pag_id_2 = resp2.json()["pagamento_id"]

    assert pag_id_1 == pag_id_2

    # Verifica que não duplicou pagamentos no banco
    total_pagamentos = db_session.query(models.Pagamento).filter(
        models.Pagamento.idempotencia_chave == f"lote-{lote.id}-item-{item.id}"
    ).count()
    assert total_pagamentos == 1

