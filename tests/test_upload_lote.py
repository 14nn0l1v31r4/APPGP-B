import io
import pytest
from unittest.mock import patch
from app.services import upload_service
from app import models

def test_extrair_dados_comprovante_reutilizavel(db_session, test_user):
    # Setup paciente
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
    Comprovante de transferência Pix
    Valor R$ 160,00
    13 SET 2026
    Origem:
    Nome: Mariana Lima
    Instituição: NU PAGAMENTOS S.A.
    ID da transação: E12345678901234567890123456789012
    """

    with patch("pdfplumber.open") as mock_pdf:
        mock_page = mock_pdf.return_value.__enter__.return_value.pages
        mock_page.__iter__.return_value = [type("MockPage", (), {"extract_text": lambda self: texto_falso})()]

        resultado = upload_service.extrair_dados_comprovante(
            db=db_session,
            content=b"%PDF-mock",
            filename="comprovante.pdf",
            content_type="application/pdf",
            valor_sessao_manual=None,
            usuario_id=test_user.id
        )

        assert resultado["pagador"] == "MARIANA LIMA"
        assert resultado["valor"] == "160,00"
        assert resultado["data"] == "13/09/2026"
        assert resultado["banco"] == "Nubank"
        assert resultado["id_transacao"] == "E12345678901234567890123456789012"
        assert resultado["paciente_id"] == paciente.id
        assert resultado["match_status"] == "Vínculo Automático"
        assert resultado["sessoes_pagas"] == 1

def test_extrair_dados_comprovante_arquivo_invalido():
    # Teste de arquivo corrompido ou formato não suportado
    with pytest.raises(Exception):
        upload_service.extrair_dados_comprovante(
            db=None,
            content=b"arquivo_totalmente_invalido_e_corrompido",
            filename="foto.jpg",
            content_type="image/jpeg",
            valor_sessao_manual=None,
            usuario_id=1
        )

