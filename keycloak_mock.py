#!/usr/bin/env python3
"""
Mock Keycloak OIDC — para prototipagem do RoPA.
Roda na porta 8080 simulando os endpoints OpenID Connect do Keycloak.
"""

import base64
import hashlib
import hmac
import json
import secrets
import time

from flask import Flask, request, redirect, jsonify, render_template_string

app = Flask(__name__)
app.secret_key = "mock-keycloak-dev"

REALM = "ropa"
ISSUER = f"http://localhost:8080/realms/{REALM}"
CLIENT_ID = "ropa-web"
CLIENT_SECRET = ""  # empty = public client (aceita qualquer)

# ── Usuários mock ─────────────────────────────────────────────────────────────
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

# Códigos de autorização pendentes: code -> user_data
_pending_codes = {}

# ── JWT simples (HMAC-SHA256) ─────────────────────────────────────────────────
JWT_SECRET = "mock-keycloak-jwt-secret-for-dev-only"


def _b64url(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _make_jwt(payload):
    header = {"alg": "HS256", "typ": "JWT"}
    h = _b64url(json.dumps(header).encode())
    p = _b64url(json.dumps(payload).encode())
    sig_input = f"{h}.{p}".encode()
    sig = hmac.new(JWT_SECRET.encode(), sig_input, hashlib.sha256).digest()
    return f"{h}.{p}.{_b64url(sig)}"


def _make_tokens(user):
    now = int(time.time())
    id_token_payload = {
        "iss": ISSUER,
        "sub": user["sub"],
        "aud": CLIENT_ID,
        "exp": now + 3600,
        "iat": now,
        "auth_time": now,
        "nonce": secrets.token_hex(8),
        "name": user["name"],
        "email": user["email"],
        "preferred_username": user["preferred_username"],
        "given_name": user["given_name"],
        "family_name": user["family_name"],
        "realm_access": {"roles": user["roles"]},
    }
    access_payload = {
        "iss": ISSUER,
        "sub": user["sub"],
        "aud": CLIENT_ID,
        "exp": now + 3600,
        "iat": now,
        "scope": "openid email profile",
        "realm_access": {"roles": user["roles"]},
    }
    return {
        "access_token": _make_jwt(access_payload),
        "token_type": "Bearer",
        "expires_in": 3600,
        "id_token": _make_jwt(id_token_payload),
        "scope": "openid email profile",
    }


# ── OIDC Discovery ───────────────────────────────────────────────────────────

@app.route(f"/realms/{REALM}/.well-known/openid-configuration")
def discovery():
    base = ISSUER
    return jsonify({
        "issuer": ISSUER,
        "authorization_endpoint": f"{base}/protocol/openid-connect/auth",
        "token_endpoint": f"{base}/protocol/openid-connect/token",
        "userinfo_endpoint": f"{base}/protocol/openid-connect/userinfo",
        "end_session_endpoint": f"{base}/protocol/openid-connect/logout",
        "jwks_uri": f"{base}/protocol/openid-connect/certs",
        "response_types_supported": ["code"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["HS256"],
        "token_endpoint_auth_methods_supported": ["client_secret_post", "client_secret_basic"],
        "scopes_supported": ["openid", "email", "profile"],
        "grant_types_supported": ["authorization_code"],
    })


@app.route(f"/realms/{REALM}/protocol/openid-connect/certs")
def jwks():
    return jsonify({"keys": []})


# ── Authorization Endpoint (tela de login) ────────────────────────────────────

LOGIN_HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Login · Keycloak (Mock)</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      background: #f0f2f5;
      font-family: 'Segoe UI', system-ui, sans-serif;
    }
    .kc-card {
      width: 420px;
      background: #fff;
      border-radius: 8px;
      box-shadow: 0 2px 12px rgba(0,0,0,0.08);
      overflow: hidden;
    }
    .kc-header {
      background: #1F3D7A;
      padding: 1.5rem 2rem;
      text-align: center;
    }
    .kc-header h1 {
      color: #fff;
      font-size: 1.1rem;
      font-weight: 600;
    }
    .kc-header p {
      color: rgba(255,255,255,0.6);
      font-size: 0.75rem;
      margin-top: 0.3rem;
    }
    .kc-mock-tag {
      display: inline-block;
      background: #e9b949;
      color: #1a1a1a;
      font-size: 0.6rem;
      font-weight: 700;
      padding: 0.15em 0.5em;
      border-radius: 3px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-top: 0.5rem;
    }
    .kc-body { padding: 2rem; }
    .kc-body label {
      display: block;
      font-size: 0.8rem;
      font-weight: 600;
      color: #444;
      margin-bottom: 0.3rem;
    }
    .kc-body input {
      width: 100%;
      padding: 0.6rem 0.75rem;
      border: 1px solid #d0d5dd;
      border-radius: 6px;
      font-size: 0.9rem;
      margin-bottom: 1rem;
      outline: none;
      transition: border 0.15s;
    }
    .kc-body input:focus { border-color: #1F3D7A; }
    .kc-body button {
      width: 100%;
      padding: 0.7rem;
      background: #1F3D7A;
      color: #fff;
      border: none;
      border-radius: 6px;
      font-size: 0.9rem;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.15s;
    }
    .kc-body button:hover { background: #162d5b; }
    .kc-error {
      background: #fef2f2;
      border: 1px solid #fecaca;
      color: #991b1b;
      padding: 0.6rem 0.8rem;
      border-radius: 6px;
      font-size: 0.8rem;
      margin-bottom: 1rem;
    }
    .kc-users {
      margin-top: 1.5rem;
      padding-top: 1rem;
      border-top: 1px solid #eee;
    }
    .kc-users h3 {
      font-size: 0.7rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: #aaa;
      margin-bottom: 0.5rem;
    }
    .kc-users table {
      width: 100%;
      font-size: 0.75rem;
      border-collapse: collapse;
    }
    .kc-users td {
      padding: 0.3rem 0.5rem;
      border-bottom: 1px solid #f5f5f5;
      color: #666;
    }
    .kc-users td:first-child { font-weight: 600; color: #333; }
    .kc-users .user-link {
      cursor: pointer;
      color: #1F3D7A;
      text-decoration: underline;
    }
  </style>
</head>
<body>
  <div class="kc-card">
    <div class="kc-header">
      <h1>Keycloak</h1>
      <p>Autenticacao Institucional</p>
      <div class="kc-mock-tag">Simulacao para Prototipagem</div>
    </div>
    <div class="kc-body">
      {% if error %}
      <div class="kc-error">{{ error }}</div>
      {% endif %}

      <form method="post">
        <input type="hidden" name="redirect_uri" value="{{ redirect_uri }}"/>
        <input type="hidden" name="state" value="{{ state }}"/>
        <input type="hidden" name="nonce" value="{{ nonce }}"/>
        <label>Usuario</label>
        <input type="text" name="username" id="username" placeholder="Login de rede" autofocus/>
        <label>Senha</label>
        <input type="password" name="password" placeholder="Senha"/>
        <button type="submit">Entrar</button>
      </form>

      <div class="kc-users">
        <h3>Usuarios de teste (senha: 123)</h3>
        <table>
          {% for uname, u in users.items() %}
          <tr>
            <td>
              <span class="user-link" onclick="document.getElementById('username').value='{{ uname }}';
                document.querySelector('input[type=password]').value='123';">
                {{ uname }}
              </span>
            </td>
            <td>{{ u.name }}</td>
            <td>{{ u.roles|join(', ') }}</td>
          </tr>
          {% endfor %}
        </table>
      </div>
    </div>
  </div>
</body>
</html>
"""


@app.route(f"/realms/{REALM}/protocol/openid-connect/auth", methods=["GET", "POST"])
def authorize():
    redirect_uri = request.args.get("redirect_uri", "") or request.form.get("redirect_uri", "")
    state = request.args.get("state", "") or request.form.get("state", "")
    nonce = request.args.get("nonce", "") or request.form.get("nonce", "")

    if request.method == "GET":
        return render_template_string(
            LOGIN_HTML,
            redirect_uri=redirect_uri,
            state=state,
            nonce=nonce,
            users=USERS,
            error=None,
        )

    username = request.form.get("username", "").strip().lower()
    password = request.form.get("password", "")

    user = USERS.get(username)
    if not user or user["password"] != password:
        return render_template_string(
            LOGIN_HTML,
            redirect_uri=redirect_uri,
            state=state,
            nonce=nonce,
            users=USERS,
            error="Usuario ou senha invalidos.",
        )

    code = secrets.token_urlsafe(32)
    _pending_codes[code] = user

    sep = "&" if "?" in redirect_uri else "?"
    return redirect(f"{redirect_uri}{sep}code={code}&state={state}")


# ── Token Endpoint ────────────────────────────────────────────────────────────

@app.route(f"/realms/{REALM}/protocol/openid-connect/token", methods=["POST"])
def token():
    code = request.form.get("code", "")
    user = _pending_codes.pop(code, None)
    if not user:
        return jsonify({"error": "invalid_grant"}), 400
    return jsonify(_make_tokens(user))


# ── Userinfo Endpoint ─────────────────────────────────────────────────────────

@app.route(f"/realms/{REALM}/protocol/openid-connect/userinfo")
def userinfo():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return jsonify({"error": "unauthorized"}), 401
    # Decodificar o JWT para extrair o sub e buscar o usuario
    token_str = auth.split(" ", 1)[1]
    try:
        payload_b64 = token_str.split(".")[1]
        payload_b64 += "=" * (4 - len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        sub = payload.get("sub", "")
    except Exception:
        return jsonify({"error": "invalid_token"}), 401

    for user in USERS.values():
        if user["sub"] == sub:
            return jsonify({
                "sub": user["sub"],
                "name": user["name"],
                "email": user["email"],
                "preferred_username": user["preferred_username"],
                "given_name": user["given_name"],
                "family_name": user["family_name"],
                "realm_access": {"roles": user["roles"]},
            })
    return jsonify({"error": "user_not_found"}), 404


# ── Logout Endpoint ───────────────────────────────────────────────────────────

@app.route(f"/realms/{REALM}/protocol/openid-connect/logout")
def logout():
    post_logout = request.args.get("post_logout_redirect_uri", "")
    if post_logout:
        return redirect(post_logout)
    return "<h3>Sessao encerrada</h3><p>Voce pode fechar esta aba.</p>"


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print()
    print("  Keycloak Mock")
    print("  http://localhost:8080")
    print()
    print("  Usuarios de teste (senha: 123):")
    for uname, u in USERS.items():
        print(f"    {uname:12s}  {u['name']}")
    print()
    app.run(host="0.0.0.0", port=8080, debug=True)
