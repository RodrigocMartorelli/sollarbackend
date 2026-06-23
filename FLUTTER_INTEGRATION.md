## Integração Flutter ↔ Backend

### 1. Adicionar dependência http

```bash
flutter pub add http
```

### 2. Criar API Service

Crie arquivo: `lib/domain/services/api_service.dart`

```dart
import 'package:http/http.dart' as http;
import 'dart:convert';
import '../models/proposal.dart';

class ApiService {
  static const String baseUrl = 'http://localhost:8000';
  static String? _token;

  // ============ AUTH ============

  /// Registrar novo usuário
  static Future<Map<String, dynamic>?> register(String email, String password) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/auth/register'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'email': email,
          'password': password,
        }),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        print('Register error: ${response.body}');
        return null;
      }
    } catch (e) {
      print('Register exception: $e');
      return null;
    }
  }

  /// Login e obter token
  static Future<bool> login(String email, String password) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/auth/login'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'email': email,
          'password': password,
        }),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        _token = data['access_token'];
        print('Login successful, token: $_token');
        return true;
      } else {
        print('Login error: ${response.body}');
        return false;
      }
    } catch (e) {
      print('Login exception: $e');
      return false;
    }
  }

  // ============ PROPOSALS ============

  /// Salvar nova proposta
  static Future<Map<String, dynamic>?> createProposal(ProposalData proposal) async {
    if (_token == null) {
      print('No token, need to login first');
      return null;
    }

    try {
      final response = await http.post(
        Uri.parse('$baseUrl/proposals/'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $_token',
        },
        body: jsonEncode(proposal.toJson()),
      );

      if (response.statusCode == 200) {
        print('Proposal saved successfully');
        return jsonDecode(response.body);
      } else {
        print('Save proposal error: ${response.body}');
        return null;
      }
    } catch (e) {
      print('Save proposal exception: $e');
      return null;
    }
  }

  /// Listar propostas do usuário
  static Future<List<ProposalData>> listProposals() async {
    if (_token == null) {
      print('No token, need to login first');
      return [];
    }

    try {
      final response = await http.get(
        Uri.parse('$baseUrl/proposals/'),
        headers: {
          'Authorization': 'Bearer $_token',
        },
      );

      if (response.statusCode == 200) {
        final List data = jsonDecode(response.body);
        return data.map((p) => ProposalData.fromJson(p)).toList();
      } else {
        print('List proposals error: ${response.body}');
        return [];
      }
    } catch (e) {
      print('List proposals exception: $e');
      return [];
    }
  }

  /// Obter proposta por ID
  static Future<ProposalData?> getProposal(int id) async {
    if (_token == null) {
      print('No token, need to login first');
      return null;
    }

    try {
      final response = await http.get(
        Uri.parse('$baseUrl/proposals/$id'),
        headers: {
          'Authorization': 'Bearer $_token',
        },
      );

      if (response.statusCode == 200) {
        return ProposalData.fromJson(jsonDecode(response.body));
      } else {
        print('Get proposal error: ${response.body}');
        return null;
      }
    } catch (e) {
      print('Get proposal exception: $e');
      return null;
    }
  }

  /// Atualizar proposta
  static Future<Map<String, dynamic>?> updateProposal(int id, ProposalData proposal) async {
    if (_token == null) {
      print('No token, need to login first');
      return null;
    }

    try {
      final response = await http.put(
        Uri.parse('$baseUrl/proposals/$id'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $_token',
        },
        body: jsonEncode(proposal.toJson()),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        print('Update proposal error: ${response.body}');
        return null;
      }
    } catch (e) {
      print('Update proposal exception: $e');
      return null;
    }
  }

  /// Deletar proposta
  static Future<bool> deleteProposal(int id) async {
    if (_token == null) {
      print('No token, need to login first');
      return false;
    }

    try {
      final response = await http.delete(
        Uri.parse('$baseUrl/proposals/$id'),
        headers: {
          'Authorization': 'Bearer $_token',
        },
      );

      if (response.statusCode == 200) {
        print('Proposal deleted');
        return true;
      } else {
        print('Delete proposal error: ${response.body}');
        return false;
      }
    } catch (e) {
      print('Delete proposal exception: $e');
      return false;
    }
  }

  /// Limpar token (logout)
  static void logout() {
    _token = null;
    print('Logged out');
  }

  /// Verificar se está autenticado
  static bool isAuthenticated() {
    return _token != null;
  }

  /// Obter token atual
  static String? getToken() {
    return _token;
  }
}
```

### 3. Adicionar método toJson/fromJson ao ProposalData

Em `lib/domain/models/proposal.dart`:

```dart
extension ProposalDataJson on ProposalData {
  Map<String, dynamic> toJson() {
    return {
      'client_name': clientName,
      'cpf_cnpj': cpfCnpj,
      'phone': phone,
      'whatsapp': whatsapp,
      'contact_preference': contactPreference,
      'cep': cep,
      'street': street,
      'neighborhood': neighborhood,
      'house_number': houseNumber,
      'complement': complement,
      'logradouro': logradouro,
      'income': income,
      'average_bill': averageBill,
      'consumption': consumption,
      'peak_hours': peakHours,
      'codigo_cidade': codigoCidade,
'installation_codigo_cidade': installationCodigoCidade,
    };
  }

  static ProposalData fromJson(Map<String, dynamic> json) {
    return ProposalData(
      clientName: json['client_name'] ?? '',
      cpfCnpj: json['cpf_cnpj'],
      phone: json['phone'],
      whatsapp: json['whatsapp'],
      contactPreference: json['contact_preference'],
      cep: json['cep'],
      street: json['street'],
      neighborhood: json['neighborhood'],
      houseNumber: json['house_number'],
      complement: json['complement'],
      logradouro: json['logradouro'],
      income: json['income']?.toDouble(),
      averageBill: json['average_bill']?.toDouble(),
      consumption: json['consumption']?.toDouble(),
      peakHours: json['peak_hours'],
    );
  }
}
```

### 4. Usar no Flutter

#### Login Page (novo)
```dart
// Adicione botão de login na sua app
ApiService.login('user@example.com', 'password123');
```

#### Salvar Proposta
```dart
// Após preencher todos os dados
final body = widget.proposalData.toJson();
print(body);
await ApiService.createProposal(widget.proposalData);
Navigator.pop(context); // Voltar
```

#### Listar Propostas (Histórico)
```dart
final proposals = await ApiService.listProposals();
// Mostrar na tela
```

---

## Fluxo Completo

1. **Login** → Obter token
2. **Preencher dados** → No formulário (já funcionando)
3. **Salvar** → `ApiService.createProposal(data)`
4. **Ver histórico** → `ApiService.listProposals()`
5. **Editar** → `ApiService.updateProposal(id, data)`

---

## Próximos Passos

1. ✅ Backend criado
2. ⏳ Instalar PostgreSQL
3. ⏳ Rodar backend (python main.py)
4. ⏳ Testar endpoints no Swagger
5. ⏳ Integrar ApiService no Flutter
6. ⏳ Criar login page
7. ⏳ Conectar formulário ao backend
