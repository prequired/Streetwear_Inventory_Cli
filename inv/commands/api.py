"""API server management commands"""

import click
import json
import requests
from pathlib import Path

from ..api.server import create_api_server, FLASK_AVAILABLE
from ..utils.database_init import with_database


@click.command()
@with_database
@click.option('--host', default='127.0.0.1', help='Host to bind to')
@click.option('--port', default=5000, type=int, help='Port to bind to')
@click.option('--debug', is_flag=True, help='Enable debug mode')
def api_server(host, port, debug):
    """Start the REST API server
    
    Usage:
      inv api-server
      inv api-server --host=0.0.0.0 --port=8080
      inv api-server --debug
    
    The API provides endpoints for external integrations:
      - GET /api/items - List items with filtering
      - GET /api/items/<sku> - Get specific item
      - PUT /api/items/<sku> - Update item
      - GET /api/locations - List locations
      - GET /api/consigners - List consigners
      - GET /api/search?q=<query> - Search items
      - GET /api/stats - Inventory statistics
    """
    
    if not FLASK_AVAILABLE:
        click.echo("❌ Flask is required to run the API server")
        click.echo("Install with: pip install flask flask-cors")
        return
    
    try:
        click.echo(f"🚀 Starting Streetwear Inventory API server...")
        click.echo(f"   Host: {host}")
        click.echo(f"   Port: {port}")
        click.echo(f"   Debug: {debug}")
        click.echo(f"   Base URL: http://{host}:{port}")
        click.echo()
        click.echo("📚 API Endpoints:")
        click.echo("   GET  /api/items")
        click.echo("   GET  /api/items/<sku>")
        click.echo("   PUT  /api/items/<sku>")
        click.echo("   GET  /api/locations")
        click.echo("   GET  /api/consigners")
        click.echo("   GET  /api/search?q=<query>")
        click.echo("   GET  /api/stats")
        click.echo()
        click.echo("Press Ctrl+C to stop the server")
        
        api = create_api_server(debug=debug)
        api.run(host=host, port=port)
        
    except KeyboardInterrupt:
        click.echo("\n👋 API server stopped")
    except Exception as e:
        click.echo(f"❌ Error starting API server: {e}")


@click.command(name='api-test')
@with_database
@click.option('--host', default='127.0.0.1', help='API server host')
@click.option('--port', default=5000, type=int, help='API server port')
def api_test(host, port):
    """Test API server connectivity and endpoints
    
    Usage:
      inv api-test
      inv api-test --host=localhost --port=8080
    """
    
    base_url = f"http://{host}:{port}"
    
    try:
        click.echo(f"🧪 Testing API server at {base_url}")
        click.echo("-" * 50)
        
        # Test index endpoint
        click.echo("Testing GET / ...")
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            click.echo("✅ Index endpoint working")
            data = response.json()
            click.echo(f"   API: {data.get('name')} v{data.get('version')}")
        else:
            click.echo(f"❌ Index endpoint failed: {response.status_code}")
            return
        
        # Test stats endpoint
        click.echo("\nTesting GET /api/stats ...")
        response = requests.get(f"{base_url}/api/stats", timeout=5)
        if response.status_code == 200:
            click.echo("✅ Stats endpoint working")
            data = response.json()
            inventory = data.get('inventory', {})
            click.echo(f"   Total items: {inventory.get('total_items', 0)}")
            click.echo(f"   Available: {inventory.get('available_items', 0)}")
            click.echo(f"   Sold: {inventory.get('sold_items', 0)}")
        else:
            click.echo(f"❌ Stats endpoint failed: {response.status_code}")
        
        # Test items endpoint
        click.echo("\nTesting GET /api/items ...")
        response = requests.get(f"{base_url}/api/items?limit=5", timeout=5)
        if response.status_code == 200:
            click.echo("✅ Items endpoint working")
            data = response.json()
            items = data.get('items', [])
            click.echo(f"   Returned {len(items)} items (limit=5)")
            if items:
                first_item = items[0]
                click.echo(f"   Sample item: {first_item.get('sku')} - {first_item.get('brand')} {first_item.get('model')}")
        else:
            click.echo(f"❌ Items endpoint failed: {response.status_code}")
        
        # Test locations endpoint
        click.echo("\nTesting GET /api/locations ...")
        response = requests.get(f"{base_url}/api/locations", timeout=5)
        if response.status_code == 200:
            click.echo("✅ Locations endpoint working")
            data = response.json()
            locations = data.get('locations', [])
            click.echo(f"   Found {len(locations)} locations")
        else:
            click.echo(f"❌ Locations endpoint failed: {response.status_code}")
        
        # Test search endpoint
        click.echo("\nTesting GET /api/search ...")
        response = requests.get(f"{base_url}/api/search?q=nike", timeout=5)
        if response.status_code == 200:
            click.echo("✅ Search endpoint working")
            data = response.json()
            items = data.get('items', [])
            click.echo(f"   Search for 'nike' returned {len(items)} items")
        else:
            click.echo(f"❌ Search endpoint failed: {response.status_code}")
        
        click.echo("\n🎉 API server test completed!")
        
    except requests.exceptions.ConnectionError:
        click.echo(f"❌ Could not connect to API server at {base_url}")
        click.echo("   Make sure the server is running with: inv api-server")
    except requests.exceptions.Timeout:
        click.echo(f"❌ Timeout connecting to API server at {base_url}")
    except Exception as e:
        click.echo(f"❌ Error testing API: {e}")


@click.command(name='api-docs')
def api_docs():
    """Show API documentation
    
    Usage:
      inv api-docs
    """
    
    click.echo("📚 Streetwear Inventory API Documentation")
    click.echo("=" * 50)
    
    click.echo("\n🚀 Starting the API Server:")
    click.echo("  inv api-server                    # Start on 127.0.0.1:5000")
    click.echo("  inv api-server --host=0.0.0.0     # Allow external connections")
    click.echo("  inv api-server --port=8080        # Use custom port")
    click.echo("  inv api-server --debug            # Enable debug mode")
    
    click.echo("\n📋 Available Endpoints:")
    
    endpoints = [
        {
            'method': 'GET',
            'path': '/',
            'description': 'API information and available endpoints'
        },
        {
            'method': 'GET',
            'path': '/api/items',
            'description': 'List items with optional filtering',
            'params': 'brand, condition, status, location_id, ownership_type, limit, offset'
        },
        {
            'method': 'GET',
            'path': '/api/items/<sku>',
            'description': 'Get specific item by SKU including photos'
        },
        {
            'method': 'PUT',
            'path': '/api/items/<sku>',
            'description': 'Update item fields (price, status, notes, etc.)'
        },
        {
            'method': 'GET',
            'path': '/api/locations',
            'description': 'List all locations with item counts'
        },
        {
            'method': 'GET',
            'path': '/api/consigners',
            'description': 'List all consigners with statistics'
        },
        {
            'method': 'GET',
            'path': '/api/search',
            'description': 'Search items by text query',
            'params': 'q (query), limit'
        },
        {
            'method': 'GET',
            'path': '/api/stats',
            'description': 'Inventory statistics and summaries'
        },
        {
            'method': 'POST',
            'path': '/api/webhook/item-updated',
            'description': 'Webhook endpoint for external integrations'
        }
    ]
    
    for endpoint in endpoints:
        click.echo(f"\n  {endpoint['method']} {endpoint['path']}")
        click.echo(f"      {endpoint['description']}")
        if 'params' in endpoint:
            click.echo(f"      Parameters: {endpoint['params']}")
    
    click.echo("\n💡 Example Usage:")
    click.echo("  # Get all Nike items")
    click.echo("  curl 'http://localhost:5000/api/items?brand=nike'")
    click.echo()
    click.echo("  # Search for Air Jordan")
    click.echo("  curl 'http://localhost:5000/api/search?q=air+jordan'")
    click.echo()
    click.echo("  # Get inventory statistics")
    click.echo("  curl 'http://localhost:5000/api/stats'")
    click.echo()
    click.echo("  # Update item price")
    click.echo("  curl -X PUT -H 'Content-Type: application/json' \\")
    click.echo("       -d '{\"current_price\": 150}' \\")
    click.echo("       'http://localhost:5000/api/items/NIK001'")
    
    click.echo("\n🔧 Testing:")
    click.echo("  inv api-test                      # Test all endpoints")
    click.echo("  inv api-test --host=localhost     # Test custom host")
    
    click.echo("\n📦 Requirements:")
    click.echo("  pip install flask flask-cors")
    
    click.echo("\n🔒 Security Notes:")
    click.echo("  - API runs without authentication by default")
    click.echo("  - Only bind to 127.0.0.1 for production unless needed")
    click.echo("  - Consider adding API keys for production use")


@click.command(name='generate-api-client')
@click.argument('language', type=click.Choice(['python', 'javascript', 'curl']))
@click.option('--output', help='Output file path')
@click.option('--host', default='localhost', help='API host')
@click.option('--port', default=5000, type=int, help='API port')
def generate_api_client(language, output, host, port):
    """Generate API client code
    
    Usage:
      inv generate-api-client python
      inv generate-api-client javascript --output=client.js
      inv generate-api-client curl --output=api_examples.sh
    """
    
    base_url = f"http://{host}:{port}"
    
    if language == 'python':
        client_code = f'''"""
Python client for Streetwear Inventory API
Generated automatically - modify as needed
"""

import requests
from typing import Optional, Dict, List, Any


class InventoryAPIClient:
    """Python client for Streetwear Inventory API"""
    
    def __init__(self, base_url="{base_url}"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
    
    def get_items(self, brand=None, condition=None, status='available', 
                  location_id=None, ownership_type=None, limit=100, offset=0):
        """Get items with optional filtering"""
        params = {{
            'brand': brand,
            'condition': condition,
            'status': status,
            'location_id': location_id,
            'ownership_type': ownership_type,
            'limit': limit,
            'offset': offset
        }}
        # Remove None values
        params = {{k: v for k, v in params.items() if v is not None}}
        
        response = self.session.get(f"{{self.base_url}}/api/items", params=params)
        response.raise_for_status()
        return response.json()
    
    def get_item(self, sku: str):
        """Get single item by SKU"""
        response = self.session.get(f"{{self.base_url}}/api/items/{{sku}}")
        response.raise_for_status()
        return response.json()
    
    def update_item(self, sku: str, data: Dict[str, Any]):
        """Update item"""
        response = self.session.put(
            f"{{self.base_url}}/api/items/{{sku}}", 
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def search_items(self, query: str, limit=50):
        """Search items"""
        params = {{'q': query, 'limit': limit}}
        response = self.session.get(f"{{self.base_url}}/api/search", params=params)
        response.raise_for_status()
        return response.json()
    
    def get_locations(self):
        """Get all locations"""
        response = self.session.get(f"{{self.base_url}}/api/locations")
        response.raise_for_status()
        return response.json()
    
    def get_consigners(self):
        """Get all consigners"""
        response = self.session.get(f"{{self.base_url}}/api/consigners")
        response.raise_for_status()
        return response.json()
    
    def get_stats(self):
        """Get inventory statistics"""
        response = self.session.get(f"{{self.base_url}}/api/stats")
        response.raise_for_status()
        return response.json()


# Example usage
if __name__ == "__main__":
    client = InventoryAPIClient()
    
    # Get all Nike items
    nike_items = client.get_items(brand="nike")
    print(f"Found {{len(nike_items['items'])}} Nike items")
    
    # Search for Air Jordan
    jordan_results = client.search_items("air jordan")
    print(f"Found {{len(jordan_results['items'])}} Air Jordan items")
    
    # Get statistics
    stats = client.get_stats()
    print(f"Total inventory: {{stats['inventory']['total_items']}} items")
'''
    
    elif language == 'javascript':
        client_code = f'''/**
 * JavaScript client for Streetwear Inventory API
 * Generated automatically - modify as needed
 */

class InventoryAPIClient {{
    constructor(baseUrl = "{base_url}") {{
        this.baseUrl = baseUrl.replace(/\\/$/, '');
    }}
    
    async getItems(options = {{}}) {{
        const {{
            brand,
            condition,
            status = 'available',
            locationId,
            ownershipType,
            limit = 100,
            offset = 0
        }} = options;
        
        const params = new URLSearchParams();
        if (brand) params.append('brand', brand);
        if (condition) params.append('condition', condition);
        if (status) params.append('status', status);
        if (locationId) params.append('location_id', locationId);
        if (ownershipType) params.append('ownership_type', ownershipType);
        params.append('limit', limit);
        params.append('offset', offset);
        
        const response = await fetch(`${{this.baseUrl}}/api/items?${{params}}`);
        if (!response.ok) throw new Error(`HTTP ${{response.status}}`);
        return response.json();
    }}
    
    async getItem(sku) {{
        const response = await fetch(`${{this.baseUrl}}/api/items/${{sku}}`);
        if (!response.ok) throw new Error(`HTTP ${{response.status}}`);
        return response.json();
    }}
    
    async updateItem(sku, data) {{
        const response = await fetch(`${{this.baseUrl}}/api/items/${{sku}}`, {{
            method: 'PUT',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify(data)
        }});
        if (!response.ok) throw new Error(`HTTP ${{response.status}}`);
        return response.json();
    }}
    
    async searchItems(query, limit = 50) {{
        const params = new URLSearchParams({{ q: query, limit }});
        const response = await fetch(`${{this.baseUrl}}/api/search?${{params}}`);
        if (!response.ok) throw new Error(`HTTP ${{response.status}}`);
        return response.json();
    }}
    
    async getLocations() {{
        const response = await fetch(`${{this.baseUrl}}/api/locations`);
        if (!response.ok) throw new Error(`HTTP ${{response.status}}`);
        return response.json();
    }}
    
    async getConsigners() {{
        const response = await fetch(`${{this.baseUrl}}/api/consigners`);
        if (!response.ok) throw new Error(`HTTP ${{response.status}}`);
        return response.json();
    }}
    
    async getStats() {{
        const response = await fetch(`${{this.baseUrl}}/api/stats`);
        if (!response.ok) throw new Error(`HTTP ${{response.status}}`);
        return response.json();
    }}
}}

// Example usage
(async () => {{
    const client = new InventoryAPIClient();
    
    try {{
        // Get all Nike items
        const nikeItems = await client.getItems({{ brand: 'nike' }});
        console.log(`Found ${{nikeItems.items.length}} Nike items`);
        
        // Search for Air Jordan
        const jordanResults = await client.searchItems('air jordan');
        console.log(`Found ${{jordanResults.items.length}} Air Jordan items`);
        
        // Get statistics
        const stats = await client.getStats();
        console.log(`Total inventory: ${{stats.inventory.total_items}} items`);
    }} catch (error) {{
        console.error('API Error:', error);
    }}
}})();
'''
    
    elif language == 'curl':
        client_code = f'''#!/bin/bash
# cURL examples for Streetwear Inventory API
# Generated automatically - modify as needed

BASE_URL="{base_url}"

echo "=== Streetwear Inventory API Examples ==="

# Get API info
echo "\\n1. Get API information:"
curl -s "$BASE_URL/" | jq '.'

# Get all items
echo "\\n2. Get all items (limit 5):"
curl -s "$BASE_URL/api/items?limit=5" | jq '.items[] | {{sku, brand, model, current_price}}'

# Get Nike items
echo "\\n3. Get Nike items:"
curl -s "$BASE_URL/api/items?brand=nike&limit=3" | jq '.items[] | {{sku, brand, model}}'

# Get specific item
echo "\\n4. Get specific item (replace NIK001 with actual SKU):"
curl -s "$BASE_URL/api/items/NIK001" | jq '.'

# Search items
echo "\\n5. Search for 'jordan':"
curl -s "$BASE_URL/api/search?q=jordan" | jq '.items[] | {{sku, brand, model}}'

# Get locations
echo "\\n6. Get all locations:"
curl -s "$BASE_URL/api/locations" | jq '.locations[] | {{code, name, item_count}}'

# Get consigners
echo "\\n7. Get all consigners:"
curl -s "$BASE_URL/api/consigners" | jq '.consigners[] | {{name, phone, stats}}'

# Get statistics
echo "\\n8. Get inventory statistics:"
curl -s "$BASE_URL/api/stats" | jq '.inventory'

# Update item price (uncomment and modify)
# echo "\\n9. Update item price:"
# curl -X PUT -H "Content-Type: application/json" \\
#      -d '{{"current_price": 150}}' \\
#      "$BASE_URL/api/items/NIK001" | jq '.'

echo "\\n=== Examples completed ==="
'''
    
    # Save to file or print
    if output:
        output_path = Path(output)
        output_path.write_text(client_code)
        click.echo(f"✅ Generated {language} API client: {output_path}")
    else:
        click.echo(f"📝 {language.title()} API Client Code:")
        click.echo("-" * 50)
        click.echo(client_code)