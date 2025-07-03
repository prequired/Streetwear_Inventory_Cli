# Configuration Guide

This guide shows how the `config.yaml` file affects system behavior and how to customize it for your needs.

## Configuration File Structure

Your `config.yaml` file controls all major aspects of the inventory system:

```yaml
database:
  url: "sqlite:///streetwear_inventory.db"

brand_prefixes:
  nike: "NIK"
  adidas: "ADI"
  supreme: "SUP"
  jordan: "JOR"
  yeezy: "YZY"

defaults:
  location: ""
  consignment_split: 70

photos:
  storage_path: "./photos"
```

## How Each Setting Affects the System

### 1. Database Configuration

**Setting:** `database.url`

**What it does:** Determines where your inventory data is stored.

**Examples:**
- `sqlite:///inventory.db` - Single file database (recommended)
- `sqlite:///data/production.db` - Database in data folder
- `sqlite:///:memory:` - Temporary database (testing only)

**Test it:**
```bash
# Change database.url in config.yaml, then:
python -c "from inv.cli import cli; cli()" add nike "test shoe" 10 white DS 100 80 box TEST-LOC
# Check if new database file is created at your specified location
```

### 2. Brand Prefixes

**Setting:** `brand_prefixes`

**What it does:** Controls the 3-letter prefixes used in SKU generation.

**Default brands:**
- `nike: NIK` → generates SKUs like NIK001, NIK002, etc.
- `adidas: ADI` → generates SKUs like ADI001, ADI002, etc.
- `supreme: SUP` → generates SKUs like SUP001, SUP002, etc.

**Adding custom brands:**
```yaml
brand_prefixes:
  nike: "NIK"
  adidas: "ADI"
  supreme: "SUP"
  jordan: "JOR"
  yeezy: "YZY"
  off-white: "OFW"        # New custom brand
  fear-of-god: "FOG"      # New custom brand
  stone-island: "STI"     # New custom brand
```

**Test it:**
```bash
# Add custom brand to config.yaml, then:
python -c "from inv.cli import cli; cli()" add off-white "chicago 1" 10 white DS 2000 1500 box TEST-LOC
# Should generate SKU: OFW001
```

### 3. Default Settings

#### Default Consignment Split

**Setting:** `defaults.consignment_split`

**What it does:** Sets the default percentage that consigners receive when you don't specify a custom split.

**Examples:**
- `70` = Consigner gets 70%, store gets 30%
- `75` = Consigner gets 75%, store gets 25%
- `80` = Consigner gets 80%, store gets 20%

**Test it:**
```bash
# Change defaults.consignment_split to 80 in config.yaml, then:
python -c "from inv.cli import cli; cli()" intake --consigner "Test User" --phone "(555) 123-4567"
# When prompted, enter: nike, test shoe, 10, white, DS, 100, box, (enter)
# Should show: "Split: 80% to consigner"
```

#### Default Location

**Setting:** `defaults.location`

**What it does:** Automatically uses this location when adding items (if set).

**Example:**
```yaml
defaults:
  location: "MAIN-FLOOR"
  consignment_split: 70
```

### 4. Photo Storage

**Setting:** `photos.storage_path`

**What it does:** Determines where product photos are stored on your filesystem.

**Examples:**
- `./photos` - Photos folder in current directory
- `./store_photos` - Custom folder name
- `/var/data/inventory_photos` - Absolute path (Linux/Mac)
- `C:\InventoryPhotos` - Absolute path (Windows)

**Test it:**
```bash
# Change photos.storage_path to "./custom_photos" in config.yaml, then:
python -c "
from inv.utils.photos import PhotoManager
pm = PhotoManager()
print(f'Photo storage: {pm.storage_path}')
print(f'Directory exists: {pm.storage_path.exists()}')
"
# Should show your custom path
```

## Validation

Always validate your configuration after making changes:

```bash
python -c "from inv.cli import cli; cli()" validate-config
```

This command will:
- ✅ Check configuration file syntax
- ✅ Validate all required sections exist
- ✅ Test database connection
- ✅ Show current settings summary

## Common Customization Scenarios

### High-End Consignment Store

For stores dealing with premium items, you might want higher default splits:

```yaml
database:
  url: "sqlite:///data/premium_inventory.db"

brand_prefixes:
  nike: "NIK"
  adidas: "ADI"
  supreme: "SUP"
  jordan: "JOR"
  off-white: "OFW"
  fear-of-god: "FOG"
  balenciaga: "BAL"

defaults:
  location: "SHOWROOM"
  consignment_split: 80  # Higher split for premium consigners

photos:
  storage_path: "./premium_photos"
```

### Multi-Location Store

For stores with multiple locations:

```yaml
database:
  url: "sqlite:///data/multi_location_inventory.db"

brand_prefixes:
  nike: "NIK"
  adidas: "ADI"
  supreme: "SUP"
  jordan: "JOR"
  yeezy: "YZY"

defaults:
  location: "MAIN-STORE"  # Set your primary location
  consignment_split: 70

photos:
  storage_path: "./photos"
```

### Streetwear Boutique

For specialized streetwear stores:

```yaml
database:
  url: "sqlite:///boutique_inventory.db"

brand_prefixes:
  nike: "NIK"
  adidas: "ADI"
  supreme: "SUP"
  jordan: "JOR"
  yeezy: "YZY"
  off-white: "OFW"
  fear-of-god: "FOG"
  stone-island: "STI"
  travis-scott: "TRS"
  fragment: "FRG"
  chrome-hearts: "CHR"

defaults:
  location: "FLOOR"
  consignment_split: 75

photos:
  storage_path: "./boutique_photos"
```

## Testing Configuration Changes

Use these test scripts to verify your configuration works:

### Test Brand Prefixes
```bash
# Test custom brand prefix
python test_config_effects.py
```

### Test Database Location
```bash
# Add an item and check if database file appears in correct location
python -c "from inv.cli import cli; cli()" add nike "config test" 10 white DS 100 80 box TEST-LOC
ls -la *.db  # Check database files created
```

### Test Photo Storage
```bash
# Check PhotoManager uses your custom path
python -c "
from inv.utils.photos import PhotoManager
from inv.utils.config import get_config
config = get_config()
pm = PhotoManager()
print(f'Config setting: {config["photos"]["storage_path"]}')
print(f'PhotoManager path: {pm.storage_path}')
print(f'Paths match: {str(pm.storage_path) == config["photos"]["storage_path"]}')
"
```

### Test Consignment Split
```bash
# Test default split percentage
python -c "from inv.cli import cli; cli()" intake --consigner "Config Test" --phone "(555) 999-0000"
# Enter test item details and verify split percentage shown
```

## Troubleshooting

### Configuration Not Taking Effect

1. **Check file location**: Configuration file must be named `config.yaml` in your working directory
2. **Validate syntax**: Run `validate-config` command to check for errors
3. **Restart if needed**: Some changes may require restarting your session
4. **Clear cache**: Configuration is cached; use `force_reload=True` in code if needed

### Common Errors

**"Database URL must be provided"**
- Check that `database.url` is set and not empty

**"Brand prefix must be exactly 3 characters"**
- All brand prefixes must be exactly 3 uppercase letters

**"consignment_split must be an integer between 0 and 100"**
- Split percentage must be a whole number from 0-100

**"Missing required section"**
- Ensure all sections exist: `database`, `brand_prefixes`, `defaults`, `photos`

## Best Practices

1. **Backup your config**: Keep a backup of your working configuration
2. **Use absolute paths**: For production, consider absolute paths for database and photos
3. **Test after changes**: Always run `validate-config` after modifications
4. **Version control**: Keep your config in version control if working in a team
5. **Document customizations**: Note why you made specific changes

## Example Complete Configuration

Here's a production-ready configuration with all options:

```yaml
# Production inventory configuration
database:
  url: "sqlite:///data/production_inventory.db"

# Brand prefixes for SKU generation
brand_prefixes:
  nike: "NIK"
  adidas: "ADI"
  supreme: "SUP"
  jordan: "JOR"
  yeezy: "YZY"
  off-white: "OFW"
  fear-of-god: "FOG"
  stone-island: "STI"
  balenciaga: "BAL"
  travis-scott: "TRS"
  fragment: "FRG"

# Default values for new entries
defaults:
  location: "MAIN-FLOOR"
  consignment_split: 75

# Photo storage configuration
photos:
  storage_path: "./store_photos"
```

This configuration:
- Stores data in `data/production_inventory.db`
- Supports 11 different brands
- Uses main floor as default location
- Sets 75% as default consignment split
- Stores photos in `store_photos` directory