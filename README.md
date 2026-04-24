# RoPA 
## Registro de Atividades de Tratamento de Dados

Aplicação web para gerenciamento de **Registros de Atividades de Tratamento (RoPA)** institucional, em conformidade com a **Lei Geral de Proteção de Dados (LGPD - Lei 13.709/2018)**

---

## 📋 Visão Geral

O RoPA é uma solução completa para documentação e rastreamento de atividades de processamento de dados pessoais, incluindo:

✅ Registro de atividades de tratamento (Art. 37 LGPD)
✅ Validação de completude conforme LGPD
✅ Autenticação institucional via Keycloak (OIDC)
✅ Gestão de dados sensíveis e direitos de titulares
✅ Exportação em múltiplos formatos (XLSX, PDF, JSON, CSV)
✅ Interface web responsiva com Bootstrap 5
✅ CLI para automação e seed de dados
✅ Mock Keycloak para prototipagem

---

## 🚀 Quick Start

### 1. Clonar o repositório
```bash
git clone <seu-repositorio>
cd ropa
```

### 2. Configurar ambiente Python
```bash
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# ou: .venv\Scripts\activate  # Windows
```

### 3. Instalar dependências
```bash
pip install -r requirements.txt
```

### 4. Rodar em desenvolvimento (com mock Keycloak)
```bash
./start_dev.sh
# ou: KEYCLOAK_MOCK=1 python app.py
```

Acesse: **http://localhost:5000**

### Usuários de teste (senha: 123)
- **encarregado** - Encarregado de Proteção de Dados (DPO, Admin)
- **admin** - Administrador TI (Admin)
- **usuario** - Maria Silva (Viewer)

---

## 📦 Instalação em Produção

### macOS — Instalação permanente com autostart (Recomendado para uso local)

Instala RoPA como serviço permanente com:
- **gunicorn** (WSGI production server, 4 workers)
- **Cloudflare Tunnel** (URL pública HTTPS `.trycloudflare.com`)
- **launchd LaunchAgents** (autostart no login, KeepAlive em crash)
- **ropa-ctl** (ferramenta de gerenciamento)

```bash
git clone https://github.com/maxiboomer/ropa.git
cd ropa
./deploy/install-macos.sh
./ropa-ctl start
./ropa-ctl status   # mostra URL pública
```

Gerenciamento:
```bash
./ropa-ctl status       # estado + URL pública
./ropa-ctl restart      # reinicia ambos serviços
./ropa-ctl logs tunnel  # tail dos logs
./ropa-ctl url          # só imprime a URL
./ropa-ctl stop         # para serviços
./ropa-ctl uninstall    # remove LaunchAgents
```

Dados persistidos em `~/Library/Application Support/ropa/`:
- `ropa.db` — banco SQLite
- `.env` — credenciais + FLASK_SECRET_KEY
- `logs/` — stdout/stderr de gunicorn e cloudflared

### Docker
```bash
docker build -t ropa .
docker run -p 8000:5000 \
  -e KEYCLOAK_URL=https://seu-keycloak.com \
  -e KEYCLOAK_REALM=ropa \
  -e KEYCLOAK_CLIENT_ID=ropa-web \
  -e KEYCLOAK_CLIENT_SECRET=seu-secret \
  -e FLASK_SECRET_KEY=seu-secret-key \
  ropa
```

### Heroku / PaaS
```bash
git push heroku main
```

O arquivo `Procfile` já está configurado:
```
web: gunicorn app:app --bind 0.0.0.0:$PORT
```

### Instalação Manual

#### Requisitos
- Python 3.9+
- Keycloak 18+ (ou mock para desenvolvimento)
- SQLite 3

#### Passos
```bash
# 1. Clonar e preparar
git clone <seu-repositorio>
cd ropa
python3 -m venv venv
source venv/bin/activate

# 2. Instalar
pip install -r requirements.txt

# 3. Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas credenciais Keycloak

# 4. Inicializar banco de dados
python app.py  # Cria ropa.db automaticamente

# 5. Rodar
gunicorn app:app --bind 0.0.0.0:5000
```

---

## 🔐 Variáveis de Ambiente

```bash
# Flask
FLASK_SECRET_KEY=sua-chave-secreta-aqui

# Keycloak OIDC
KEYCLOAK_URL=http://keycloak.example.com
KEYCLOAK_REALM=ropa
KEYCLOAK_CLIENT_ID=ropa-web
KEYCLOAK_CLIENT_SECRET=seu-client-secret

# Desenvolvimento (ativar mock Keycloak)
KEYCLOAK_MOCK=1  # ou "true", "yes"
```

Veja `.env.example` para template completo.

---

## 🛠️ Uso da CLI

```bash
# Novo registro
python ropa.py novo

# Listar atividades
python ropa.py listar

# Ver detalhes
python ropa.py ver <id>

# Editar
python ropa.py editar <id>

# Validar completude
python ropa.py validar

# Popular com dados de exemplo
python ropa.py seed

# Exportar
python ropa.py exportar [json|csv|xlsx]

# Gerar relatório PDF
python ropa.py relatorio
```

---

## 📊 Estrutura de Dados

### Atividades de Tratamento
Cada registro inclui:
- Nome da atividade
- Finalidade do tratamento
- Base legal (Art. 7 LGPD)
- Categorias de titulares
- Tipos de dados processados
- Dados sensíveis? (Sim/Não)
- Destinatários
- Transferência internacional
- Prazo de retenção
- Medidas de segurança
- Unidade controladora
- Sistema SEI
- Observações

### Validação (Art. 37 LGPD)
Campos obrigatórios para completude mínima (80%):
- Nome da atividade
- Base legal
- Categorias de titulares
- Medidas de segurança
- Unidade controladora

---

## 🔑 Autenticação

### Com Keycloak Real
1. Configurar `KEYCLOAK_URL`, `KEYCLOAK_REALM`, `KEYCLOAK_CLIENT_ID`, `KEYCLOAK_CLIENT_SECRET`
2. Criar realm `ropa` e cliente `ropa-web` no Keycloak
3. Remover variável `KEYCLOAK_MOCK` ou defini-la como `0`/`false`

### Mock Keycloak (Desenvolvimento)
- Ativar `KEYCLOAK_MOCK=1`
- Roda como Blueprint Flask na mesma porta 5000
- URL: `http://localhost:5000/mock-kc`
- Usuários hardcoded (veja `keycloak_blueprint.py`)

---

## 📁 Estrutura do Projeto

```
ropa/
├── app.py                      # Aplicação Flask principal
├── ropa.py                     # CLI (linha de comando)
├── keycloak_blueprint.py       # Mock Keycloak (Blueprint)
├── keycloak_mock.py            # Mock Keycloak standalone (não usado)
├── gerar_roadmap.py            # Gera documento DOCX roadmap
├── requirements.txt            # Dependências Python
├── Dockerfile                  # Container Docker
├── Procfile                    # Heroku deployment
├── .env.example                # Template de variáveis de ambiente
├── start_dev.sh                # Script inicialização dev
├── setup_ropa.sh               # Setup script
│
├── templates/                  # Templates Jinja2
│   ├── base.html               # Base layout
│   ├── login.html              # Tela de login
│   ├── index.html              # Dashboard
│   ├── listar.html             # Tabela de atividades
│   ├── ver.html                # Detalhes + histórico
│   ├── form.html               # Criar/editar
│   └── validar.html            # Validação de completude
│
└── .claude/
    ├── launch.json             # Config Claude Code preview
    └── settings.local.json     # Configurações locais
```

---

## 🧪 Testes

Ativar mock Keycloak para testes sem infraestrutura real:

```bash
KEYCLOAK_MOCK=1 python app.py
```

Login na tela:
1. Clique em "Entrar com Keycloak"
2. Digite: `encarregado` / `123`
3. Dashboard carrega automaticamente

---

## 📋 Roadmap Técnico

Veja `Roadmap_Implantacao_RoPA.docx` para implementação em infraestrutura institucional:
- Arquitetura
- Cronograma
- Requisitos de produção
- Plano de continuidade

---

## 🔗 Referências

- **LGPD**: Lei 13.709/2018 - Lei Geral de Proteção de Dados
- **Art. 37 LGPD**: Obrigação de manter Registro de Atividades de Tratamento

- **Keycloak**: https://www.keycloak.org
- **Flask**: https://flask.palletsprojects.com
- **Bootstrap 5**: https://getbootstrap.com

---

## 👥 Contribuição

Para contribuir:
1. Criar branch: `git checkout -b feature/sua-feature`
2. Commit: `git commit -am "Add: sua feature"`
3. Push: `git push origin feature/sua-feature`
4. Pull Request

---



**Desenvolvido com ❤️ para LGPD Compliance**
