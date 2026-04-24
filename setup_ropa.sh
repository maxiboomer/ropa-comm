#!/bin/bash
# ─────────────────────────────────────────────────────────────
#  RoPA — Setup local para Claude Code
#  Cria a estrutura do projeto e abre no Claude Code
# ─────────────────────────────────────────────────────────────

set -e

PROJECT_DIR="$HOME/ropa"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║   RoPA  ·  Setup local                           ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# 1. Criar pasta do projeto
mkdir -p "$PROJECT_DIR/exports"
echo "  ✔  Pasta criada: $PROJECT_DIR"

# 2. Copiar ropa.py se estiver na pasta atual
if [ -f "./ropa.py" ]; then
  cp ./ropa.py "$PROJECT_DIR/ropa.py"
  echo "  ✔  ropa.py copiado"
else
  echo "  ⚠  ropa.py não encontrado na pasta atual."
  echo "     Coloque o ropa.py na mesma pasta deste script e rode de novo."
  exit 1
fi

# 3. Criar requirements.txt
cat > "$PROJECT_DIR/requirements.txt" << 'EOF'
openpyxl>=3.1.0
reportlab>=4.0.0
EOF
echo "  ✔  requirements.txt criado"

# 4. Criar CLAUDE.md — instruções pro Claude Code
cat > "$PROJECT_DIR/CLAUDE.md" << 'EOF'
# RoPA — Contexto para Claude Code

## O que é este projeto
CLI em Python para gestão do Registro de Atividades de Tratamento (RoPA)
institucional, conforme LGPD (Lei 13.709/2018).

Desenvolvido pela Unidade de Proteção de Dados institucional.
Encarregado(a) de Proteção de Dados (DPO) designado(a) conforme Art. 41 LGPD.

## Stack
- Python 3.10+
- SQLite (banco local: ropa.db)
- openpyxl (export XLSX)
- reportlab (geração de PDF)

## Estrutura
```
ropa/
├── ropa.py              # script principal (CLI)
├── ropa.db       # banco SQLite (criado automaticamente)
├── requirements.txt
├── CLAUDE.md            # este arquivo
└── exports/             # JSON, CSV, XLSX, PDF gerados
```

## Comandos principais
```bash
python ropa.py seed          # popular com exemplos
python ropa.py novo          # cadastrar nova atividade
python ropa.py listar        # listar todas
python ropa.py ver <id>      # ver detalhes
python ropa.py editar <id>   # editar
python ropa.py validar       # checar completude (LGPD Art. 37)
python ropa.py exportar      # gerar JSON + CSV + XLSX
python ropa.py relatorio     # gerar PDF institucional
```

## Normas de referência
- LGPD — Lei 13.709/2018 (esp. Arts. 7, 11, 37, 46)
- Regulamentos e portarias internos da Instituição

## Como evoluir este projeto
- Adicionar autenticação de usuário (quem fez cada alteração)
- Integrar com SEI via API (quando disponível)
- Adicionar módulo de RIPD vinculado às atividades
- Interface web leve (Flask/FastAPI) para uso em rede interna
EOF
echo "  ✔  CLAUDE.md criado"

# 5. Criar ambiente virtual e instalar deps
echo ""
echo "  → Criando ambiente virtual..."
python3 -m venv "$PROJECT_DIR/.venv"
source "$PROJECT_DIR/.venv/bin/activate"
pip install --quiet openpyxl reportlab
echo "  ✔  Dependências instaladas"

# 6. Testar o script
echo ""
echo "  → Testando com seed..."
cd "$PROJECT_DIR"
python ropa.py seed
echo ""

# 7. Abrir no Claude Code
if command -v claude &> /dev/null; then
  echo "  → Abrindo no Claude Code..."
  claude "$PROJECT_DIR"
else
  echo "  ⚠  Claude Code não encontrado no PATH."
  echo "     Para abrir manualmente:"
  echo ""
  echo "     cd $PROJECT_DIR"
  echo "     source .venv/bin/activate"
  echo "     claude ."
  echo ""
fi

echo ""
echo "  ✔  Tudo pronto! Projeto em: $PROJECT_DIR"
echo ""
