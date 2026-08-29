import os
import base64
from functools import wraps
from flask import Flask, request, jsonify

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Credenciais de laboratório (fixas via variáveis de ambiente no Render)
# ---------------------------------------------------------------------------
VALID_USERNAME = os.environ.get("LAB_USERNAME", "admin")
VALID_PASSWORD = os.environ.get("LAB_PASSWORD", "secret123")
VALID_API_KEY = os.environ.get("LAB_API_KEY", "chave-de-teste-123")


def check_basic_auth(auth_header: str) -> bool:
    """Valida o header Authorization: Basic <base64(user:pass)>."""
    if not auth_header or not auth_header.startswith("Basic "):
        return False
    encoded = auth_header.split(" ", 1)[1]
    try:
        decoded = base64.b64decode(encoded).decode("utf-8")
        username, password = decoded.split(":", 1)
    except Exception:
        return False
    return username == VALID_USERNAME and password == VALID_PASSWORD


def require_dual_auth(f):
    """Exige, ao mesmo tempo, Basic Auth válido E o header user_key correto."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        user_key = request.headers.get("user-key", "")

        basic_ok = check_basic_auth(auth_header)
        key_ok = user_key == VALID_API_KEY

        if not basic_ok and not key_ok:
            return jsonify({
                "error": "unauthorized",
                "message": "Faltam Basic Auth (Authorization) e o header user_key."
            }), 401

        if not basic_ok:
            return jsonify({
                "error": "unauthorized",
                "message": "Basic Auth ausente ou inválido (Authorization: Basic <base64 user:pass>)."
            }), 401

        if not key_ok:
            return jsonify({
                "error": "unauthorized",
                "message": "Header 'user_key' ausente ou inválido."
            }), 401

        return f(*args, **kwargs)
    return wrapper


@app.route("/", methods=["GET"])
def root():
    return jsonify({
        "service": "copilot-auth-lab",
        "status": "online",
        "docs": "Use GET /data com Basic Auth + header user_key.",
    })


@app.route("/data", methods=["GET"])
@require_dual_auth
def get_data():
    # Aceita query params livremente, apenas ecoa de volta no JSON
    query_params = request.args.to_dict()

    return jsonify({
        "message": "Autenticado com sucesso (Basic Auth + user_key).",
        "authenticated_user": VALID_USERNAME,
        "query_params_received": query_params,
        "sample_data": [
            {"id": 1, "name": "Item A", "value": 100},
            {"id": 2, "name": "Item B", "value": 250},
            {"id": 3, "name": "Item C", "value": 75},
        ],
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
