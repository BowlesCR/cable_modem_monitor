***REMOVED*** Contributing to Cable Modem Monitor

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

***REMOVED******REMOVED*** Ways to Contribute

- 🐛 Report bugs via [GitHub Issues](https://github.com/kwschulz/cable_modem_monitor/issues)
- 💡 Suggest features or improvements
- 📝 Improve documentation
- 🧪 Add support for additional modem models
- 🔧 Submit bug fixes or enhancements

***REMOVED******REMOVED*** Development Setup

***REMOVED******REMOVED******REMOVED*** Prerequisites
- Python 3.11 or 3.12
- Home Assistant development environment
- Git

***REMOVED******REMOVED******REMOVED*** Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/kwschulz/cable_modem_monitor.git
   cd cable_modem_monitor
   ```

2. **Install test dependencies**
   ```bash
   pip install -r tests/requirements.txt
   ```

3. **Run tests**
   ```bash
   pytest tests/ -v
   ```

4. **Deploy to your Home Assistant instance**
   ```bash
   ***REMOVED*** Edit deploy_to_ha.sh with your settings
   ./deploy_to_ha.sh
   ```

***REMOVED******REMOVED*** Adding Support for New Modem Models

If you have a modem model that isn't currently supported:

1. **Capture HTML from your modem**
   ```bash
   curl -u username:password http://MODEM_IP/status_page.html > tests/fixtures/brand_model.html
   ```

2. **Create tests** for the new HTML structure in `tests/test_modem_scraper.py`

3. **Update scraper** in `custom_components/cable_modem_monitor/modem_scraper.py`

4. **Verify** both old and new modems work:
   ```bash
   pytest tests/ -v
   ```

5. **Submit a pull request** with:
   - Test fixtures (sanitize any personal info)
   - Test cases
   - Scraper updates
   - Documentation of supported modem model

***REMOVED******REMOVED*** Code Style

- Follow [PEP 8](https://pep8.org/) style guidelines
- Use type hints where appropriate
- Add docstrings to functions and classes
- Keep functions focused and small
- Use async/await for I/O operations

***REMOVED******REMOVED******REMOVED*** Linting
```bash
ruff check custom_components/cable_modem_monitor/
```

***REMOVED******REMOVED*** Testing

All code changes should include appropriate tests:

***REMOVED******REMOVED******REMOVED*** Running Tests
```bash
***REMOVED*** All tests
pytest tests/ -v

***REMOVED*** With coverage
pytest tests/ --cov=custom_components/cable_modem_monitor --cov-report=html

***REMOVED*** Specific test
pytest tests/test_modem_scraper.py::TestModemScraper::test_parse_downstream_channels -v
```

***REMOVED******REMOVED******REMOVED*** Test Requirements
- Unit tests for new parsing functions
- Integration tests for complete workflows
- Fixtures for new HTML structures
- Validation of data ranges and types

See [TESTING.md](TESTING.md) for comprehensive testing documentation.

***REMOVED******REMOVED*** Submitting Changes

***REMOVED******REMOVED******REMOVED*** Pull Request Process

1. **Fork the repository** and create a feature branch
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following code style guidelines

3. **Add/update tests** for your changes

4. **Run the test suite**
   ```bash
   pytest tests/ -v
   ```

5. **Update documentation** if needed (README.md, CHANGELOG.md)

6. **Commit your changes** with clear commit messages
   ```bash
   git commit -m "Add support for Arris TG1682G modem"
   ```

7. **Push to your fork** and create a pull request
   ```bash
   git push origin feature/your-feature-name
   ```

***REMOVED******REMOVED******REMOVED*** Pull Request Guidelines

- **Clear description**: Explain what changes you made and why
- **Link issues**: Reference any related GitHub issues
- **Test results**: Include test output showing all tests pass
- **Screenshots**: For UI changes, include before/after screenshots
- **Documentation**: Update README, CHANGELOG, or other docs as needed

***REMOVED******REMOVED******REMOVED*** Commit Message Format

Use clear, descriptive commit messages:

```
Add support for Arris TG1682G modem

- Added HTML parser for Arris status page format
- Created test fixtures from real modem output
- Updated documentation with supported models
- All existing tests still pass
```

***REMOVED******REMOVED*** Release Process

Maintainers will handle releases following semantic versioning:

- **Major (1.0.0)**: Breaking changes
- **Minor (0.1.0)**: New features, backward compatible
- **Patch (0.0.1)**: Bug fixes, backward compatible

Each release includes:
- Version bump in `manifest.json`
- Updated `CHANGELOG.md`
- Git tag
- GitHub Release with notes

***REMOVED******REMOVED*** Code of Conduct

***REMOVED******REMOVED******REMOVED*** Our Standards

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on what is best for the community
- Show empathy towards others

***REMOVED******REMOVED******REMOVED*** Unacceptable Behavior

- Harassment, discrimination, or offensive comments
- Trolling or insulting comments
- Publishing others' private information
- Unprofessional conduct

***REMOVED******REMOVED*** Questions?

- 💬 Open a [GitHub Discussion](https://github.com/kwschulz/cable_modem_monitor/discussions)
- 🐛 Report issues via [GitHub Issues](https://github.com/kwschulz/cable_modem_monitor/issues)
- 📧 Contact maintainers via GitHub

***REMOVED******REMOVED*** Resources

- [Home Assistant Developer Docs](https://developers.home-assistant.io/)
- [HACS Documentation](https://hacs.xyz/)
- [Python asyncio](https://docs.python.org/3/library/asyncio.html)
- [pytest Documentation](https://docs.pytest.org/)

Thank you for contributing to Cable Modem Monitor! 🎉
