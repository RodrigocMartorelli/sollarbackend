# Setup Backend

## 1. Instalar PostgreSQL

### Windows
- Download: https://www.postgresql.org/download/windows/
- Instalar (salvar password do superuser)
- Abrir pgAdmin ou psql

### Criar database
```sql
CREATE DATABASE sollar_db;
```

## 2. Setup do Backend

### Clonar/Navegar para pasta
```bash
cd c:\Sollar\sollar_backend
```

### Criar virtual environment
```bash
python -m venv venv
venv\Scripts\activate
```

### Instalar dependências
```bash
pip install -r requirements.txt
```

### Configurar .env
```bash
cp .env.example .env
```

Editar `.env` com seus dados:
```
DATABASE_URL=postgresql://user:password@localhost:5432/sollar_db
SECRET_KEY=sua-chave-super-secreta-aqui-mude-para-algo-aleatorio-em-prod
ENCRYPTION_KEY=sua-chave-de-encriptacao-32-bytes-mude-isso-tambem
API_PORT=8000
```

### Rodar servidor
```bash
python main.py
```

O servidor vai estar em: **http://localhost:8000**

### Documentação API
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 3. Endpoints Disponíveis

### Auth
- `POST /auth/register` - Registrar novo usuário
- `POST /auth/login` - Login e obter token

### Proposals (requer token)
- `POST /proposals/` - Criar proposta
- `GET /proposals/` - Listar propostas
- `GET /proposals/{id}` - Obter proposta
- `PUT /proposals/{id}` - Atualizar proposta
- `DELETE /proposals/{id}` - Deletar proposta

---

## 4. Como usar do Flutter

### Instalar pacote http
```bash
flutter pub add http
```

### Service para requisições
```dart
import 'package:http/http.dart' as http;

class ApiService {
  static const String baseUrl = 'http://localhost:8000';
  static String? _token;

  // Login
  static Future<String?> login(String email, String password) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'email': email,
        'password': password,
      }),
    );

    if (response.statusCode == 200) {
      _token = jsonDecode(response.body)['access_token'];
      return _token;
    }
    return null;
  }

  // Salvar proposta
  static Future<bool> saveProposal(ProposalData data) async {
    final response = await http.post(
      Uri.parse('$baseUrl/proposals/'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $_token',
      },
      body: jsonEncode(data.toJson()),
    );

    return response.statusCode == 200;
  }

  // Listar propostas
  static Future<List<ProposalData>> getProposals() async {
    final response = await http.get(
      Uri.parse('$baseUrl/proposals/'),
      headers: {
        'Authorization': 'Bearer $_token',
      },
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body) as List;
      return data.map((p) => ProposalData.fromJson(p)).toList();
    }
    return [];
  }
}
```

---

## 5. Segurança

- ✅ Senhas com bcrypt (hash)
- ✅ Tokens JWT com expiração
- ✅ CPF, telefone, endereço encriptados com AES-256 (Fernet)
- ✅ CORS configurado
- ⚠️ Mude `SECRET_KEY` e `ENCRYPTION_KEY` em produção!

---

## Troubleshooting

**"Connection refused"** - PostgreSQL não está rodando
```bash
# Windows
net start postgresql-x64-15
```

**"ModuleNotFoundError"** - Esqueceu de ativar venv
```bash
venv\Scripts\activate
```

**CORS error no Flutter** - Rode o backend com `allow_origins=["*"]` (já está configurado)

---

Próximos passos:
1. Instalar PostgreSQL
2. Criar database `sollar_db`
3. Configurar `.env`
4. Rodar `python main.py`
5. Testar no Swagger UI
6. Integrar no Flutter
