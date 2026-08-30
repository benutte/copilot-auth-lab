import os
import re
import base64
from functools import wraps
from flask import Flask, request, jsonify

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Dados fake por "formulário", simulando a estrutura real (ex: atendimento)
# ---------------------------------------------------------------------------
SAMPLE_FORMS = {
    "atendimento": [
        {"Nome": "João Silva", "Vagas": 5, "Status": "ativo", "Estado": "SP"},
        {"Nome": "Maria Souza", "Vagas": 3, "Status": "ativo", "Estado": "RJ"},
        {"Nome": "Carlos Lima", "Vagas": 0, "Status": "inativo", "Estado": "MG"},
        {"Nome": "Ana Paula", "Vagas": 8, "Status": "ativo", "Estado": "BA"},
        {"Nome": "Pedro Rocha", "Vagas": 2, "Status": "ativo", "Estado": "SP"},
        {"Nome": "Fernanda Dias", "Vagas": 1, "Status": "inativo", "Estado": "RJ"},
    ],
    "vagas": [
        {"Nome": "Analista PCD", "Vagas": 4, "Status": "ativo", "Estado": "SP"},
        {"Nome": "Estagiário", "Vagas": 2, "Status": "ativo", "Estado": "PR"},
        {"Nome": "Coordenador", "Vagas": 0, "Status": "inativo", "Estado": "SP"},
    ],
}


def parse_filter(q: str):
    """Interpreta algo como: Status=="ativo" AND Estado!="SP" """
    conditions = []
    if not q:
        return conditions
    q = q.strip().strip("()")
    parts = re.split(r"\s+AND\s+", q, flags=re.IGNORECASE)
    for part in parts:
        m = re.search(r'(\w+)\s*(==|!=)\s*"?([^"()]+?)"?\s*$', part.strip())
        if m:
            field, op, value = m.group(1), m.group(2), m.group(3).strip()
            conditions.append((field, op, value))
    return conditions


def apply_filter(records, conditions):
    result = []
    for r in records:
        match = True
        for field, op, value in conditions:
            record_value = str(r.get(field, ""))
            if op == "==" and record_value != value:
                match = False
            elif op == "!=" and record_value == value:
                match = False
        if match:
            result.append(r)
    return result


def project_fields(records, fields_param: str):
    """Interpreta algo como: values(Nome, Vagas, Status) ou Nome,Vagas,Status"""
    if not fields_param:
        return records
    cleaned = fields_param.replace("values(", "").replace(")", "")
    fields = [f.strip() for f in cleaned.split(",") if f.strip()]
    return [{f: r.get(f) for f in fields if f in r} for r in records]

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
    """Exige, ao mesmo tempo, Basic Auth válido E o header user-key correto."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        user_key = request.headers.get("user-key", "")

        basic_ok = check_basic_auth(auth_header)
        key_ok = user_key == VALID_API_KEY

        if not basic_ok and not key_ok:
            return jsonify({
                "error": "unauthorized",
                "message": "Faltam Basic Auth (Authorization) e o header user-key."
            }), 401

        if not basic_ok:
            return jsonify({
                "error": "unauthorized",
                "message": "Basic Auth ausente ou inválido (Authorization: Basic <base64 user:pass>)."
            }), 401

        if not key_ok:
            return jsonify({
                "error": "unauthorized",
                "message": "Header 'user-key' ausente ou inválido."
            }), 401

        return f(*args, **kwargs)
    return wrapper


@app.route("/", methods=["GET"])
def root():
    return jsonify({
        "service": "copilot-auth-lab",
        "status": "online",
        "docs": "Use GET /data com Basic Auth + header user-key.",
    })


@app.route("/data", methods=["GET"])
@require_dual_auth
def get_data():
    # Aceita query params livremente, apenas ecoa de volta no JSON
    query_params = request.args.to_dict()

    return jsonify({
        "message": "Autenticado com sucesso (Basic Auth + user-key).",
        "authenticated_user": VALID_USERNAME,
        "query_params_received": query_params,
        "sample_data": [
            {"id": 1, "name": "Item A", "value": 100},
            {"id": 2, "name": "Item B", "value": 250},
            {"id": 3, "name": "Item C", "value": 75},
        ],
    })


@app.route("/consulta/<form>", methods=["GET"])
@require_dual_auth
def consulta(form):
    q = request.args.get("q", "")
    fields_param = request.args.get("fields", "")
    diary_field_size = request.args.get("diaryFieldSize", "")

    dataset = SAMPLE_FORMS.get(form)
    if dataset is None:
        return jsonify({
            "error": "not_found",
            "message": f"Formulário '{form}' não encontrado.",
            "formularios_disponiveis": list(SAMPLE_FORMS.keys()),
        }), 404

    conditions = parse_filter(q)
    filtered = apply_filter(dataset, conditions)
    projected = project_fields(filtered, fields_param)

    return jsonify({
        "form": form,
        "query_recebida": q,
        "fields_recebidos": fields_param,
        "diaryFieldSize_recebido": diary_field_size,
        "total": len(projected),
        "values": projected,
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)