import io
import pytest
from unittest.mock import patch
from app.services import importacao_service
from app import models

def test_criar_lote_processamento_com_falha_isolada(db_session, test_user):
    # Setup paciente
    paciente = models.Paciente(
        nome="Mariana Lima",
        valor_sessao=160.0,
        status="Ativo",
        data_inicio="2026-09-01",
        usuario_id=test_user.id
    )
    db_session.add(paciente)
    db_session.commit()

    texto_valido = """
    Comprovante Pix
    Valor R$ 160,00
    13 SET 2026
    Origem:
    Nome: Mariana Lima
    Instituição: NU PAGAMENTOS S.A.
    """

    arquivos = [
        (b"%PDF-valido-1", "recibo1.pdf", "application/pdf"),
        (b"corrompido", "invalido.jpg", "image/jpeg"),
        (b"%PDF-valido-3", "recibo3.pdf", "application/pdf")
    ]

    with patch("app.services.upload_service.pdfplumber.open") as mock_pdf:
        mock_page = mock_pdf.return_value.__enter__.return_value.pages
        mock_page.__iter__.return_value = [type("MockPage", (), {"extract_text": lambda self: texto_valido})()]

        resultado = importacao_service.criar_lote_e_processar(
            db=db_session,
            arquivos=arquivos,
            valor_sessao_manual=None,
            usuario_id=test_user.id
        )

        assert resultado["status"] == "CONCLUIDO"
        assert resultado["total"] == 3
        assert resultado["pendentes"] == 2
        assert resultado["erros"] == 1
        assert len(resultado["itens"]) == 3

        # Item 1: Pendente
        assert resultado["itens"][0].status == "PENDENTE_REVISAO"
        assert resultado["itens"][0].pagador == "MARIANA LIMA"

        # Item 2: Erro isolado (não derrubou o lote)
        assert resultado["itens"][1].status == "ERRO"
        assert resultado["itens"][1].etapa_erro == "leitura"

        # Item 3: Pendente
        assert resultado["itens"][2].status == "PENDENTE_REVISAO"

