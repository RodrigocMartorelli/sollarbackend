# 📱 API de Clientes - Sollar Backend

## ✨ Novo: Gerenciamento de Clientes

Adicionamos suporte completo para **salvar, listar, atualizar e deletar clientes** com autenticação JWT.

## 📁 Estrutura Adicionada

```
app/
├── models.py              ← Adicionado: Modelo Client
├── schemas.py             ← Adicionado: Schemas de Client
└── routes/
    └── clients.py         ← NOVO: Rotas de clientes
```

## 📊 Banco de Dados - Tabela Clientes

```sql
CREATE TABLE clients (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,  -- Usuário que criou
    nome VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    telefone VARCHAR(20),
    whatsapp VARCHAR(20),
    cpf_cnpj VARCHAR(20) UNIQUE,
    cep VARCHAR(10),
    rua VARCHAR(255),
    numero VARCHAR(10),
    complemento VARCHAR(255),
    bairro VARCHAR(100),
    cidade VARCHAR(100),
    estado VARCHAR(2),
    data_criacao DATETIME DEFAULT NOW(),
    data_atualizacao DATETIME DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

## 📡 API Endpoints

### 1. Criar Cliente
```bash
POST /api/v1/clients/
Authorization: Bearer {token}
Content-Type: application/json

{
  "nome": "João Silva",
  "email": "joao@example.com",
  "telefone": "11999999999",
  "whatsapp": "11999999999",
  "cpf_cnpj": "12345678901",
  "cep": "01310100",
  "rua": "Avenida Paulista",
  "numero": "1000",
  "complemento": "Apt 123",
  "bairro": "Bela Vista",
  "cidade": "São Paulo",
  "estado": "SP"
}
```

**Resposta (201):**
```json
{
  "id": 1,
  "user_id": 1,
  "nome": "João Silva",
  "email": "joao@example.com",
  "telefone": "11999999999",
  "whatsapp": "11999999999",
  "cpf_cnpj": "12345678901",
  "cep": "01310100",
  "rua": "Avenida Paulista",
  "numero": "1000",
  "complemento": "Apt 123",
  "bairro": "Bela Vista",
  "cidade": "São Paulo",
  "estado": "SP",
  "data_criacao": "2026-04-27T12:00:00",
  "data_atualizacao": "2026-04-27T12:00:00"
}
```

### 2. Listar Clientes
```bash
GET /api/v1/clients/
Authorization: Bearer {token}
```

**Resposta (200):**
```json
[
  {
    "id": 1,
    "user_id": 1,
    "nome": "João Silva",
    "email": "joao@example.com",
    ...
  }
]
```

### 3. Obter Cliente
```bash
GET /api/v1/clients/{cliente_id}
Authorization: Bearer {token}
```

### 4. Atualizar Cliente
```bash
PUT /api/v1/clients/{cliente_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "telefone": "11991234567",
  "cidade": "Rio de Janeiro"
}
```

### 5. Deletar Cliente
```bash
DELETE /api/v1/clients/{cliente_id}
Authorization: Bearer {token}
```

**Resposta (204):** Sem conteúdo

## 🔐 Autenticação

Todos os endpoints de clientes requerem autenticação JWT.

### Passo 1: Registrar
```bash
POST /api/v1/auth/register
{
  "email": "usuario@example.com",
  "password": "senhaSegura123"
}
```

### Passo 2: Login
```bash
POST /api/v1/auth/login
{
  "email": "usuario@example.com",
  "password": "senhaSegura123"
}
```

**Resposta:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Passo 3: Usar Token
```bash
Authorization: Bearer {access_token}
```

## 🧪 Exemplos com cURL

### Registrar usuário
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email":"user@example.com",
    "password":"SenhaSegura123"
  }'
```

### Fazer login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email":"user@example.com",
    "password":"SenhaSegura123"
  }'
```

### Criar cliente (com token)
```bash
TOKEN="seu_token_aqui"

curl -X POST http://localhost:8000/api/v1/clients/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "nome":"João Silva",
    "email":"joao@example.com",
    "telefone":"11999999999",
    "cidade":"São Paulo",
    "estado":"SP"
  }'
```

### Listar clientes
```bash
TOKEN="seu_token_aqui"

curl -X GET http://localhost:8000/api/v1/clients/ \
  -H "Authorization: Bearer $TOKEN"
```

## 📖 Documentação Interativa

Acesse http://localhost:8000/docs para testar todos os endpoints diretamente no Swagger UI!

## 🚀 Como Rodar

```bash
cd C:\Sollar\sollar_backend

# Instalar dependências
pip install -r requirements.txt

# Executar servidor
python main.py
```

Servidor rodará em: http://0.0.0.0:8000

## 📊 Dados Salvos

Todos os clientes são salvos em banco de dados SQLite:
- **Arquivo**: `db/clientes.db` (dentro de sollar_backend)
- **Persiste**: Sim, dados são salvos permanentemente

## ✅ Características

- ✅ CRUD completo de clientes
- ✅ Autenticação com JWT
- ✅ Validação de email (único)
- ✅ Validação de CPF/CNPJ (único)
- ✅ Dados completos de endereço
- ✅ Timestamps (criação e atualização)
- ✅ Banco de dados SQLite
- ✅ CORS habilitado
- ✅ Documentação Swagger automática

---

**Status**: ✅ Pronto para usar!
