"""
Mock Keycloak OIDC — Blueprint integrado ao Flask app.
Simula os endpoints OpenID Connect do Keycloak para prototipagem.
"""

import base64
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import time
from pathlib import Path

from flask import Blueprint, request, redirect, jsonify, render_template_string

kc = Blueprint("keycloak_mock", __name__, url_prefix="/mock-kc/realms/ropa")

ISSUER = None  # definido em register_mock_keycloak()
CLIENT_ID = "ropa-web"

# Storage compartilhado entre workers do gunicorn para authorization codes.
# Usa SQLite porque o dict em memória seria per-process (4 workers = 4 dicts).
_CODES_DB = None


def _init_codes_db():
    """Cria (se necessário) a tabela de pending codes no DB compartilhado."""
    global _CODES_DB
    data_dir = Path(os.environ.get("ROPA_DATA_DIR", Path(__file__).parent))
    data_dir.mkdir(parents=True, exist_ok=True)
    _CODES_DB = str(data_dir / "mock_kc_codes.db")
    with sqlite3.connect(_CODES_DB) as c:
        c.execute("""CREATE TABLE IF NOT EXISTS codes (
            code TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            created_at INTEGER NOT NULL
        )""")
        # Limpa codes com mais de 5 min (auth code TTL)
        c.execute("DELETE FROM codes WHERE created_at < ?", (int(time.time()) - 300,))


def _codes_put(code, username):
    with sqlite3.connect(_CODES_DB) as c:
        c.execute("INSERT INTO codes (code, username, created_at) VALUES (?, ?, ?)",
                  (code, username, int(time.time())))


def _codes_pop(code):
    """Consome um code (single-use): retorna username ou None."""
    with sqlite3.connect(_CODES_DB) as c:
        row = c.execute("SELECT username, created_at FROM codes WHERE code = ?", (code,)).fetchone()
        if not row:
            return None
        c.execute("DELETE FROM codes WHERE code = ?", (code,))
        # expira após 5 min
        if int(time.time()) - row[1] > 300:
            return None
        return row[0]

USERS = {
    "encarregado": {
        "password": "123",
        "sub": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
        "name": "Encarregado de Proteção de Dados",
        "email": "encarregado@example.org",
        "preferred_username": "encarregado",
        "given_name": "Encarregado",
        "family_name": "Dados",
        "roles": ["dpo", "admin", "ropa-editor"],
    },
    "admin": {
        "password": "123",
        "sub": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "name": "Administrador TI",
        "email": "admin@example.org",
        "preferred_username": "admin",
        "given_name": "Administrador",
        "family_name": "TI",
        "roles": ["admin", "ropa-editor"],
    },
    "usuario": {
        "password": "123",
        "sub": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
        "name": "Maria Silva",
        "email": "maria.silva@example.org",
        "preferred_username": "usuario",
        "given_name": "Maria",
        "family_name": "Silva",
        "roles": ["ropa-viewer"],
    },
}

JWT_SECRET = "mock-keycloak-jwt-secret-for-dev-only"


def _b64url(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _make_jwt(payload):
    header = {"alg": "HS256", "typ": "JWT"}
    h = _b64url(json.dumps(header).encode())
    p = _b64url(json.dumps(payload).encode())
    sig = hmac.new(JWT_SECRET.encode(), f"{h}.{p}".encode(), hashlib.sha256).digest()
    return f"{h}.{p}.{_b64url(sig)}"


def _make_tokens(user):
    now = int(time.time())
    common = {"iss": ISSUER, "sub": user["sub"], "aud": CLIENT_ID, "exp": now + 3600, "iat": now}
    id_payload = {
        **common, "auth_time": now, "nonce": secrets.token_hex(8),
        "name": user["name"], "email": user["email"],
        "preferred_username": user["preferred_username"],
        "given_name": user["given_name"], "family_name": user["family_name"],
        "realm_access": {"roles": user["roles"]},
    }
    access_payload = {**common, "scope": "openid email profile", "realm_access": {"roles": user["roles"]}}
    return {
        "access_token": _make_jwt(access_payload),
        "token_type": "Bearer",
        "expires_in": 3600,
        "id_token": _make_jwt(id_payload),
        "scope": "openid email profile",
    }


# ── Endpoints ─────────────────────────────────────────────────────────────────

@kc.route("/.well-known/openid-configuration")
def discovery():
    return jsonify({
        "issuer": ISSUER,
        "authorization_endpoint": f"{ISSUER}/protocol/openid-connect/auth",
        "token_endpoint": f"{ISSUER}/protocol/openid-connect/token",
        "userinfo_endpoint": f"{ISSUER}/protocol/openid-connect/userinfo",
        "end_session_endpoint": f"{ISSUER}/protocol/openid-connect/logout",
        "jwks_uri": f"{ISSUER}/protocol/openid-connect/certs",
        "response_types_supported": ["code"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["HS256"],
        "token_endpoint_auth_methods_supported": ["client_secret_post", "client_secret_basic"],
        "scopes_supported": ["openid", "email", "profile"],
        "grant_types_supported": ["authorization_code"],
    })


@kc.route("/protocol/openid-connect/certs")
def jwks():
    return jsonify({"keys": []})


LOGIN_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Login · Keycloak</title>
  <style>
    *{box-sizing:border-box;margin:0;padding:0}
    body{min-height:100vh;display:flex;align-items:center;justify-content:center;
         background:#f0f2f5;font-family:'Segoe UI',system-ui,sans-serif}
    .kc{width:420px;background:#fff;border-radius:8px;box-shadow:0 2px 12px rgba(0,0,0,.08);overflow:hidden}
    .kc-h{background:#1F3D7A;padding:1.5rem 2rem;text-align:center}
    .kc-h h1{color:#fff;font-size:1.1rem;font-weight:600}
    .kc-h p{color:rgba(255,255,255,.6);font-size:.75rem;margin-top:.3rem}
    .kc-tag{display:inline-block;background:#e9b949;color:#1a1a1a;font-size:.6rem;font-weight:700;
            padding:.15em .5em;border-radius:3px;text-transform:uppercase;letter-spacing:.05em;margin-top:.5rem}
    .kc-b{padding:2rem}
    .kc-b label{display:block;font-size:.8rem;font-weight:600;color:#444;margin-bottom:.3rem}
    .kc-b input{width:100%;padding:.6rem .75rem;border:1px solid #d0d5dd;border-radius:6px;
                font-size:.9rem;margin-bottom:1rem;outline:none;transition:border .15s}
    .kc-b input:focus{border-color:#1F3D7A}
    .kc-b button{width:100%;padding:.7rem;background:#1F3D7A;color:#fff;border:none;
                 border-radius:6px;font-size:.9rem;font-weight:600;cursor:pointer;transition:background .15s}
    .kc-b button:hover{background:#162d5b}
    .kc-err{background:#fef2f2;border:1px solid #fecaca;color:#991b1b;
            padding:.6rem .8rem;border-radius:6px;font-size:.8rem;margin-bottom:1rem}
    .kc-u{margin-top:1.5rem;padding-top:1rem;border-top:1px solid #eee}
    .kc-u h3{font-size:.7rem;text-transform:uppercase;letter-spacing:.05em;color:#aaa;margin-bottom:.5rem}
    .kc-u table{width:100%;font-size:.75rem;border-collapse:collapse}
    .kc-u td{padding:.3rem .5rem;border-bottom:1px solid #f5f5f5;color:#666}
    .kc-u td:first-child{font-weight:600;color:#333}
    .ul{cursor:pointer;color:#1F3D7A;text-decoration:underline}
  </style>
</head>
<body>
  <div class="kc">
    <div class="kc-h">
      <h1>Keycloak</h1>
      <p>Autenticacao Institucional</p>
      <div class="kc-tag">Simulacao para Prototipagem</div>
    </div>
    <div class="kc-b">
      {% if error %}<div class="kc-err">{{ error }}</div>{% endif %}
      <form method="post">
        <input type="hidden" name="redirect_uri" value="{{ redirect_uri }}"/>
        <input type="hidden" name="state" value="{{ state }}"/>
        <input type="hidden" name="nonce" value="{{ nonce }}"/>
        <label>Usuario</label>
        <input type="text" name="username" id="u" placeholder="Login de rede" autofocus/>
        <label>Senha</label>
        <input type="password" name="password" id="p" placeholder="Senha"/>
        <button type="submit">Entrar</button>
      </form>
      <div class="kc-u">
        <h3>Usuarios de teste (senha: 123)</h3>
        <table>
          {% for uname, u in users.items() %}
          <tr>
            <td><span class="ul" onclick="document.getElementById('u').value='{{uname}}';document.getElementById('p').value='123';">{{uname}}</span></td>
            <td>{{u.name}}</td>
            <td>{{u.roles|join(', ')}}</td>
          </tr>
          {% endfor %}
        </table>
      </div>
    </div>
  </div>
</body>
</html>"""


@kc.route("/protocol/openid-connect/auth", methods=["GET", "POST"])
def authorize():
    redirect_uri = request.args.get("redirect_uri", "") or request.form.get("redirect_uri", "")
    state = request.args.get("state", "") or request.form.get("state", "")
    nonce = request.args.get("nonce", "") or request.form.get("nonce", "")

    if request.method == "GET":
        return render_template_string(LOGIN_HTML,
            redirect_uri=redirect_uri, state=state, nonce=nonce, users=USERS, error=None)

    username = request.form.get("username", "").strip().lower()
    password = request.form.get("password", "")
    user = USERS.get(username)
    if not user or user["password"] != password:
        return render_template_string(LOGIN_HTML,
            redirect_uri=redirect_uri, state=state, nonce=nonce, users=USERS,
            error="Usuario ou senha invalidos.")

    code = secrets.token_urlsafe(32)
    _codes_put(code, username)
    sep = "&" if "?" in redirect_uri else "?"
    return redirect(f"{redirect_uri}{sep}code={code}&state={state}")


@kc.route("/protocol/openid-connect/token", methods=["POST"])
def token():
    code = request.form.get("code", "")
    username = _codes_pop(code)
    if not username or username not in USERS:
        return jsonify({"error": "invalid_grant"}), 400
    return jsonify(_make_tokens(USERS[username]))


@kc.route("/protocol/openid-connect/userinfo")
def userinfo():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return jsonify({"error": "unauthorized"}), 401
    try:
        payload_b64 = auth.split(" ", 1)[1].split(".")[1]
        payload_b64 += "=" * (4 - len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        sub = payload.get("sub", "")
    except Exception:
        return jsonify({"error": "invalid_token"}), 401
    for user in USERS.values():
        if user["sub"] == sub:
            return jsonify({k: user[k] for k in
                ("sub", "name", "email", "preferred_username", "given_name", "family_name")} |
                {"realm_access": {"roles": user["roles"]}})
    return jsonify({"error": "user_not_found"}), 404


@kc.route("/protocol/openid-connect/logout")
def logout():
    post_logout = request.args.get("post_logout_redirect_uri", "")
    return redirect(post_logout) if post_logout else ("<h3>Sessao encerrada</h3>", 200)


# ── Registro ──────────────────────────────────────────────────────────────────

def register_mock_keycloak(app, base_url="http://localhost:5000"):
    global ISSUER
    ISSUER = f"{base_url}/mock-kc/realms/ropa"
    _init_codes_db()
    app.register_blueprint(kc)
