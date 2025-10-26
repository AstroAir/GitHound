# GitHound Web Frontend Testing Guide

## 🎯 Overview

This comprehensive testing suite ensures the GitHound web frontend works correctly across all browsers, devices, and use cases. The tests cover authentication, search functionality, API integration, UI/UX, and performance.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# From project root
make test-web-install

# Or manually
pip install playwright pytest-playwright axe-playwright
playwright install
```

### 2. Start Required Services

```bash
# Start Redis (required for WebSocket tests)
docker run -d -p 6379:6379 redis:7-alpine

# Or use existing Redis instance
export REDIS_URL=redis://localhost:6379/15
```

### 3. Run Tests

```bash
# Run all web tests
make test-web

# Run specific test categories
make test-web-auth          # Authentication tests
make test-web-search        # Search functionality
make test-web-api           # API integration
make test-web-ui            # UI/UX tests
make test-web-performance   # Performance tests
make test-web-accessibility # Accessibility tests

# Run with different browsers
make test-web-firefox       # Firefox
make test-web-webkit        # Safari/WebKit

# Debug mode (visible browser)
make test-web-headed
```

## 📋 Test Categories

### 🔐 Authentication Tests

**Location**: `auth/test_authentication.py`

**Coverage**:

- ✅ User registration with validation
- ✅ Login/logout functionality
- ✅ Password change and validation
- ✅ Role-based access control (admin vs user)
- ✅ JWT token refresh and expiration
- ✅ Session persistence across page reloads
- ✅ Form validation and error handling

**Key Test Cases**:

```python
test_user_registration_flow()
test_user_login_flow()
test_invalid_login_credentials()
test_role_based_access_control()
test_token_refresh_flow()
```

### 🔍 Search Tests

**Location**: `search/test_search_interface.py`, `search/test_websocket_updates.py`

**Coverage**:

- ✅ Advanced search with filters (file types, authors, dates)
- ✅ Fuzzy search with typo tolerance
- ✅ Historical search across commit ranges
- ✅ Real-time progress updates via WebSocket
- ✅ Search result display and pagination
- ✅ Export functionality (JSON, CSV, YAML)
- ✅ Search history and quick re-run

**Key Test Cases**:

```python
test_advanced_search_form()
test_fuzzy_search_functionality()
test_historical_search_functionality()
test_websocket_connection_establishment()
test_search_progress_updates()
```

### 🔌 API Integration Tests

**Location**: `api/test_api_integration.py`

**Coverage**:

- ✅ All API endpoints through frontend interface
- ✅ Authentication headers and JWT tokens
- ✅ Error handling and user feedback
- ✅ Rate limiting behavior and notifications
- ✅ Request/response validation
- ✅ API caching and performance

**Key Test Cases**:

```python
test_search_api_through_frontend()
test_authentication_api_calls()
test_api_error_handling()
test_rate_limiting_behavior()
test_export_api_integration()
```

### 🎨 UI/UX Tests

**Location**: `ui/test_responsive_design.py`, `ui/test_accessibility.py`

**Coverage**:

- ✅ Responsive design (mobile, tablet, desktop)
- ✅ Cross-browser compatibility (Chrome, Firefox, Safari)
- ✅ Accessibility compliance (WCAG 2.1)
- ✅ Keyboard navigation and focus management
- ✅ Screen reader compatibility
- ✅ Touch targets and mobile usability
- ✅ Color contrast and readability

**Key Test Cases**:

```python
test_mobile_layout()
test_tablet_layout()
test_desktop_layout()
test_keyboard_navigation()
test_aria_labels_and_roles()
test_color_contrast()
```

### ⚡ Performance Tests

**Location**: `performance/test_performance.py`

**Coverage**:

- ✅ Page load times and rendering performance
- ✅ Search operation performance
- ✅ WebSocket connection and message latency
- ✅ Memory usage and leak detection
- ✅ Large result set handling
- ✅ Concurrent user simulation
- ✅ Resource loading optimization

**Key Test Cases**:

```python
test_page_load_performance()
test_search_performance()
test_websocket_performance()
test_memory_usage()
test_concurrent_user_simulation()
```

## 🛠️ Test Infrastructure

### Test Fixtures

- **Test Server**: Automatic startup/shutdown of GitHound web server
- **Test Users**: Pre-created users with different roles
- **Test Repositories**: Sample Git repositories with known content
- **Test Data**: Consistent mock data across test runs
- **Browser Management**: Automatic browser lifecycle management

### Test Utilities

- **Helper Functions**: Common operations like login, search, navigation
- **Wait Utilities**: Reliable waiting for elements and conditions
- **Accessibility Checks**: Automated WCAG compliance verification
- **Performance Monitoring**: Metrics collection and analysis
- **Screenshot/Video**: Automatic capture on test failures

### Configuration

- **Multi-browser**: Chrome, Firefox, Safari support
- **Multi-device**: Desktop, tablet, mobile viewports
- **Environment Variables**: Configurable test settings
- **Parallel Execution**: Faster test runs with worker processes
- **Retry Logic**: Automatic retry on transient failures

## 📊 Test Reports

### Generated Reports

```bash
# View Playwright HTML report
playwright show-report

# View coverage report
open test-results/coverage-html/index.html

# View individual test reports
open test-results/auth-test-report.html
open test-results/search-test-report.html
open test-results/api-test-report.html
open test-results/ui-test-report.html
open test-results/performance-test-report.html
```

### CI/CD Integration

- **GitHub Actions**: Automated testing on pull requests
- **Multi-platform**: Ubuntu, Windows, macOS testing
- **Artifact Collection**: Screenshots, videos, reports
- **Coverage Reporting**: Codecov integration
- **Test Result Publishing**: JUnit XML reports

## 🐛 Debugging

### Debug Mode

```bash
# Run single test with debug
playwright test auth/test_authentication.py::TestAuthentication::test_user_login_flow --debug

# Run with visible browser
make test-web-headed

# Enable verbose logging
PLAYWRIGHT_DEBUG=1 make test-web
```

### Common Issues

#### Browser Not Found

```bash
# Reinstall browsers
playwright install --force
playwright install-deps
```

#### Server Connection Issues

```bash
# Check server status
curl http://localhost:8000/health

# Check Redis connection
redis-cli ping
```

#### Test Data Issues

```bash
# Clean test data
rm -rf test-results/
mkdir -p test-results/{screenshots,videos,traces}
```

## 📈 Performance Benchmarks

### Target Metrics

- **Page Load**: <3 seconds initial load
- **Search Response**: <30 seconds for complex queries
- **WebSocket Latency**: <100ms for real-time updates
- **Memory Usage**: <50MB increase during operations
- **Test Coverage**: >90% code coverage

### Monitoring

- **Load Time Tracking**: Automated performance regression detection
- **Memory Leak Detection**: Long-running test scenarios
- **Cross-browser Performance**: Consistent behavior verification
- **Mobile Performance**: Touch interaction and rendering speed

## 🔒 Security Testing

### Security Checks

- **Authentication**: JWT token security and expiration
- **Authorization**: Role-based access control verification
- **Input Validation**: XSS and injection prevention
- **CSRF Protection**: Cross-site request forgery prevention
- **HTTPS Enforcement**: Secure communication verification

### Privacy Compliance

- **Data Handling**: User data protection verification
- **Session Management**: Secure session handling
- **Cookie Security**: Secure cookie configuration
- **Error Information**: No sensitive data in error messages

## 🤝 Contributing

### Adding New Tests

1. **Choose Category**: Place tests in appropriate directory
2. **Follow Conventions**: Use `test_*.py` naming and `@pytest.mark.*` markers
3. **Add Test IDs**: Use `data-testid` attributes for reliable element selection
4. **Document Tests**: Add clear docstrings explaining test purpose
5. **Update CI**: Add new test categories to GitHub Actions workflow

### Test Review Checklist

- [ ] Tests are independent and isolated
- [ ] Appropriate test markers are used (`@pytest.mark.auth`, etc.)
- [ ] Error scenarios are covered
- [ ] Cross-browser compatibility verified
- [ ] Accessibility requirements met
- [ ] Performance implications considered
- [ ] Documentation updated

## 📚 Resources

- **Playwright Docs**: https://playwright.dev/python/
- **Pytest Docs**: https://docs.pytest.org/
- **WCAG Guidelines**: https://www.w3.org/WAI/WCAG21/quickref/
- **GitHound Web Docs**: ../README.md

---

**Need Help?** Open an issue in the GitHound repository or contact the development team.
