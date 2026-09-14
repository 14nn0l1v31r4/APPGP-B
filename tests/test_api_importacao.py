from unittest.mock import patch
import io
from app import models

def test_api_criar_lote_e_consultar(client, db_session, test_user):
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

    with patch("app.services.upload_service.pdfplumber.open") as mock_pdf:
        mock_page = mock_pdf.return_value.__enter__.return_value.pages
        mock_page.__iter__.return_value = [type("MockPage", (), {"extract_text": lambda self: texto_valido})()]

        files = [
            ("files", ("recibo1.pdf", b"%PDF-1", "application/pdf")),
            ("files", ("recibo2.pdf", b"%PDF-2", "application/pdf"))
        ]

        response = client.post("/upload-pix/lotes", files=files)
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "CONCLUIDO"
        assert data["total"] == 2
        assert data["pendentes"] == 2
        lote_id = data["id"]

        # Consulta lote via GET
        get_resp = client.get(f"/upload-pix/lotes/{lote_id}")
        assert get_resp.status_code == 200
        get_data = get_resp.json()
        assert get_data["id"] == lote_id
        assert len(get_data["itens"]) == 2

def test_api_consultar_lote_inexistente(client):
    response = client.get("/upload-pix/lotes/99999")
    assert response.status_code == 404

