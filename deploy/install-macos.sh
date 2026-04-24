#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# Instalador do RoPA em produção (macOS)
#
# Instala:
#   • .venv com todas as deps Python
#   • Diretório de dados em ~/Library/Application Support/ropa
#   • cloudflared (Cloudflare Tunnel) em ~/bin
#   • LaunchAgents para autostart (gunicorn + tunnel)
#   • ropa-ctl para gerenciamento
#
# Uso: ./deploy/install-macos.sh
# ─────────────────────────────────────────────────────────────────────────────
set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DATA_DIR="$HOME/Library/Application Support/ropa"
LAUNCH_DIR="$HOME/Library/LaunchAgents"
BIN_DIR="$HOME/bin"

echo "══════════════════════════════════════════════════════════════════"
echo "  RoPA — Instalação em produção (macOS)"
echo "══════════════════════════════════════════════════════════════════"
echo "  Repo:    $REPO_DIR"
echo "  Dados:   $DATA_DIR"
echo "  Agents:  $LAUNCH_DIR"
echo "══════════════════════════════════════════════════════════════════"

# 1. Python venv
echo ""
echo "→ [1/6] Criando ambiente Python virtual..."
cd "$REPO_DIR"
if [ ! -d .venv ]; then
    python3 -m venv .venv
fi
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -r requirements.txt
echo "  ✓ .venv pronto"

# 2. Data directory
echo ""
echo "→ [2/6] Criando diretório de dados..."
mkdir -p "$DATA_DIR/logs" "$DATA_DIR/exports"
if [ ! -f "$DATA_DIR/.env" ]; then
    SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")
    cat > "$DATA_DIR/.env" <<EOF
FLASK_SECRET_KEY=$SECRET
KEYCLOAK_MOCK=1
ROPA_DB_PATH="$DATA_DIR/ropa.db"
ROPA_DATA_DIR="$DATA_DIR"
EOF
    chmod 600 "$DATA_DIR/.env"
    echo "  ✓ .env gerado com FLASK_SECRET_KEY aleatório"
else
    echo "  · .env já existe, mantido"
fi

# 3. Wrapper scripts
echo ""
echo "→ [3/6] Instalando wrapper scripts..."
cat > "$DATA_DIR/start-gunicorn.sh" <<EOF
#!/bin/bash
set -e
set -a
source "$DATA_DIR/.env"
set +a
cd "$REPO_DIR"
exec "$REPO_DIR/.venv/bin/gunicorn" -c "$REPO_DIR/gunicorn_config.py" app:app
EOF
cat > "$DATA_DIR/start-tunnel.sh" <<EOF
#!/bin/bash
set -e
LOG_FILE="$DATA_DIR/logs/cloudflared.log"
for i in \$(seq 1 30); do
  if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/login 2>/dev/null | grep -qE "^(200|302|401)$"; then
    break
  fi
  sleep 2
done
exec "$BIN_DIR/cloudflared" tunnel --url http://127.0.0.1:8000 --logfile "\$LOG_FILE" --loglevel info --metrics 127.0.0.1:0 --no-autoupdate
EOF
chmod +x "$DATA_DIR/start-gunicorn.sh" "$DATA_DIR/start-tunnel.sh"
echo "  ✓ wrappers criados"

# 4. cloudflared
echo ""
echo "→ [4/6] Instalando cloudflared..."
mkdir -p "$BIN_DIR"
if [ ! -x "$BIN_DIR/cloudflared" ]; then
    ARCH=$(uname -m)
    if [ "$ARCH" = "arm64" ]; then
        URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-arm64.tgz"
    else
        URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-amd64.tgz"
    fi
    curl -L -s -o /tmp/cloudflared.tgz "$URL"
    tar -xzf /tmp/cloudflared.tgz -C "$BIN_DIR/"
    chmod +x "$BIN_DIR/cloudflared"
    echo "  ✓ cloudflared $("$BIN_DIR/cloudflared" --version 2>&1 | head -1 | awk '{print $3}')"
else
    echo "  · cloudflared já instalado"
fi

# 5. LaunchAgents
echo ""
echo "→ [5/6] Instalando LaunchAgents..."
mkdir -p "$LAUNCH_DIR"
for NAME in ropa.app ropa.tunnel; do
    sed -e "s|{{HOME}}|$HOME|g" -e "s|{{REPO_DIR}}|$REPO_DIR|g" \
        "$REPO_DIR/deploy/$NAME.plist.template" > "$LAUNCH_DIR/$NAME.plist"
    echo "  ✓ $NAME.plist"
done

# 6. ropa-ctl
echo ""
echo "→ [6/6] Finalizando..."
chmod +x "$REPO_DIR/ropa-ctl"
echo "  ✓ ropa-ctl pronto"

echo ""
echo "══════════════════════════════════════════════════════════════════"
echo "  ✅ Instalação concluída!"
echo "══════════════════════════════════════════════════════════════════"
echo ""
echo "  Próximos passos:"
echo ""
echo "    1. Iniciar serviços agora:"
echo "         $REPO_DIR/ropa-ctl start"
echo ""
echo "    2. Ver status e URL pública:"
echo "         $REPO_DIR/ropa-ctl status"
echo ""
echo "    3. Os serviços iniciarão automaticamente no próximo login."
echo ""
