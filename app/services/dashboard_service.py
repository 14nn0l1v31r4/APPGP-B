from datetime import datetime
from sqlalchemy.orm import Session
from app.repositories import dashboard_repository

MESES_NUM = {
    "Janeiro": "01", "Fevereiro": "02", "Março": "03", "Abril": "04",
    "Maio": "05", "Junho": "06", "Julho": "07", "Agosto": "08",
    "Setembro": "09", "Outubro": "10", "Novembro": "11", "Dezembro": "12"
}

def gerar_relatorio_dashboard(db: Session, mes_nome: str, usuario_id: int):
    mes_num = MESES_NUM.get(mes_nome, "04")
    hoje = datetime.now()
    
    lancamentos_mes = dashboard_repository.buscar_pagamentos_mes(db, usuario_id, mes_num)
    todos_pacientes, todos_pagamentos = dashboard_repository.buscar_todos_dados_usuario(db, usuario_id)
    
    total_recebido_mes = sum(p.valor for p in lancamentos_mes)
    total_sessoes_mes = sum(p.sessoes_pagas for p in lancamentos_mes if p.sessoes_pagas)
    
    valor_pendente_global = 0.0
    for p in todos_pacientes:
        try:
            data_inicio = datetime.strptime(p.data_inicio, "%Y-%m-%d")
            data_fim = datetime.strptime(p.data_inativo, "%Y-%m-%d") if (p.status == "Inativo" and p.data_inativo) else hoje
            
            dias_passados = (data_fim - data_inicio).days
            sessoes_esperadas = (dias_passados // 7) + 1 if dias_passados >= 0 else 0
            
            sessoes_pagas = sum(pg.sessoes_pagas for pg in todos_pagamentos if pg.paciente_id == p.id and pg.sessoes_pagas)
            sessoes_desmarcadas = dashboard_repository.contar_desmarcadas_por_paciente(db, p.id)
            
            sessoes_devidas = sessoes_esperadas - sessoes_pagas - sessoes_desmarcadas
            if sessoes_devidas > 0:
                valor_pendente_global += (sessoes_devidas * p.valor_sessao)
        except:
            continue

    return {
        "estatisticas": {
            "recebido": f"{total_recebido_mes:,.2f}".replace('.', ','),
            "pendente": f"{valor_pendente_global:,.2f}".replace('.', ','),
            "sessoesPagas": total_sessoes_mes,
            "sessoesPendentes": 0
        },
        "lancamentos": lancamentos_mes
    }