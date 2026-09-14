from unittest.mock import patch
from app.utils.parsers import extrair_os_dados
from app.services import upload_service
from app import models

def test_parser_nubank():
    texto_nubank = """
    Comprovante de transferência Pix
    Valor R$ 160,00
    13 SET 2026
    Origem:
    Nome: Mariana Lima
    Instituição: NU PAGAMENTOS S.A.
    ID da transação: E12345678901234567890123456789012
    """
    dados = extrair_os_dados(texto_nubank)
    assert dados["banco"] == "Nubank"
    assert dados["valor"] == "160,00"
    assert dados["pagador"] == "MARIANA LIMA"
    assert dados["data"] == "13/09/2026"
    assert dados["id_transacao"] == "E12345678901234567890123456789012"

def test_upload_service_vinculo_automatico(db_session, test_user):
    # Cria paciente no banco
    paciente = models.Paciente(
        nome="MARIANA LIMA",
        valor_sessao=160.0,
        status="Ativo",
        data_inicio="2026-09-01",
        usuario_id=test_user.id
    )
    db_session.add(paciente)
    db_session.commit()

    texto_falso = """
    Comprovante Pix
    Valor R$ 320,00
    13 SET 2026
    Origem:
    Nome: Mariana Lima
    Instituição: NU PAGAMENTOS S.A.
    """

    with patch("pdfplumber.open") as mock_pdf:
        # Mock de extração de texto
        mock_page = mock_pdf.return_value.__enter__.return_value.pages
        mock_page.__iter__.return_value = [type("MockPage", (), {"extract_text": lambda self: texto_falso})()]

        resultado = upload_service.processar_arquivo_pix(
            db=db_session,
            content=b"%PDF-mock",
            filename="comprovante.pdf",
            content_type="application/pdf",
            valor_sessao_manual=None,
            usuario_id=test_user.id
        )

        assert resultado["match_status"] == "Vínculo Automático"
        assert resultado["paciente_id"] == paciente.id
        assert resultado["sessoes_pagas"] == 2
        assert resultado["valor"] == "320,00"

