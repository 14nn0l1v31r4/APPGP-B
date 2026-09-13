from app import models

def test_api_post_pagamento_rapido_sucesso(client, db_session, test_user):
    # Setup paciente
    paciente = models.Paciente(
        nome="Mariana Lima",
        valor_sessao=130.0,
        status="Ativo",
        data_inicio="2026-09-01",
        usuario_id=test_user.id
    )
    db_session.add(paciente)
    db_session.commit()
    db_session.refresh(paciente)

    response = client.post(
        "/pagamentos/rapido",
        json={"paciente_id": paciente.id, "sessoes_pagas": 2}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "sucesso"
    assert data["paciente_id"] == paciente.id
    assert data["valor"] == 260.0
    assert data["sessoes_pagas"] == 2

    # Verifica se refletiu no resumo do paciente
    resumo_resp = client.get(f"/pacientes/{paciente.id}/resumo")
    assert resumo_resp.status_code == 200
    resumo_data = resumo_resp.json()
    assert resumo_data["total_sessoes_pagas"] == 2
    assert resumo_data["total_valor_pago"] == 260.0

def test_api_post_pagamento_rapido_paciente_inexistente(client):
    response = client.post(
        "/pagamentos/rapido",
        json={"paciente_id": 99999, "sessoes_pagas": 1}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Paciente não encontrado"

def test_api_post_pagamento_manual_com_novo_paciente(client, db_session, test_user):
    response = client.post(
        "/pagamentos/",
        json={
            "pagador": "Roberto Carlos",
            "valor": 150.0,
            "data_hora": "13/09/2026 15:30",
            "sessoes_pagas": 1,
            "novo_paciente_nome": "Roberto Carlos",
            "valor_sessao_manual": 150.0,
            "data_inicio_manual": "2026-09-01"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "sucesso"
    assert data["paciente_id"] is not None

    # Verifica lista de pacientes
    pacientes_resp = client.get("/pacientes/")
    assert pacientes_resp.status_code == 200
    nomes = [p["nome"] for p in pacientes_resp.json()]
    assert "Roberto Carlos" in nomes
