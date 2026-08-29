# copilot-auth-lab

API de laboratório que exige, na MESMA requisição:
1. **Basic Auth** (`Authorization: Basic base64(username:password)`)
2. **API Key adicional** (`user_key: <valor>`)

Se faltar qualquer um dos dois, retorna 401.

Credenciais padrão (mude via variáveis de ambiente no Render):
- username: `admin`
- password: `secret123`
- user_key: `chave-de-teste-123`

## 1. Subir no GitHub

```bash
cd copilot-auth-lab
git init
git add .
git commit -m "lab api dual auth"
```

Crie um repositório vazio no GitHub (github.com/new) e depois:

```bash
git remote add origin https://github.com/SEU_USUARIO/copilot-auth-lab.git
git branch -M main
git push -u origin main
```

## 2. Deploy no Render (grátis)

1. Crie conta em https://render.com (login com GitHub facilita).
2. No dashboard: **New +** → **Web Service**.
3. Conecte o repositório `copilot-auth-lab`.
4. Configurações:
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Instance Type**: Free
5. (Opcional) Em **Environment**, adicione variáveis para trocar as credenciais padrão:
   - `LAB_USERNAME`
   - `LAB_PASSWORD`
   - `LAB_API_KEY`
6. Clique em **Create Web Service**. Em 1-2 minutos você recebe uma URL tipo:
   `https://copilot-auth-lab.onrender.com`

> Nota: no plano free do Render, o serviço "dorme" após ~15 min sem uso e demora
> alguns segundos para acordar na primeira chamada seguinte. Normal para testes.

## 3. Testar com cURL

```bash
curl -u admin:secret123 \
  -H "user_key: chave-de-teste-123" \
  "https://copilot-auth-lab.onrender.com/data?status=ativo"
```

## 4. Testar com Python (igual ao seu modelo original)

```python
import requests
import base64

username = "admin"
password = "secret123"
api_key = "chave-de-teste-123"

credentials = f"{username}:{password}"
authorization = "Basic " + base64.b64encode(credentials.encode()).decode()

headers = {
    "Authorization": authorization,
    "user_key": api_key
}

response = requests.get(
    "https://copilot-auth-lab.onrender.com/data",
    headers=headers,
    params={"status": "ativo"}
)
print(response.status_code, response.json())
```

## 5. Usando no Microsoft Copilot Studio (Custom Connector)

No editor do Custom Connector (Power Platform):
- **Security** → tipo **Basic Authentication** (username/password).
- Como o Custom Connector nativo só suporta 1 esquema de auth por vez, o header
  `user_key` extra deve ser adicionado como **Default Header Parameter** fixo
  na definição de cada operação (aba "Request" → "+ Import from sample" ou
  adicionando um parâmetro do tipo Header chamado `user_key`, marcado como
  obrigatório).
- Isso reproduz exatamente o comportamento do seu modelo corporativo: Basic Auth
  cuida do usuário/senha, e o `user_key` vai como header adicional em toda chamada.
