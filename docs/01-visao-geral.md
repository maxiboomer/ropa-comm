# RoPA-Comm — Visão Geral do Sistema

## O que é o RoPA?

**RoPA** (Registro de Atividades de Tratamento) é uma aplicação web para gestão e documentação de atividades de tratamento de dados pessoais, em conformidade com a **Lei Geral de Proteção de Dados (LGPD — Lei 13.709/2018)**.

O sistema atende ao Art. 37 da LGPD, que obriga controladores e operadores a manterem um registro das operações de tratamento de dados pessoais realizadas.

---

## Problema que resolve

Organizações brasileiras precisam documentar todas as suas atividades de tratamento de dados pessoais, incluindo:
- A finalidade do tratamento
- A base legal utilizada (consentimento, obrigação legal, legítimo interesse, etc.)
- Quais categorias de dados e titulares são envolvidos
- Por quanto tempo os dados são retidos
- Quais medidas de segurança são aplicadas
- Se há transferência internacional de dados

O RoPA oferece uma interface centralizada para esse registro, com controle de acesso por papéis, histórico de auditoria e exportação para múltiplos formatos.

---

## Tecnologias utilizadas

### Backend

| Componente | Tecnologia | Versão |
|---|---|---|
| Framework web | Flask | 3.0.0+ |
| Servidor de produção | Gunicorn | 21.2.0+ |
| Banco de dados | SQLite 3 | (embutido) |
| ORM (módulo ACL) | SQLAlchemy | integrado no Flask |
| Autenticação | Authlib (OIDC) | 1.3.0+ |
| Cliente HTTP | Requests | 2.31.0+ |
| Exportação Excel | OpenPyXL | 3.1.0+ |
| Geração de PDF | ReportLab | 4.0.0+ |

### Frontend

| Componente | Tecnologia |
|---|---|
| Framework CSS | Bootstrap 5.3.3 |
| Ícones | Bootstrap Icons |
| Templating | Jinja2 (nativo Flask) |
| JavaScript | Vanilla JS (sem framework) |

### Infraestrutura

| Componente | Opção |
|---|---|
| Containerização | Docker |
| PaaS | Heroku |
| Servidor local (macOS) | macOS LaunchAgent |
| Acesso público (local) | Cloudflare Tunnel |

---

## Padrão arquitetural

O sistema é um **monólito web MVC** com renderização server-side:

- **Model:** SQLite via SQLAlchemy (ACL) e sqlite3 nativo (dados RoPA)
- **View:** Templates Jinja2 com Bootstrap 5
- **Controller:** Rotas Flask em `app.py`

Não há API REST separada — todas as operações são realizadas via formulários HTML com rotas Flask que retornam páginas renderizadas.

---

## Funcionalidades principais

### Registro de atividades
- Cadastro de atividades de tratamento com 15 campos estruturados
- Campos obrigatórios mapeados diretamente para Art. 37 LGPD
- Soft delete (atividades são desativadas, não excluídas)

### Validação de completude
- Pontuação automática de 0–100 por atividade
- 9 campos obrigatórios com pesos distintos
- Classificação: verde (≥80%), amarelo (50–79%), vermelho (<50%)
- Relatório de conformidade por unidade

### Histórico de auditoria
- Rastreamento de todas as alterações campo a campo
- Registro de valor anterior e valor novo
- Timestamp automático

### Exportação e importação
- **Exportação:** JSON, CSV, XLSX (Excel formatado), PDF
- **Importação:** CNIL PIA (formato francês GDPR → mapeamento LGPD)
- Estratégias de importação: pular duplicatas, mesclar ou sobrescrever

### Controle de acesso (ACL)
- 11 papéis predefinidos (de visualizador a administrador)
- 22 permissões atômicas organizadas em grupos
- Escopo por papel: global, unidade, tipo de operação, próprio registro
- Atribuições com validade opcional (expiração)

### Interface web
- Design responsivo com Bootstrap 5
- Navegação lateral (sidebar)
- Formulário multi-abas para cadastro
- Mensagens de feedback (flash messages)

### Interface CLI
- Comandos interativos para operações sem browser
- Seed de dados de exemplo
- Exportação em lote

---

## Implantações suportadas

| Ambiente | Mecanismo |
|---|---|
| Desenvolvimento local | `python app.py` com mock Keycloak |
| Docker | `docker build` + `docker run` |
| Heroku | `git push heroku main` via Procfile |
| macOS (servidor local) | LaunchAgent + Cloudflare Tunnel |
| Servidor Unix genérico | Gunicorn + virtualenv |
