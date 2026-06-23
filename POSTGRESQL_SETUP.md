# 🎯 Configurar Backend com PostgreSQL "sollar"

## ✅ Status
- ✅ Banco PostgreSQL "sollar" encontrado
- ✅ Backend configurado
- ⏳ Pronto para iniciar

## 📋 Configuração Realizada

### 1. Arquivo `.env` criado
```
DATABASE_URL=postgresql://postgres:sollarmaxx01@localhost:5432/sollar
SECRET_KEY=sollar-super-secreta-2024-...
API_PORT=8000
```

### 2. Banco de dados PostgreSQL
- **Host**: localhost
- **Porta**: 5432
- **Banco**: sollar
- **Usuário**: postgres

### 3. Tabelas que serão criadas
- `users` - Usuários (autenticação)
- `clients` - Clientes (novos!)
- `proposals` - Propostas

---

## 🚀 Como Rodar

### Passo 1: Instalar dependências
```bash
cd C:\Sollar\sollar_backend
pip install -r requirements.txt
```

### Passo 2: Testar conexão (opcional)
```bash
python test_db.py
```

Você deve ver:
```
✅ Conexão com PostgreSQL OK!
✅ Tabelas criadas/verificadas com sucesso!
✅ TUDO PRONTO!
```

### Passo 3: Rodar servidor
```bash
python main.py
```

Você verá:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### Passo 4: Acessar API
- 🌐 **API**: http://localhost:8000
- 📚 **Docs**: http://localhost:8000/docs
- 🏥 **Health**: http://localhost:8000/health

---

## 📊 Endpoints Disponíveis

### Autenticação
- `POST /api/v1/auth/register` - Registrar novo usuário
- `POST /api/v1/auth/login` - Fazer login

### Clientes (NOVO!)
- `POST /api/v1/clients/` - Criar cliente
- `GET /api/v1/clients/` - Listar clientes
- `GET /api/v1/clients/{id}` - Obter cliente
- `PUT /api/v1/clients/{id}` - Atualizar cliente
- `DELETE /api/v1/clients/{id}` - Deletar cliente

### Propostas
- `POST /api/v1/proposals/` - Criar proposta
- `GET /api/v1/proposals/` - Listar propostas
- etc...

---

## 🧪 Testar com cURL

### 1. Registrar usuário
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "usuario@example.com",
    "password": "SenhaForte123"
  }'
```

### 2. Fazer login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "usuario@example.com",
    "password": "SenhaForte123"
  }'
```

Você receberá um `access_token`. Copie!

### 3. Criar cliente
```bash
TOKEN="seu_token_aqui"

curl -X POST http://localhost:8000/api/v1/clients/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "João Silva",
    "email": "joao@example.com",
    "telefone": "11999999999",
    "cidade": "São Paulo",
    "estado": "SP"
  }'
```

### 4. Listar clientes
```bash
TOKEN="seu_token_aqui"

curl http://localhost:8000/api/v1/clients/ \
  -H "Authorization: Bearer $TOKEN"
```

---

## 💾 Dados Salvos no PostgreSQL

Todos os dados são salvos no banco PostgreSQL "sollar":

```sql
-- Ver clientes
SELECT * FROM clients;

-- Contar clientes
SELECT COUNT(*) FROM clients;

-- Ver usuários
SELECT * FROM users;
```

---

## ⚠️ Se Houver Erro

### Erro: "could not connect to server"
```
A conexão com PostgreSQL falhou.
Verifique:
- PostgreSQL está rodando?
- Credenciais corretas no .env?
- Porta 5432 está aberta?
```

### Erro: "database does not exist"
```
O banco "sollar" não existe.
Crie com:
CREATE DATABASE sollar;
```

### Erro: "authentication failed"
```
Senha incorreta.
Verifique em .env:
DATABASE_URL=postgresql://postgres:SENHA@localhost:5432/sollar
```

---

## 📱 Integração com Flutter

No app Flutter, use a URL:
```
http://localhost:8000/api/v1
```

Exemplo:
```dart
final baseUrl = 'http://localhost:8000/api/v1';

// Registrar
POST $baseUrl/auth/register

// Login
POST $baseUrl/auth/login

// Criar cliente
POST $baseUrl/clients/
Headers: Authorization: Bearer {token}
```

---

**Próximo**: Execute `python main.py` e acesse http://localhost:8000/docs! 🚀
