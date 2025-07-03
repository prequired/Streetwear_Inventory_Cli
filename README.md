# 👟 Streetwear Inventory CLI

**Professional-grade inventory management system for streetwear resellers**

[![CI](https://github.com/prequired/Streetwear_Inventory_Cli/actions/workflows/ci.yml/badge.svg)](https://github.com/prequired/Streetwear_Inventory_Cli/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/streetwear-inventory-cli.svg)](https://badge.fury.io/py/streetwear-inventory-cli)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🚀 **Quick Start**

```bash
# Clone and setup
git clone <repository>
cd streetwear-inventory-cli

# Install dependencies
pip install -r requirements.txt

# Initialize system
python -m inv.cli setup

# Add your first item
python -m inv.cli add nike "air jordan 1" 10 chicago DS 250 200 box HOME

# Start managing your inventory!
python -m inv.cli search --brand nike
```

For a complete 5-minute walkthrough, see [QUICK_START.md](QUICK_START.md).

## 📋 **What's Included**

### **✅ Core Inventory Management**
- **Item Management**: Add, edit, search, and track inventory with 34 CLI commands
- **SKU Generation**: Automatic brand-prefixed SKU system (NIK001, SUP001, etc.)
- **Location Tracking**: Multi-location inventory support with codes
- **Status Management**: Available, sold, held item states with transitions

### **📷 Photo Management** 
- **EXIF Removal**: Automatic privacy protection for all photos
- **Image Optimization**: Compress and resize photos to reduce storage
- **Bulk Operations**: Add multiple photos at once from directories
- **Primary Photos**: Set featured images for items with management tools

### **💰 Consignment System**
- **Intake Workflow**: Process consignment items with split calculations
- **Platform Fees**: Support for eBay, GOAT, StockX, Grailed fee structures
- **Consigner Management**: Track consigner information and payout history
- **Reporting**: Detailed consignment reports and payout summaries

### **📊 Data Export & Backup**
- **Export Formats**: CSV, JSON, Excel support for all data
- **Filtering Options**: Export by brand, status, date ranges, ownership type
- **API Server**: REST API with full CRUD operations
- **Database Backup**: Complete backup system with compression

### **🔧 Advanced Features**
- **Search System**: Full-text search across all item fields
- **API Client Generation**: Auto-generate Python, JavaScript, cURL clients
- **Photo Analytics**: Find duplicates, optimize storage, get statistics
- **Import Templates**: Generate templates for bulk data import

---

# 📚 **Complete Command Reference**

## **Core Inventory Commands**

### `add` - Add New Items
Add new items to your inventory with full details.

```bash
# Basic usage
inv add BRAND MODEL SIZE COLOR CONDITION CURRENT_PRICE PURCHASE_PRICE BOX_STATUS [LOCATION]

# Examples
inv add nike "air jordan 1" 10 chicago DS 250 200 box HOME
inv add supreme "box logo tee" L white DS 120 100 tag STORAGE
inv add adidas "yeezy 350" 9.5 "cream white" VNDS 220 180 box STORE-A1

# Options
--notes TEXT      # Additional notes about the item
--consignment     # Mark as consignment item
```

**Arguments:**
- `BRAND`: Brand name (nike, adidas, supreme, etc.)
- `MODEL`: Model name (use quotes for spaces)
- `SIZE`: Size (10, 10.5, M, L, XL, etc.)
- `COLOR`: Color/colorway description
- `CONDITION`: DS (deadstock), VNDS (very near deadstock), Used
- `CURRENT_PRICE`: Current selling price
- `PURCHASE_PRICE`: Purchase/cost price
- `BOX_STATUS`: box, tag, both, neither
- `LOCATION`: Location code (optional, will prompt if not provided)

### `search` - Find Items
Search and filter your inventory with powerful options.

```bash
# Basic search
inv search                    # Show all items
inv search "jordan"           # Search all fields for "jordan"
inv search --brand=nike       # Filter by brand
inv search --available        # Show only available items

# Advanced filtering
inv search --brand=nike --condition=DS --min-price=200
inv search --location=STORE-A1 --sold
inv search --consignment --max-price=150
inv search --sku=NIK001

# Options
--brand TEXT       # Filter by brand
--model TEXT       # Filter by model
--size TEXT        # Filter by size
--color TEXT       # Filter by color
--condition TEXT   # Filter by condition (DS, VNDS, Used)
--location TEXT    # Filter by location code
--available        # Show only available items
--sold             # Show only sold items
--held             # Show only held items
--consignment      # Show only consignment items
--owned            # Show only owned items
--min-price FLOAT  # Minimum price filter
--max-price FLOAT  # Maximum price filter
--count            # Show count only
--sku TEXT         # Search by SKU
--detailed         # Show detailed information
```

### `show` - View Item Details
Display complete information for any item.

```bash
inv show NIK001          # Show item details
inv show NIK001 --edit   # Show details and open edit mode
```

### `edit` - Update Items
Edit existing items with interactive or direct updates.

```bash
# Interactive editing (recommended)
inv edit NIK001

# Direct updates
inv edit NIK001 --price=300 --status=sold --sold-price=275
inv edit NIK001 --condition=VNDS --notes="Minor scuffing"
inv edit NIK001 --location=STORE-B2
inv edit NIK001 --box-status=neither

# Options
--price TEXT              # Update current price
--status TEXT             # available|sold|held|deleted
--sold-price TEXT         # Set sold price (required when marking as sold)
--sold-platform TEXT      # Platform where item was sold
--condition TEXT          # DS|VNDS|Used
--location TEXT           # Move to different location (location code)
--notes TEXT              # Update notes
--box-status TEXT         # box|tag|both|neither
--round-price             # Round price up to nearest $5
-i, --interactive         # Interactive edit mode
```

### `move` - Relocate Items
Move items between locations quickly.

```bash
inv move NIK001 STORE-FLOOR-A1    # Move item to specific location
inv move SUP005 WAREHOUSE-B2      # Move to warehouse location
```

### `update-status` - Quick Status Updates
Fast status changes for items.

```bash
inv update-status NIK001 --status=sold --sold-price=275 --sold-platform=StockX
inv update-status SUP005 --status=available
inv update-status ADI003 --status=held
```

### `add-variant` - Create Size Variants
Create variants of existing items (different sizes).

```bash
inv add-variant NIK001              # Create variant with guided prompts
inv add-variant NIK001 --interactive # Interactive variant creation
```

---

## **Photo Management Commands**

### `add-photo` - Add Single Photos
Add individual photos to items.

```bash
inv add-photo NIK001 /path/to/photo.jpg
inv add-photo SUP005 ./image.png --filename="front_view.png"
inv add-photo ADI003 photo.jpg --primary

# Options
--filename TEXT    # Custom filename for the photo
--primary          # Set as primary photo
```

### `bulk-add-photos` - Add Multiple Photos
Add multiple photos from a directory at once.

```bash
inv bulk-add-photos NIK001 /path/to/photos/
inv bulk-add-photos SUP005 ./photos/ --pattern="*.jpg"
inv bulk-add-photos ADI003 ./photos/ --set-primary=1

# Options
--pattern TEXT           # File pattern to match (e.g., "*.jpg")
--set-primary INTEGER    # Set photo number as primary (1-based)
```

### `copy-photos` - Copy Photos Between Items
Copy photos from one item to another (useful for variants).

```bash
inv copy-photos NIK001 NIK002    # Copy all photos from NIK001 to NIK002
inv copy-photos SUP005 SUP006    # Copy photos between variants
```

### `list-photos` - View Photo Information
List all photos for an item.

```bash
inv list-photos NIK001           # List photos
inv list-photos SUP005 --details # Show detailed photo information
```

### `remove-photo` - Delete Photos
Remove specific photos from items.

```bash
inv remove-photo NIK001 photo.jpg            # Remove specific photo
inv remove-photo SUP005 front_view.png --confirm # Skip confirmation
```

### `set-primary-photo` - Set Featured Image
Set the primary photo for an item.

```bash
inv set-primary-photo NIK001 best_angle.jpg
inv set-primary-photo SUP005 front_view.png
```

### `optimize-photos` - Reduce File Sizes
Optimize photos to save storage space.

```bash
inv optimize-photos NIK001    # Optimize photos for one item
inv optimize-photos --all     # Optimize all photos
```

### `photo-stats` - Storage Analytics
View photo storage statistics and cleanup.

```bash
inv photo-stats               # Show storage statistics
inv photo-stats --cleanup     # Remove orphaned photo directories
```

### `find-duplicate-photos` - Find Duplicates
Find and optionally remove duplicate photos.

```bash
inv find-duplicate-photos                           # Find duplicates
inv find-duplicate-photos --directory=/path/to/photos # Search specific directory
inv find-duplicate-photos --remove                  # Remove duplicates (keeps first)
```

### `remove-exif` - Strip Metadata
Remove EXIF metadata from image files.

```bash
inv remove-exif photo.jpg                    # Remove EXIF in-place
inv remove-exif input.jpg clean_output.jpg   # Remove EXIF to new file
```

---

## **Consignment Management Commands**

### `intake` - Process New Consignments
Process new consignment items with full workflow.

```bash
# Single item intake
inv intake --consigner="John Doe" --phone="555-1234"

# Multiple items
inv intake --batch=3 --consigner="Mike Chen" --phone="555-5678" --email="mike@example.com"

# Custom split percentage
inv intake --consigner="Sarah" --phone="555-9999" --split=75

# Interactive mode
inv intake --interactive

# Options
--consigner TEXT    # Consigner name (required)
--phone TEXT        # Phone number (required for new consigners)
--email TEXT        # Email address (optional)
--batch INTEGER     # Number of items to intake
--split INTEGER     # Override default split percentage (0-100)
-i, --interactive   # Interactive intake mode
```

### `consign-sold` - Mark Consignment Sales
Mark consignment items as sold and calculate payouts.

```bash
# Basic sale
inv consign-sold NIK001 250.00

# With platform fees
inv consign-sold SUP005 120.00 --platform=ebay
inv consign-sold ADI003 180.00 --platform=stockx --buyer="John Smith"

# Custom platform fee
inv consign-sold JOR001 275.00 --platform=goat --platform-fee=25.50

# Options
--buyer TEXT          # Buyer information (optional)
--platform TEXT       # store|ebay|goat|stockx|grailed|depop
--platform-fee FLOAT  # Platform fee amount (overrides default)
```

**Platform Fees:**
- **store**: 0% (in-person sales)
- **ebay**: ~10% of sale price
- **goat**: ~9.5% of sale price
- **stockx**: ~9.5% of sale price
- **grailed**: ~6% of sale price + $0.30
- **depop**: ~10% of sale price

### `hold-item` - Place Items on Hold
Put consignment items on hold temporarily.

```bash
inv hold-item NIK001 --reason="Needs cleaning"
inv hold-item SUP005 --reason="Damage assessment"
inv hold-item ADI003 --release   # Release from hold

# Options
--reason TEXT    # Reason for holding (optional)
--release        # Release item from hold
```

### `consign` - Calculate Payouts
Calculate and process consignment payouts for consigners.

```bash
inv consign "John Doe"                    # Calculate payout
inv consign "John" --phone="555-1234"    # Disambiguate by phone
inv consign "Mike Chen" --show-items      # Show individual items
inv consign "Sarah Jones" --mark-paid     # Mark as paid

# Options
--phone TEXT      # Phone number for disambiguation
--mark-paid       # Mark payouts as paid (for record keeping)
--show-items      # Show individual items in payout calculation
```

### `list-consigners` - View All Consigners
List consigners with optional statistics.

```bash
inv list-consigners               # List all consigners
inv list-consigners --stats       # Include statistics
inv list-consigners --search="john" # Search by name/phone/email
```

### `consigner-report` - Detailed Reports
Generate comprehensive reports for specific consigners.

```bash
inv consigner-report "John Doe"
inv consigner-report "John" --phone="555-1234"
```

### `payout-summary` - Payout Overview
View summary of all consignment payouts.

```bash
inv payout-summary                        # All payouts
inv payout-summary --pending-only         # Only pending payouts
inv payout-summary --consigner="John Doe" # Specific consigner
inv payout-summary --min-amount=50.00     # Minimum amount filter
```

---

## **Location Management Commands**

### `location` - Manage Storage Locations
Create and manage inventory locations.

```bash
# Create new location
inv location --create --code=STORE-A1 --type=store-floor --description="Store Floor Section A1"

# List locations
inv location --list                 # Active locations only
inv location --list --show-inactive # Include inactive locations
inv location --stats                # Show location statistics

# Move items
inv location --move=NIK001 --to=WAREHOUSE-B2

# Deactivate location
inv location --deactivate=OLD-STORAGE

# Get code suggestions
inv location --suggest --type=warehouse --description="Main Warehouse Section B"

# Options
--create           # Create a new location
--list             # List all locations
--show-inactive    # Include inactive locations in list
--stats            # Show location statistics
--code TEXT        # Location code
--type TEXT        # Location type (store-floor, warehouse, storage, etc.)
--description TEXT # Location description
--move TEXT        # Move item (specify SKU)
--to TEXT          # Target location for move operation
--deactivate TEXT  # Deactivate location (specify code)
--suggest          # Suggest location code based on type and description
```

**Location Types:**
- `store-floor`: Retail floor display
- `warehouse`: Main storage facility
- `storage`: Secondary storage
- `home`: Home storage
- `other`: Custom location type

### `update-location` - Modify Locations
Update existing location details.

```bash
inv update-location STORE-A1 --description="Updated description"
inv update-location OLD-STORAGE --activate    # Reactivate location
inv update-location WAREHOUSE-A --type=storage

# Options
--type TEXT        # New location type
--description TEXT # New description
--activate         # Reactivate location
```

### `find-location` - Search Locations
Find locations by code or description.

```bash
inv find-location "store"    # Search for locations with "store"
inv find-location "A1"       # Search for locations with "A1"
```

---

## **Export and Import Commands**

### `export-inventory` - Export Item Data
Export inventory data in multiple formats with filtering.

```bash
# Basic exports
inv export-inventory csv      # Export to CSV
inv export-inventory json     # Export to JSON
inv export-inventory excel    # Export to Excel

# Custom output file
inv export-inventory csv --output=my_inventory.csv
inv export-inventory json --output=backup.json

# Filtering options
inv export-inventory csv --filter-brand=nike
inv export-inventory json --filter-status=available
inv export-inventory excel --ownership-type=consignment
inv export-inventory csv --filter-location=STORE-A1

# Include additional data
inv export-inventory json --include-photos --include-consigner
inv export-inventory excel --include-photos

# Date range filtering
inv export-inventory csv --date-from=2024-01-01 --date-to=2024-12-31

# Options
-o, --output TEXT            # Output file path (auto-generated if not provided)
--filter-brand TEXT          # Filter by brand
--filter-status TEXT         # Filter by status
--filter-condition TEXT      # Filter by condition
--filter-location TEXT       # Filter by location code
--ownership-type TEXT        # owned|consignment
--include-photos             # Include photo information
--include-consigner          # Include consigner details
--date-from TEXT             # Include items added after this date (YYYY-MM-DD)
--date-to TEXT               # Include items added before this date (YYYY-MM-DD)
```

### `export-consigners` - Export Consigner Data
Export consigner information and statistics.

```bash
inv export-consigners csv                           # Basic export
inv export-consigners json --include-stats          # Include statistics
inv export-consigners excel --include-stats --include-items # Include items

# Options
-o, --output TEXT    # Output file path
--include-stats      # Include detailed statistics
--include-items      # Include items for each consigner
```

### `export-locations` - Export Location Data
Export location information and item counts.

```bash
inv export-locations csv                    # Basic export
inv export-locations json --include-items   # Include item counts
inv export-locations excel --output=locations.xlsx

# Options
-o, --output TEXT    # Output file path
--include-items      # Include item counts
```

### `export-template` - Generate Import Templates
Create templates for bulk data import.

```bash
inv export-template csv                              # Basic CSV template
inv export-template excel --include-examples        # Excel with examples
inv export-template csv --output=import_template.csv

# Options
-o, --output TEXT      # Template file path
--include-examples     # Include example data
```

---

## **API Server Commands**

### `api-server` - Start REST API
Launch the REST API server for external integrations.

```bash
inv api-server                              # Start on localhost:5000
inv api-server --host=0.0.0.0 --port=8080  # Custom host and port
inv api-server --debug                      # Enable debug mode

# Options
--host TEXT        # Host to bind to
--port INTEGER     # Port to bind to
--debug            # Enable debug mode
```

**Available Endpoints:**
- `GET /api/items` - List items with filtering
- `GET /api/items/<sku>` - Get specific item
- `PUT /api/items/<sku>` - Update item
- `GET /api/locations` - List locations
- `GET /api/consigners` - List consigners
- `GET /api/search?q=<query>` - Search items
- `GET /api/stats` - Inventory statistics

### `api-test` - Test API Connectivity
Test API server endpoints and connectivity.

```bash
inv api-test                               # Test localhost:5000
inv api-test --host=localhost --port=8080  # Test custom host/port
```

### `api-docs` - View API Documentation
Display comprehensive API documentation.

```bash
inv api-docs    # Show complete API documentation
```

### `generate-api-client` - Create API Clients
Generate client code for different programming languages.

```bash
# Generate clients
inv generate-api-client python                    # Python client
inv generate-api-client javascript --output=client.js
inv generate-api-client curl --output=examples.sh

# Custom API endpoint
inv generate-api-client python --host=myserver.com --port=8080

# Options
--output TEXT     # Output file path
--host TEXT       # API host
--port INTEGER    # API port
```

---

## **System Management Commands**

### `setup` - Initial Configuration
Interactive setup wizard for first-time configuration.

```bash
inv setup    # Run interactive setup wizard
```

**Setup configures:**
- Database connection
- Service key
- Default location
- Consignment split percentage
- Photo storage path

### `test-connection` - Verify Database
Test database connectivity and configuration.

```bash
inv test-connection    # Test database connection
```

### `backup-database` - Create Backups
Create complete database backups with optional compression.

```bash
inv backup-database                                    # Basic backup
inv backup-database --output=backup.json --compress   # Compressed backup
inv backup-database --include-photos                  # Include photos in backup

# Options
-o, --output TEXT    # Backup file path
--compress           # Compress the backup
--include-photos     # Include photos in backup
```

---

# 🔧 **Installation & Setup**

## **Requirements**
- Python 3.8 or higher
- 150MB+ available disk space
- SQLite (included with Python)

## **Installation Methods**

### **Method 1: Development Installation**
```bash
# Clone repository
git clone <repository-url>
cd streetwear-inventory-cli

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .

# Run setup
python -m inv.cli setup
```

### **Method 2: Package Installation**
```bash
# Install core package
pip install streetwear-inventory-cli

# Install with optional features
pip install streetwear-inventory-cli[api]     # API server support
pip install streetwear-inventory-cli[excel]   # Excel export support
pip install streetwear-inventory-cli[all]     # All optional features

# Run setup
inv setup
```

### **Method 3: Production Installation**
```bash
# Install with all features
pip install streetwear-inventory-cli[all]

# Configure for production use
inv setup
# Use default SQLite database or specify custom path

# Create initial location
inv location --create --code=MAIN --type=warehouse --description="Main Storage"
```

---

# 📊 **Configuration**

## **Configuration File Structure**
The system uses YAML configuration stored in `config.yaml`:

```yaml
database:
  url: "sqlite:///streetwear_inventory.db"  # Database connection
  
service:
  key: "your_service_key"                   # Unique service identifier

defaults:
  location: "HOME"                          # Default location code
  consignment_split: 70                     # Default consignment split %

storage:
  photos_path: "./photos"                   # Photo storage directory
  max_photo_size: 10                        # Max photo size in MB
  photo_quality: 85                         # Photo compression quality

api:
  host: "127.0.0.1"                        # API server host
  port: 5000                               # API server port
  debug: false                             # Debug mode
```

## **Environment Variables**
Override config with environment variables:

```bash
export DATABASE_URL="sqlite:///path/to/production_inventory.db"
export SERVICE_KEY="production_key"
export PHOTOS_PATH="/var/lib/streetwear/photos"
export API_HOST="0.0.0.0"
export API_PORT="8080"
```

---

# 🚀 **Usage Examples**

## **Daily Operations**

### **Adding New Inventory**
```bash
# Add sneakers
inv add nike "air jordan 1" 10 "chicago" DS 275 200 box HOME
inv add adidas "yeezy 350 v2" 9.5 "cream white" VNDS 220 180 box STORE-A1

# Add clothing
inv add supreme "box logo hoodie" L "black" DS 450 350 tag WAREHOUSE-B2
inv add off-white "virgil abloh tee" M "white" Used 180 120 tag HOME

# Add with detailed notes
inv add travis-scott "cactus jack hoodie" XL "brown" DS 300 250 tag STORE-A1 \
  --notes="Limited release from Astroworld tour"
```

### **Managing Photos**
```bash
# Add single photo
inv add-photo NIK001 ./photos/jordan_front.jpg --primary

# Add multiple photos
inv bulk-add-photos SUP005 ./item_photos/ --pattern="*.jpg" --set-primary=1

# Organize and optimize
inv photo-stats                    # Check storage usage
inv optimize-photos --all          # Optimize all photos
inv find-duplicate-photos --remove # Clean up duplicates
```

### **Processing Sales**
```bash
# Mark items as sold
inv update-status NIK001 --status=sold --sold-price=275 --sold-platform=StockX
inv update-status SUP005 --status=sold --sold-price=450 --sold-platform=ebay

# Process consignment sales
inv consign-sold JOR001 300.00 --platform=goat --buyer="Verified Buyer"
inv consign "John Doe" --show-items  # Calculate payout
```

### **Inventory Analysis**
```bash
# Check inventory status
inv search --available --count             # Count available items
inv search --brand=nike --min-price=200    # High-value Nike items
inv search --consignment --sold            # Sold consignment items

# Location analysis
inv location --stats                        # Location utilization
inv search --location=STORE-A1 --detailed  # Items in specific location
```

## **Consignment Workflow**

### **Complete Consignment Process**
```bash
# 1. Intake new consignment
inv intake --consigner="Mike Chen" --phone="(555) 123-4567" --email="mike@example.com" --split=70

# 2. Add photos after intake
inv add-photo JOR001 ./photos/jordan_main.jpg --primary
inv bulk-add-photos JOR001 ./photos/jordan_details/ --pattern="*.jpg"

# 3. Track item until sold
inv search --consignment --available --consigner="Mike Chen"

# 4. Process sale
inv consign-sold JOR001 285.00 --platform=stockx --buyer="StockX Buyer"

# 5. Generate payout report
inv consigner-report "Mike Chen"
inv consign "Mike Chen" --mark-paid
```

### **Consigner Management**
```bash
# List all consigners with stats
inv list-consigners --stats

# Generate reports
inv consigner-report "Sarah Johnson"
inv payout-summary --pending-only
inv payout-summary --consigner="Mike Chen"

# Export consigner data
inv export-consigners excel --include-stats --include-items
```

## **Data Management**

### **Regular Backups**
```bash
# Create backups
inv backup-database --output="backup_$(date +%Y%m%d).json" --compress
inv backup-database --include-photos  # Full backup with photos

# Export data for analysis
inv export-inventory excel --include-photos --include-consigner
inv export-inventory csv --filter-brand=nike --date-from=2024-01-01
```

### **Multi-Location Management**
```bash
# Set up locations
inv location --create --code=STORE-A1 --type=store-floor --description="Store Floor Section A1"
inv location --create --code=WAREHOUSE-B2 --type=warehouse --description="Warehouse Bay B2"
inv location --create --code=HOME-CLOSET --type=home --description="Home Closet Storage"

# Move items between locations
inv move NIK001 STORE-A1      # Move to store floor
inv move SUP005 WAREHOUSE-B2  # Move to warehouse

# Location analytics
inv location --stats                           # Overview
inv export-locations excel --include-items    # Detailed export
```

---

# 🔗 **Integration & API**

## **REST API Usage**

### **Start API Server**
```bash
# Development
inv api-server --debug

# Production
inv api-server --host=0.0.0.0 --port=8080
```

### **API Examples**
```bash
# Test connectivity
curl http://localhost:5000/api/items

# Get specific item
curl http://localhost:5000/api/items/NIK001

# Search items
curl "http://localhost:5000/api/search?q=jordan&limit=10"

# Update item
curl -X PUT http://localhost:5000/api/items/NIK001 \
  -H "Content-Type: application/json" \
  -d '{"current_price": 300.00, "status": "sold"}'

# Get statistics
curl http://localhost:5000/api/stats
```

### **Generate API Clients**
```bash
# Python client
inv generate-api-client python --output=client.py

# JavaScript client
inv generate-api-client javascript --output=client.js

# cURL examples
inv generate-api-client curl --output=api_examples.sh
```

For complete API documentation, see [API_DOCUMENTATION.md](API_DOCUMENTATION.md).

---

# 📈 **Performance & Optimization**

## **Photo Storage Optimization**
```bash
# Analyze photo storage
inv photo-stats

# Optimize storage
inv optimize-photos --all           # Reduce file sizes
inv find-duplicate-photos --remove  # Remove duplicates
inv photo-stats --cleanup          # Clean orphaned directories
```

## **Database Optimization**
```bash
# Test performance
inv test-connection

# Regular maintenance
inv backup-database --compress       # Regular backups
inv export-inventory json           # Export for safety
```

## **Bulk Operations**
```bash
# Bulk photo management
inv bulk-add-photos NIK001 ./photos/ --pattern="*.jpg"
inv copy-photos NIK001 NIK002  # Copy between variants

# Bulk data export
inv export-inventory csv --filter-brand=nike    # Brand-specific exports
inv export-inventory excel --date-from=2024-01-01 --include-photos
```

---

# 🛠️ **Advanced Configuration**

## **Production Deployment**

### **Database Setup**
```bash
# SQLite production database setup
inv setup
# Enter custom path: /var/lib/streetwear/production_inventory.db
# Or use default: sqlite:///streetwear_inventory.db
```

### **System Service**
```bash
# Create systemd service
sudo tee /etc/systemd/system/streetwear-api.service << EOF
[Unit]
Description=Streetwear Inventory API
After=network.target

[Service]
Type=simple
User=inventory
WorkingDirectory=/home/inventory/streetwear-inventory-cli
ExecStart=/home/inventory/.local/bin/inv api-server --host=0.0.0.0 --port=8080
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable streetwear-api
sudo systemctl start streetwear-api
```

### **Nginx Reverse Proxy**
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location /api/ {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

# 🔒 **Security & Privacy**

## **Photo Privacy**
- **EXIF Removal**: All photos automatically stripped of metadata
- **Storage Isolation**: Photos stored in organized directories
- **Access Control**: File permissions managed automatically

## **Data Security**
- **Database Protection**: Secure file permissions for SQLite database
- **Backup Security**: Compress and encrypt backups
- **API Security**: Consider adding authentication for production APIs

## **Best Practices**
```bash
# Regular backups
inv backup-database --compress --output="secure_backup_$(date +%Y%m%d).json"

# Clean sensitive data
inv remove-exif photo.jpg         # Remove EXIF from photos
inv photo-stats --cleanup         # Clean orphaned data

# Secure configuration
export DATABASE_URL="sqlite:///secure/path/inventory.db"
export SERVICE_KEY="$(openssl rand -hex 32)"  # Generate secure key
```

---

# 🆘 **Troubleshooting**

## **Common Issues**

### **Database Connection Issues**
```bash
# Test connection
inv test-connection

# Check configuration
cat config.yaml

# Reset database
rm streetwear_inventory.db  # For SQLite
inv setup                   # Reconfigure
```

### **Photo Storage Issues**
```bash
# Check photo storage
inv photo-stats

# Fix permissions
chmod -R 755 photos/

# Clean up storage
inv photo-stats --cleanup
inv find-duplicate-photos --remove
```

### **Performance Issues**
```bash
# Check database size
du -h streetwear_inventory.db

# Optimize photos
inv optimize-photos --all

# Clean exports
rm *.csv *.json *.xlsx
```

### **Command Issues**
```bash
# Update installation
pip install -e . --force-reinstall

# Check Python path
which python
python -m inv.cli --help

# Reset configuration
rm config.yaml
inv setup
```

## **Getting Help**
- Run `inv [command] --help` for command-specific help
- Check [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines
- Report issues at [GitHub Issues](https://github.com/yourusername/streetwear-inventory-cli/issues)

---

# 📄 **Additional Documentation**

- **[QUICK_START.md](QUICK_START.md)** - 5-minute setup guide
- **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)** - Complete REST API reference
- **[CHANGELOG.md](CHANGELOG.md)** - Version history and updates
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Development and contribution guidelines

---

**Built for streetwear resellers who demand professional tools.** 🚀
