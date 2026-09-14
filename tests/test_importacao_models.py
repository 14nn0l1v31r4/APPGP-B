from datetime import datetime
from decimal import Decimal
from app import models

def test_criar_lote_e_itens_model(db_session, test_user):
    lote = models.LoteImportacao(
        usuario_id=test_user.id,
        status="PROCESSANDO"
    )
    db_session.add(lote)
    db_session.commit()
    db_session.refresh(lote)

    assert lote.id is not None
    assert lote.usuario_id == test_user.id
    assert lote.status == "PROCESSANDO"

    item1 = models.ItemImportacao(
        lote_id=lote.id,
        nome_arquivo="recibo1.pdf",
        content_type="application/pdf",
        hash_sha256="abc123hash",
        banco="Nubank",
        pagador="Mariana Lima",
        valor=Decimal("150.00"),
        data_hora="13/09/2026",
        status="PENDENTE_REVISAO",
        sessoes_pagas=1,
        dados_extraidos={"chave": "valor"}
    )
    item2 = models.ItemImportacao(
        lote_id=lote.id,
        nome_arquivo="recibo2.png",
        content_type="image/png",
        status="ERRO",
        etapa_erro="leitura",
        mensagem_erro="Imagem ilegível"
    )

    db_session.add_all([item1, item2])
    db_session.commit()

    db_session.refresh(lote)
    assert len(lote.itens) == 2
    assert lote.itens[0].nome_arquivo == "recibo1.pdf"
    assert lote.itens[0].valor == Decimal("150.00")
    assert lote.itens[1].status == "ERRO"

