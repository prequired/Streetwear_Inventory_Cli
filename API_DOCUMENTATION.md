# 🚀 API Documentation

**REST API for Streetwear Inventory CLI**

## 📋 **Overview**

The Streetwear Inventory CLI includes a full REST API for external integrations, mobile apps, web interfaces, and automation tools.

### **Features**
- ✅ **Full CRUD Operations** on inventory items
- ✅ **Advanced Search** with filtering and pagination
- ✅ **Statistics & Analytics** endpoints
- ✅ **JSON Response Format** with consistent structure
- ✅ **CORS Support** for web applications
- ✅ **Error Handling** with meaningful HTTP status codes

## 🚀 **Starting the API Server**

### **Basic Usage**
```bash
# Start API on localhost:5000
inv api-server

# Start with custom host/port
inv api-server --host=0.0.0.0 --port=8080

# Start in debug mode
inv api-server --debug
```

### **Requirements**
```bash
# Install API dependencies
pip install flask flask-cors

# Or install with extras
pip install -e .[api]
```

### **Testing Connection**
```bash
# Test API endpoints
inv api-test

# Test custom host
inv api-test --host=localhost --port=8080
```

## 📚 **API Endpoints**

### **Base URL**: `http://localhost:5000`

---

## 📦 **Items Endpoints**

### **GET /api/items**
List all items with optional filtering and pagination.

**Query Parameters:**
- `brand` (string): Filter by brand name
- `condition` (string): Filter by condition (DS, VNDS, Used)
- `status` (string): Filter by status (available, sold, held)
- `location_id` (integer): Filter by location ID
- `ownership_type` (string): Filter by ownership (owned, consignment)
- `limit` (integer): Maximum items to return (default: 100)
- `offset` (integer): Number of items to skip (default: 0)

**Example Request:**
```bash
curl "http://localhost:5000/api/items?brand=nike&status=available&limit=10"
```

**Example Response:**
```json
{
  "items": [
    {
      "sku": "NIK001",
      "variant_id": 1,
      "brand": "nike",
      "model": "air jordan 1",
      "size": "10",
      "color": "chicago",
      "condition": "DS",
      "box_status": "box",
      "current_price": 250.00,
      "purchase_price": 200.00,
      "sold_price": null,
      "location": {
        "id": 1,
        "code": "HOME",
        "name": "Home Storage"
      },
      "status": "available",
      "ownership_type": "owned",
      "notes": null,
      "date_added": "2025-01-02T10:30:00",
      "sold_date": null,
      "consigner": null,
      "split_percentage": null,
      "photos": ["photo1.jpg", "photo2.jpg"],
      "primary_photo": "photo1.jpg"
    }
  ],
  "total": 1,
  "limit": 10,
  "offset": 0
}
```

---

### **GET /api/items/{sku}**
Get detailed information for a specific item.

**Parameters:**
- `sku` (string): Item SKU (e.g., NIK001)

**Example Request:**
```bash
curl "http://localhost:5000/api/items/NIK001"
```

**Example Response:**
```json
{
  "sku": "NIK001",
  "variant_id": 1,
  "brand": "nike",
  "model": "air jordan 1",
  "size": "10",
  "color": "chicago",
  "condition": "DS",
  "box_status": "box",
  "current_price": 250.00,
  "purchase_price": 200.00,
  "location": {
    "id": 1,
    "code": "HOME",
    "name": "Home Storage"
  },
  "status": "available",
  "ownership_type": "owned",
  "photos": [
    {
      "filename": "photo1.jpg",
      "size_mb": 2.1,
      "dimensions": "1200x800",
      "created_at": "2025-01-02T10:35:00"
    }
  ]
}
```

---

### **PUT /api/items/{sku}**
Update an existing item.

**Parameters:**
- `sku` (string): Item SKU to update

**Request Body:**
```json
{
  "current_price": 275.00,
  "status": "sold",
  "sold_price": 275.00,
  "notes": "Sold on eBay"
}
```

**Allowed Fields:**
- `current_price` (number)
- `status` (string): available, sold, held
- `notes` (string)
- `condition` (string): DS, VNDS, Used
- `location_id` (integer)
- `sold_price` (number)

**Example Request:**
```bash
curl -X PUT "http://localhost:5000/api/items/NIK001" \
  -H "Content-Type: application/json" \
  -d '{"current_price": 275.00, "status": "sold", "sold_price": 275.00}'
```

**Example Response:**
```json
{
  "sku": "NIK001",
  "current_price": 275.00,
  "status": "sold",
  "sold_price": 275.00,
  "date_added": "2025-01-02T10:30:00"
}
```

---

## 🔍 **Search Endpoint**

### **GET /api/search**
Search items with text query.

**Query Parameters:**
- `q` (string): Search query (searches brand, model, color, notes)
- `limit` (integer): Maximum results (default: 50)

**Example Request:**
```bash
curl "http://localhost:5000/api/search?q=jordan&limit=5"
```

**Example Response:**
```json
{
  "items": [
    {
      "sku": "NIK001",
      "brand": "nike",
      "model": "air jordan 1",
      "current_price": 250.00,
      "status": "available",
      "primary_photo": "photo1.jpg"
    }
  ],
  "total": 1,
  "query": "jordan"
}
```

---

## 📍 **Locations Endpoint**

### **GET /api/locations**
List all storage locations.

**Example Request:**
```bash
curl "http://localhost:5000/api/locations"
```

**Example Response:**
```json
{
  "locations": [
    {
      "id": 1,
      "code": "HOME",
      "type": "home",
      "name": "Home Storage",
      "created_date": "2025-01-01T10:00:00",
      "item_count": 25
    },
    {
      "id": 2,
      "code": "STORAGE",
      "type": "storage",
      "name": "Storage Unit",
      "created_date": "2025-01-01T10:05:00",
      "item_count": 15
    }
  ]
}
```

---

## 👥 **Consigners Endpoint**

### **GET /api/consigners**
List all consigners with statistics.

**Example Request:**
```bash
curl "http://localhost:5000/api/consigners"
```

**Example Response:**
```json
{
  "consigners": [
    {
      "id": 1,
      "name": "John Doe",
      "phone": "(555) 123-4567",
      "email": "john@example.com",
      "default_split_percentage": 70,
      "created_date": "2025-01-01T10:00:00",
      "stats": {
        "total_items": 10,
        "available_items": 8,
        "sold_items": 2
      }
    }
  ]
}
```

---

## 📊 **Statistics Endpoint**

### **GET /api/stats**
Get comprehensive inventory statistics.

**Example Request:**
```bash
curl "http://localhost:5000/api/stats"
```

**Example Response:**
```json
{
  "inventory": {
    "total_items": 50,
    "available_items": 42,
    "sold_items": 6,
    "held_items": 2,
    "owned_items": 35,
    "consignment_items": 15
  },
  "values": {
    "available_value": 12500.00,
    "sold_value": 1650.00
  },
  "brands": {
    "nike": 20,
    "adidas": 8,
    "supreme": 12,
    "jordan": 10
  },
  "photos": {
    "total_files": 125,
    "total_size_mb": 450.2,
    "directories": 45
  },
  "generated_at": "2025-01-02T15:30:00"
}
```

---

## 🔗 **Webhook Endpoint**

### **POST /api/webhook/item-updated**
Webhook endpoint for external integrations.

**Request Body:**
```json
{
  "event": "item_updated",
  "sku": "NIK001",
  "changes": {
    "status": "sold",
    "sold_price": 275.00
  },
  "timestamp": "2025-01-02T15:30:00"
}
```

**Example Response:**
```json
{
  "status": "received",
  "webhook_id": "2025-01-02T15:30:00"
}
```

---

## ⚠️ **Error Handling**

### **HTTP Status Codes**
- `200` - Success
- `400` - Bad Request (invalid parameters)
- `404` - Not Found (item/resource doesn't exist)
- `500` - Internal Server Error

### **Error Response Format**
```json
{
  "error": "Item with SKU 'INVALID001' not found"
}
```

### **Common Errors**
- **404**: Item not found
- **400**: Invalid request parameters
- **500**: Database connection issues

---

## 🛠️ **Client Code Generation**

### **Generate API Clients**
```bash
# Python client
inv generate-api-client python --output=client.py

# JavaScript client
inv generate-api-client javascript --output=client.js

# cURL examples
inv generate-api-client curl --output=examples.sh
```

### **Python Client Example**
```python
from client import InventoryAPIClient

# Initialize client
client = InventoryAPIClient("http://localhost:5000")

# Get all Nike items
nike_items = client.get_items(brand="nike")

# Search for Air Jordan
results = client.search_items("air jordan")

# Update item price
client.update_item("NIK001", {"current_price": 275.00})
```

### **JavaScript Client Example**
```javascript
const client = new InventoryAPIClient("http://localhost:5000");

// Get inventory statistics
const stats = await client.getStats();
console.log(`Total items: ${stats.inventory.total_items}`);

// Search items
const results = await client.searchItems("supreme");
console.log(`Found ${results.items.length} Supreme items`);
```

---

## 🔒 **Security Considerations**

### **Development vs Production**
- **Development**: API runs without authentication
- **Production**: Consider adding API key authentication

### **CORS Configuration**
- CORS is enabled for all origins by default
- Configure specific origins for production use

### **Rate Limiting**
- No rate limiting by default
- Consider adding rate limiting for production APIs

---

## 🧪 **Testing the API**

### **Using curl**
```bash
# Test API health
curl "http://localhost:5000/"

# Get items
curl "http://localhost:5000/api/items"

# Search
curl "http://localhost:5000/api/search?q=nike"

# Update item
curl -X PUT "http://localhost:5000/api/items/NIK001" \
  -H "Content-Type: application/json" \
  -d '{"current_price": 275.00}'
```

### **Using the built-in tester**
```bash
# Test all endpoints
inv api-test

# Test specific host
inv api-test --host=localhost --port=8080
```

---

## 🔧 **Configuration**

### **API Server Settings**
```yaml
# config.yaml
api:
  host: "127.0.0.1"
  port: 5000
  debug: false
  cors_origins: ["*"]
```

### **Environment Variables**
```bash
export API_HOST="0.0.0.0"
export API_PORT="8080"
export API_DEBUG="true"
```

---

**🎉 Happy integrating with your streetwear inventory API!**