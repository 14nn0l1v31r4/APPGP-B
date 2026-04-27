from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import models, schemas, security
from database import get_db

router = APIRouter(prefix="/pagamentos", tags=["Pagamentos"])

@router.post("/")
def registrar_pagamento(pg: schemas.PagamentoCreate, db: Session = Depends(get_db), current_user: models.Usuario = Depends(security.get_current_user)):
    
    id_final = pg.paciente_id

    # ✨ A MÁGICA: Se não tem ID, vamos criar o paciente agora
    if not id_final and pg.novo_paciente_nome:
        # Criamos o objeto do paciente usando os dados que vieram do comprovante
        novo_paciente = models.Paciente(
            nome=pg.novo_paciente_nome,
            valor_sessao=pg.valor_sessao_manual, # O valor que você definiu na tela
            data_inicio=pg.data_inicio_manual,   # A data que você escolheu
            usuario_id=current_user.id,
            status="Ativo"
        )
        db.add(novo_paciente)
        db.commit()
        db.refresh(novo_paciente)
        
        # Agora o paciente existe e tem um ID!
        id_final = novo_paciente.id

    # Agora salvamos o pagamento com o ID (seja o existente ou o novo que acabamos de criar)
    novo_pagamento = models.Pagamento(
        paciente_id=id_final,
        valor=pg.valor,
        data_hora=pg.data_hora,
        sessoes_pagas=pg.sessoes_pagas,
        pagador=pg.pagador,
        status="Pago",
        usuario_id=current_user.id
    )
    
    db.add(novo_pagamento)
    db.commit()
    
    return {"status": "sucesso", "paciente_id": id_final}

@router.delete("/{pagamento_id}")
def deletar_pagamento(pagamento_id: int, db: Session = Depends(get_db), current_user: models.Usuario = Depends(security.get_current_user)):
    pg = db.query(models.Pagamento).filter(models.Pagamento.id == pagamento_id, models.Pagamento.usuario_id == current_user.id).first()
    if not pg:
        raise HTTPException(status_code=404, detail="Lançamento não encontrado")
    db.delete(pg)
    db.commit()
    return {"status": "excluído"}