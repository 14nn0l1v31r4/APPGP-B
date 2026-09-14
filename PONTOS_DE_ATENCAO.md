# Pontos de Atenção e Diagnóstico Técnico - APPGP-B

Este documento consolida os problemas críticos, riscos de integridade e inconsistências encontrados no código do backend do APPGP-B.

---

## 1. Falha Crítica: Índice de Mês no Dashboard
* **Arquivo**: [`app/services/dashboard_service.py`](file:///c:/Users/iannm/Desktop/atransferencia/APPGP-B/app/services/dashboard_service.py#L19-L23)
* **Código**:
  ```python
  if not mes_nome:
      mes_atual_index = hoje.month 
      mes_nome = MESES_LISTA[mes_atual_index]
  ```
* **Problema**:
  - `datetime.now().month` retorna inteiros de `1` a `12`.
  - `MESES_LISTA` é uma lista Python indexada em `0` (`0 = Janeiro`, `11 = Dezembro`).
  - **Consequência**:
    - Em qualquer mês comum, seleciona o mês seguinte (ex: mês 1 / Janeiro vira `MESES_LISTA[1]` / Fevereiro).
    - Em Dezembro (`month = 12`), `MESES_LISTA[12]` causa **`IndexError: list index out of range`**, derrubando a requisição com Erro 500.
* **Correção necessária**:
  ```python
  mes_atual_index = hoje.month - 1
  mes_nome = MESES_LISTA[mes_atual_index]
  ```

---

## 2. Inconsistência de Schema em Pagamentos
* **Arquivo**: [`app/services/pagamentos_service.py`](file:///c:/Users/iannm/Desktop/atransferencia/APPGP-B/app/services/pagamentos_service.py#L9-L18) vs [`app/schemas.py`](file:///c:/Users/iannm/Desktop/atransferencia/APPGP-B/app/schemas.py#L19-L26)
* **Código em `pagamentos_service.py`**:
  ```python
  if not id_final and pg.novo_paciente_nome:
      dados_novo_paciente = {
          "nome": pg.novo_paciente_nome,
          "valor_sessao": pg.valor_sessao_manual,
          "data_inicio": pg.data_inicio_manual,
          ...
      }
  ```
* **Código em `schemas.py`**:
  ```python
  class PagamentoCreate(BaseModel):
      pagador: str
      valor: float
      data_hora: str
      sessoes_pagas: int = 0                
      paciente_id: Optional[int] = None    
      id_transacao: Optional[str] = None
  ```
* **Problema**:
  - Os campos `novo_paciente_nome`, `valor_sessao_manual` e `data_inicio_manual` não estão definidos em `PagamentoCreate`.
  - Se o backend tentar acessar `pg.novo_paciente_nome`, o Pydantic terá descartado ou não reconhecido o atributo, resultando em **`AttributeError: 'PagamentoCreate' object has no attribute 'novo_paciente_nome'`**.
* **Correção necessária**:
  - Adicionar os campos opcionais no schema `PagamentoCreate` ou criar um schema específico `PagamentoManualComNovoPacienteCreate`.

---

## 3. Inconsistência de Formato de Datas e Filtro Frágil
* **Arquivos**:
  - [`app/models.py`](file:///c:/Users/iannm/Desktop/atransferencia/APPGP-B/app/models.py#L28,L56)
  - [`app/repositories/dashboard_repository.py`](file:///c:/Users/iannm/Desktop/atransferencia/APPGP-B/app/repositories/dashboard_repository.py#L7)
  - [`app/services/dashboard_service.py`](file:///c:/Users/iannm/Desktop/atransferencia/APPGP-B/app/services/dashboard_service.py#L37-L38)
* **Problema**:
  - `Paciente.data_inicio` usa padrão `YYYY-MM-DD` (`datetime.now().strftime("%Y-%m-%d")`).
  - `Pagamento.data_hora` é salvo como string arbitrária vinda do OCR ou do frontend (frequentemente `DD/MM/YYYY` ou `DD/MM/YYYY HH:MM`).
  - A busca mensal do dashboard faz:
    ```python
    models.Pagamento.data_hora.contains(f"/{filtro_mes}/")
    ```
  - Se o pagamento for gravado no padrão ISO (`YYYY-MM-DD`), o filtro `/{filtro_mes}/` falhará e retornará lista vazia de pagamentos.
  - Além disso, comparações de string em SQL sem tipagem de data (`Date` / `DateTime`) impedem ordenações confiáveis e índices de performance.
* **Correção necessária**:
  - Padronizar entrada de datas no backend (converter strings para formato canônico ISO `YYYY-MM-DD` ou usar tipo nativo SQLAlchemy `DateTime`/`Date`).

---

## 4. Fragilidade no Match Heurístico de Paciente no OCR
* **Arquivo**: [`app/services/upload_service.py`](file:///c:/Users/iannm/Desktop/atransferencia/APPGP-B/app/services/upload_service.py#L37)
* **Código**:
  ```python
  if " ".join(nome_lido.split()[:2]) == " ".join(nome_db.split()[:2]):
      paciente_encontrado = p
  ```
* **Problema**:
  - Compara apenas as duas primeiras palavras do nome. Se houver pacientes com o mesmo primeiro e segundo nome (ex: "Maria Silva Santos" e "Maria Silva Souza"), causará vínculo com o paciente errado.
  - Se o pagador do Pix for parente (mãe, pai, cônjuge) com sobrenome ou primeiro nome diferente, o vínculo automático falha silenciosamente.
* **Correção necessária**:
  - Suporte a aliases/responsáveis financeiros cadastrados no paciente (ex: campo `nomes_pagadores_autorizados` ou similar).
  - Algoritmo de similaridade mais resiliente (ex: Levenshtein / `difflib.SequenceMatcher`) e confirmação explícita no frontend quando a confiança for intermediária.

---

## 5. Falta de Tratamento e Feedback para Tipos de Contrato
* **Arquivo**: [`app/models.py`](file:///c:/Users/iannm/Desktop/atransferencia/APPGP-B/app/models.py#L25) e [`app/services/dashboard_service.py`](file:///c:/Users/iannm/Desktop/atransferencia/APPGP-B/app/services/dashboard_service.py#L40-L46)
* **Problema**:
  - O modelo possui `tipo_contrato = Column(String, default="Por Sessão")` e `dia_vencimento = Column(Integer, nullable=True)`.
  - O cálculo do dashboard ignora esses campos e assume rigidamente que todo paciente tem exatamente 1 sessão por semana (`dias_passados // 7`), desconsiderando contratos mensais fechados ou dias de vencimento fixo.
* **Correção necessária**:
  - Implementar lógica condicional de cálculo no dashboard para contratos "Mensal" vs "Por Sessão".

