# Inventory API Endpoints

## Base URL
```
http://localhost:8000/api/v1
```

## Endpoints

### 1. List Inventory Items (GET)
**Endpoint:** `GET /inventory`

**Query Parameters:**
- `page` (int, optional): Page number (default: 1)
- `per_page` (int, optional): Items per page (default: 10, max: 100)
- `search` (string, optional): Search by name or brand
- `type` (string, optional): Filter by type (e.g., "Cabo", "Placa Solar", etc.)

**Example Request:**
```bash
curl "http://localhost:8000/api/v1/inventory?page=1&per_page=10&search=Cabo&type=Cabo"
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "Cabo Solar 4mm²",
      "brand": "Siemens",
      "quantity": 150.5,
      "unit": "m",
      "type": "Cabo",
      "observations": "Estoque principal",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total": 50,
    "pages": 5
  }
}
```

---

### 2. Get Single Item (GET)
**Endpoint:** `GET /inventory/{id}`

**Path Parameters:**
- `id` (int, required): Item ID

**Example Request:**
```bash
curl "http://localhost:8000/api/v1/inventory/1"
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "Cabo Solar 4mm²",
    "brand": "Siemens",
    "quantity": 150.5,
    "unit": "m",
    "type": "Cabo",
    "observations": "Estoque principal",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
}
```

**Response (404 Not Found):**
```json
{
  "success": false,
  "detail": "Item not found"
}
```

---

### 3. Create Item (POST)
**Endpoint:** `POST /inventory`

**Request Body:**
```json
{
  "name": "Cabo Solar 6mm²",
  "brand": "Siemens",
  "quantity": 50,
  "unit": "m",
  "type": "Cabo",
  "observations": "Qualidade premium"
}
```

**Required Fields:**
- `name` (string): Product name (must be unique)
- `brand` (string): Brand name
- `quantity` (number): Quantity in stock (>= 0)
- `unit` (string): Unit of measurement (e.g., "m", "un")
- `type` (string): Product type

**Optional Fields:**
- `observations` (string): Additional notes

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/inventory" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Cabo Solar 6mm²",
    "brand": "Siemens",
    "quantity": 50,
    "unit": "m",
    "type": "Cabo",
    "observations": "Qualidade premium"
  }'
```

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "id": 11,
    "name": "Cabo Solar 6mm²",
    "brand": "Siemens",
    "quantity": 50,
    "unit": "m",
    "type": "Cabo",
    "observations": "Qualidade premium",
    "created_at": "2024-01-20T15:45:00Z",
    "updated_at": "2024-01-20T15:45:00Z"
  }
}
```

**Response (400 Bad Request):**
```json
{
  "success": false,
  "detail": "Product name already exists"
}
```

---

### 4. Update Item (PUT)
**Endpoint:** `PUT /inventory/{id}`

**Path Parameters:**
- `id` (int, required): Item ID

**Request Body (all fields optional):**
```json
{
  "brand": "New Brand",
  "quantity": 100,
  "unit": "m",
  "type": "Cabo",
  "observations": "Updated observations"
}
```

**Example Request:**
```bash
curl -X PUT "http://localhost:8000/api/v1/inventory/1" \
  -H "Content-Type: application/json" \
  -d '{
    "quantity": 200,
    "observations": "Stock updated"
  }'
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "Cabo Solar 4mm²",
    "brand": "Siemens",
    "quantity": 200,
    "unit": "m",
    "type": "Cabo",
    "observations": "Stock updated",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-20T16:00:00Z"
  }
}
```

**Response (404 Not Found):**
```json
{
  "success": false,
  "detail": "Item not found"
}
```

---

### 5. Delete Item (DELETE)
**Endpoint:** `DELETE /inventory/{id}`

**Path Parameters:**
- `id` (int, required): Item ID

**Example Request:**
```bash
curl -X DELETE "http://localhost:8000/api/v1/inventory/1"
```

**Response (204 No Content):**
```
(Empty response body)
```

**Response (404 Not Found):**
```json
{
  "success": false,
  "detail": "Item not found"
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "success": false,
  "detail": "Invalid input: quantity must be a positive number"
}
```

### 500 Internal Server Error
```json
{
  "success": false,
  "detail": "An error occurred while processing your request"
}
```

---

## Type Values (Allowed)
- `Cabo`
- `Placa Solar`
- `Inversor`
- `Estrutura`
- `Conector`
- `Proteção`
- `Caixa`
- `Aterramento`
- `Acessório`

## Unit Values (Common)
- `m` (meters)
- `un` (units)

---

## Rate Limiting
Currently no rate limiting implemented. May be added in future versions.

## Authentication
Currently no authentication required. Should be implemented for production.
