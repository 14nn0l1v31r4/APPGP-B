import pytest
from decimal import Decimal
from pydantic import ValidationError
from app import schemas

def test_schemas_item_update_validacoes():
    # Sucesso com valores válidos
    update_valido = schemas.ItemImportacaoUpdate(
        pagador="Carlos Silva",
        valor=Decimal("150.00"),
        sessoes_pagas=2,
        paciente_id=10
    )
    assert update_valido.valor == Decimal("150.00")
    assert update_valido.sessoes_pagas == 2

    # Falha com valor <= 0
    with pytest.raises(ValidationError):
        schemas.ItemImportacaoUpdate(valor=Decimal("0.00"))

    with pytest.raises(ValidationError):
        schemas.ItemImportacaoUpdate(valor=Decimal("-10.00"))

    # Falha com sessoes_pagas < 1
    with pytest.raises(ValidationError):
        schemas.ItemImportacaoUpdate(sessoes_pagas=0)

def test_schemas_aprovar_selecionados_validacao():
    # Sucesso com lista com itens
    req = schemas.AprovarSelecionadosRequest(item_ids=[1, 2, 3])
    assert req.item_ids == [1, 2, 3]

    # Falha com lista vazia
    with pytest.raises(ValidationError):
        schemas.AprovarSelecionadosRequest(item_ids=[])

