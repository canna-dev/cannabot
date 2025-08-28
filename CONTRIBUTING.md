# Contributing to CannaBot

Thank you for your interest in contributing to CannaBot! This document provides guidelines and instructions for contributing to the project.

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- Discord Developer Account (for bot testing)
- Basic knowledge of Discord.py and async programming

### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/yourusername/CannaBot.git
   cd CannaBot
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux  
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install pytest pytest-asyncio black flake8  # Development tools
   ```

4. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your Discord bot token
   ```

5. **Run tests**
   ```bash
   python tests/test_simple.py
   ```

## 📋 Development Guidelines

### Code Style

- **Python Style**: Follow PEP 8 guidelines
- **Formatting**: Use Black for code formatting (`black .`)
- **Linting**: Use flake8 for linting (`flake8 .`)
- **Type Hints**: Use type hints for function parameters and returns
- **Docstrings**: Use Google-style docstrings for all functions and classes

### Example Code Style

```python
async def search_strain(self, name: str) -> Optional[pd.Series]:
    """
    Search for a strain by name in the database.
    
    Args:
        name (str): The strain name to search for (case-insensitive)
        
    Returns:
        Optional[pd.Series]: Strain data if found, None otherwise
        
    Raises:
        DatabaseError: If database connection fails
    """
    if not name.strip():
        return None
        
    # Implementation here
    pass
```

### Project Structure

- **bot/**: Main bot code
  - **main.py**: Bot entry point
  - **config.py**: Configuration management
  - **commands/**: Command implementations
  - **database/**: Database models and operations
  - **services/**: Business logic
  - **utils/**: Utility functions
- **tests/**: Test suite
- **data/**: Data files (strain database, etc.)
- **docs/**: Documentation
- **.github/**: GitHub workflows and templates

## 🐛 Reporting Issues

### Bug Reports

When reporting bugs, please include:

1. **Description**: Clear description of the issue
2. **Steps to reproduce**: Detailed steps to recreate the bug
3. **Expected behavior**: What should have happened
4. **Actual behavior**: What actually happened
5. **Environment**: Python version, OS, Discord.py version
6. **Logs**: Relevant error messages or log output

### Feature Requests

For feature requests, please include:

1. **Use case**: Why is this feature needed?
2. **Description**: Detailed description of the proposed feature
3. **Examples**: How would users interact with this feature?
4. **Alternatives**: Are there existing workarounds?

## 💻 Making Changes

### Workflow

1. **Create a branch** for your feature/fix
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the guidelines above

3. **Write tests** for new functionality
   ```bash
   # Add tests to tests/test_simple.py or create new test files
   python tests/test_simple.py
   ```

4. **Run the full test suite**
   ```bash
   # Code formatting
   black .
   
   # Linting
   flake8 .
   
   # Tests
   python tests/test_simple.py
   ```

5. **Commit your changes**
   ```bash
   git add .
   git commit -m "Add feature: brief description of changes"
   ```

6. **Push and create a Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```

### Commit Message Guidelines

- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit first line to 72 characters
- Reference issues and pull requests when applicable

Examples:
```
Add strain recommendation algorithm
Fix bioavailability calculation for edibles
Update help command with new examples
Refactor database connection handling
```

## 🧪 Testing

### Running Tests

```bash
# Simple test runner (no dependencies)
python tests/test_simple.py

# Full pytest suite (requires pytest)
python -m pytest tests/ -v

# Test specific modules
python -m pytest tests/test_core.py -v
```

### Writing Tests

- Add tests for all new functionality
- Test both success and failure cases
- Use descriptive test names
- Mock external dependencies (Discord API, database)

### Test Structure

```python
def test_feature_name():
    """Test description of what is being tested."""
    # Arrange
    input_data = "test_input"
    expected_result = "expected_output"
    
    # Act
    result = function_to_test(input_data)
    
    # Assert
    assert result == expected_result, "Descriptive error message"
```

## 📚 Documentation

### Code Documentation

- All public functions and classes must have docstrings
- Use type hints for better code clarity
- Comment complex logic or algorithms
- Keep comments up to date with code changes

### User Documentation

- Update README.md for new features
- Add examples for new commands
- Update help text in the bot
- Consider creating separate documentation files for complex features

## 🔍 Code Review Process

### Pull Request Requirements

1. **Description**: Clear description of changes and why they're needed
2. **Testing**: Evidence that changes have been tested
3. **Documentation**: Updated documentation if applicable
4. **No breaking changes**: Unless discussed and approved
5. **Passes CI**: All automated checks must pass

### Review Criteria

- Code follows project style guidelines
- Changes are well-tested
- Documentation is updated
- No security vulnerabilities introduced
- Performance impact is acceptable

## 🏷️ Release Process

### Versioning

We use [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backwards compatible)
- **PATCH**: Bug fixes (backwards compatible)

### Release Checklist

1. Update version numbers
2. Update CHANGELOG.md
3. Run full test suite
4. Create release notes
5. Tag release in Git
6. Deploy to production

## 🤝 Community Guidelines

### Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Respect different perspectives and experiences

### Getting Help

- **Discord**: Join our development Discord server
- **Issues**: Create a GitHub issue for bugs or questions
- **Discussions**: Use GitHub Discussions for general questions

## 🎯 Priority Areas

We're currently looking for contributions in:

1. **Testing**: Expand test coverage
2. **Documentation**: Improve user guides and API docs
3. **Performance**: Optimize database queries and memory usage
4. **Features**: New strain analysis capabilities
5. **Mobile**: Mobile-friendly Discord interactions
6. **Internationalization**: Multi-language support

## 📞 Contact

- **Project Maintainer**: [Contact Info]
- **Discord Server**: [Server Link]
- **Email**: [Project Email]

Thank you for contributing to CannaBot! 🌿
