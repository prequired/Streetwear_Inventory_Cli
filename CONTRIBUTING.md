# 🤝 Contributing to Streetwear Inventory CLI

Thank you for your interest in contributing! This guide will help you get started with contributing to the project.

## 📋 **Table of Contents**
- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contributing Process](#contributing-process)
- [Code Standards](#code-standards)
- [Testing](#testing)
- [Documentation](#documentation)

## 🤝 **Code of Conduct**

This project is built for the streetwear community and small business owners. We're committed to providing a welcoming and inclusive experience for everyone. Please be respectful and constructive in all interactions.

## 🚀 **Getting Started**

### **What You Can Contribute**
- 🐛 **Bug fixes**: Fix issues or improve error handling
- ✨ **Features**: Add new functionality or commands
- 📚 **Documentation**: Improve docs, add examples, or create guides
- 🧪 **Tests**: Add test coverage or improve existing tests
- 🎨 **UI/UX**: Improve CLI interface and user experience
- 🔧 **Performance**: Optimize code or database queries

### **Areas That Need Help**
- E-commerce platform integrations (eBay, StockX, GOAT APIs)
- Mobile app companion
- Advanced analytics and reporting
- Multi-user access controls
- Cloud storage integration
- Performance optimizations

## 🛠️ **Development Setup**

### **1. Fork and Clone**
```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/streetwear-inventory-cli.git
cd streetwear-inventory-cli
```

### **2. Set Up Development Environment**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements.txt
pip install flask flask-cors pandas openpyxl  # Optional features

# Install in development mode
pip install -e .
```

### **3. Set Up Test Environment**
```bash
# Run tests to ensure everything works
python -m pytest tests/ -v

# Create test configuration
python -m inv.cli setup
# Use SQLite for development
# Set test photos path

# Create test location
python -m inv.cli location add TEST-LOC test "Test Location"
```

### **4. Verify Installation**
```bash
# Test core functionality
python -m inv.cli add nike "test item" 10 white DS 100 80 box TEST-LOC
python -m inv.cli search --brand nike
python -m inv.cli export-inventory csv --output test.csv

# Clean up test data
rm test.csv
```

## 🔄 **Contributing Process**

### **1. Create an Issue** (Recommended)
Before starting work, create an issue to:
- Describe the problem or feature
- Get feedback from maintainers
- Avoid duplicate work
- Plan the implementation

### **2. Create a Feature Branch**
```bash
# Create branch from main
git checkout main
git pull origin main
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/bug-description
```

### **3. Make Your Changes**
- Follow the [Code Standards](#code-standards)
- Add tests for new functionality
- Update documentation as needed
- Keep commits focused and atomic

### **4. Test Your Changes**
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/test_add.py  # For item management changes
python -m pytest tests/test_search.py  # For search changes
python -m pytest tests/test_business_logic.py  # For business logic

# Test your specific changes
python -m pytest tests/ -k "test_your_feature"

# Ensure no regressions
python -m pytest tests/ --tb=short
```

### **5. Update Documentation**
- Update README.md if adding new commands
- Add to CHANGELOG.md under "Unreleased"
- Update docstrings for new functions
- Add examples for new features

### **6. Submit Pull Request**
```bash
# Push your branch
git push origin feature/your-feature-name

# Create pull request on GitHub with:
# - Clear title and description
# - Reference to related issue
# - List of changes made
# - Screenshots/examples if applicable
```

## 📝 **Code Standards**

### **Python Code Style**
```python
# Follow PEP 8 style guidelines
# Use meaningful variable names
# Add type hints where helpful
# Keep functions focused and small

# Example function structure:
def add_item(brand: str, model: str, size: str) -> str:
    """Add new item to inventory.
    
    Args:
        brand: Item brand name
        model: Item model/name
        size: Item size
        
    Returns:
        Generated SKU for the item
        
    Raises:
        ValueError: If validation fails
    """
    # Implementation here
```

### **CLI Command Structure**
```python
@click.command()
@with_database
@click.argument('required_arg')
@click.option('--optional-flag', help='Description of flag')
def your_command(required_arg, optional_flag):
    """Brief description of what the command does
    
    Usage:
      inv your-command value --optional-flag
      inv your-command value
    
    Options:
      --optional-flag  Description of the flag
    """
    try:
        # Command implementation
        click.echo("✅ Success message")
    except Exception as e:
        click.echo(f"❌ Error: {e}")
```

### **Database Models**
```python
# Follow SQLAlchemy best practices
# Use proper relationships
# Add indexes for performance
# Include validation constraints

class YourModel(Base):
    __tablename__ = 'your_table'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, index=True)
    created_date = Column(TIMESTAMP, default=func.current_timestamp())
    
    # Relationships
    items = relationship("Item", back_populates="your_model")
```

### **Error Handling**
```python
# Consistent error handling pattern
try:
    # Operation that might fail
    result = risky_operation()
    click.echo(f"✅ Success: {result}")
except SpecificException as e:
    click.echo(f"❌ Specific error: {e}")
except Exception as e:
    click.echo(f"❌ Unexpected error: {e}")
    # Optional: Log full traceback for debugging
    import traceback
    traceback.print_exc()
```

## 🧪 **Testing**

### **Test Structure**
```python
# Test file naming: test_[module_name].py
# Test class naming: Test[FeatureName]
# Test function naming: test_[specific_behavior]

class TestItemManagement:
    """Test item management functionality"""
    
    def test_add_basic_item(self, temp_config_and_db):
        """Test adding a basic item to inventory"""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'add', 'nike', 'test shoe', '10', 'white', 'DS', '100', '80', 'box', 'TEST-LOC'
        ])
        
        assert result.exit_code == 0
        assert '✅ Added item' in result.output
        assert 'NIK001' in result.output
```

### **Test Categories**
- **Unit Tests**: Individual function testing
- **Integration Tests**: Command workflow testing
- **Business Logic Tests**: Validation and calculation testing
- **Performance Tests**: Photo and export operations

### **Running Tests**
```bash
# All tests
python -m pytest tests/ -v

# Specific test file
python -m pytest tests/test_add.py -v

# Specific test
python -m pytest tests/test_add.py::TestAddCommand::test_add_basic_item -v

# With coverage
python -m pytest tests/ --cov=inv --cov-report=html
```

## 📚 **Documentation**

### **Code Documentation**
- Add docstrings to all public functions
- Include usage examples in docstrings
- Document complex business logic
- Add type hints where helpful

### **User Documentation**
- Update README.md for new commands
- Add examples to command help text
- Update API documentation if applicable
- Add troubleshooting info for common issues

### **Changelog**
Add entries to CHANGELOG.md under "Unreleased":
```markdown
### Added
- New feature description

### Changed
- Modified behavior description

### Fixed
- Bug fix description
```

## 🎯 **Development Guidelines**

### **Adding New Commands**
1. Create command in appropriate file under `inv/commands/`
2. Register command in `inv/cli.py`
3. Add comprehensive tests
4. Update documentation
5. Add usage examples

### **Modifying Database Schema**
1. Update models in `inv/database/models.py`
2. Add migration logic if needed
3. Update test fixtures
4. Test with existing data
5. Document breaking changes

### **Adding Dependencies**
1. Add to `requirements.txt` with version constraints
2. Make optional dependencies clearly marked
3. Test installation on clean environment
4. Document new dependency requirements

## ❓ **Questions or Issues?**

### **Getting Help**
- Create an issue for questions
- Check existing issues and documentation
- Test locally before asking for help
- Provide minimal reproduction examples

### **Reporting Bugs**
Include in bug reports:
- Python version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Error messages and stack traces

### **Feature Requests**
Include in feature requests:
- Use case description
- Proposed implementation
- Alternatives considered
- Willingness to contribute

## 🙏 **Recognition**

Contributors will be:
- Listed in the README.md contributors section
- Mentioned in CHANGELOG.md for their contributions
- Given credit in commit messages and pull requests

Thank you for helping make this tool better for the streetwear community! 🎉