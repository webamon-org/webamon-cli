# Contributing to Webamon CLI

Thank you for your interest in contributing to **Webamon Search CLI** - The Google of Threat Intelligence! 🚀

## Quick Start

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**
4. **Add tests if applicable**
5. **Submit a pull request**

## Development Setup

### Prerequisites

- Python 3.8+
- Git

### Local Development

1. **Clone your fork:**
```bash
git clone https://github.com/your-username/webamon-cli.git
cd webamon-cli
```

2. **Set up development environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
```

3. **Test your installation:**
```bash
webamon --help
webamon status
```

## Development Guidelines

### Code Style

- Follow PEP 8 Python style guidelines
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions focused and small

### Testing

- Test your changes with both free and pro API tiers
- Verify all output formats work (table, JSON, CSV)
- Test error conditions and edge cases
- Ensure export functionality works correctly

### API Integration

- Use the `WebamonClient` class for all API interactions
- Handle errors gracefully with user-friendly messages
- Respect API rate limits and quotas
- Test with both `search.webamon.com` (free) and `pro.webamon.com` (pro)

## Types of Contributions

### 🐛 Bug Reports

When filing a bug report, please include:

- **Environment**: OS, Python version, CLI version
- **Command used**: Exact command that caused the issue
- **Expected behavior**: What you expected to happen
- **Actual behavior**: What actually happened
- **Error output**: Full error message or unexpected output

### 💡 Feature Requests

When suggesting a new feature:

- **Use case**: Describe the problem you're trying to solve
- **Proposed solution**: How you envision the feature working
- **API compatibility**: Consider impact on existing API endpoints
- **User experience**: How it fits with existing CLI patterns

### 🔧 Code Contributions

**Areas where contributions are especially welcome:**

- **New commands**: Additional API endpoints or utility functions
- **Output formats**: New export formats or display options
- **Error handling**: Better error messages and recovery
- **Documentation**: Examples, tutorials, or improved help text
- **Performance**: Optimization of API calls or data processing
- **Cross-platform**: Windows compatibility improvements

## Submitting Changes

### Pull Request Process

1. **Update documentation** if you've changed functionality
2. **Add examples** to `EXAMPLES.md` for new features
3. **Update `README.md`** if adding new commands or options
4. **Test thoroughly** with different scenarios
5. **Write clear commit messages** describing your changes

### Commit Message Format

Use conventional commit format:

```
type(scope): brief description

- Detailed explanation of changes
- Why the change was needed
- Any breaking changes or migration notes

Closes #issue-number
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

### Code Review

All submissions go through code review. Reviewers will check for:

- **Functionality**: Does it work as intended?
- **Code quality**: Is it readable and maintainable?
- **Error handling**: Are edge cases covered?
- **Documentation**: Are changes properly documented?
- **API compatibility**: Does it maintain backward compatibility?

## API Development Notes

### Webamon API Endpoints

The CLI interacts with these endpoints:
- `/search` - Basic and Lucene search
- `/scan` - Website security scanning  
- `/screenshot` - Website screenshots
- `/infostealers` - Compromised credentials search

### Response Handling

- **Search responses**: May have `results` or `data` arrays
- **Pagination**: Uses `from`/`size` parameters
- **Error codes**: Handle 401, 403, 404, 429 appropriately
- **Rate limits**: Different limits for free vs pro tiers

## Getting Help

- **Questions**: Open a GitHub issue with the `question` label
- **Discussions**: Use GitHub Discussions for general topics
- **Documentation**: Check `README.md` and `EXAMPLES.md` first

## Recognition

Contributors will be:
- Added to the project's acknowledgments
- Mentioned in release notes for significant contributions
- Credited in commit co-author lines where appropriate

## License

By contributing, you agree that your contributions will be licensed under the same Apache 2.0 License that covers the project.

---

**Thank you for helping make Webamon CLI better!** 🎉

For questions about contributing, feel free to open an issue or reach out to the maintainers.