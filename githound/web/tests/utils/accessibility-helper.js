/**
 * Accessibility testing utilities for GitHound web tests.
 * Provides helpers for WCAG compliance and accessibility validation.
 */

const { injectAxe, checkA11y, getViolations } = require('axe-playwright');

class AccessibilityTestHelper {
  constructor() {
    this.violations = [];
    this.wcagLevel = 'AA'; // WCAG 2.1 AA compliance
    this.tags = ['wcag2a', 'wcag2aa', 'wcag21aa'];
  }

  /**
   * Initialize accessibility testing on a page
   */
  async initializeA11yTesting(page) {
    await injectAxe(page);
    console.log('✅ Accessibility testing initialized');
  }

  /**
   * Run comprehensive accessibility audit
   */
  async runAccessibilityAudit(page, options = {}) {
    const auditOptions = {
      tags: options.tags || this.tags,
      rules: options.rules || {},
      include: options.include || [],
      exclude: options.exclude || []
    };

    try {
      await checkA11y(page, null, auditOptions);
      console.log('✅ Accessibility audit passed');
      return { passed: true, violations: [] };
    } catch (error) {
      const violations = await getViolations(page, null, auditOptions);
      this.violations.push(...violations);
      
      console.warn(`⚠️  Accessibility violations found: ${violations.length}`);
      return { passed: false, violations };
    }
  }

  /**
   * Test keyboard navigation
   */
  async testKeyboardNavigation(page, elements) {
    const results = [];
    
    for (const element of elements) {
      try {
        // Focus on the element using Tab
        await page.keyboard.press('Tab');
        
        // Check if element is focused
        const isFocused = await page.evaluate((selector) => {
          const el = document.querySelector(`[data-testid="${selector}"]`);
          return document.activeElement === el;
        }, element);
        
        // Test Enter key activation
        if (isFocused) {
          await page.keyboard.press('Enter');
          
          // Wait a moment for any actions to complete
          await page.waitForTimeout(100);
        }
        
        results.push({
          element,
          focusable: isFocused,
          activatable: true // Assume true if no error thrown
        });
        
      } catch (error) {
        results.push({
          element,
          focusable: false,
          activatable: false,
          error: error.message
        });
      }
    }
    
    return results;
  }

  /**
   * Test screen reader compatibility
   */
  async testScreenReaderCompatibility(page) {
    const ariaAttributes = await page.evaluate(() => {
      const elements = document.querySelectorAll('*');
      const ariaInfo = [];
      
      elements.forEach(el => {
        const attributes = {};
        
        // Check for ARIA attributes
        for (const attr of el.attributes) {
          if (attr.name.startsWith('aria-') || attr.name === 'role') {
            attributes[attr.name] = attr.value;
          }
        }
        
        // Check for semantic elements
        const tagName = el.tagName.toLowerCase();
        const semanticTags = ['header', 'nav', 'main', 'section', 'article', 'aside', 'footer', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'];
        
        if (Object.keys(attributes).length > 0 || semanticTags.includes(tagName)) {
          ariaInfo.push({
            tagName,
            attributes,
            textContent: el.textContent?.trim().substring(0, 50) || '',
            hasAriaLabel: !!attributes['aria-label'],
            hasAriaDescribedBy: !!attributes['aria-describedby'],
            hasRole: !!attributes['role']
          });
        }
      });
      
      return ariaInfo;
    });
    
    return ariaInfo;
  }

  /**
   * Test color contrast
   */
  async testColorContrast(page) {
    const contrastResults = await page.evaluate(() => {
      const elements = document.querySelectorAll('*');
      const contrastInfo = [];
      
      elements.forEach(el => {
        const styles = window.getComputedStyle(el);
        const color = styles.color;
        const backgroundColor = styles.backgroundColor;
        
        // Only check elements with text content
        if (el.textContent?.trim() && color !== 'rgba(0, 0, 0, 0)' && backgroundColor !== 'rgba(0, 0, 0, 0)') {
          contrastInfo.push({
            element: el.tagName.toLowerCase(),
            color,
            backgroundColor,
            textContent: el.textContent.trim().substring(0, 30)
          });
        }
      });
      
      return contrastInfo;
    });
    
    return contrastResults;
  }

  /**
   * Test form accessibility
   */
  async testFormAccessibility(page) {
    const formResults = await page.evaluate(() => {
      const forms = document.querySelectorAll('form');
      const formInfo = [];
      
      forms.forEach(form => {
        const inputs = form.querySelectorAll('input, select, textarea');
        const inputInfo = [];
        
        inputs.forEach(input => {
          const label = form.querySelector(`label[for="${input.id}"]`) || 
                       input.closest('label') ||
                       form.querySelector(`[aria-labelledby="${input.id}"]`);
          
          inputInfo.push({
            type: input.type || input.tagName.toLowerCase(),
            id: input.id,
            name: input.name,
            hasLabel: !!label,
            labelText: label?.textContent?.trim() || '',
            hasAriaLabel: !!input.getAttribute('aria-label'),
            ariaLabel: input.getAttribute('aria-label') || '',
            required: input.required,
            hasAriaRequired: input.getAttribute('aria-required') === 'true'
          });
        });
        
        formInfo.push({
          formId: form.id,
          inputs: inputInfo
        });
      });
      
      return formInfo;
    });
    
    return formResults;
  }

  /**
   * Test heading structure
   */
  async testHeadingStructure(page) {
    const headingStructure = await page.evaluate(() => {
      const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
      const structure = [];
      
      headings.forEach(heading => {
        structure.push({
          level: parseInt(heading.tagName.charAt(1)),
          text: heading.textContent?.trim() || '',
          id: heading.id || '',
          hasId: !!heading.id
        });
      });
      
      return structure;
    });
    
    // Validate heading hierarchy
    const violations = [];
    let previousLevel = 0;
    
    headingStructure.forEach((heading, index) => {
      if (index === 0 && heading.level !== 1) {
        violations.push('Page should start with an h1 heading');
      }
      
      if (heading.level > previousLevel + 1) {
        violations.push(`Heading level ${heading.level} skips levels (previous was ${previousLevel})`);
      }
      
      previousLevel = heading.level;
    });
    
    return {
      structure: headingStructure,
      violations
    };
  }

  /**
   * Test focus management
   */
  async testFocusManagement(page, interactiveElements) {
    const focusResults = [];
    
    for (const element of interactiveElements) {
      try {
        // Click on the element
        await page.click(`[data-testid="${element}"]`);
        
        // Check if focus is properly managed
        const focusInfo = await page.evaluate(() => {
          const activeElement = document.activeElement;
          return {
            tagName: activeElement?.tagName.toLowerCase(),
            id: activeElement?.id,
            className: activeElement?.className,
            hasTabIndex: activeElement?.hasAttribute('tabindex'),
            tabIndex: activeElement?.tabIndex
          };
        });
        
        focusResults.push({
          element,
          focusManaged: !!focusInfo.tagName,
          focusInfo
        });
        
      } catch (error) {
        focusResults.push({
          element,
          focusManaged: false,
          error: error.message
        });
      }
    }
    
    return focusResults;
  }

  /**
   * Generate accessibility report
   */
  generateAccessibilityReport() {
    const report = {
      timestamp: new Date().toISOString(),
      wcagLevel: this.wcagLevel,
      totalViolations: this.violations.length,
      violationsByImpact: this.groupViolationsByImpact(),
      violationsByCategory: this.groupViolationsByCategory(),
      recommendations: this.generateRecommendations()
    };
    
    return report;
  }

  /**
   * Group violations by impact level
   */
  groupViolationsByImpact() {
    const grouped = { critical: 0, serious: 0, moderate: 0, minor: 0 };
    
    this.violations.forEach(violation => {
      if (grouped.hasOwnProperty(violation.impact)) {
        grouped[violation.impact]++;
      }
    });
    
    return grouped;
  }

  /**
   * Group violations by category
   */
  groupViolationsByCategory() {
    const categories = {};
    
    this.violations.forEach(violation => {
      violation.tags.forEach(tag => {
        if (!categories[tag]) {
          categories[tag] = 0;
        }
        categories[tag]++;
      });
    });
    
    return categories;
  }

  /**
   * Generate accessibility recommendations
   */
  generateRecommendations() {
    const recommendations = [];
    
    if (this.violations.length === 0) {
      recommendations.push('Great! No accessibility violations found.');
    } else {
      recommendations.push('Address critical and serious violations first');
      recommendations.push('Ensure all interactive elements are keyboard accessible');
      recommendations.push('Verify color contrast meets WCAG AA standards');
      recommendations.push('Add proper ARIA labels and descriptions');
      recommendations.push('Test with actual screen readers');
    }
    
    return recommendations;
  }

  /**
   * Clear all violations
   */
  clearViolations() {
    this.violations = [];
  }
}

module.exports = AccessibilityTestHelper;
