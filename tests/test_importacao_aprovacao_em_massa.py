from decimal import Decimal
from app import models
from app.repositories import importacao_repository

def test_aprovar_selecionados_com_sucesso_parcial_e_isolamento(client, db_session, test_user):
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
    
    # Item 1: Válido
    item1 = importacao_repository.criar_item(db_session, lote.id, {
        "nome_arquivo": "recibo1.pdf",
        "content_type": "application/pdf",
        "pagador": "Mariana Lima",
        "valor": Decimal("160.00"),
        "paciente_id": paciente.id,
        "status": "PENDENTE_REVISAO"
    })

    # Item 2: Inválido (sem valor definido)
    item2 = importacao_repository.criar_item(db_session, lote.id, {
        "nome_arquivo": "recibo2.pdf",
        "content_type": "application/pdf",
        "pagador": "Mariana Lima",
        "valor": None, # Vai falhar na aprovação
        "paciente_id": paciente.id,
        "status": "PENDENTE_REVISAO"
    })

    # Item 3: Válido
    item3 = importacao_repository.criar_item(db_session, lote.id, {
        "nome_arquivo": "recibo3.pdf",
        "content_type": "application/pdf",
        "pagador": "Mariana Lima",
        "valor": Decimal("320.00"),
        "sessoes_pagas": 2,
        "paciente_id": paciente.id,
        "status": "PENDENTE_REVISAO"
    })

    resp = client.post(
        f"/upload-pix/lotes/{lote.id}/aprovar-selecionados",
        json={"item_ids": [item1.id, item2.id, item3.id]}
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["lote_id"] == lote.id
    assert data["total"] == 3
    assert data["aprovados"] == 2
    assert data["erros"] == 1

    # Verifica itens
    status_map = {item["item_id"]: item["status"] for item in data["itens"]}
    assert status_map[item1.id] == "APROVADO"
    assert status_map[item2.id] == "ERRO"
    assert status_map[item3.id] == "APROVADO"

    # Pagamentos no banco: 2 criados
    pagamentos = db_session.query(models.Pagamento).filter(models.Pagamento.usuario_id == test_user.id).all()
    assert len(pagamentos) == 2

