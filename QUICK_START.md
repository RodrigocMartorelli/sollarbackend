# 🚀 Backend Setup Rápido

## ✅ Estrutura criada em: `c:\Sollar\sollar_backend\`

```
sollar_backend/
├── main.py                 ← Rodar servidor aqui
├── requirements.txt        ← Dependências Python
├── .env.example           ← Copiar para .env
├── README.md              ← Instruções completas
├── FLUTTER_INTEGRATION.md ← Como conectar ao Flutter
├── .gitignore
└── app/
    ├── config.py          ← Configurações
    ├── database.py        ← Conexão BD
    ├── models.py          ← Tabelas BD
    ├── schemas.py         ← Validação Pydantic
    ├── security.py        ← JWT + Encriptação
    └── routes/
        ├── auth.py        ← Login/Register
        └── proposals.py    ← CRUD propostas
```

---

## 🎯 Passos Próximos

### 1. Instalar PostgreSQL
- **Windows**: https://www.postgresql.org/download/windows/
- Anotar password do `postgres` user
- Instalar pgAdmin (incluso)

### 2. Criar database
```bash
# Abrir pgAdmin ou psql
createdb sollar
```

### 3. Configurar .env
```bash
cd c:\Sollar\sollar_backend
copy .env.example .env
```

Editar `.env`:
```env
DATABASE_URL=postgresql://postgres:sua_password@localhost:5432/sollar
SECRET_KEY=mude-isso-para-algo-aleatorio-lungo
ENCRYPTION_KEY=sua-chave-de-encriptacao-32-bytes-mude
API_PORT=8000
```

### 4. Setup Python
```bash
# Criar venv
python -m venv venv

# Ativar
venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt
```

### 5. Rodar servidor
```bash
python main.py
```

Vai estar em: **http://localhost:8000**

---

## 🧪 Testar

### Swagger UI
Abrir: http://localhost:8000/docs

1. Clicar **"Try it out"** em `/auth/register`
2. Colocar email e password
3. Executar

4. Depois login em `/auth/login`
5. Copiar o token retornado

6. Autorizar (botão verde no topo) com o token
7. Criar proposta em `/proposals/` ✅

---

## 📱 Integração Flutter

Depois que backend estiver rodando:

1. Adicionar `import 'app/api_service.dart'` (que você vai criar)
2. Colocar o `ApiService` que está em `FLUTTER_INTEGRATION.md`
3. Usar:
   ```dart
   await ApiService.login('user@example.com', 'senha');
   await ApiService.createProposal(proposalData);
   ```

---

## 🔐 Segurança

✅ **Implementado:**
- Senhas com bcrypt (irreversível)
- JWT tokens com expiração
- CPF, telefone, endereço encriptados com AES-256
- CORS apenas para localhost em dev

⚠️ **Em Produção mudar:**
- `SECRET_KEY` para chave aleatória
- `ENCRYPTION_KEY` para chave segura
- `DATABASE_URL` para BD remota
- CORS para domínio específico

---

Avisa quando tiver PostgreSQL instalado! 🎉
