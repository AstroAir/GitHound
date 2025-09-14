# GitHound Web Frontend Test Suite

Comprehensive Playwright-based testing suite for the GitHound web interface, covering authentication, search functionality, API integration, UI/UX, and performance testing.

## 🏗️ Test Architecture

### Directory Structure
```
githound/web/tests/
├── README.md                     # This file
├── conftest.py                   # Pytest configuration and shared fixtures
├── pytest.ini                   # Pytest settings
├── playwright.config.js          # Playwright configuration
├── test-reporting.config.js      # Test reporting configuration
├── package.json                  # Node.js dependencies
├── run-tests.sh                  # Test runner script (Linux/Mac)
├── run-tests.bat                 # Test runner script (Windows)
├── fixtures/                     # Test fixtures and utilities
│   ├── __init__.py
│   ├── auth_fixtures.py          # Authentication fixtures
│   ├── data_fixtures.py          # Test data fixtures
│   ├── page_fixtures.py          # Page object fixtures
│   └── server_fixtures.py        # Test server fixtures
├── pages/                        # Page Object Model
│   ├── __init__.py
│   ├── base_page.py              # Base page class
│   ├── login_page.py             # Login page object
│   ├── search_page.py            # Search page object
│   ├── profile_page.py           # Profile page object
│   └── export_page.py            # Export page object
├── utils/                        # Test utilities
│   ├── __init__.py
│   ├── test_data_manager.py      # Test data management
│   ├── performance_helper.py     # Performance testing utilities
│   ├── accessibility_helper.py   # Accessibility testing utilities
│   ├── custom_reporter.js        # Custom test reporter
│   ├── coverage_reporter.js      # Coverage reporter
│   └── artifact_manager.js       # Artifact management
├── auth/                         # Authentication tests
│   ├── authentication.spec.js    # Login/logout tests
│   ├── registration.spec.js      # User registration tests
│   └── password_reset.spec.js    # Password reset tests
├── search/                       # Search functionality tests
│   ├── basic_search.spec.js      # Basic search tests
│   ├── advanced_search.spec.js   # Advanced search tests
│   ├── fuzzy_search.spec.js      # Fuzzy search tests
│   └── historical_search.spec.js # Historical search tests
├── ui/                           # UI/UX tests
│   ├── responsive_design.spec.js # Responsive design tests
│   ├── navigation.spec.js        # Navigation tests
│   └── form_validation.spec.js   # Form validation tests
├── api/                          # API integration tests
│   ├── search_api.spec.js        # Search API tests
│   ├── auth_api.spec.js          # Authentication API tests
│   └── export_api.spec.js        # Export API tests
├── accessibility/                # Accessibility tests
│   ├── wcag_compliance.spec.js   # WCAG compliance tests
│   └── form_accessibility.spec.js # Form accessibility tests
├── performance/                  # Performance tests
│   ├── page_performance.spec.js  # Page load performance
│   ├── load_testing.spec.js      # Load testing
│   ├── stress_testing.spec.js    # Stress testing
│   └── benchmark.spec.js         # Performance benchmarks
├── visual/                       # Visual regression tests
│   ├── visual_regression.spec.js # Visual regression tests
│   └── README.md                 # Visual testing guide
├── error_handling/               # Error handling tests
│   ├── network_errors.spec.js    # Network error tests
│   ├── api_errors.spec.js        # API error tests
│   └── form_validation_errors.spec.js # Form validation tests
└── test_results/                 # Test output directory
    ├── html_report/              # HTML test reports
    ├── screenshots/              # Test screenshots
    ├── videos/                   # Test videos
    ├── traces/                   # Playwright traces
    ├── coverage/                 # Coverage reports
    └── custom/                   # Custom reports
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Redis server (for WebSocket and caching tests)
- Git (for test repository creation)

### Installation
```bash
# Install Python dependencies
pip install -e ".[dev,test]"

# Install Playwright and browsers
pip install playwright pytest-playwright
playwright install

# Install Node.js dependencies (optional, for advanced Playwright features)
cd githound/web/tests
npm install
```

### Running Tests

#### Using the Test Runner Script (Recommended)
```bash
# Run all tests
./run-tests.sh                    # Linux/Mac
./run-tests.bat                   # Windows

# Run with coverage and performance tests
./run-tests.sh --coverage --performance

# Run accessibility tests
./run-tests.sh --accessibility

# Run visual regression tests
./run-tests.sh --visual

# Run load tests
./run-tests.sh --load

# Run all browsers with verbose output
./run-tests.sh --browser all --verbose

# Run with custom output directory
./run-tests.sh --output custom-results --clean
```

#### Using Playwright Directly
```bash
cd githound/web/tests

# Run all tests
playwright test

# Run specific browsers
playwright test --project=chromium
playwright test --project=firefox
playwright test --project=webkit

# Run mobile tests
playwright test --project="Mobile Chrome"
playwright test --project="Mobile Safari"

# Run with UI mode
playwright test --ui

# Run in debug mode
playwright test --debug
```

#### Using Pytest
```bash
# Run specific test categories
pytest githound/web/tests/ -m "auth"
pytest githound/web/tests/ -m "search"
pytest githound/web/tests/ -m "api"
pytest githound/web/tests/ -m "ui"
pytest githound/web/tests/ -m "performance"

# Run with specific browser
pytest githound/web/tests/ --browser=firefox

# Run with coverage
pytest githound/web/tests/ --cov=githound.web
```

## 📋 Test Categories

### 🔐 Authentication Tests (`auth/`)
- **User Registration**: Form validation, duplicate username handling
- **Login/Logout**: Credential validation, session management
- **Password Management**: Password change, validation
- **Role-Based Access**: Admin vs user permissions
- **Token Management**: JWT refresh, expiration handling
- **Session Persistence**: Cross-page navigation, reload behavior

### 🔍 Search Tests (`search/`)
- **Search Forms**: Advanced search, fuzzy search, historical search
- **Result Display**: Pagination, filtering, sorting
- **Real-time Updates**: WebSocket progress notifications
- **Search History**: Previous searches, quick re-run
- **Export Functionality**: JSON, CSV, YAML export formats
- **Error Handling**: Invalid repositories, network failures

### 🔌 API Integration Tests (`api/`)
- **Authentication APIs**: Login, registration, profile management
- **Search APIs**: All search endpoints through frontend
- **Analysis APIs**: Blame, diff, repository statistics
- **Export APIs**: Result export in various formats
- **Webhook APIs**: Configuration and management
- **Error Handling**: API failures, rate limiting, validation

### 🎨 UI/UX Tests (`ui/`)
- **Responsive Design**: Mobile, tablet, desktop layouts
- **Accessibility**: WCAG compliance, keyboard navigation, screen readers
- **Cross-browser Compatibility**: Chrome, Firefox, Safari
- **Form Validation**: Client-side validation, error messages
- **Navigation**: Menu functionality, breadcrumbs, routing
- **Visual Regression**: Layout consistency, styling

### ⚡ Performance Tests (`performance/`)
- **Page Load Times**: Initial load, navigation performance
- **Search Performance**: Query execution, result rendering
- **WebSocket Performance**: Connection speed, message latency
- **Memory Usage**: Memory leaks, garbage collection
- **Large Result Sets**: Pagination, virtual scrolling
- **Concurrent Users**: Multi-user load simulation

## 🛠️ Configuration

### Environment Variables
```bash
# Test environment
TESTING=true
JWT_SECRET_KEY=test-secret-key-for-testing-only
REDIS_URL=redis://localhost:6379/15
GITHOUND_LOG_LEVEL=WARNING

# Browser settings
HEADLESS=true
SLOW_MO=0
RECORD_VIDEO=false
```

### Playwright Configuration
Key settings in `playwright.config.js`:
- **Browsers**: Chromium, Firefox, WebKit, Mobile Chrome/Safari
- **Timeouts**: 30s action timeout, 60s test timeout
- **Retries**: 2 retries on CI, 0 locally
- **Reporters**: HTML, JUnit, JSON reports
- **Screenshots**: On failure only
- **Videos**: Retain on failure

### Pytest Configuration
Key settings in `pytest.ini`:
- **Test Discovery**: `test_*.py` files
- **Markers**: `auth`, `search`, `api`, `ui`, `performance`, `e2e`
- **Coverage**: HTML and XML reports
- **Parallel Execution**: Configurable worker count

## 📊 Test Reports

### Generated Reports
- **HTML Report**: `test-results/playwright-report/index.html`
- **Coverage Report**: `test-results/coverage-html/index.html`
- **JUnit XML**: `test-results/playwright-results.xml`
- **Screenshots**: `test-results/screenshots/`
- **Videos**: `test-results/videos/`

### Viewing Reports
```bash
# Open Playwright HTML report
playwright show-report

# Open coverage report
open test-results/coverage-html/index.html

# Generate comprehensive report
python githound/web/tests/run_tests.py report
```

## 🔧 Development

### Adding New Tests
1. **Choose the appropriate directory** based on test category
2. **Follow naming conventions**: `test_*.py` files, `test_*` functions
3. **Use appropriate markers**: `@pytest.mark.auth`, `@pytest.mark.search`, etc.
4. **Add data-testid attributes** to UI elements for reliable selection
5. **Use test helpers** from `utils/test_helpers.py`

### Test Data Management
- **Test Users**: Created via `test_data_manager.create_test_user()`
- **Test Repositories**: Generated with sample Git history
- **Mock Data**: Consistent test data across test runs
- **Cleanup**: Automatic cleanup after each test

### Best Practices
- **Page Object Model**: Use locators with `data-testid` attributes
- **Async/Await**: All Playwright operations are async
- **Explicit Waits**: Use `expect()` for reliable element waiting
- **Error Handling**: Test both success and failure scenarios
- **Isolation**: Each test should be independent
- **Documentation**: Add docstrings explaining test purpose

## 🚀 CI/CD Integration

### GitHub Actions
The test suite integrates with GitHub Actions via `.github/workflows/web-frontend-tests.yml`:

- **Multi-browser Testing**: Chrome, Firefox, Safari
- **Multi-platform**: Ubuntu, Windows, macOS
- **Parallel Execution**: Matrix strategy for faster runs
- **Artifact Collection**: Screenshots, videos, reports
- **Coverage Reporting**: Codecov integration
- **PR Comments**: Automated test result summaries

### Running in CI
```bash
# Install dependencies
pip install -e ".[dev,test]"
playwright install

# Run test suite
playwright test --reporter=html --reporter=junit

# Upload artifacts
# Screenshots, videos, and reports are automatically collected
```

## 🐛 Troubleshooting

### Common Issues

#### Browser Installation
```bash
# Reinstall browsers
playwright install --force

# Install system dependencies
playwright install-deps
```

#### Test Server Issues
```bash
# Check if server is running
curl http://localhost:8000/health

# Restart test server
python -m githound.web.main
```

#### WebSocket Connection Issues
```bash
# Check Redis connection
redis-cli ping

# Verify WebSocket endpoint
curl -H "Upgrade: websocket" http://localhost:8000/ws
```

#### Permission Issues
```bash
# Fix file permissions
chmod +x githound/web/tests/run_tests.py

# Create test directories
mkdir -p test-results/{screenshots,videos,traces}
```

### Debug Mode
```bash
# Run single test in debug mode
playwright test auth/test_authentication.py::TestAuthentication::test_user_login_flow --debug

# Run with headed browser
playwright test --headed --slowmo=1000

# Enable verbose logging
PLAYWRIGHT_DEBUG=1 playwright test
```

## 📈 Metrics and Monitoring

### Test Metrics
- **Test Coverage**: Aim for >90% code coverage
- **Test Execution Time**: Monitor for performance regressions
- **Flaky Test Detection**: Track test stability over time
- **Browser Compatibility**: Ensure consistent behavior across browsers

### Performance Benchmarks
- **Page Load**: <3 seconds for initial load
- **Search Response**: <30 seconds for complex queries
- **WebSocket Latency**: <100ms for real-time updates
- **Memory Usage**: <50MB increase during test runs

## 🤝 Contributing

### Adding New Test Categories
1. Create new directory under `githound/web/tests/`
2. Add `__init__.py` and test files
3. Update `conftest.py` with new fixtures if needed
4. Add new markers to `pytest.ini`
5. Update this README with documentation

### Test Review Checklist
- [ ] Tests are independent and isolated
- [ ] Appropriate test markers are used
- [ ] Error scenarios are covered
- [ ] Performance implications considered
- [ ] Accessibility requirements met
- [ ] Cross-browser compatibility verified
- [ ] Documentation updated

## 📚 Resources

- [Playwright Documentation](https://playwright.dev/python/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Web Accessibility Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [GitHound Web Architecture](../README.md)

---

For questions or issues with the test suite, please open an issue in the GitHound repository or contact the development team.
