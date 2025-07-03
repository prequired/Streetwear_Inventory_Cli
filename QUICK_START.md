# ⚡ Quick Start Guide

**Get your streetwear inventory system running in 5 minutes!**

---

## 🚀 **Installation (2 minutes)**

### **Option 1: Development Setup**
```bash
# 1. Clone the repository
git clone <repository-url>
cd streetwear-inventory-cli

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install in development mode
pip install -e .

# 4. Run setup wizard
inv setup
```

### **Option 2: Package Installation**
```bash
# 1. Install package
pip install streetwear-inventory-cli

# 2. Install optional features (recommended)
pip install streetwear-inventory-cli[all]  # API + Excel support

# 3. Run setup wizard
inv setup
```

**Setup Wizard Answers:**
- **Database URL**: `sqlite:///streetwear_inventory.db` (press Enter for default)
- **Service Key**: `local_key` (press Enter for default)
- **Default location**: `HOME`
- **Consignment split**: `70`
- **Photo storage**: `./photos` (press Enter for default)

---

## 📦 **Create Your First Location (30 seconds)**

```bash
inv location --create --code=HOME --type=home --description="Home Storage"
```

**Optional: Create additional locations**
```bash
inv location --create --code=STORE-A1 --type=store-floor --description="Store Floor Section A1"
inv location --create --code=WAREHOUSE --type=warehouse --description="Main Warehouse"
```

---

## 👟 **Add Your First Items (1 minute)**

### **Add Sneakers**
```bash
# Nike Air Jordan 1
inv add nike "air jordan 1" 10 chicago DS 250 200 box HOME

# Adidas Yeezy 350
inv add adidas "yeezy 350 v2" 9.5 "cream white" VNDS 220 180 box HOME

# Add with notes
inv add nike "dunk low" 10.5 "panda" DS 120 100 box HOME --notes="StockX purchase"
```

### **Add Clothing**  
```bash
# Supreme Box Logo Tee
inv add supreme "box logo tee" L white DS 120 100 tag HOME

# Off-White Hoodie
inv add off-white "diag hoodie" M black VNDS 300 250 tag HOME
```

### **Command Breakdown:**
```bash
inv add BRAND "MODEL" SIZE COLOR CONDITION CURRENT_PRICE COST BOX_STATUS LOCATION
```

- **BRAND**: nike, adidas, supreme, off-white, etc.
- **MODEL**: Use quotes for multi-word names
- **SIZE**: 10, 10.5, M, L, XL, etc.
- **COLOR**: Color or colorway name
- **CONDITION**: DS (deadstock), VNDS (very near deadstock), Used
- **CURRENT_PRICE**: Your selling price
- **COST**: What you paid for it
- **BOX_STATUS**: box, tag, both, neither
- **LOCATION**: Location code you created

---

## 🔍 **Search Your Inventory (30 seconds)**

### **Basic Searches**
```bash
# See all items
inv search

# Search by brand
inv search --brand nike

# Search by text
inv search "jordan"

# Show only available items
inv search --available
```

### **Advanced Searches**
```bash
# Nike items over $200
inv search --brand=nike --min-price=200

# Available items in specific location
inv search --location=HOME --available

# Get counts only
inv search --brand=supreme --count
```

---

## 📷 **Add Photos (1 minute)**

### **Single Photo**
```bash
# Add a photo and set as primary
inv add-photo NIK001 /path/to/your/photo.jpg --primary

# Add with custom filename
inv add-photo SUP001 ./photo.jpg --filename="front_view.jpg"
```

### **Multiple Photos**
```bash
# Add all photos from a directory
inv bulk-add-photos NIK001 /path/to/photos/ --pattern="*.jpg" --set-primary=1

# Copy photos between items (useful for variants)
inv copy-photos NIK001 NIK002
```

### **View Photos**
```bash
# List photos for an item
inv list-photos NIK001

# Show detailed photo info
inv list-photos NIK001 --details
```

---

## 💰 **Process Sales (1 minute)**

### **Mark Items as Sold**
```bash
# Basic sale
inv update-status NIK001 --status=sold --sold-price=275

# Sale with platform info
inv update-status SUP001 --status=sold --sold-price=150 --sold-platform=StockX
```

### **Advanced Item Management**
```bash
# Edit item details
inv edit NIK001  # Interactive editing

# Move item to different location
inv move NIK001 STORE-A1

# Show detailed item info
inv show NIK001
```

---

## 🤝 **Consignment Workflow (2 minutes)**

### **Intake New Consignment**
```bash
# Single item intake
inv intake --consigner="John Doe" --phone="(555) 123-4567" --split=70

# Multiple items
inv intake --batch=3 --consigner="Mike Chen" --phone="(555) 234-5678" --email="mike@example.com"
```

### **Process Consignment Sale**
```bash
# Mark consignment item as sold
inv consign-sold JOR001 285.00 --platform=stockx --buyer="StockX Buyer"

# Calculate payout for consigner
inv consign "John Doe" --show-items

# Mark payout as paid
inv consign "John Doe" --mark-paid
```

### **Manage Consigners**
```bash
# List all consigners
inv list-consigners --stats

# Generate detailed report
inv consigner-report "John Doe"

# View payout summary
inv payout-summary --pending-only
```

---

## 📊 **Export Your Data (30 seconds)**

### **Basic Exports**
```bash
# Export to CSV
inv export-inventory csv

# Export to JSON with photos
inv export-inventory json --include-photos

# Export to Excel
inv export-inventory excel --include-photos --include-consigner
```

### **Filtered Exports**
```bash
# Export only Nike items
inv export-inventory csv --filter-brand=nike

# Export available items only
inv export-inventory json --filter-status=available

# Export consignment items
inv export-inventory excel --ownership-type=consignment
```

---

## 🏪 **Manage Locations (1 minute)**

### **Location Operations**
```bash
# List all locations
inv location --list --stats

# Create new location
inv location --create --code=STORE-B1 --type=store-floor --description="Store Floor B1"

# Find locations
inv find-location "store"

# Update location
inv update-location STORE-A1 --description="Updated Store Section A1"
```

---

## 🛡️ **Photo Privacy & Management**

### **EXIF Removal (Automatic)**
All photos automatically have EXIF metadata removed for privacy protection.

### **Manual EXIF Removal**
```bash
# Remove EXIF from external photo
inv remove-exif photo.jpg

# Remove EXIF and save to new file
inv remove-exif input.jpg clean_output.jpg
```

### **Photo Optimization**
```bash
# Check photo storage
inv photo-stats

# Optimize all photos
inv optimize-photos --all

# Find and remove duplicates
inv find-duplicate-photos --remove
```

---

## 🌐 **API Server (Optional)**

### **Start API Server**
```bash
# Start on localhost:5000
inv api-server

# Start on all interfaces
inv api-server --host=0.0.0.0 --port=8080 --debug
```

### **Test API**
```bash
# Test connectivity
inv api-test

# View API documentation
inv api-docs

# Generate Python client
inv generate-api-client python --output=client.py
```

---

## 🔄 **Daily Commands Cheat Sheet**

### **Most Used Commands**
```bash
# Add new item
inv add nike "air jordan 1" 10 chicago DS 250 200 box HOME

# Search inventory
inv search --brand=nike --available

# Add photo
inv add-photo NIK001 photo.jpg --primary

# Mark as sold
inv update-status NIK001 --status=sold --sold-price=275

# Export data
inv export-inventory csv
```

### **Weekly Maintenance**
```bash
# Backup database
inv backup-database --compress

# Check photo storage
inv photo-stats

# Optimize photos
inv optimize-photos --all

# Export for records
inv export-inventory excel --include-photos
```

---

## 🆘 **Quick Troubleshooting**

### **Database Issues**
```bash
# Test connection
inv test-connection

# Reset if needed
rm streetwear_inventory.db
inv setup
```

### **Photo Issues**
```bash
# Check storage
inv photo-stats

# Clean up
inv photo-stats --cleanup
inv find-duplicate-photos --remove
```

### **Command Help**
```bash
# Get help for any command
inv [command] --help

# Example
inv add --help
inv search --help
```

---

## 🎯 **Next Steps**

### **Ready to Use!**
You now have a fully functional streetwear inventory system. Here's what to do next:

1. **Start adding your inventory** with the `add` command
2. **Take and add photos** to your items for better tracking
3. **Set up additional locations** if you have multiple storage areas
4. **Create regular backups** with `backup-database --compress`
5. **Explore advanced features** in the full [README.md](README.md)

### **Advanced Features to Explore**
- **Consignment Management**: Full intake and payout workflow
- **API Integration**: REST API for external tools
- **Bulk Operations**: Import templates and bulk photo management
- **Analytics**: Location stats and inventory reports

### **Get More Help**
- **Complete Command List**: See [COMMAND_REFERENCE.md](COMMAND_REFERENCE.md)
- **Full Documentation**: Read [README.md](README.md)
- **API Documentation**: Check [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- **Command Help**: Run `inv [command] --help` for any command

---

**🎉 You're ready to manage your streetwear inventory like a pro!**

**Total setup time: ~5 minutes** ⏱️