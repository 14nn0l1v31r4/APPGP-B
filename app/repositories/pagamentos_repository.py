from sqlalchemy.orm import Session
from app import models

def criar_paciente_via_pagamento(db: Session, dados_paciente: dict):
    novo_paciente = models.Paciente(**dados_paciente)
    db.add(novo_paciente)
    db.commit()
    db.refresh(novo_paciente)
    return novo_paciente

def criar_pagamento(db: Session, dados_pagamento: dict):
    novo_pagamento = models.Pagamento(**dados_pagamento)
    db.add(novo_pagamento)
    db.commit()
    return novo_pagamento

def buscar_por_id(db: Session, pagamento_id: int, usuario_id: int):
    return db.query(models.Pagamento).filter(
        models.Pagamento.id == pagamento_id, 
        models.Pagamento.usuario_id == usuario_id
    ).first()

def deletar(db: Session, pagamento: models.Pagamento):
    db.delete(pagamento)
    db.commit()