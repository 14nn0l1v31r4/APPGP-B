# Plano de Implementação: Pagamentos Pix Diretos e Sem Burocracia

Adicionar registro de pagamentos Pix direto/sem envio de comprovante (baixa rápida em 1 clique e cadastro simultâneo), mantendo a tabela única `pagamentos` e o fluxo de upload/OCR existente.

---

## 1. Decisões de Arquitetura

* **Tabela Única (`pagamentos`)**:
  - Sem criação de tabela adicional. Manter todos os pagamentos em `pagamentos`.
  - Evita queries paralelas, `UNION`, duplicação de regras no dashboard e lentidão.
* **Diferenciação por Metadados**:
  - Pagamento com comprovante: armazena código Pix no campo `id_transacao` (ex: `E12345...`).
  - Pagamento manual/rápido: armazena `id_transacao = "MANUAL"` ou `None`.
* **Foco Exclusivo em Pix**:
  - Sistema focado em gestão Pix para psicólogas, mantendo regras simples e diretas (YAGNI).
* **OCR 100% Preservado**:
  - Rota `POST /upload-pix/` segue ativa sem alterações para quem quiser subir comprovante em PDF ou imagem.

---

## 2. Modos de Lançamento Pix

1. **Modo 1: Baixa Rápida em 1-Clique (`POST /pagamentos/rapido`)**:
   - Psicóloga seleciona o paciente ou clica em "Dar Baixa" no card/devedor.
   - Envia apenas `paciente_id` e opcionalmente `sessoes_pagas` (padrão 1) e `data_hora` (padrão data/hora atual).
   - Backend busca `paciente.valor_sessao`, calcula `valor = valor_sessao * sessoes_pagas`, preenche `pagador = paciente.nome` e persiste na tabela `pagamentos`.
2. **Modo 2: Pagamento Manual / Com Cadastro Rápido (`POST /pagamentos/`)**:
   - Permite lançar valor Pix customizado ou pagador alternativo (ex: familiar).
   - Permite criar paciente simultaneamente caso ainda não exista (`novo_paciente_nome`, `valor_sessao_manual`), corrigindo a lógica pendente em `app/services/pagamentos_service.py`.
3. **Modo 3: Upload com OCR (Existente)**:
   - Mantido via `POST /upload-pix/`.

---

## 3. Alterações Planejadas por Arquivo

### A. Esquemas de Dados (`app/schemas.py`)
* Atualizar `PagamentoCreate` para incluir campos opcionais de criação rápida e evitar `AttributeError`:
  ```python
  class PagamentoCreate(BaseModel):
      pagador: str
      valor: float
      data_hora: str
      sessoes_pagas: int = 1
      paciente_id: Optional[int] = None
      id_transacao: Optional[str] = None
      novo_paciente_nome: Optional[str] = None
      valor_sessao_manual: Optional[float] = None
      data_inicio_manual: Optional[str] = None
  ```
* Criar schema enxuto `PagamentoRapidoCreate`:
  ```python
  class PagamentoRapidoCreate(BaseModel):
      paciente_id: int
      sessoes_pagas: int = 1
      data_hora: Optional[str] = None
  ```

### B. Regras de Negócio (`app/services/pagamentos_service.py`)
* Criar função `registrar_pagamento_rapido(db: Session, dados: schemas.PagamentoRapidoCreate, usuario_id: int)`:
  - Valida se paciente existe e pertence ao `usuario_id` logado (segurança multi-tenant).
  - Calcula `valor_total = paciente.valor_sessao * dados.sessoes_pagas`.
  - Atribui `pagador = paciente.nome`.
  - Atribui `data_hora = dados.data_hora or datetime.now().strftime("%d/%m/%Y %H:%M")`.
  - Salva em `Pagamento` com `id_transacao = "MANUAL"`.
* Atualizar `processar_pagamento`:
  - Garantir criação segura de paciente se `novo_paciente_nome` for fornecido.

### C. Correção de Bug no Dashboard (`app/services/dashboard_service.py`)
* Corrigir bug de índice do mês (`hoje.month` retorna 1..12, lista é base 0):
  ```python
  mes_atual_index = hoje.month - 1
  mes_nome = MESES_LISTA[mes_atual_index]
  ```

### D. Rotas HTTP (`app/controllers/pagamentos_controller.py`)
* Adicionar rota de baixa rápida:
  ```python
  @router.post("/rapido")
  def pagamento_rapido(
      dados: schemas.PagamentoRapidoCreate,
      db: Session = Depends(get_db),
      current_user: models.Usuario = Depends(security.get_current_user)
  ):
      return pagamentos_service.registrar_pagamento_rapido(db, dados, current_user.id)
  ```

### E. Testes Automatizados (`tests/test_pagamentos.py`)
* `test_pagamento_rapido_calculo_automatico`: Valida cálculo de valor automático a partir do `valor_sessao`.
* `test_pagamento_com_criacao_paciente`: Valida criação simultânea de paciente e pagamento.
* `test_seguranca_tenant_pagamento`: Impede que usuário acerte paciente de outro usuário.
* `test_dashboard_calculo_mes_dezembro`: Valida integridade do dashboard no mês 12.
* `test_ocr_upload_retrocompativel`: Valida que o upload de comprovante segue compatível.

---

## 4. Plano de Verificação

1. **Execução de Testes Automatizados**:
   - Rodar `rtk pytest tests/ -v`.
2. **Verificação de Regressão**:
   - Garantir que `/upload-pix/` segue operando.
   - Garantir que `/dashboard/` reflete os lançamentos manuais no total recebido e reduz o saldo devedor.

