# GitHound Web Frontend Testing Troubleshooting

Common issues and solutions for the GitHound web frontend testing framework.

## 🚨 Common Issues

### Installation Problems

#### Issue: Playwright installation fails
```
Error: Failed to download browser binaries
```

**Solutions:**
1. **Check network connectivity:**
   ```bash
   curl -I https://playwright.azureedge.net/
   ```

2. **Install with force flag:**
   ```bash
   playwright install --force
   ```

3. **Set proxy if behind corporate firewall:**
   ```bash
   export HTTPS_PROXY=http://proxy.company.com:8080
   playwright install
   ```

4. **Install specific browsers only:**
   ```bash
   playwright install chromium
   ```

#### Issue: Python dependencies conflict
```
ERROR: pip's dependency resolver does not currently consider all the packages that are installed
```

**Solutions:**
1. **Use virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   pip install -e ".[dev,test]"
   ```

2. **Clear pip cache:**
   ```bash
   pip cache purge
   pip install --no-cache-dir -e ".[dev,test]"
   ```

### Test Execution Issues

#### Issue: Tests timeout frequently
```
Test timeout of 30000ms exceeded
```

**Solutions:**
1. **Increase timeout in configuration:**
   ```javascript
   // playwright.config.js
   timeout: 60000  // 60 seconds
   ```

2. **Add specific waits:**
   ```javascript
   await page.waitForSelector('[data-testid="results"]', { timeout: 60000 });
   ```

3. **Check for slow network requests:**
   ```javascript
   // Monitor network activity
   page.on('request', request => console.log('Request:', request.url()));
   page.on('response', response => console.log('Response:', response.url(), response.status()));
   ```

#### Issue: Element not found errors
```
Error: locator.click: Target closed
```

**Solutions:**
1. **Verify selector accuracy:**
   ```javascript
   // Use Playwright inspector to verify selectors
   await page.pause();
   ```

2. **Wait for element to be ready:**
   ```javascript
   await page.waitForSelector('[data-testid="button"]', { state: 'visible' });
   await page.locator('[data-testid="button"]').click();
   ```

3. **Check for dynamic content:**
   ```javascript
   // Wait for network to be idle
   await page.waitForLoadState('networkidle');
   ```

#### Issue: Flaky tests
```
Test passes sometimes, fails other times
```

**Solutions:**
1. **Add proper wait conditions:**
   ```javascript
   // Instead of fixed timeout
   await page.waitForTimeout(1000);
   
   // Use condition-based waits
   await page.waitForFunction(() => document.querySelector('[data-testid="results"]').children.length > 0);
   ```

2. **Use stable selectors:**
   ```javascript
   // Prefer data-testid over CSS classes
   page.locator('[data-testid="search-button"]')  // Good
   page.locator('.btn.btn-primary')               // Avoid
   ```

3. **Implement retry logic:**
   ```javascript
   // playwright.config.js
   retries: process.env.CI ? 3 : 1
   ```

### Browser-Specific Issues

#### Issue: Tests fail only in Firefox
```
Error: Protocol error (Runtime.callFunctionOn): Object reference chain is too long
```

**Solutions:**
1. **Reduce object complexity:**
   ```javascript
   // Avoid deep object nesting in page.evaluate()
   const result = await page.evaluate(() => {
     return { simple: 'data' };
   });
   ```

2. **Use browser-specific configuration:**
   ```javascript
   // playwright.config.js
   projects: [
     {
       name: 'firefox',
       use: { 
         ...devices['Desktop Firefox'],
         timeout: 45000  // Longer timeout for Firefox
       }
     }
   ]
   ```

#### Issue: Safari/WebKit tests fail
```
Error: browserType.launch: Executable doesn't exist
```

**Solutions:**
1. **Install WebKit browser:**
   ```bash
   playwright install webkit
   ```

2. **Check system requirements:**
   - macOS: WebKit works natively
   - Linux: Requires additional dependencies
   - Windows: Limited WebKit support

### Performance Test Issues

#### Issue: Performance tests fail inconsistently
```
Expected load time < 2000ms, got 3500ms
```

**Solutions:**
1. **Run performance tests in isolation:**
   ```bash
   playwright test --project=chromium performance/
   ```

2. **Use performance budgets with tolerance:**
   ```javascript
   const loadTime = await measureLoadTime();
   expect(loadTime).toBeLessThan(2500); // Add 25% tolerance
   ```

3. **Warm up the application:**
   ```javascript
   // Navigate to page once before measuring
   await page.goto('/');
   await page.waitForLoadState('networkidle');
   
   // Now measure performance
   const startTime = Date.now();
   await page.goto('/');
   const loadTime = Date.now() - startTime;
   ```

### Accessibility Test Issues

#### Issue: axe-playwright not working
```
Error: Cannot find module 'axe-playwright'
```

**Solutions:**
1. **Install axe-playwright (JavaScript/npm):**
   ```bash
   npm install axe-playwright
   ```

   **For Python accessibility testing, install axe-playwright-python:**
   ```bash
   pip install axe-playwright-python
   ```

2. **Import correctly:**
   ```javascript
   const { injectAxe, checkA11y } = require('axe-playwright');
   ```

3. **Initialize in test:**
   ```javascript
   await injectAxe(page);
   await checkA11y(page);
   ```

### Visual Regression Issues

#### Issue: Screenshots don't match
```
Screenshot comparison failed: 15% difference
```

**Solutions:**
1. **Update baseline screenshots:**
   ```bash
   playwright test --update-snapshots
   ```

2. **Adjust threshold:**
   ```javascript
   await expect(page).toHaveScreenshot('page.png', { threshold: 0.3 });
   ```

3. **Disable animations:**
   ```javascript
   await page.addStyleTag({
     content: `
       *, *::before, *::after {
         animation-duration: 0s !important;
         animation-delay: 0s !important;
         transition-duration: 0s !important;
         transition-delay: 0s !important;
       }
     `
   });
   ```

### CI/CD Issues

#### Issue: Tests pass locally but fail in CI
```
Tests work on local machine but fail in GitHub Actions
```

**Solutions:**
1. **Check environment differences:**
   ```bash
   # Compare environment variables
   env | grep -E "(HEADLESS|CI|DISPLAY)"
   ```

2. **Use consistent browser versions:**
   ```javascript
   // playwright.config.js
   use: {
     channel: 'chrome',  // Use stable Chrome channel
   }
   ```

3. **Add CI-specific configuration:**
   ```javascript
   // playwright.config.js
   workers: process.env.CI ? 2 : 4,
   retries: process.env.CI ? 3 : 1,
   ```

#### Issue: Artifacts not uploaded
```
Test artifacts missing from CI run
```

**Solutions:**
1. **Check artifact paths:**
   ```yaml
   # .github/workflows/web-frontend-tests.yml
   - name: Upload test results
     uses: actions/upload-artifact@v3
     if: always()
     with:
       path: |
         test-results/
         githound/web/tests/test-results/
   ```

2. **Ensure directories exist:**
   ```bash
   mkdir -p test-results/{screenshots,videos,traces}
   ```

### Memory and Resource Issues

#### Issue: Tests consume too much memory
```
Error: Page crashed
```

**Solutions:**
1. **Limit concurrent workers:**
   ```javascript
   // playwright.config.js
   workers: 2  // Reduce from default
   ```

2. **Close contexts properly:**
   ```javascript
   test.afterEach(async ({ context }) => {
     await context.close();
   });
   ```

3. **Monitor memory usage:**
   ```javascript
   const memoryUsage = await page.evaluate(() => {
     return performance.memory ? {
       used: performance.memory.usedJSHeapSize,
       total: performance.memory.totalJSHeapSize
     } : null;
   });
   ```

## 🔧 Debugging Tools

### Playwright Inspector
```bash
# Debug specific test
playwright test --debug auth/authentication.spec.js

# Debug with UI mode
playwright test --ui
```

### Trace Viewer
```bash
# View trace file
playwright show-trace test-results/traces/trace.zip

# Generate trace on all tests
playwright test --trace on
```

### Screenshots and Videos
```bash
# Force screenshot capture
playwright test --screenshot=on

# Force video recording
playwright test --video=on
```

### Network Monitoring
```javascript
// Log all network requests
page.on('request', request => {
  console.log(`Request: ${request.method()} ${request.url()}`);
});

page.on('response', response => {
  console.log(`Response: ${response.status()} ${response.url()}`);
});
```

## 📊 Performance Optimization

### Test Execution Speed
1. **Run tests in parallel:**
   ```javascript
   workers: 4  // Adjust based on CPU cores
   ```

2. **Use test sharding:**
   ```bash
   playwright test --shard=1/4
   ```

3. **Skip unnecessary tests:**
   ```javascript
   test.skip(condition, 'Reason for skipping');
   ```

### Resource Usage
1. **Reuse browser contexts:**
   ```javascript
   test.describe.configure({ mode: 'serial' });
   ```

2. **Optimize selectors:**
   ```javascript
   // Fast
   page.locator('[data-testid="button"]')
   
   // Slow
   page.locator('div > ul > li:nth-child(3) > button')
   ```

## 🆘 Getting Help

### Log Analysis
1. **Enable verbose logging:**
   ```bash
   DEBUG=pw:api playwright test
   ```

2. **Check test output:**
   ```bash
   playwright test --reporter=line
   ```

### Community Resources
- [Playwright Discord](https://discord.gg/playwright-807756831384403968)
- [Playwright GitHub Issues](https://github.com/microsoft/playwright/issues)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/playwright)

### Internal Support
- Check GitHound project documentation
- Create issue in GitHound repository
- Contact development team

---

If you encounter an issue not covered here, please document the problem and solution to help improve this troubleshooting guide.
