from decimal import Decimal
from app import models, schemas
from app.repositories import importacao_repository

def test_api_editar_item_pendente_sucesso(client, db_session, test_user):
    lote = importacao_repository.criar_lote(db_session, test_user.id)
    item = importacao_repository.criar_item(db_session, lote.id, {
        "nome_arquivo": "recibo.pdf",
        "content_type": "application/pdf",
        "pagador": "Nome Incorreto",
        "valor": Decimal("100.00"),
        "status": "PENDENTE_REVISAO"
    })

    paciente = models.Paciente(
        nome="Mariana Lima",
        valor_sessao=150.0,
        status="Ativo",
        data_inicio="2026-09-01",
        usuario_id=test_user.id
    )
    db_session.add(paciente)
    db_session.commit()

    # Edita o item
    patch_resp = client.patch(
        f"/upload-pix/lotes/{lote.id}/itens/{item.id}",
        json={
            "pagador": "Mariana Lima",
            "valor": 150.0,
            "paciente_id": paciente.id,
            "sessoes_pagas": 1
        }
    )

    assert patch_resp.status_code == 200
    data = patch_resp.json()
    assert data["pagador"] == "Mariana Lima"
    assert Decimal(str(data["valor"])) == Decimal("150.00")
    assert data["paciente_id"] == paciente.id

def test_api_rejeitar_item(client, db_session, test_user):
    lote = importacao_repository.criar_lote(db_session, test_user.id)
    item = importacao_repository.criar_item(db_session, lote.id, {
        "nome_arquivo": "recibo_duplicado.pdf",
        "content_type": "application/pdf",
        "status": "PENDENTE_REVISAO"
    })

    resp = client.post(
        f"/upload-pix/lotes/{lote.id}/itens/{item.id}/rejeitar",
        json={"motivo": "Comprovante duplicado"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "REJEITADO"
