# Relatório de Efetividade LGPD — RoPA-Comm

**Data:** 09/05/2026
**Escopo:** Revisão crítica completa do código-fonte
**Versão analisada:** commit `a32c139` (feat(acl): estrutura de papéis, permissões e escopo)

---

## Sumário executivo

O RoPA-Comm é uma ferramenta de documentação de atividades de tratamento de dados pessoais, atendendo ao Art. 37 da LGPD (Lei 13.709/2018). O sistema demonstra **conformidade moderada**, com pontos fortes na estruturação do registro de atividades e lacunas críticas em controles de segurança, direitos do titular, gestão de incidentes e rastreabilidade de auditoria.

**Nota geral de conformidade: ~55–60%**

---

## Tabela resumo por artigo LGPD

| Artigo | Requisito | Status atual | Nota | Severidade da lacuna |
|---|---|---|---|---|
| **Art. 37** | Registro de atividades de tratamento | Documentado, sem fluxo de aprovação | 70% | ALTA |
| **Art. 46** | Medidas de segurança | Documentadas nos campos, não implementadas | 40% | CRÍTICA |
| **Art. 48** | Notificação de incidentes | Não endereçado | 0% | CRÍTICA |
| **Art. 49** | Papel do encarregado (DPO) | Papel definido, não utilizado | 40% | CRÍTICA |
| **Art. 50** | Contratos com operadores | Não endereçado | 0% | CRÍTICA |
| **Art. 18** | Direitos do titular | Permissões definidas, sem rotas | 15% | CRÍTICA |
| **Art. 11** | Dados sensíveis | Documentados, sem proteção adicional | 60% | ALTA |
| **Art. 7** | Bases legais | Todas as bases mapeadas | 85% | MÉDIA |
| **Art. 6, II** | Minimização de dados | Política não aplicada | 40% | ALTA |
| **Art. 17** | Exclusão e retenção | Documentado, não aplicado | 30% | ALTA |
| **Art. 26** | Transferências internacionais | Documentadas, não validadas | 25% | ALTA |
| **Criptografia (Art. 46)** | Proteção em repouso | Sem criptografia | 0% | CRÍTICA |
| **Trilha de auditoria (Art. 37, 49)** | Rastreabilidade | Parcial (apenas campos alterados) | 50% | CRÍTICA |

---

## 1. O que o sistema cobre bem

### Art. 37 — Registro de atividades (70%)

O sistema mapeia corretamente os 15 campos exigidos pelo Art. 37 e valida os 9 campos obrigatórios com pesos de completude (0–100 pontos). Todas as bases legais do Art. 7 estão disponíveis no formulário, incluindo as bases para dados sensíveis do Art. 11.

A exportação em PDF, XLSX, JSON e CSV permite apresentar o registro a auditores externos.

**O que falta:**
- Nenhum registro de **quem** criou ou aprovou cada atividade — o campo `user_id` nunca é gravado no banco.
- Nenhum fluxo de aprovação (rascunho → enviado → aprovado → publicado).
- O historico registra *o que* mudou, mas não *quem* mudou.

### Art. 7 — Bases legais (85%)

Todas as hipóteses do Art. 7 e Art. 11 estão mapeadas no código (`app.py` e `ropa.py`), incluindo consentimento, obrigação legal, execução de contrato, interesse legítimo, tutela da saúde e demais bases. O formulário exige seleção de base legal.

---

## 2. Lacunas críticas

### 2.1 Trilha de auditoria sem identificação de responsável

**Artigos violados:** Art. 37 e Art. 49
**Localização:** `app.py` — tabela `historico`

A tabela `historico` registra alterações campo a campo, mas **nunca registra quem fez a alteração**. O `session['user']` está disponível no contexto da requisição, mas não é gravado:

```python
# O que existe: registra o campo e o valor, mas não o usuário
conn.execute(
    "INSERT INTO historico (atividade_id, campo, valor_antigo, valor_novo) VALUES (?,?,?,?)",
    (atividade_id, campo, valor_antigo, valor_novo)
)

# O que deveria existir:
conn.execute(
    "INSERT INTO historico (atividade_id, campo, valor_antigo, valor_novo, alterado_por) VALUES (?,?,?,?,?)",
    (atividade_id, campo, valor_antigo, valor_novo, session['user']['sub'])
)
```

Além disso, não existe rastreamento de:

| Evento | Registrado? |
|---|---|
| Login de usuário | ❌ |
| Exportação de dados | ❌ |
| Exclusão (soft delete) | Parcialmente — sem `user_id` |
| Aprovação de atividade | ❌ (não existe fluxo) |
| Atribuição de papéis | ❌ |
| Certificação pelo DPO | ❌ |
| Tentativas de acesso negadas | ❌ |

---

### 2.2 Controle de acesso (ACL) definido mas não integrado

**Artigos violados:** Art. 46, Art. 49
**Localização:** `app.py` — todas as rotas

O módulo `acl/` está **completamente implementado** — 11 papéis, 22+ permissões atômicas, 4 tipos de escopo — mas **nenhuma rota em `app.py` utiliza os decoradores `@require_permission`**. A única proteção existente é o `@login_required`, que verifica apenas se o usuário está autenticado:

```python
# O que existe: qualquer usuário autenticado acessa qualquer rota
@app.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar(id):
    ...

# O que deveria existir:
@app.route("/editar/<int:id>", methods=["GET", "POST"])
@require_permission(Permission.OPERACAO_EDITAR_QUALQUER)
def editar(id):
    ...
```

**Consequência prática:** Um usuário com papel de "visualizador" pode editar, excluir ou exportar qualquer atividade. O sistema de papéis existe mas não tem efeito em produção.

---

### 2.3 Sem criptografia de dados em repouso

**Artigo violado:** Art. 46
**Localização:** `app.py` — acesso ao banco de dados

O banco SQLite armazena todos os dados em texto plano. A chave secreta do Flask tem valor padrão inseguro:

```python
# app.py — chave padrão hardcoded
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "ropa-dev-only-change-in-prod")
```

Se `FLASK_SECRET_KEY` não estiver configurada em produção, sessões podem ser forjadas. Nenhum campo é criptografado em repouso — uma cópia do arquivo `ropa.db` expõe todos os dados de tratamento sem necessidade de credenciais.

---

### 2.4 Gestão de incidentes ausente (Art. 48 — 0%)

O Art. 48 exige notificação à ANPD em caso de incidente de segurança com risco relevante aos titulares. O sistema não possui:

- Nenhum mecanismo de detecção de acessos anômalos
- Nenhum fluxo de classificação de incidentes
- Nenhum modelo de notificação à ANPD
- Nenhum mecanismo de notificação ao titular
- Nenhuma linha do tempo de incidentes

Os logs do Gunicorn registram requisições HTTP, mas não eventos de segurança.

---

### 2.5 Direitos do titular não implementados (Art. 18 — 15%)

O Art. 18 garante ao titular direitos de acesso, correção, exclusão, portabilidade e oposição. O sistema é voltado ao controlador (gestão interna do RoPA) e não oferece:

- Nenhuma interface para solicitações de titulares
- Nenhum rastreamento de prazo de resposta (15–30 dias)
- Nenhum mecanismo de exclusão sob demanda
- Nenhum mecanismo de portabilidade de dados do titular

A permissão `COMPLIANCE_ATENDER_TITULAR` existe no módulo ACL mas não há nenhuma rota correspondente em `app.py`.

---

### 2.6 Contratos com operadores ausentes (Art. 50 — 0%)

O campo `destinatarios` é texto livre — qualquer destinatário pode ser cadastrado sem validação. Não há:

- Registro de operadores e suboperadores
- Upload ou referência a contratos de processamento de dados (DPA)
- Rastreamento de status contratual
- Verificação de cláusulas obrigatórias

---

### 2.7 Retenção de dados: documentada, não aplicada (Art. 17 — 30%)

O campo `prazo_retencao` captura o período de retenção como texto livre (ex.: "5 anos"), mas:

- Nenhuma data de exclusão é calculada automaticamente
- Nenhum processo agendado de purga de dados existe
- Dados permanecem indefinidamente mesmo após o prazo vencer
- Não há auditoria das exclusões realizadas

---

### 2.8 Transferências internacionais sem validação (Art. 26 — 25%)

O campo `transferencia_inter` permite registro de transferências, mas:

- Países de destino não são validados contra lista de adequação da ANPD
- Não há campo para referência a cláusulas contratuais padrão (SCC)
- Não há rastreamento de aprovação ou decisão de adequação
- Não há exigência de avaliação de impacto para países sem adequação

---

### 2.9 Consentimento: base legal mapeada, sem gestão (Art. 7, I — 40%)

O sistema permite selecionar "Consentimento do titular" como base legal, mas não rastreia:

- Onde e como o consentimento foi coletado
- Link para o sistema de gestão de consentimento
- Mecanismo de retirada do consentimento
- Histórico do ciclo de vida do consentimento

---

## 3. Vulnerabilidades de segurança identificadas

### 3.1 Credenciais hardcoded no código (ALTA)

`keycloak_blueprint.py` contém usuários e senha de teste diretamente no código:

```python
USERS = {
    "encarregado": {"password": "123", ...},
    "admin":       {"password": "123", ...},
    "usuario":     {"password": "123", ...},
}
JWT_SECRET = "mock-keycloak-jwt-secret-for-dev-only"
```

Se o ambiente de produção for iniciado com `KEYCLOAK_MOCK=1` por engano, qualquer pessoa com acesso ao repositório pode autenticar-se.

### 3.2 Ausência de proteção CSRF (ALTA)

Nenhum token CSRF é gerado ou verificado nos formulários. Um atacante pode induzir um usuário autenticado a submeter formulários maliciosos (ex.: criar, editar ou excluir atividades).

### 3.3 IDOR — Acesso direto a objetos (MÉDIA)

As rotas `/ver/<id>` e `/editar/<id>` não verificam se o usuário tem permissão sobre aquele registro específico. Um usuário autenticado pode acessar atividades de outras unidades incrementando o ID na URL.

### 3.4 Cabeçalhos de segurança HTTP ausentes (MÉDIA)

Nenhum cabeçalho de segurança está configurado:

| Cabeçalho | Status |
|---|---|
| `X-Frame-Options` | ❌ ausente |
| `X-Content-Type-Options` | ❌ ausente |
| `Content-Security-Policy` | ❌ ausente |
| `Strict-Transport-Security` | ❌ ausente |

### 3.5 Timeout de sessão não configurado (BAIXA)

Sessões Flask não têm timeout definido — uma sessão pode permanecer válida indefinidamente após o login.

---

## 4. Dados sensíveis: proteção insuficiente (Art. 11 — 60%)

O sistema permite marcar uma atividade como "dados sensíveis" e exibe um badge visual, mas:

- Qualquer usuário autenticado acessa atividades com dados sensíveis
- Não há controle de acesso diferenciado para dados sensíveis
- Não há exigência de aprovação prévia do DPO para novas atividades com dados sensíveis
- Os dados não recebem criptografia de campo

---

## 5. O módulo ACL: bem projetado, não integrado

O módulo `acl/` representa o componente mais sofisticado do sistema:

**O que está implementado:**
- 11 papéis com segregação de funções
- 22+ permissões atômicas em 4 grupos (OPERACAO, AUDITORIA, ADMIN, API)
- 4 tipos de escopo (GLOBAL, UNIDADE, TIPO_OP, PROPRIO)
- Atribuições temporárias com data de expiração
- Testes de sanidade de segregação de funções

**O que falta para funcionar:**
- Middleware que popule `g.current_user` com o usuário do Keycloak
- Aplicação dos decoradores `@require_permission` nas rotas de `app.py`
- Resolução de escopo por atividade (qual unidade pertence cada registro)

Sem a integração, o módulo ACL é letra morta — existe no código mas não tem efeito na execução.

---

## 6. Pontos positivos do projeto

- **Mapeamento completo das bases legais** do Art. 7 e Art. 11
- **Sistema de pontuação de completude** (0–100) com classificação visual
- **Exportação multiformat** (PDF, XLSX, CSV, JSON) para auditorias externas
- **Histórico de alterações campo a campo** (mesmo sem `user_id`)
- **Importação CNIL PIA** com mapeamento GDPR → LGPD
- **Mock Keycloak** isolado — não contamina ambiente de produção quando `KEYCLOAK_MOCK=0`
- **Soft delete** preserva histórico sem perda de dados
- **Seed de dados de exemplo** facilita onboarding e treinamento
- **Estrutura de ACL bem projetada**, pronta para integração

---

## 7. Recomendações por prioridade

### Fase 1 — Imediata (semanas 1–2)

1. **Gravar `user_id` em todas as operações de auditoria**
   - Adicionar `alterado_por` na tabela `historico`
   - Registrar `criado_por` na tabela `atividades`
   - Registrar exportações em tabela de auditoria

2. **Integrar o módulo ACL nas rotas**
   - Criar middleware que popule `g.current_user` a partir da sessão
   - Aplicar `@require_permission` em todas as rotas protegidas
   - Implementar verificação de escopo por unidade

3. **Remover credenciais hardcoded**
   - Mover usuários de teste para variáveis de ambiente
   - Garantir que `KEYCLOAK_MOCK=1` nunca seja definido em produção

### Fase 2 — Alta prioridade (semanas 3–4)

4. **Implementar fluxo de direitos do titular (Art. 18)**
   - Rota `/solicitacoes-titular` com rastreamento de prazo
   - Tipos: acesso, correção, exclusão, portabilidade, oposição

5. **Adicionar fluxo de incidentes (Art. 48)**
   - Registro de incidentes com classificação e timeline
   - Template de notificação à ANPD
   - Mecanismo de notificação aos titulares

6. **Aplicar retenção automatizada**
   - Calcular `data_exclusao` a partir de `prazo_retencao`
   - Processo de purga com auditoria de exclusão

### Fase 3 — Média prioridade (semanas 5–6)

7. **Gestão de consentimento**
   - Campo para link/referência ao documento de consentimento
   - Rastreamento de retirada do consentimento

8. **Validação de transferências internacionais**
   - Lista de países com decisão de adequação da ANPD
   - Exigência de SCC para países sem adequação

9. **Proteção de dados sensíveis**
   - Controle de acesso diferenciado
   - Exigência de aprovação do DPO

### Fase 4 — Complementar (semana 7+)

10. Cabeçalhos HTTP de segurança (`X-Frame-Options`, `CSP`, `HSTS`)
11. Proteção CSRF (Flask-WTF)
12. Criptografia do banco de dados (SQLCipher ou migração para PostgreSQL)
13. Timeout de sessão configurável
14. Limitação de taxa em exportações

---

## 8. Conclusão

O RoPA-Comm é uma **ferramenta de documentação sólida** para o Art. 37 da LGPD, com UX adequada e estrutura de dados bem mapeada. Entretanto, **não está em condições de produção para dados reais** sem as implementações da Fase 1 e 2.

As lacunas mais graves são:
1. **Auditoria sem responsabilidade** — impossível saber quem fez o quê
2. **ACL sem efeito** — qualquer usuário autenticado tem acesso irrestrito
3. **Art. 48 totalmente ausente** — sem capacidade de resposta a incidentes
4. **Art. 18 sem implementação** — titulares não podem exercer seus direitos
5. **Dados em texto plano** — violação do Art. 46 em caso de brecha

**Esforço estimado para conformidade mínima:** 4 semanas (Fases 1 e 2)
**Esforço para conformidade plena:** 6–8 semanas (Fases 1 a 3)

> **Recomendação:** Não utilizar em ambiente de produção com dados pessoais reais antes de completar ao menos a Fase 1. O sistema atual é adequado para fins de treinamento, homologação e mapeamento inicial de atividades em ambiente controlado.
