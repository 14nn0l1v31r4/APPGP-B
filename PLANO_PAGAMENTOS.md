# Plano de Implementação: Pagamentos Pix Diretos e Sem Burocracia

> **Para agentes de implementação:** executar as tarefas em ordem, mantendo o ciclo TDD: escrever teste falho, confirmar a falha, implementar o mínimo, confirmar todos os testes e só então refatorar.

**Objetivo:** adicionar baixa Pix rápida e lançamento manual com cadastro opcional de paciente, sem quebrar o upload/OCR existente.

**Arquitetura:** manter a tabela `pagamentos`. Pagamentos OCR persistem o `id_transacao` real; pagamentos manuais usam `id_transacao = NULL`, nunca um valor sentinela. Toda operação valida o paciente pelo `usuario_id` autenticado e confirma paciente + pagamento na mesma transação.

**Stack:** FastAPI, Pydantic, SQLAlchemy, PostgreSQL, Alembic e pytest.

**Especificação-base:** `PONTOS_DE_ATENCAO.md`.

## Restrições globais

- Não criar tabela paralela de pagamentos.
- Não aceitar `paciente_id` de outro usuário em nenhum endpoint.
- Não usar `float` para valores monetários na API ou no banco; usar `Decimal` e `Numeric(12, 2)`.
- Não usar `"MANUAL"` em `id_transacao`: a coluna é única e esse valor colidiria no segundo lançamento manual.
- Datas novas devem ser timezone-aware e persistidas em `DateTime(timezone=True)`.
- A funcionalidade de frontend não está neste repositório; documentar o contrato HTTP para o cliente.
- Não alterar dados de produção sem backup, migração versionada e plano de rollback.
- Toda tarefa de código segue RED → GREEN → REFACTOR; nenhum código de produção entra antes do teste falhar.

---

## Decisões de domínio e contrato

### Modos de lançamento

1. **Baixa rápida — `POST /pagamentos/rapido`**
   - Entrada: `paciente_id`, `sessoes_pagas` opcional (padrão `1`), `data_hora` opcional e `idempotencia_chave` obrigatória.
   - O paciente precisa pertencer ao usuário autenticado.
   - Valor: `paciente.valor_sessao * sessoes_pagas`.
   - Pagador: `paciente.nome`.
   - Repetição com a mesma `idempotencia_chave` retorna o lançamento já criado; não cria duplicata.

2. **Lançamento manual — `POST /pagamentos/`**
   - Permite `valor` e `pagador` personalizados.
   - `paciente_id` existente precisa pertencer ao usuário autenticado.
   - Sem `paciente_id`, exige `novo_paciente_nome`, `valor_sessao_manual` e `data_inicio_manual` válidos.
   - Cria paciente e pagamento na mesma transação.

3. **Upload/OCR — `POST /upload-pix/`**
   - Mantém rota e formato de resposta atuais.
   - Ao confirmar o pagamento após o OCR, persistir `data_hora` normalizada e `id_transacao` extraído.
   - Upload não deve criar pagamento automaticamente sem confirmação explícita do cliente.

### Regras de validação

- `sessoes_pagas >= 1`.
- `valor > 0`.
- `valor_sessao_manual > 0`.
- Nome de paciente e pagador não podem ser vazios após `strip()`.
- `id_transacao`, quando informada, deve ser não vazia; duplicata deve retornar HTTP 409.
- `paciente_id` e dados de novo paciente são mutuamente exclusivos.
- `data_hora` aceita os formatos legados `DD/MM/YYYY` e `DD/MM/YYYY HH:MM`, além de ISO 8601; o serviço converte tudo para datetime timezone-aware antes de persistir.
- `id_transacao` só é preenchido quando o cliente confirma um pagamento vindo do OCR; baixa rápida e lançamento manual sem comprovante deixam o campo `NULL`.

### Contratos Pydantic

Atualizar `app/schemas.py`:

```python
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field

class PagamentoCreate(BaseModel):
    pagador: str
    valor: Decimal = Field(..., gt=0, decimal_places=2)
    data_hora: datetime
    sessoes_pagas: int = Field(default=1, ge=1)
    paciente_id: Optional[int] = None
    id_transacao: Optional[str] = None
    idempotencia_chave: Optional[UUID] = None
    novo_paciente_nome: Optional[str] = None
    valor_sessao_manual: Optional[Decimal] = Field(default=None, gt=0, decimal_places=2)
    data_inicio_manual: Optional[date] = None

class PagamentoRapidoCreate(BaseModel):
    paciente_id: int
    sessoes_pagas: int = Field(default=1, ge=1)
    data_hora: Optional[datetime] = None
    idempotencia_chave: UUID
```

Criar `app/utils/dates.py` com parser explícito para os três formatos aceitos e usar esse parser em validador de `PagamentoCreate` e `PagamentoRapidoCreate`. O validador deve rejeitar combinações incompletas e impedir `paciente_id` combinado com `novo_paciente_nome`.

---

## Tarefas de implementação

### Tarefa 1: Preparar migração de dados

**Arquivos:**

- Criar: `alembic.ini`
- Criar: `migrations/env.py`
- Criar: `migrations/versions/20260913_pagamentos.py`
- Modificar: `requirements.txt`
- Modificar: `app/models.py`
- Modificar: `app/core/database.py` somente se necessário para configuração do Alembic

**Alterações:**

- Adicionar `alembic` e `pytest` às dependências.
- Alterar `Pagamento.valor` para `Numeric(12, 2)`.
- Alterar `Paciente.valor_sessao` para `Numeric(12, 2)`, evitando multiplicação entre `Decimal` e `float`.
- Alterar `Pagamento.data_hora` para `DateTime(timezone=True)`.
- Adicionar `Pagamento.idempotencia_chave` como `String`, nullable e unique.
- Criar índice único PostgreSQL para `idempotencia_chave`; valores `NULL` continuam permitidos e não colidem.
- Backfill de datas reconhecendo `DD/MM/YYYY`, `DD/MM/YYYY HH:MM` e ISO 8601.
- Interpretar datas sem timezone no fuso `America/Sao_Paulo` durante o backfill; rejeitar datas ambíguas ou inválidas.
- Interromper a migração e listar registros inválidos; não converter silenciosamente para `NULL`.
- Fazer backup antes da migração e documentar rollback da revisão.

**Verificação:** executar a migração em cópia do banco, conferir contagem de pagamentos, valores, IDs Pix e datas antes/depois.

### Tarefa 2: Criar testes de schema

**Arquivos:**

- Criar: `tests/conftest.py`
- Criar: `tests/test_schemas_pagamentos.py`
- Criar: `app/utils/dates.py`

Escrever primeiro testes para:

- aceitar `sessoes_pagas` omitido e produzir `1`;
- rejeitar zero e valores negativos;
- aceitar os três formatos de data e normalizar o resultado;
- rejeitar cadastro de paciente incompleto;
- rejeitar `paciente_id` combinado com `novo_paciente_nome`.

Executar: `pytest tests/test_schemas_pagamentos.py -q`.

### Tarefa 3: Tornar repositórios transacionais e seguros

**Arquivos:**

- Modificar: `app/repositories/pagamentos_repository.py`
- Modificar: `app/repositories/pacientes_repository.py`

**Alterações:**

- Remover `commit()` de funções internas de criação; usar `flush()` para obter IDs.
- Deixar `commit()` e `rollback()` sob responsabilidade do serviço.
- Expor busca de paciente por `paciente_id` e `usuario_id`.
- Expor busca de pagamento por `idempotencia_chave` e `usuario_id`.
- Manter busca e exclusão de pagamentos filtradas por `usuario_id`.

Escrever testes de repositório para impedir leitura/uso de paciente de outro usuário e para confirmar rollback sem paciente órfão.

### Tarefa 4: Implementar serviço de lançamento manual

**Arquivo:** `app/services/pagamentos_service.py`

**Alterações:**

- Validar paciente existente com filtro de `usuario_id`.
- Quando for novo paciente, criar objeto com `usuario_id` autenticado e dados já validados.
- Criar pagamento com `id_transacao` recebido; não preencher valor sentinela para lançamento manual.
- Usar uma única transação: `flush()`, criar dependências, `commit()` no sucesso e `rollback()` em falha.
- Converter exceção de unicidade de `id_transacao` para HTTP 409.
- Retornar `pagamento_id`, `paciente_id` e status sem expor dados de outro usuário.

Teste primeiro: `test_pagamento_com_criacao_paciente`, `test_pagamento_rejeita_paciente_de_outro_usuario`, `test_pagamento_faz_rollback_da_criacao_do_paciente` e `test_id_transacao_duplicada_retorna_409`.

### Tarefa 5: Implementar baixa rápida idempotente

**Arquivos:**

- Modificar: `app/services/pagamentos_service.py`
- Modificar: `app/controllers/pagamentos_controller.py`

**Alterações:**

- Criar `registrar_pagamento_rapido(db, dados, usuario_id)`.
- Buscar paciente pelo par `(paciente_id, usuario_id)`; ausência retorna HTTP 404.
- Calcular com `Decimal` e persistir `sessoes_pagas >= 1`.
- Consultar `idempotencia_chave` antes de criar.
- Tratar corrida de duas requisições pela restrição única do banco; a segunda deve recuperar o lançamento existente ou retornar resposta idempotente, nunca duplicar.
- Adicionar `POST /pagamentos/rapido` antes das demais rotas e retornar HTTP 201 na criação.

Testes: `test_pagamento_rapido_calculo_automatico`, `test_pagamento_rapido_multiplas_sessoes`, `test_pagamento_rapido_paciente_de_outro_usuario` e `test_pagamento_rapido_idempotente`.

### Tarefa 6: Corrigir dashboard sem ocultar erros

**Arquivos:**

- Modificar: `app/services/dashboard_service.py`
- Modificar: `app/repositories/dashboard_repository.py`

**Alterações:**

- Derivar o mês numérico diretamente do mapa `MESES_NUM` e remover o acesso por índice a `MESES_LISTA`.
- Filtrar pagamentos por intervalo de datetime (`início do mês <= data < início do mês seguinte`), sem `contains()` em texto.
- Remover `except:` amplo; capturar erros de dados conhecidos, registrar contexto e falhar de modo observável quando a inconsistência não puder ser corrigida.
- Manter filtros por `usuario_id`.
- Preservar a redução de saldo devedor por `sessoes_pagas`.

**Contrato pendente:** o modelo atual não informa o valor mensal de contratos `Mensal`. Não inventar regra usando `valor_sessao`. Antes de alterar esse cálculo, definir se `valor_sessao` representa mensalidade ou criar campo específico em uma migração separada.

Testes: `test_dashboard_calculo_mes_dezembro`, `test_dashboard_filtra_datetime_por_intervalo`, `test_dashboard_considera_pagamento_rapido` e `test_dashboard_nao_vaza_dados_entre_usuarios`.

### Tarefa 7: Preservar integração OCR

**Arquivos:**

- Modificar: `app/services/upload_service.py` somente para normalização necessária
- Modificar: `app/controllers/upload_controller.py` somente se o contrato de data exigir
- Criar: `tests/test_upload.py`

Testar:

- resposta de upload continua contendo pagador, valor, data, banco, ID Pix e status de match;
- ID Pix extraído chega ao lançamento confirmado e é persistido;
- paciente sem match continua exigindo confirmação manual;
- pagamentos OCR de usuários diferentes não compartilham candidatos.

Não automatizar a confirmação do pagamento no upload.

### Tarefa 8: Testar API e documentar contrato

**Arquivos:**

- Criar: `tests/test_pagamentos_api.py`
- Atualizar: `PLANO_PAGAMENTOS.md`
- Modificar: `app/controllers/pagamentos_controller.py` para incluir descrições e exemplos no schema OpenAPI das rotas

Cobrir HTTP 201, 404, 409 e 422 com dependência de usuário autenticado sobrescrita no teste. Incluir exemplos mínimos de request/response para os dois endpoints novos e conferir esses exemplos no schema OpenAPI gerado.

---

## Verificação final

Executar na raiz:

```bash
pytest -q
```

Critérios de aceite:

- Todos os testes passam; suíte inclui testes novos e regressão OCR.
- Dezembro e demais meses retornam dados corretos.
- Segundo lançamento manual não falha por colisão de `"MANUAL"`; nenhum lançamento manual usa esse sentinela.
- Usuário não consegue lançar pagamento para paciente de outro usuário.
- Requisições repetidas com a mesma chave não duplicam pagamento.
- Falha no pagamento não deixa paciente recém-criado no banco.
- Datas antigas migradas permanecem consultáveis; datas novas usam datetime timezone-aware.
- ID Pix OCR fica persistido e continua único.
- Regra de contrato mensal fica explicitamente definida antes de ser implementada; ausência dessa definição bloqueia somente essa parte do dashboard.

## Fora do escopo

- Criação de tabela separada para pagamentos.
- Confirmação automática de pagamentos durante upload.
- Algoritmo de similaridade ou cadastro de aliases de pagadores; isso exige decisão própria de UX e integridade.
- Implementação de frontend neste repositório.
- Regra financeira de contratos mensais sem definição do valor contratual.
