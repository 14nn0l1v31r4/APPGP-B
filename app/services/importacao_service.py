import hashlib
from datetime import datetime
from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.repositories import importacao_repository
from app.services import upload_service
from app import models, schemas

MAX_ARQUIVOS_POR_LOTE = 20
MAX_TAMANHO_ARQUIVO_BYTES = 10 * 1024 * 1024  # 10 MB

def _montar_resumo_lote(lote: models.LoteImportacao, itens: list[models.ItemImportacao]) -> dict:
    total = len(itens)
    pendentes = sum(1 for i in itens if i.status == "PENDENTE_REVISAO")
    aprovados = sum(1 for i in itens if i.status == "APROVADO")
    rejeitados = sum(1 for i in itens if i.status == "REJEITADO")
    erros = sum(1 for i in itens if i.status == "ERRO")

    return {
        "id": lote.id,
        "usuario_id": lote.usuario_id,
        "status": lote.status,
        "total": total,
        "pendentes": pendentes,
        "aprovados": aprovados,
        "rejeitados": rejeitados,
        "erros": erros,
        "itens": itens
    }

def criar_lote_e_processar(
    db: Session, 
    arquivos: list[tuple[bytes, str, str]], 
    valor_sessao_manual: float, 
    usuario_id: int
) -> dict:
    if not arquivos:
        raise HTTPException(status_code=400, detail="Nenhum arquivo enviado para importação.")

    if len(arquivos) > MAX_ARQUIVOS_POR_LOTE:
        raise HTTPException(
            status_code=413, 
            detail=f"Limite de {MAX_ARQUIVOS_POR_LOTE} arquivos por lote excedido."
        )

    for content, filename, _ in arquivos:
        if len(content) > MAX_TAMANHO_ARQUIVO_BYTES:
            raise HTTPException(
                status_code=413, 
                detail=f"Arquivo '{filename}' excede o tamanho máximo de 10 MB."
            )

    lote = importacao_repository.criar_lote(db, usuario_id)
    itens_criados = []

    for content, filename, content_type in arquivos:
        sha256_hash = hashlib.sha256(content).hexdigest()

        # Cria item em estado PROCESSANDO
        dados_iniciais = {
            "nome_arquivo": filename,
            "content_type": content_type,
            "hash_sha256": sha256_hash,
            "status": "PROCESSANDO"
        }
        item = importacao_repository.criar_item(db, lote.id, dados_iniciais)

        try:
            dados_ocr = upload_service.extrair_dados_comprovante(
                db=db,
                content=content,
                filename=filename,
                content_type=content_type,
                valor_sessao_manual=valor_sessao_manual,
                usuario_id=usuario_id
            )

            valor_str = dados_ocr.get("valor", "0").replace(".", "").replace(",", ".")
            try:
                valor_decimal = Decimal(valor_str) if valor_str and float(valor_str) > 0 else None
            except Exception:
                valor_decimal = None

            sugestao_sessao = dados_ocr.get("valor_sessao_sugerido")
            sugestao_decimal = Decimal(str(sugestao_sessao)) if sugestao_sessao else None

            # Serialização segura para o campo JSON
            dados_extraidos_serializavel = {}
            for k, v in dados_ocr.items():
                if isinstance(v, Decimal):
                    dados_extraidos_serializavel[k] = float(v)
                else:
                    dados_extraidos_serializavel[k] = v

            item.banco = dados_ocr.get("banco")
            item.pagador = dados_ocr.get("pagador")
            item.valor = valor_decimal
            item.data_hora = dados_ocr.get("data")
            item.id_transacao = dados_ocr.get("id_transacao")
            item.paciente_id = dados_ocr.get("paciente_id")
            item.sessoes_pagas = dados_ocr.get("sessoes_pagas", 1)
            item.valor_sessao_sugerido = sugestao_decimal
            item.dados_extraidos = dados_extraidos_serializavel
            item.status = "PENDENTE_REVISAO"
            item.etapa_erro = None
            item.mensagem_erro = None

            importacao_repository.salvar(db, item)

        except Exception as err:
            # Isolamento total: erro na leitura afeta apenas este item
            db.rollback()
            item.status = "ERRO"
            item.etapa_erro = "leitura"
            item.mensagem_erro = "Falha ao extrair dados do comprovante (arquivo ilegível ou corrompido)."
            importacao_repository.salvar(db, item)

        itens_criados.append(item)

    lote.status = "CONCLUIDO"
    importacao_repository.salvar(db, lote)

    return _montar_resumo_lote(lote, itens_criados)

def obter_lote(db: Session, lote_id: int, usuario_id: int) -> dict:
    lote = importacao_repository.buscar_lote(db, lote_id, usuario_id)
    if not lote:
        raise HTTPException(status_code=404, detail="Lote não encontrado.")

    itens = importacao_repository.listar_itens(db, lote.id, usuario_id)
    return _montar_resumo_lote(lote, itens)

def editar_item(
    db: Session, 
    lote_id: int, 
    item_id: int, 
    dados: schemas.ItemImportacaoUpdate, 
    usuario_id: int
) -> models.ItemImportacao:
    item = importacao_repository.buscar_item(db, lote_id, item_id, usuario_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item de importação não encontrado.")

    if item.status in ["APROVADO", "REJEITADO"]:
        raise HTTPException(
            status_code=409, 
            detail=f"Não é possível editar um item com status {item.status}."
        )

    if dados.paciente_id is not None:
        paciente = db.query(models.Paciente).filter(
            models.Paciente.id == dados.paciente_id,
            models.Paciente.usuario_id == usuario_id
        ).first()
        if not paciente:
            raise HTTPException(status_code=404, detail="Paciente informado não encontrado.")
        item.paciente_id = dados.paciente_id

    if dados.pagador is not None:
        item.pagador = dados.pagador
    if dados.valor is not None:
        item.valor = dados.valor
    if dados.data_hora is not None:
        item.data_hora = dados.data_hora
    if dados.sessoes_pagas is not None:
        item.sessoes_pagas = dados.sessoes_pagas
    if dados.id_transacao is not None:
        item.id_transacao = dados.id_transacao

    # Se estava com erro e foi editado, volta para pendente de revisão
    if item.status == "ERRO":
        item.status = "PENDENTE_REVISAO"
        item.etapa_erro = None
        item.mensagem_erro = None

    importacao_repository.salvar(db, item)
    return item

def rejeitar_item(
    db: Session, 
    lote_id: int, 
    item_id: int, 
    motivo: str, 
    usuario_id: int
) -> models.ItemImportacao:
    item = importacao_repository.buscar_item(db, lote_id, item_id, usuario_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item de importação não encontrado.")

    if item.status == "APROVADO":
        raise HTTPException(status_code=409, detail="Não é possível rejeitar um item já aprovado.")

    if item.status == "REJEITADO":
        return item

    item.status = "REJEITADO"
    if motivo:
        item.mensagem_erro = motivo

    importacao_repository.salvar(db, item)
    return item

def _normalizar_datetime(data_hora_raw) -> datetime:
    if isinstance(data_hora_raw, datetime):
        return data_hora_raw
    if isinstance(data_hora_raw, str):
        formatos = [
            "%d/%m/%Y %H:%M:%S",
            "%d/%m/%Y %H:%M",
            "%d/%m/%Y",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%d %H:%M:%S%z"
        ]
        for fmt in formatos:
            try:
                return datetime.strptime(data_hora_raw.strip(), fmt)
            except ValueError:
                continue
    return datetime.now()

def aprovar_item_logica(db: Session, item: models.ItemImportacao, usuario_id: int) -> models.ItemImportacao:
    if item.status == "APROVADO" and item.pagamento_id:
        return item

    if not item.valor or item.valor <= 0:
        raise HTTPException(status_code=422, detail="Item não possui valor válido para aprovação.")
    if not item.pagador:
        raise HTTPException(status_code=422, detail="Item não possui pagador definido.")

    chave_idempotencia = f"lote-{item.lote_id}-item-{item.id}"
    
    pag_existente = db.query(models.Pagamento).filter(
        models.Pagamento.idempotencia_chave == chave_idempotencia
    ).first()

    if pag_existente:
        item.pagamento_id = pag_existente.id
        item.status = "APROVADO"
        importacao_repository.salvar(db, item)
        return item

    data_hora_val = _normalizar_datetime(item.data_hora)

    dados_pagamento = {
        "paciente_id": item.paciente_id,
        "valor": item.valor,
        "data_hora": data_hora_val,
        "sessoes_pagas": item.sessoes_pagas or 1,
        "pagador": item.pagador,
        "status": "Pago",
        "id_transacao": item.id_transacao,
        "idempotencia_chave": chave_idempotencia,
        "usuario_id": usuario_id
    }

    novo_pagamento = models.Pagamento(**dados_pagamento)
    db.add(novo_pagamento)
    db.commit()
    db.refresh(novo_pagamento)

    item.pagamento_id = novo_pagamento.id
    item.status = "APROVADO"
    item.etapa_erro = None
    item.mensagem_erro = None
    importacao_repository.salvar(db, item)
    return item

def aprovar_item_individual(
    db: Session, 
    lote_id: int, 
    item_id: int, 
    usuario_id: int
) -> models.ItemImportacao:
    item = importacao_repository.buscar_item(db, lote_id, item_id, usuario_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item de importação não encontrado.")

    return aprovar_item_logica(db, item, usuario_id)

def aprovar_selecionados(
    db: Session, 
    lote_id: int, 
    item_ids: list[int], 
    usuario_id: int
) -> dict:
    lote = importacao_repository.buscar_lote(db, lote_id, usuario_id)
    if not lote:
        raise HTTPException(status_code=404, detail="Lote não encontrado.")

    resultados = []
    aprovados = 0
    erros = 0

    for item_id in item_ids:
        item = importacao_repository.buscar_item(db, lote_id, item_id, usuario_id)
        if not item:
            resultados.append({
                "item_id": item_id,
                "status": "ERRO",
                "etapa_erro": "aprovacao",
                "mensagem": "Item não encontrado no lote."
            })
            erros += 1
            continue

        try:
            item_aprovado = aprovar_item_logica(db, item, usuario_id)
            resultados.append({
                "item_id": item_id,
                "status": "APROVADO",
                "pagamento_id": item_aprovado.pagamento_id
            })
            aprovados += 1
        except Exception as err:
            db.rollback()
            item.status = "ERRO"
            item.etapa_erro = "aprovacao"
            item.mensagem_erro = str(getattr(err, "detail", err))
            importacao_repository.salvar(db, item)
            resultados.append({
                "item_id": item_id,
                "status": "ERRO",
                "etapa_erro": "aprovacao",
                "mensagem": item.mensagem_erro
            })
            erros += 1

    return {
        "lote_id": lote_id,
        "total": len(item_ids),
        "aprovados": aprovados,
        "erros": erros,
        "itens": resultados
    }
