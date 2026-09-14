from decimal import Decimal
from app.repositories import importacao_repository
from app import models

def test_criar_e_buscar_lote_com_isolamento_usuario(db_session, test_user, test_user_2):
    # Cria lote para test_user
    lote = importacao_repository.criar_lote(db_session, test_user.id)
    assert lote.id is not None
    assert lote.usuario_id == test_user.id

    # Busca com test_user -> Sucesso
    buscado = importacao_repository.buscar_lote(db_session, lote.id, test_user.id)
    assert buscado is not None
    assert buscado.id == lote.id

    # Busca com test_user_2 -> Deve retornar None (isolamento)
    buscado_outro = importacao_repository.buscar_lote(db_session, lote.id, test_user_2.id)
    assert buscado_outro is None

def test_criar_e_buscar_item_com_isolamento(db_session, test_user, test_user_2):
    lote = importacao_repository.criar_lote(db_session, test_user.id)
    dados_item = {
        "nome_arquivo": "recibo.pdf",
        "content_type": "application/pdf",
        "pagador": "Mariana Lima",
        "valor": Decimal("100.00"),
        "status": "PENDENTE_REVISAO"
    }
    item = importacao_repository.criar_item(db_session, lote.id, dados_item)
    assert item.id is not None
    assert item.lote_id == lote.id

    # Busca item como test_user -> Sucesso
    item_buscado = importacao_repository.buscar_item(db_session, lote.id, item.id, test_user.id)
    assert item_buscado is not None
    assert item_buscado.pagador == "Mariana Lima"

    # Busca item como test_user_2 -> Deve retornar None
    item_outro = importacao_repository.buscar_item(db_session, lote.id, item.id, test_user_2.id)
    assert item_outro is None

