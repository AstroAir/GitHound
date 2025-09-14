# Visual Regression Testing

This directory contains visual regression tests for the GitHound web interface. These tests capture screenshots of UI components and compare them against baseline images to detect visual changes.

## Overview

Visual regression testing helps catch:
- Unintended UI changes
- Layout issues across browsers
- Responsive design problems
- CSS regression bugs
- Font and styling inconsistencies

## Test Structure

### Test Categories

1. **Homepage Visual Tests** (`@visual @homepage`)
   - Full page layout
   - Navigation components
   - Dashboard elements

2. **Authentication Visual Tests** (`@visual @auth`)
   - Login modal
   - Registration modal
   - User menu states

3. **Search Interface Visual Tests** (`@visual @search`)
   - Search form layout
   - Search tabs
   - Results display
   - Empty states

4. **Export Modal Visual Tests** (`@visual @export`)
   - Export dialog layout
   - Form elements
   - Option selections

5. **Responsive Visual Tests** (`@visual @responsive`)
   - Mobile layouts (375px width)
   - Tablet layouts (768px width)
   - Mobile navigation menu

6. **Error States Visual Tests** (`@visual @errors`)
   - Form validation errors
   - Network error displays
   - Loading states

7. **Dark Mode Visual Tests** (`@visual @darkmode`)
   - Dark theme layouts
   - Component styling in dark mode

## Running Visual Tests

### Run All Visual Tests
```bash
npx playwright test --grep "@visual"
```

### Run Specific Visual Test Categories
```bash
# Homepage tests only
npx playwright test --grep "@visual @homepage"

# Authentication tests only
npx playwright test --grep "@visual @auth"

# Responsive tests only
npx playwright test --grep "@visual @responsive"
```

### Update Visual Baselines
When UI changes are intentional, update the baseline screenshots:

```bash
# Update all visual baselines
npx playwright test --grep "@visual" --update-snapshots

# Update specific test baselines
npx playwright test visual-regression.spec.js --update-snapshots
```

## Screenshot Configuration

Visual tests are configured with:
- **Threshold**: 0.2% difference tolerance
- **Mode**: Percentage-based comparison
- **Animations**: Disabled for consistency
- **Full Page**: Captures entire page when needed

## Best Practices

### 1. Hide Dynamic Content
Always hide elements that change between test runs:
```javascript
await page.addStyleTag({
  content: `
    [data-testid="search-id"],
    [data-testid="results-count"],
    .timestamp {
      visibility: hidden !important;
    }
  `
});
```

### 2. Wait for Stability
Ensure page is fully loaded before capturing:
```javascript
await page.waitForLoadState('networkidle');
await page.waitForTimeout(500); // Additional stability wait
```

### 3. Consistent Test Data
Use deterministic test data to ensure consistent visuals:
```javascript
const testUser = {
  username: `visual_${Date.now()}`,
  email: `visual_${Date.now()}@example.com`,
  password: 'Visual123!'
};
```

### 4. Cross-Browser Testing
Visual tests run across all configured browsers:
- Chromium
- Firefox
- WebKit (Safari)
- Microsoft Edge

## Screenshot Storage

Screenshots are stored in:
- `test-results/` - Test run artifacts
- `tests/visual/visual-regression.spec.js-snapshots/` - Baseline images

### Baseline Management
- **Initial Run**: Creates baseline screenshots
- **Subsequent Runs**: Compares against baselines
- **Failures**: Generates diff images showing changes

## Troubleshooting

### Common Issues

1. **Font Rendering Differences**
   - Ensure consistent font loading
   - Use web-safe fonts for testing
   - Consider font-display: swap

2. **Animation Timing**
   - Disable animations in tests
   - Use consistent timing waits
   - Set animation-duration: 0

3. **Dynamic Content**
   - Hide timestamps and IDs
   - Use fixed test data
   - Mock dynamic API responses

4. **Browser Differences**
   - Accept minor rendering differences
   - Adjust threshold if needed
   - Use browser-specific baselines

### Debugging Failed Tests

1. **View Diff Images**
   ```bash
   npx playwright show-report
   ```

2. **Run in Headed Mode**
   ```bash
   npx playwright test --grep "@visual" --headed
   ```

3. **Debug Specific Test**
   ```bash
   npx playwright test --grep "should match homepage layout" --debug
   ```

## Integration with CI/CD

Visual tests are configured to:
- Run on all pull requests
- Generate artifacts for review
- Fail builds on visual regressions
- Store baseline images in version control

### CI Configuration
```yaml
- name: Run Visual Tests
  run: npx playwright test --grep "@visual"
  
- name: Upload Visual Test Results
  uses: actions/upload-artifact@v3
  if: always()
  with:
    name: visual-test-results
    path: test-results/
```

## Maintenance

### Regular Tasks

1. **Review Baselines**: Periodically review and update baselines
2. **Clean Artifacts**: Remove old test result artifacts
3. **Update Tests**: Add visual tests for new UI components
4. **Monitor Flakiness**: Address flaky visual tests promptly

### Adding New Visual Tests

1. Create test in appropriate category
2. Use consistent naming convention
3. Add appropriate tags (@visual @category)
4. Hide dynamic elements
5. Generate initial baseline
6. Verify across browsers
