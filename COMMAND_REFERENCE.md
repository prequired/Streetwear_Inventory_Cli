# 📚 Complete Command Reference

**Comprehensive guide to all 34 commands in the Streetwear Inventory CLI**

This document provides detailed technical reference for every command, flag, and option available in the system. For quick start information, see [QUICK_START.md](QUICK_START.md).

---

## **Table of Contents**

- [Core Inventory Commands](#core-inventory-commands)
- [Photo Management Commands](#photo-management-commands)
- [Consignment Management Commands](#consignment-management-commands)
- [Location Management Commands](#location-management-commands)
- [Export and Import Commands](#export-and-import-commands)
- [API Server Commands](#api-server-commands)
- [System Management Commands](#system-management-commands)
- [Command Categories](#command-categories)
- [Common Patterns](#common-patterns)

---

# Core Inventory Commands

## `add` - Add New Items

**Purpose:** Add new items to inventory with complete details and automatic SKU generation.

**Usage:**
```bash
inv add BRAND MODEL SIZE COLOR CONDITION CURRENT_PRICE PURCHASE_PRICE BOX_STATUS [LOCATION]
```

**Arguments:**
- `BRAND` *(required)*: Brand name (nike, adidas, supreme, etc.)
- `MODEL` *(required)*: Model name (use quotes for multi-word names)
- `SIZE` *(required)*: Size (10, 10.5, M, L, XL, etc.)
- `COLOR` *(required)*: Color/colorway description
- `CONDITION` *(required)*: DS, VNDS, or Used
- `CURRENT_PRICE` *(required)*: Current selling price (numeric)
- `PURCHASE_PRICE` *(required)*: Purchase/cost price (numeric)
- `BOX_STATUS` *(required)*: box, tag, both, or neither
- `LOCATION` *(optional)*: Location code (prompts if not provided)

**Options:**
- `-n, --notes TEXT`: Additional notes about the item
- `--consignment`: Mark as consignment item

**Examples:**
```bash
# Basic item addition
inv add nike "air jordan 1" 10 chicago DS 250 200 box HOME

# With notes
inv add supreme "box logo tee" L white DS 120 100 tag STORAGE --notes="2019 release"

# Consignment item
inv add adidas "yeezy 350" 9.5 "cream white" VNDS 220 0 box STORE-A1 --consignment
```

**Output:** Returns generated SKU and item summary

---

## `search` - Find Items

**Purpose:** Search and filter inventory with comprehensive filtering options.

**Usage:**
```bash
inv search [OPTIONS] [QUERY]
```

**Arguments:**
- `QUERY` *(optional)*: Free-text search across all fields

**Options:**
- `--brand TEXT`: Filter by specific brand
- `--model TEXT`: Filter by model name
- `--size TEXT`: Filter by size
- `--color TEXT`: Filter by color/colorway
- `--condition TEXT`: Filter by condition (DS, VNDS, Used)
- `--location TEXT`: Filter by location code
- `--available`: Show only available items
- `--sold`: Show only sold items
- `--held`: Show only held items
- `--consignment`: Show only consignment items
- `--owned`: Show only owned items
- `--min-price FLOAT`: Minimum price filter
- `--max-price FLOAT`: Maximum price filter
- `--count`: Show count only (no item details)
- `--sku TEXT`: Search by specific SKU
- `--detailed`: Show detailed information for each item

**Examples:**
```bash
# Basic searches
inv search                          # Show all items
inv search "jordan"                 # Text search
inv search --brand=nike             # Brand filter
inv search --available --count      # Count available items

# Advanced filtering
inv search --brand=nike --condition=DS --min-price=200
inv search --location=STORE-A1 --sold
inv search --consignment --max-price=150
inv search --sku=NIK001
```

**Output:** List of matching items with key details

---

## `show` - View Item Details

**Purpose:** Display complete information for a specific item.

**Usage:**
```bash
inv show [OPTIONS] SKU
```

**Arguments:**
- `SKU` *(required)*: Item SKU to display

**Options:**
- `--edit`: Open edit mode after displaying item details

**Examples:**
```bash
inv show NIK001           # Display item details
inv show NIK001 --edit    # Display and then edit
```

**Output:** Complete item information including photos, consigner details, and history

---

## `edit` - Update Items

**Purpose:** Edit existing inventory items with interactive or direct updates.

**Usage:**
```bash
inv edit [OPTIONS] SKU
```

**Arguments:**
- `SKU` *(required)*: Item SKU to edit

**Options:**
- `--price TEXT`: Update current price
- `--status [available|sold|held|deleted]`: Update item status
- `--sold-price TEXT`: Set sold price (required when marking as sold)
- `--sold-platform TEXT`: Platform where item was sold
- `--condition [DS|VNDS|Used]`: Update condition
- `--location TEXT`: Move to different location (location code)
- `--notes TEXT`: Update notes
- `--box-status [box|tag|both|neither]`: Update box status
- `--round-price`: Round price up to nearest $5
- `-i, --interactive`: Interactive edit mode with prompts

**Examples:**
```bash
# Interactive editing
inv edit NIK001

# Direct updates
inv edit NIK001 --price=300 --status=sold --sold-price=275
inv edit NIK001 --condition=VNDS --notes="Minor scuffing"
inv edit NIK001 --location=STORE-B2
inv edit NIK001 --box-status=neither --round-price
```

**Output:** Confirmation of changes made

---

## `move` - Relocate Items

**Purpose:** Move items between locations quickly.

**Usage:**
```bash
inv move SKU LOCATION_CODE
```

**Arguments:**
- `SKU` *(required)*: Item SKU to move
- `LOCATION_CODE` *(required)*: Target location code

**Examples:**
```bash
inv move NIK001 STORE-FLOOR-A1
inv move SUP005 WAREHOUSE-B2
```

**Output:** Confirmation of item relocation

---

## `update-status` - Quick Status Updates

**Purpose:** Fast status changes for items with minimal input.

**Usage:**
```bash
inv update-status [OPTIONS] SKU
```

**Arguments:**
- `SKU` *(required)*: Item SKU to update

**Options:**
- `--status [available|sold|held]` *(required)*: New status
- `--sold-price TEXT`: Sold price (required for sold status)
- `--sold-platform TEXT`: Platform where sold

**Examples:**
```bash
inv update-status NIK001 --status=sold --sold-price=275 --sold-platform=StockX
inv update-status SUP005 --status=available
inv update-status ADI003 --status=held
```

**Output:** Status change confirmation with details

---

## `add-variant` - Create Size Variants

**Purpose:** Create variants of existing items (different sizes).

**Usage:**
```bash
inv add-variant [OPTIONS] SKU
```

**Arguments:**
- `SKU` *(required)*: Base item SKU to create variant from

**Options:**
- `-i, --interactive`: Interactive variant creation with guided prompts

**Examples:**
```bash
inv add-variant NIK001                # Guided variant creation
inv add-variant NIK001 --interactive  # Interactive mode
```

**Output:** New variant SKU and details

---

# Photo Management Commands

## `add-photo` - Add Single Photos

**Purpose:** Add individual photos to inventory items.

**Usage:**
```bash
inv add-photo [OPTIONS] SKU PHOTO_PATH
```

**Arguments:**
- `SKU` *(required)*: Item SKU to add photo to
- `PHOTO_PATH` *(required)*: Path to the photo file

**Options:**
- `--filename TEXT`: Custom filename for the photo
- `--primary`: Set as primary photo for the item

**Examples:**
```bash
inv add-photo NIK001 /path/to/photo.jpg
inv add-photo SUP005 ./image.png --filename="front_view.png"
inv add-photo ADI003 photo.jpg --primary
```

**Output:** Photo processing confirmation and file details

---

## `bulk-add-photos` - Add Multiple Photos

**Purpose:** Add multiple photos from a directory to an item.

**Usage:**
```bash
inv bulk-add-photos [OPTIONS] SKU PHOTOS_DIRECTORY
```

**Arguments:**
- `SKU` *(required)*: Item SKU to add photos to
- `PHOTOS_DIRECTORY` *(required)*: Directory containing photos

**Options:**
- `--pattern TEXT`: File pattern to match (e.g., "*.jpg", "*.png")
- `--set-primary INTEGER`: Set photo number as primary (1-based index)

**Examples:**
```bash
inv bulk-add-photos NIK001 /path/to/photos/
inv bulk-add-photos SUP005 ./photos/ --pattern="*.jpg"
inv bulk-add-photos ADI003 ./photos/ --set-primary=1
```

**Output:** Summary of photos added and processing status

---

## `copy-photos` - Copy Photos Between Items

**Purpose:** Copy all photos from one item to another (useful for variants).

**Usage:**
```bash
inv copy-photos SOURCE_SKU DEST_SKU
```

**Arguments:**
- `SOURCE_SKU` *(required)*: Source item SKU
- `DEST_SKU` *(required)*: Destination item SKU

**Examples:**
```bash
inv copy-photos NIK001 NIK002    # Copy all photos
inv copy-photos SUP005 SUP006    # Useful for variants
```

**Output:** Summary of photos copied

---

## `list-photos` - View Photo Information

**Purpose:** List all photos associated with an item.

**Usage:**
```bash
inv list-photos [OPTIONS] SKU
```

**Arguments:**
- `SKU` *(required)*: Item SKU to list photos for

**Options:**
- `--details`: Show detailed photo information (size, dimensions, metadata)

**Examples:**
```bash
inv list-photos NIK001            # Basic photo list
inv list-photos SUP005 --details  # Detailed information
```

**Output:** List of photos with file information

---

## `remove-photo` - Delete Photos

**Purpose:** Remove specific photos from inventory items.

**Usage:**
```bash
inv remove-photo [OPTIONS] SKU FILENAME
```

**Arguments:**
- `SKU` *(required)*: Item SKU to remove photo from
- `FILENAME` *(required)*: Photo filename to remove

**Options:**
- `--confirm`: Skip confirmation prompt

**Examples:**
```bash
inv remove-photo NIK001 photo.jpg
inv remove-photo SUP005 front_view.png --confirm
```

**Output:** Deletion confirmation

---

## `set-primary-photo` - Set Featured Image

**Purpose:** Set the primary (featured) photo for an item.

**Usage:**
```bash
inv set-primary-photo SKU FILENAME
```

**Arguments:**
- `SKU` *(required)*: Item SKU
- `FILENAME` *(required)*: Photo filename to set as primary

**Examples:**
```bash
inv set-primary-photo NIK001 best_angle.jpg
inv set-primary-photo SUP005 front_view.png
```

**Output:** Primary photo update confirmation

---

## `optimize-photos` - Reduce File Sizes

**Purpose:** Optimize photos to reduce storage space while maintaining quality.

**Usage:**
```bash
inv optimize-photos [OPTIONS] [SKU]
```

**Arguments:**
- `SKU` *(optional)*: Item SKU to optimize (if not provided, use --all)

**Options:**
- `--all`: Optimize photos for all items

**Examples:**
```bash
inv optimize-photos NIK001     # Optimize one item's photos
inv optimize-photos --all      # Optimize all photos
```

**Output:** Optimization results and space saved

---

## `photo-stats` - Storage Analytics

**Purpose:** Display photo storage statistics and perform cleanup.

**Usage:**
```bash
inv photo-stats [OPTIONS]
```

**Options:**
- `--cleanup`: Remove orphaned photo directories

**Examples:**
```bash
inv photo-stats                # Show storage statistics
inv photo-stats --cleanup      # Clean up orphaned directories
```

**Output:** Storage usage statistics and cleanup results

---

## `find-duplicate-photos` - Find Duplicates

**Purpose:** Find and optionally remove duplicate photos in storage.

**Usage:**
```bash
inv find-duplicate-photos [OPTIONS]
```

**Options:**
- `--directory TEXT`: Search in specific directory (default: photos storage)
- `--remove`: Remove duplicate photos (keeps first occurrence)

**Examples:**
```bash
inv find-duplicate-photos                               # Find duplicates
inv find-duplicate-photos --directory=/path/to/photos  # Search specific directory
inv find-duplicate-photos --remove                     # Remove duplicates
```

**Output:** List of duplicates found and removal results

---

## `remove-exif` - Strip Metadata

**Purpose:** Remove EXIF metadata from image files for privacy.

**Usage:**
```bash
inv remove-exif INPUT_PATH [OUTPUT_PATH]
```

**Arguments:**
- `INPUT_PATH` *(required)*: Input image file path
- `OUTPUT_PATH` *(optional)*: Output image file path (overwrites input if not provided)

**Examples:**
```bash
inv remove-exif photo.jpg                      # Remove EXIF in-place
inv remove-exif input.jpg clean_output.jpg     # Save to new file
```

**Output:** EXIF removal confirmation

---

# Consignment Management Commands

## `intake` - Process New Consignments

**Purpose:** Process new consignment items with full intake workflow.

**Usage:**
```bash
inv intake [OPTIONS]
```

**Options:**
- `--consigner TEXT` *(required)*: Consigner name
- `--phone TEXT`: Consigner phone number (required for new consigners)
- `--email TEXT`: Consigner email address (optional)
- `--batch INTEGER`: Number of items to intake (default: 1)
- `--split INTEGER`: Override default split percentage (0-100)
- `-i, --interactive`: Interactive intake mode with guidance

**Examples:**
```bash
# Single item intake
inv intake --consigner="John Doe" --phone="555-1234"

# Multiple items
inv intake --batch=3 --consigner="Mike Chen" --phone="555-5678" --email="mike@example.com"

# Custom split
inv intake --consigner="Sarah" --phone="555-9999" --split=75

# Interactive mode
inv intake --interactive
```

**Output:** Intake summary with generated SKUs and consigner information

---

## `consign-sold` - Mark Consignment Sales

**Purpose:** Mark consignment items as sold and calculate payouts with platform fees.

**Usage:**
```bash
inv consign-sold [OPTIONS] SKU SOLD_PRICE
```

**Arguments:**
- `SKU` *(required)*: Item SKU
- `SOLD_PRICE` *(required)*: Price the item was sold for

**Options:**
- `--buyer TEXT`: Buyer information (optional)
- `--platform [store|ebay|goat|stockx|grailed|depop]`: Sales platform
- `--platform-fee FLOAT`: Custom platform fee amount (overrides default)

**Platform Fee Structure:**
- **store**: 0% (in-person sales)
- **ebay**: ~10% of sale price
- **goat**: ~9.5% of sale price
- **stockx**: ~9.5% of sale price
- **grailed**: ~6% of sale price + $0.30
- **depop**: ~10% of sale price

**Examples:**
```bash
# Basic sale
inv consign-sold NIK001 250.00

# With platform fees
inv consign-sold SUP005 120.00 --platform=ebay
inv consign-sold ADI003 180.00 --platform=stockx --buyer="John Smith"

# Custom platform fee
inv consign-sold JOR001 275.00 --platform=goat --platform-fee=25.50
```

**Output:** Sale confirmation with payout calculation breakdown

---

## `hold-item` - Place Items on Hold

**Purpose:** Temporarily place consignment items on hold or release them.

**Usage:**
```bash
inv hold-item [OPTIONS] SKU
```

**Arguments:**
- `SKU` *(required)*: Item SKU to hold/release

**Options:**
- `--reason TEXT`: Reason for holding (optional)
- `--release`: Release item from hold

**Examples:**
```bash
inv hold-item NIK001 --reason="Needs cleaning"
inv hold-item SUP005 --reason="Damage assessment"
inv hold-item ADI003 --release
```

**Output:** Hold status confirmation

---

## `consign` - Calculate Payouts

**Purpose:** Calculate and process consignment payouts for consigners.

**Usage:**
```bash
inv consign [OPTIONS] CONSIGNER_NAME
```

**Arguments:**
- `CONSIGNER_NAME` *(required)*: Name of the consigner

**Options:**
- `--phone TEXT`: Phone number for disambiguation
- `--mark-paid`: Mark payouts as paid (for record keeping)
- `--show-items`: Show individual items in payout calculation

**Examples:**
```bash
inv consign "John Doe"                     # Calculate payout
inv consign "John" --phone="555-1234"     # Disambiguate by phone
inv consign "Mike Chen" --show-items       # Show individual items
inv consign "Sarah Jones" --mark-paid      # Mark as paid
```

**Output:** Payout calculation with breakdown and payment instructions

---

## `list-consigners` - View All Consigners

**Purpose:** List all consigners with optional statistics and search.

**Usage:**
```bash
inv list-consigners [OPTIONS]
```

**Options:**
- `--stats`: Include statistics for each consigner
- `--search TEXT`: Search consigners by name, phone, or email

**Examples:**
```bash
inv list-consigners                    # List all consigners
inv list-consigners --stats            # Include statistics
inv list-consigners --search="john"    # Search by name
```

**Output:** List of consigners with contact information and optional statistics

---

## `consigner-report` - Detailed Reports

**Purpose:** Generate comprehensive reports for specific consigners.

**Usage:**
```bash
inv consigner-report [OPTIONS] CONSIGNER_NAME
```

**Arguments:**
- `CONSIGNER_NAME` *(required)*: Name of the consigner

**Options:**
- `--phone TEXT`: Phone number for disambiguation

**Examples:**
```bash
inv consigner-report "John Doe"
inv consigner-report "John" --phone="555-1234"
```

**Output:** Detailed consigner report with item history, payouts, and statistics

---

## `payout-summary` - Payout Overview

**Purpose:** Generate summary of all consignment payouts with filtering options.

**Usage:**
```bash
inv payout-summary [OPTIONS]
```

**Options:**
- `--pending-only`: Show only pending payouts
- `--consigner TEXT`: Filter by specific consigner name
- `--min-amount FLOAT`: Minimum payout amount to show

**Examples:**
```bash
inv payout-summary                          # All payouts
inv payout-summary --pending-only           # Only pending
inv payout-summary --consigner="John Doe"   # Specific consigner
inv payout-summary --min-amount=50.00       # Minimum amount filter
```

**Output:** Summary of payouts with totals and filtering results

---

# Location Management Commands

## `location` - Manage Storage Locations

**Purpose:** Create and manage inventory storage locations.

**Usage:**
```bash
inv location [OPTIONS]
```

**Options:**
- `--create`: Create a new location
- `--list`: List all locations
- `--show-inactive`: Include inactive locations in list
- `--stats`: Show location statistics
- `--code TEXT`: Location code
- `--type TEXT`: Location type (store-floor, warehouse, storage, home, other)
- `--description TEXT`: Location description
- `--move TEXT`: Move item (specify SKU)
- `--to TEXT`: Target location for move operation
- `--deactivate TEXT`: Deactivate location (specify code)
- `--suggest`: Suggest location code based on type and description

**Location Types:**
- `store-floor`: Retail floor display
- `warehouse`: Main storage facility
- `storage`: Secondary storage
- `home`: Home storage
- `other`: Custom location type

**Examples:**
```bash
# Create locations
inv location --create --code=STORE-A1 --type=store-floor --description="Store Floor Section A1"
inv location --create --code=WAREHOUSE-B2 --type=warehouse --description="Warehouse Bay B2"

# List and stats
inv location --list                    # Active locations
inv location --list --show-inactive    # Include inactive
inv location --stats                   # Statistics

# Operations
inv location --move=NIK001 --to=WAREHOUSE-B2
inv location --deactivate=OLD-STORAGE
inv location --suggest --type=warehouse --description="Main Storage"
```

**Output:** Location creation confirmation, lists, or operation results

---

## `update-location` - Modify Locations

**Purpose:** Update existing location details.

**Usage:**
```bash
inv update-location [OPTIONS] CODE
```

**Arguments:**
- `CODE` *(required)*: Location code to update

**Options:**
- `--type TEXT`: New location type
- `--description TEXT`: New description
- `--activate`: Reactivate location

**Examples:**
```bash
inv update-location STORE-A1 --description="Updated description"
inv update-location OLD-STORAGE --activate
inv update-location WAREHOUSE-A --type=storage
```

**Output:** Update confirmation with changed details

---

## `find-location` - Search Locations

**Purpose:** Find locations by code or description.

**Usage:**
```bash
inv find-location SEARCH_TERM
```

**Arguments:**
- `SEARCH_TERM` *(required)*: Search term for location code or description

**Examples:**
```bash
inv find-location "store"     # Search for locations with "store"
inv find-location "A1"        # Search for locations with "A1"
```

**Output:** List of matching locations

---

# Export and Import Commands

## `export-inventory` - Export Item Data

**Purpose:** Export inventory data in multiple formats with comprehensive filtering.

**Usage:**
```bash
inv export-inventory [OPTIONS] {csv|json|excel}
```

**Arguments:**
- `{csv|json|excel}` *(required)*: Export format

**Options:**
- `-o, --output TEXT`: Output file path (auto-generated if not provided)
- `--filter-brand TEXT`: Filter by brand
- `--filter-status TEXT`: Filter by status
- `--filter-condition TEXT`: Filter by condition
- `--filter-location TEXT`: Filter by location code
- `--ownership-type [owned|consignment]`: Filter by ownership type
- `--include-photos`: Include photo information
- `--include-consigner`: Include consigner details
- `--date-from TEXT`: Include items added after this date (YYYY-MM-DD)
- `--date-to TEXT`: Include items added before this date (YYYY-MM-DD)

**Examples:**
```bash
# Basic exports
inv export-inventory csv
inv export-inventory json --output=backup.json
inv export-inventory excel

# Filtered exports
inv export-inventory csv --filter-brand=nike --include-photos
inv export-inventory json --filter-status=available --ownership-type=consignment
inv export-inventory excel --date-from=2024-01-01 --date-to=2024-12-31

# Comprehensive export
inv export-inventory json --include-photos --include-consigner
```

**Output:** Export file creation confirmation with file path and record count

---

## `export-consigners` - Export Consigner Data

**Purpose:** Export consigner information and statistics.

**Usage:**
```bash
inv export-consigners [OPTIONS] {csv|json|excel}
```

**Arguments:**
- `{csv|json|excel}` *(required)*: Export format

**Options:**
- `-o, --output TEXT`: Output file path
- `--include-stats`: Include detailed statistics
- `--include-items`: Include items for each consigner

**Examples:**
```bash
inv export-consigners csv
inv export-consigners json --include-stats
inv export-consigners excel --include-stats --include-items --output=consigners.xlsx
```

**Output:** Export confirmation with consigner count

---

## `export-locations` - Export Location Data

**Purpose:** Export location information and item counts.

**Usage:**
```bash
inv export-locations [OPTIONS] {csv|json|excel}
```

**Arguments:**
- `{csv|json|excel}` *(required)*: Export format

**Options:**
- `-o, --output TEXT`: Output file path
- `--include-items`: Include item counts for each location

**Examples:**
```bash
inv export-locations csv
inv export-locations json --include-items
inv export-locations excel --output=locations.xlsx
```

**Output:** Export confirmation with location count

---

## `export-template` - Generate Import Templates

**Purpose:** Create templates for bulk data import operations.

**Usage:**
```bash
inv export-template [OPTIONS] {csv|excel}
```

**Arguments:**
- `{csv|excel}` *(required)*: Template format

**Options:**
- `-o, --output TEXT`: Template file path
- `--include-examples`: Include example data rows

**Examples:**
```bash
inv export-template csv
inv export-template excel --include-examples
inv export-template csv --output=import_template.csv
```

**Output:** Template file creation confirmation

---

# API Server Commands

## `api-server` - Start REST API

**Purpose:** Launch the REST API server for external integrations.

**Usage:**
```bash
inv api-server [OPTIONS]
```

**Options:**
- `--host TEXT`: Host to bind to (default: 127.0.0.1)
- `--port INTEGER`: Port to bind to (default: 5000)
- `--debug`: Enable debug mode

**Available Endpoints:**
- `GET /api/items` - List items with filtering
- `GET /api/items/<sku>` - Get specific item
- `PUT /api/items/<sku>` - Update item
- `GET /api/locations` - List locations
- `GET /api/consigners` - List consigners
- `GET /api/search?q=<query>` - Search items
- `GET /api/stats` - Inventory statistics

**Examples:**
```bash
inv api-server                               # Start on localhost:5000
inv api-server --host=0.0.0.0 --port=8080   # Custom host and port
inv api-server --debug                       # Debug mode
```

**Output:** Server startup confirmation with endpoint information

---

## `api-test` - Test API Connectivity

**Purpose:** Test API server endpoints and connectivity.

**Usage:**
```bash
inv api-test [OPTIONS]
```

**Options:**
- `--host TEXT`: API server host (default: localhost)
- `--port INTEGER`: API server port (default: 5000)

**Examples:**
```bash
inv api-test                                # Test localhost:5000
inv api-test --host=localhost --port=8080   # Test custom endpoint
```

**Output:** Connection test results and endpoint status

---

## `api-docs` - View API Documentation

**Purpose:** Display comprehensive API documentation.

**Usage:**
```bash
inv api-docs
```

**Examples:**
```bash
inv api-docs    # Show complete API documentation
```

**Output:** Complete API documentation with endpoints and examples

---

## `generate-api-client` - Create API Clients

**Purpose:** Generate client code for different programming languages.

**Usage:**
```bash
inv generate-api-client [OPTIONS] {python|javascript|curl}
```

**Arguments:**
- `{python|javascript|curl}` *(required)*: Client type to generate

**Options:**
- `--output TEXT`: Output file path
- `--host TEXT`: API host (default: localhost)
- `--port INTEGER`: API port (default: 5000)

**Examples:**
```bash
# Generate clients
inv generate-api-client python
inv generate-api-client javascript --output=client.js
inv generate-api-client curl --output=examples.sh

# Custom API endpoint
inv generate-api-client python --host=myserver.com --port=8080
```

**Output:** Client code generation confirmation with file path

---

# System Management Commands

## `setup` - Initial Configuration

**Purpose:** Interactive setup wizard for first-time system configuration.

**Usage:**
```bash
inv setup
```

**Configuration Items:**
- Database connection (SQLite)
- Service key generation
- Default location setup
- Consignment split percentage
- Photo storage path configuration

**Examples:**
```bash
inv setup    # Run interactive setup wizard
```

**Output:** Configuration confirmation with setup summary

---

## `test-connection` - Verify Database

**Purpose:** Test database connectivity and configuration.

**Usage:**
```bash
inv test-connection
```

**Examples:**
```bash
inv test-connection    # Test current database connection
```

**Output:** Connection test results with database information

---

## `backup-database` - Create Backups

**Purpose:** Create complete database backups with optional features.

**Usage:**
```bash
inv backup-database [OPTIONS]
```

**Options:**
- `-o, --output TEXT`: Backup file path (auto-generated if not provided)
- `--compress`: Compress the backup file
- `--include-photos`: Include photos in backup archive

**Examples:**
```bash
inv backup-database                                      # Basic backup
inv backup-database --output=backup.json --compress     # Compressed backup
inv backup-database --include-photos                    # Full backup with photos
```

**Output:** Backup creation confirmation with file size and location

---

# Command Categories

## **By Frequency of Use**

### **Daily Operations**
- `add` - Add new items
- `search` - Find items
- `add-photo` - Add photos
- `update-status` - Quick status updates
- `move` - Relocate items

### **Weekly Operations**
- `edit` - Update item details
- `consign-sold` - Process sales
- `backup-database` - Create backups
- `photo-stats` - Check storage

### **Monthly Operations**
- `export-inventory` - Data exports
- `payout-summary` - Review payouts
- `optimize-photos` - Storage optimization
- `consigner-report` - Generate reports

### **Setup/Maintenance**
- `setup` - Initial configuration
- `location` - Manage locations
- `test-connection` - Verify system
- `find-duplicate-photos` - Clean up storage

## **By Data Type**

### **Item Management**
- `add`, `edit`, `show`, `search`, `move`, `update-status`, `add-variant`

### **Photo Management**
- `add-photo`, `bulk-add-photos`, `copy-photos`, `list-photos`, `remove-photo`, `set-primary-photo`, `optimize-photos`, `photo-stats`, `find-duplicate-photos`, `remove-exif`

### **Consignment Management**
- `intake`, `consign-sold`, `hold-item`, `consign`, `list-consigners`, `consigner-report`, `payout-summary`

### **Location Management**
- `location`, `update-location`, `find-location`

### **Data Management**
- `export-inventory`, `export-consigners`, `export-locations`, `export-template`, `backup-database`

### **API/Integration**
- `api-server`, `api-test`, `api-docs`, `generate-api-client`

### **System Administration**
- `setup`, `test-connection`

---

# Common Patterns

## **Filtering Patterns**

Most search and export commands support common filtering patterns:

```bash
# Brand filtering
--filter-brand=nike
--brand=nike

# Status filtering
--filter-status=available
--available
--sold
--held

# Date filtering
--date-from=2024-01-01
--date-to=2024-12-31

# Price filtering
--min-price=100
--max-price=500

# Ownership filtering
--ownership-type=consignment
--consignment
--owned
```

## **Output Patterns**

Commands follow consistent output patterns:

```bash
# Count operations
--count              # Show count only
--stats              # Include statistics
--detailed           # Show detailed information

# Include additional data
--include-photos     # Include photo information
--include-consigner  # Include consigner details
--include-items      # Include item lists
--include-stats      # Include statistics
```

## **File Operations**

File-related commands use consistent patterns:

```bash
# Output specification
-o, --output=filename.ext    # Custom output file
--output=filename.ext        # Auto-generate if not provided

# File processing
--pattern="*.jpg"            # File pattern matching
--filename="custom.jpg"      # Custom filename
--compress                   # Compression option
```

## **Interactive Mode**

Many commands support interactive mode:

```bash
-i, --interactive           # Interactive mode with prompts
--confirm                   # Skip confirmation prompts
--suggest                   # Get suggestions
```

## **Common Flags**

Frequently used flags across commands:

```bash
--help                      # Command help
--debug                     # Debug mode
--all                       # Apply to all items
--cleanup                   # Perform cleanup
--remove                    # Remove/delete operation
--primary                   # Set as primary
--release                   # Release from hold
--activate                  # Activate/reactivate
```

---

**For interactive help with any command, use: `inv [command] --help`**

**Complete documentation available at: [README.md](README.md)**