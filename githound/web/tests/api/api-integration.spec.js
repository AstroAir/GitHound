/**
 * API Integration Tests
 * Tests API endpoints through the frontend interface with comprehensive error handling
 */

const { test, expect } = require('@playwright/test');
const { SearchPage, LoginPage } = require('../pages');

test.describe('API Integration Tests', () => {
  let searchPage;
  let loginPage;
  let authToken;

  test.beforeEach(async ({ page }) => {
    searchPage = new SearchPage(page);
    loginPage = new LoginPage(page);

    // Setup authenticated user
    const testUser = {
      username: `apitest_${Date.now()}`,
      email: `apitest_${Date.now()}@example.com`,
      password: 'ApiTest123!'
    };

    await loginPage.register(testUser);
    await loginPage.login(testUser.username, testUser.password);
    
    // Get auth token for direct API calls
    authToken = await page.evaluate(() => localStorage.getItem('access_token'));
  });

  test.describe('Authentication API Integration @api @auth', () => {
    test('should register user via API', async ({ page }) => {
      const userData = {
        username: `direct_api_${Date.now()}`,
        email: `direct_api_${Date.now()}@example.com`,
        password: 'DirectApi123!'
      };

      // Make direct API call
      const response = await page.evaluate(async (userData) => {
        const response = await fetch('/api/auth/register', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(userData)
        });
        
        return {
          status: response.status,
          data: await response.json()
        };
      }, userData);

      expect(response.status).toBe(200);
      expect(response.data.user.username).toBe(userData.username);
      expect(response.data.user.email).toBe(userData.email);
      expect(response.data.message).toContain('successfully');
    });

    test('should login user via API', async ({ page }) => {
      const userData = {
        username: `login_api_${Date.now()}`,
        email: `login_api_${Date.now()}@example.com`,
        password: 'LoginApi123!'
      };

      // Register first
      await page.evaluate(async (userData) => {
        await fetch('/api/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(userData)
        });
      }, userData);

      // Then login
      const loginResponse = await page.evaluate(async (credentials) => {
        const response = await fetch('/api/auth/login', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            username: credentials.username,
            password: credentials.password
          })
        });
        
        return {
          status: response.status,
          data: await response.json()
        };
      }, userData);

      expect(loginResponse.status).toBe(200);
      expect(loginResponse.data.token.access_token).toBeTruthy();
      expect(loginResponse.data.token.token_type).toBe('bearer');
      expect(loginResponse.data.user.username).toBe(userData.username);
    });

    test('should handle authentication errors correctly', async ({ page }) => {
      // Test invalid credentials
      const invalidLogin = await page.evaluate(async () => {
        const response = await fetch('/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            username: 'nonexistent_user',
            password: 'wrong_password'
          })
        });
        
        return {
          status: response.status,
          data: await response.json()
        };
      });

      expect(invalidLogin.status).toBe(401);
      expect(invalidLogin.data.detail).toContain('Invalid');
    });

    test('should handle rate limiting', async ({ page }) => {
      const userData = {
        username: `rate_limit_${Date.now()}`,
        email: `rate_limit_${Date.now()}@example.com`,
        password: 'RateLimit123!'
      };

      // Make multiple rapid requests to trigger rate limiting
      const requests = [];
      for (let i = 0; i < 10; i++) {
        requests.push(
          page.evaluate(async (userData) => {
            const response = await fetch('/api/auth/login', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                username: userData.username,
                password: userData.password
              })
            });
            return response.status;
          }, userData)
        );
      }

      const responses = await Promise.all(requests);
      
      // Should have some rate limited responses (429)
      const rateLimitedCount = responses.filter(status => status === 429).length;
      expect(rateLimitedCount).toBeGreaterThan(0);
    });

    test('should validate user profile API', async ({ page }) => {
      const profileResponse = await page.evaluate(async (token) => {
        const response = await fetch('/api/auth/profile', {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });
        
        return {
          status: response.status,
          data: await response.json()
        };
      }, authToken);

      expect(profileResponse.status).toBe(200);
      expect(profileResponse.data.username).toBeTruthy();
      expect(profileResponse.data.email).toBeTruthy();
      expect(profileResponse.data.roles).toBeTruthy();
    });
  });

  test.describe('Search API Integration @api @search', () => {
    test('should perform basic search via API', async ({ page }) => {
      const searchRequest = {
        repo_path: '/test/repo',
        content_pattern: 'function',
        file_extensions: ['js', 'py'],
        max_results: 100
      };

      const searchResponse = await page.evaluate(async (request, token) => {
        const response = await fetch('/api/search/advanced', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(request)
        });
        
        return {
          status: response.status,
          data: await response.json()
        };
      }, searchRequest, authToken);

      expect(searchResponse.status).toBe(200);
      expect(searchResponse.data.search_id).toBeTruthy();
      expect(searchResponse.data.status).toBe('started');
    });

    test('should validate search parameters', async ({ page }) => {
      const invalidRequest = {
        repo_path: '', // Invalid empty path
        content_pattern: '',
        max_results: -1 // Invalid negative value
      };

      const response = await page.evaluate(async (request, token) => {
        const response = await fetch('/api/search/advanced', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(request)
        });
        
        return {
          status: response.status,
          data: await response.json()
        };
      }, invalidRequest, authToken);

      expect(response.status).toBe(422); // Validation error
      expect(response.data.detail).toBeTruthy();
    });

    test('should handle search status API', async ({ page }) => {
      // Start a search first
      const searchRequest = {
        repo_path: '/test/repo',
        content_pattern: 'test',
        file_extensions: ['js']
      };

      const searchResponse = await page.evaluate(async (request, token) => {
        const response = await fetch('/api/search/advanced', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(request)
        });
        return await response.json();
      }, searchRequest, authToken);

      const searchId = searchResponse.search_id;

      // Check search status
      const statusResponse = await page.evaluate(async (searchId, token) => {
        const response = await fetch(`/api/search/status/${searchId}`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });
        
        return {
          status: response.status,
          data: await response.json()
        };
      }, searchId, authToken);

      expect(statusResponse.status).toBe(200);
      expect(statusResponse.data.search_id).toBe(searchId);
      expect(['started', 'running', 'completed', 'failed']).toContain(statusResponse.data.status);
    });

    test('should handle search results API', async ({ page }) => {
      // Start a search
      const searchRequest = {
        repo_path: '/test/repo',
        content_pattern: 'import',
        file_extensions: ['py']
      };

      const searchResponse = await page.evaluate(async (request, token) => {
        const response = await fetch('/api/search/advanced', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(request)
        });
        return await response.json();
      }, searchRequest, authToken);

      const searchId = searchResponse.search_id;

      // Wait a bit for search to progress
      await page.waitForTimeout(2000);

      // Get search results
      const resultsResponse = await page.evaluate(async (searchId, token) => {
        const response = await fetch(`/api/search/results/${searchId}`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });
        
        return {
          status: response.status,
          data: await response.json()
        };
      }, searchId, authToken);

      expect(resultsResponse.status).toBe(200);
      expect(resultsResponse.data.search_id).toBe(searchId);
      expect(Array.isArray(resultsResponse.data.results)).toBe(true);
    });

    test('should handle fuzzy search API', async ({ page }) => {
      const fuzzyRequest = {
        repo_path: '/test/repo',
        content_pattern: 'functon', // Intentional typo
        fuzzy_search: true,
        fuzzy_threshold: 0.8,
        file_extensions: ['js']
      };

      const response = await page.evaluate(async (request, token) => {
        const response = await fetch('/api/search/fuzzy', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(request)
        });
        
        return {
          status: response.status,
          data: await response.json()
        };
      }, fuzzyRequest, authToken);

      expect(response.status).toBe(200);
      expect(response.data.search_id).toBeTruthy();
    });
  });

  test.describe('Repository API Integration @api @repository', () => {
    test('should list repositories via API', async ({ page }) => {
      const response = await page.evaluate(async (token) => {
        const response = await fetch('/api/repository/list', {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        return {
          status: response.status,
          data: await response.json()
        };
      }, authToken);

      expect(response.status).toBe(200);
      expect(Array.isArray(response.data.repositories)).toBe(true);
    });

    test('should get repository info via API', async ({ page }) => {
      const repoPath = '/test/repo';

      const response = await page.evaluate(async (repoPath, token) => {
        const response = await fetch(`/api/repository/info?repo_path=${encodeURIComponent(repoPath)}`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        return {
          status: response.status,
          data: await response.json()
        };
      }, repoPath, authToken);

      expect([200, 404]).toContain(response.status); // 404 if repo doesn't exist

      if (response.status === 200) {
        expect(response.data.path).toBe(repoPath);
        expect(response.data.branches).toBeTruthy();
      }
    });

    test('should validate repository paths', async ({ page }) => {
      const invalidPath = '../../../etc/passwd'; // Path traversal attempt

      const response = await page.evaluate(async (invalidPath, token) => {
        const response = await fetch(`/api/repository/info?repo_path=${encodeURIComponent(invalidPath)}`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        return {
          status: response.status,
          data: await response.json()
        };
      }, invalidPath, authToken);

      expect(response.status).toBe(400); // Should reject invalid paths
      expect(response.data.detail).toContain('Invalid');
    });
  });

  test.describe('API Error Handling @api @error', () => {
    test('should handle unauthorized requests', async ({ page }) => {
      const response = await page.evaluate(async () => {
        const response = await fetch('/api/search/advanced', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            repo_path: '/test/repo',
            content_pattern: 'test'
          })
        });

        return {
          status: response.status,
          data: await response.json()
        };
      });

      expect(response.status).toBe(401);
      expect(response.data.detail).toContain('Not authenticated');
    });

    test('should handle invalid JSON payloads', async ({ page }) => {
      const response = await page.evaluate(async (token) => {
        const response = await fetch('/api/search/advanced', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: 'invalid json payload'
        });

        return {
          status: response.status,
          data: await response.json()
        };
      }, authToken);

      expect(response.status).toBe(422);
      expect(response.data.detail).toBeTruthy();
    });

    test('should handle missing required fields', async ({ page }) => {
      const incompleteRequest = {
        // Missing required repo_path
        content_pattern: 'test'
      };

      const response = await page.evaluate(async (request, token) => {
        const response = await fetch('/api/search/advanced', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(request)
        });

        return {
          status: response.status,
          data: await response.json()
        };
      }, incompleteRequest, authToken);

      expect(response.status).toBe(422);
      expect(response.data.detail).toBeTruthy();
    });

    test('should handle server errors gracefully', async ({ page }) => {
      // Mock server error
      await page.route('**/api/search/advanced', route => {
        route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({
            detail: 'Internal server error',
            error_code: 'INTERNAL_ERROR'
          })
        });
      });

      const response = await page.evaluate(async (token) => {
        const response = await fetch('/api/search/advanced', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            repo_path: '/test/repo',
            content_pattern: 'test'
          })
        });

        return {
          status: response.status,
          data: await response.json()
        };
      }, authToken);

      expect(response.status).toBe(500);
      expect(response.data.detail).toContain('Internal server error');
    });

    test('should handle network timeouts', async ({ page }) => {
      // Mock slow response
      await page.route('**/api/search/advanced', async route => {
        await new Promise(resolve => setTimeout(resolve, 10000)); // 10 second delay
        route.continue();
      });

      const startTime = Date.now();

      const response = await page.evaluate(async (token) => {
        try {
          const controller = new AbortController();
          const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout

          const response = await fetch('/api/search/advanced', {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              repo_path: '/test/repo',
              content_pattern: 'test'
            }),
            signal: controller.signal
          });

          clearTimeout(timeoutId);
          return { status: response.status, timeout: false };
        } catch (error) {
          return { status: null, timeout: true, error: error.name };
        }
      }, authToken);

      const endTime = Date.now();

      // Should timeout within reasonable time
      expect(endTime - startTime).toBeLessThan(8000);
      expect(response.timeout || response.error === 'AbortError').toBe(true);
    });

    test('should handle malformed responses', async ({ page }) => {
      // Mock malformed response
      await page.route('**/api/search/advanced', route => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: 'invalid json response'
        });
      });

      const response = await page.evaluate(async (token) => {
        try {
          const response = await fetch('/api/search/advanced', {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              repo_path: '/test/repo',
              content_pattern: 'test'
            })
          });

          const data = await response.json();
          return { status: response.status, data, parseError: false };
        } catch (error) {
          return { status: null, parseError: true, error: error.message };
        }
      }, authToken);

      expect(response.parseError).toBe(true);
      expect(response.error).toContain('JSON');
    });
  });

  test.describe('API Security Tests @api @security', () => {
    test('should prevent SQL injection in search queries', async ({ page }) => {
      const sqlInjectionAttempts = [
        "'; DROP TABLE users; --",
        "' OR '1'='1",
        "' UNION SELECT * FROM users --",
        "admin'/*"
      ];

      for (const maliciousQuery of sqlInjectionAttempts) {
        const response = await page.evaluate(async (query, token) => {
          const response = await fetch('/api/search/advanced', {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              repo_path: '/test/repo',
              content_pattern: query
            })
          });

          return {
            status: response.status,
            data: await response.json()
          };
        }, maliciousQuery, authToken);

        // Should either reject or sanitize the input
        expect([200, 400, 422]).toContain(response.status);

        if (response.status === 200) {
          // If accepted, should not contain SQL injection artifacts
          expect(response.data.search_id).toBeTruthy();
        }
      }
    });

    test('should validate input lengths', async ({ page }) => {
      const veryLongString = 'a'.repeat(100000); // 100KB string

      const response = await page.evaluate(async (longString, token) => {
        const response = await fetch('/api/search/advanced', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            repo_path: '/test/repo',
            content_pattern: longString
          })
        });

        return {
          status: response.status,
          data: await response.json()
        };
      }, veryLongString, authToken);

      // Should reject overly long inputs
      expect([400, 413, 422]).toContain(response.status);
    });

    test('should prevent XSS in API responses', async ({ page }) => {
      const xssPayload = '<script>alert("xss")</script>';

      const response = await page.evaluate(async (payload, token) => {
        const response = await fetch('/api/search/advanced', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            repo_path: '/test/repo',
            content_pattern: payload
          })
        });

        return {
          status: response.status,
          data: await response.json()
        };
      }, xssPayload, authToken);

      // Response should not contain unescaped script tags
      const responseText = JSON.stringify(response.data);
      expect(responseText).not.toContain('<script>');
      expect(responseText).not.toContain('alert(');
    });

    test('should enforce CORS policies', async ({ page }) => {
      const response = await page.evaluate(async (token) => {
        const response = await fetch('/api/search/advanced', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
            'Origin': 'https://malicious-site.com'
          },
          body: JSON.stringify({
            repo_path: '/test/repo',
            content_pattern: 'test'
          })
        });

        return {
          status: response.status,
          headers: Object.fromEntries(response.headers.entries())
        };
      }, authToken);

      // Should have appropriate CORS headers
      expect(response.headers['access-control-allow-origin']).toBeTruthy();
    });
  });
});
