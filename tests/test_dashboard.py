from datetime import datetime
from zoneinfo import ZoneInfo
from unittest.mock import patch
from app.services import dashboard_service
from app import models

def test_dashboard_sem_parametro_mes_nao_lanca_index_error(db_session, test_user):
    # Simula o mês de Dezembro (mês 12)
    with patch("app.services.dashboard_service.datetime") as mock_dt:
        mock_dt.now.return_value = datetime(2026, 12, 15)
        mock_dt.strptime = datetime.strptime
        
        relatorio = dashboard_service.gerar_relatorio_dashboard(
            db=db_session,
            mes_nome=None,
            usuario_id=test_user.id
        )
        
        assert "estatisticas" in relatorio
        assert relatorio["estatisticas"]["recebido"] == "0,00"

def test_dashboard_mes_atual_corresponde_ao_mes_correto(db_session, test_user):
    # Simula Setembro (mês 9 -> index 8 -> Setembro)
    with patch("app.services.dashboard_service.datetime") as mock_dt:
        mock_dt.now.return_value = datetime(2026, 9, 13)
        mock_dt.strptime = datetime.strptime
        
        # Adiciona um pagamento no mês 09
        pg = models.Pagamento(
            pagador="Paciente Teste",
            valor=250.0,
            data_hora=datetime(2026, 9, 10, 14, tzinfo=ZoneInfo("America/Sao_Paulo")),
            sessoes_pagas=2,
            id_transacao=None,
            usuario_id=test_user.id
        )
        db_session.add(pg)
        db_session.commit()
        
        relatorio = dashboard_service.gerar_relatorio_dashboard(
            db=db_session,
            mes_nome=None, # Deve buscar automaticamente Setembro (09)
            usuario_id=test_user.id
        )
        
        assert relatorio["estatisticas"]["recebido"] == "250,00"
        assert relatorio["estatisticas"]["sessoesPagas"] == 2

def test_dashboard_encontra_pagamento_em_formato_iso(db_session, test_user):
    pg = models.Pagamento(
        pagador="Paciente ISO",
        valor=90.0,
        data_hora=datetime(2026, 9, 13, 14, tzinfo=ZoneInfo("America/Sao_Paulo")),
        sessoes_pagas=1,
        usuario_id=test_user.id
    )
    db_session.add(pg)
    db_session.commit()

    relatorio = dashboard_service.gerar_relatorio_dashboard(
        db=db_session,
        mes_nome="Setembro",
        usuario_id=test_user.id
    )

    assert relatorio["estatisticas"]["recebido"] == "90,00"
