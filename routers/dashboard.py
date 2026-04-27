from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime
import models, security
from database import get_db

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

MESES_NUM = {
    "Janeiro": "01", "Fevereiro": "02", "Março": "03", "Abril": "04",
    "Maio": "05", "Junho": "06", "Julho": "07", "Agosto": "08",
    "Setembro": "09", "Outubro": "10", "Novembro": "11", "Dezembro": "12"
}

@router.get("/")
def get_dashboard(mes: str = "Abril", db: Session = Depends(get_db), current_user: models.Usuario = Depends(security.get_current_user)):
    mes_num = MESES_NUM.get(mes, "04")
    
    # 🔒 Filtra tudo pelo current_user.id
    lancamentos_mes = db.query(models.Pagamento).filter(
        models.Pagamento.usuario_id == current_user.id,
        models.Pagamento.data_hora.contains(f"/{mes_num}/")
    ).all()
    
    total_recebido_mes = sum(p.valor for p in lancamentos_mes)
    total_sessoes_mes = sum(p.sessoes_pagas for p in lancamentos_mes if p.sessoes_pagas)
    
    todos_pacientes = db.query(models.Paciente).filter(models.Paciente.usuario_id == current_user.id).all()
    todos_pagamentos = db.query(models.Pagamento).filter(models.Pagamento.usuario_id == current_user.id).all()
    
    valor_pendente_global = 0.0
    hoje = datetime.now()

    for p in todos_pacientes:
        try:
            data_inicio = datetime.strptime(p.data_inicio, "%Y-%m-%d")
        except:
            data_inicio = hoje
            
        if p.status == "Inativo" and p.data_inativo:
            try:
                data_fim = datetime.strptime(p.data_inativo, "%Y-%m-%d")
            except:
                data_fim = hoje
        else:
            data_fim = hoje
            
        dias_passados = (data_fim - data_inicio).days
        sessoes_esperadas = (dias_passados // 7) + 1 if dias_passados >= 0 else 0
        
        sessoes_pagas = sum(pg.sessoes_pagas for pg in todos_pagamentos if pg.paciente_id == p.id and pg.sessoes_pagas)
        sessoes_desmarcadas = db.query(models.SessaoDesmarcada).filter(models.SessaoDesmarcada.paciente_id == p.id).count()
        
        sessoes_devidas = sessoes_esperadas - sessoes_pagas - sessoes_desmarcadas
        
        if sessoes_devidas > 0:
            valor_pendente_global += (sessoes_devidas * p.valor_sessao)
        
    return {
        "estatisticas": {
            "recebido": f"{total_recebido_mes:,.2f}".replace('.', ','),
            "pendente": f"{valor_pendente_global:,.2f}".replace('.', ','),
            "sessoesPagas": total_sessoes_mes,
            "sessoesPendentes": 0
        },
        "lancamentos": lancamentos_mes
    }