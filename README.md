# RoPA — Registro de Operações de Tratamento (PPSI 2.0)

Aplicação web para gestão do **Registro de Operações de Tratamento de Dados Pessoais (ROPA)**,
alinhada ao **Programa de Privacidade e Segurança da Informação (PPSI 2.0)** — controle 19 do
framework da Portaria SGD/MGI nº 9.511/2025 — e à **LGPD (Lei 13.709/2018, art. 37)**.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.x-000000?logo=flask)
![PPSI 2.0](https://img.shields.io/badge/PPSI%202.0-alinhado-1F3D7A)
![LGPD](https://img.shields.io/badge/LGPD-Art.%2037-green)
![License](https://img.shields.io/badge/Licen%C3%A7a-MIT-blue)

---

## 📋 Visão geral

O RoPA é uma solução completa para documentar e rastrear as operações de tratamento de dados
pessoais de um órgão ou entidade da administração pública federal (SISP), em conformidade com:

- **Controle 19 do PPSI 2.0** — registro das operações de tratamento de dados pessoais;
- **Art. 37 da LGPD** — obrigação de manter o registro das operações de tratamento;
- **Guia para Elaboração do Registro das Operações de Tratamento (PPSI 2.0, v1.0)** — conteúdo
  mínimo dos blocos 4.1 a 4.6, adotado como modelo de dados do sistema.

### Funcionalidades

- ✅ Registro completo das operações de tratamento, cobrindo o **conteúdo mínimo do Guia PPSI 2.0**;
- ✅ **Versionamento semântico** de cada registro, com snapshot e **restauração** de versões anteriores;
- ✅ Situação do registro (em andamento / em revisão / concluído / descontinuado / cancelado);
- ✅ Taxonomia de tipos de dados **compatível com o FCI da ANPD**;
- ✅ Validação de completude ponderada (soma 100) e dashboard;
- ✅ Autenticação institucional via **Keycloak (OIDC)**, com mock para desenvolvimento;
- ✅ Exportação em múltiplos formatos (**JSON, CSV, XLSX, PDF**);
- ✅ Interface web responsiva (Bootstrap 5);
- ✅ CLI para automação e seed de dados;
- ✅ Importador de **PIA CNIL** (JSON).

---

## 🗂️ Conteúdo do registro (Guia PPSI 2.0)

O modelo de dados segue o conteúdo mínimo da Tabela 1 do Guia do ROPA:

| Bloco | Informações |
|-------|-------------|
| **4.1 Identificação** | identificador único, nome do produto/serviço, unidade responsável, responsável pelo preenchimento, situação, versão/histórico |
| **4.2 Dados pessoais tratados** | categorias de titulares (com estimativa), proteção reforçada, tipos de dados (por categoria FCI-ANPD), tipos sensíveis |
| **4.3 Ciclo de vida dos dados** | fluxo de tratamento, origem, local/meio de armazenamento, retenção, eliminação/destinação final, frequência |
| **4.4 Finalidade e fundamentação** | finalidade, hipótese legal (base legal), previsão normativa específica |
| **4.5 Agentes de tratamento** | controladores, operadores |
| **4.6 Compartilhamento e transferência** | compartilhamentos, transferência internacional |

### Versionamento

Cada edição relevante gera uma nova versão (ex.: v1.0 → v1.1 → v2.0), com **snapshot completo**,
data, responsável e síntese das alterações. Alterações estruturais (finalidade, base legal, tipos de
dados, agentes etc.) promovem **versão major**. A **restauração** de uma versão anterior gera uma nova
versão documentando a reversão (o histórico nunca é apagado).

---

## 🚀 Início rápido (desenvolvimento)

```bash
# 1. Ambiente
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Rodar com mock Keycloak
./start_dev.sh
# ou: KEYCLOAK_MOCK=1 python app.py
```

Acesse **http://localhost:5000**

### Usuários de teste (senha: `123`)
- **encarregado** — Encarregado de Proteção de Dados (DPO, admin)
- **admin** — Administrador TI (admin)
- **usuario** — Maria Silva (visualização)

---

## 🏭 Implantação em produção (Linux / systemd)

O serviço roda com **gunicorn** atrás de um proxy reverso (Caddy) e Keycloak mock:

```ini
# /etc/systemd/system/ropa.service
[Unit]
Description=RoPA - Registro de Atividades de Tratamento (LGPD)
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/ropa-comm
Environment=KEYCLOAK_MOCK=1
Environment=ROPA_BASE_URL=https://seu-dominio
Environment=ROPA_MOCK_INTERNAL_URL=http://127.0.0.1:5000
Environment=FLASK_SECRET_KEY=troque-por-um-segredo-gerado
ExecStart=/opt/ropa-comm/.venv/bin/gunicorn app:app --bind 127.0.0.1:5000 --workers 2 --chdir /opt/ropa-comm
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload && systemctl enable --now ropa
systemctl status ropa
```

> **Importante:** gere um `FLASK_SECRET_KEY` forte para produção
> (`python -c "import secrets; print(secrets.token_hex(32))"`). Nunca use o valor de exemplo.

---

## 🛠️ Uso da CLI

```bash
python ropa.py novo          # Criar nova atividade de tratamento
python ropa.py listar        # Listar atividades
python ropa.py ver <id>      # Ver detalhes
python ropa.py editar <id>   # Editar (gera nova versão)
python ropa.py validar       # Validar completude (PPSI 2.0)
python ropa.py exportar      # Exportar JSON + CSV + XLSX
python ropa.py relatorio     # Relatório institucional PDF
python ropa.py seed          # Popular com dados de exemplo
python ropa.py importar pia.json [--strategy skip|merge|overwrite]  # Importar PIA CNIL
```

---

## 🔐 Variáveis de ambiente

```bash
# Flask
FLASK_SECRET_KEY=sua-chave-secreta

# Keycloak OIDC
KEYCLOAK_URL=https://keycloak.example.com
KEYCLOAK_REALM=ropa
KEYCLOAK_CLIENT_ID=ropa-web
KEYCLOAK_CLIENT_SECRET=seu-client-secret

# Desenvolvimento (mock Keycloak)
KEYCLOAK_MOCK=1

# Identidade institucional (opcional)
ROPA_ORGANIZACAO=Organização
ROPA_UNIDADE=Unidade de Proteção de Dados
ROPA_ENCARREGADO=Encarregado(a) de Proteção de Dados
ROPA_NORMAS_REFERENCIA=Documento produzido nos termos da LGPD – Lei 13.709/2018, Art. 37
```

Veja `.env.example` para o template completo.

---

## 📁 Estrutura do projeto

```
ropa-comm/
├── app.py                  # Aplicação Flask (web)
├── ropa.py                 # CLI
├── modelo_ppsi.py          # Campos/taxonomia PPSI 2.0 (FCI-ANPD), migração, versionamento
├── keycloak_blueprint.py   # Mock Keycloak (Blueprint)
├── cnil_pia_importer.py    # Importador PIA CNIL
├── requirements.txt
├── .env.example
├── templates/              # Jinja2 (form, ver, listar, index, validar, importar)
└── static/                 # Bootstrap (vendor), assets
```

---

## 🔗 Referências

- **PPSI 2.0** — Programa de Privacidade e Segurança da Informação (Portaria SGD/MGI nº 9.511/2025):
  https://www.gov.br/governodigital/pt-br/privacidade-e-seguranca/ppsi-2.0
- **Guia para Elaboração do Registro das Operações de Tratamento (PPSI 2.0, v1.0)**
- **LGPD** — Lei 13.709/2018, especialmente o **art. 37** (registro das operações de tratamento)

---

## 📄 Licença

MIT — veja o arquivo `LICENSE`.

**Desenvolvido para conformidade com a LGPD e o PPSI 2.0 (SGD/MGI).**
