/**
 * API Utilities
 *
 * Centralized API communication utilities.
 */

/**
 * Base API configuration
 */
export const API_CONFIG = {
  baseURL: '',
  timeout: 30000,
  retries: 3,
  retryDelay: 1000
};

/**
 * HTTP status codes
 */
export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  NO_CONTENT: 204,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  CONFLICT: 409,
  INTERNAL_SERVER_ERROR: 500,
  SERVICE_UNAVAILABLE: 503
};

/**
 * API error class
 */
export class APIError extends Error {
  constructor(message, status, response) {
    super(message);
    this.name = 'APIError';
    this.status = status;
    this.response = response;
  }
}

/**
 * Make HTTP request with retry logic
 */
export async function makeRequest(url, options = {}) {
  const config = {
    timeout: API_CONFIG.timeout,
    retries: API_CONFIG.retries,
    retryDelay: API_CONFIG.retryDelay,
    ...options
  };

  let lastError;

  for (let attempt = 0; attempt <= config.retries; attempt++) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), config.timeout);

      const response = await fetch(url, {
        ...config,
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new APIError(
          errorData.detail || `HTTP ${response.status}: ${response.statusText}`,
          response.status,
          response
        );
      }

      return response;
    } catch (error) {
      lastError = error;

      // Don't retry on client errors (4xx) except 408, 429
      if (error.status >= 400 && error.status < 500
          && error.status !== 408 && error.status !== 429) {
        throw error;
      }

      // Don't retry on the last attempt
      if (attempt === config.retries) {
        throw error;
      }

      // Wait before retrying
      await new Promise(resolve => setTimeout(resolve, config.retryDelay * (attempt + 1)));
    }
  }

  throw lastError;
}

/**
 * GET request
 */
export async function get(url, options = {}) {
  const response = await makeRequest(url, {
    method: 'GET',
    ...options
  });
  return response.json();
}

/**
 * POST request
 */
export async function post(url, data, options = {}) {
  const response = await makeRequest(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...options.headers
    },
    body: JSON.stringify(data),
    ...options
  });
  return response.json();
}

/**
 * PUT request
 */
export async function put(url, data, options = {}) {
  const response = await makeRequest(url, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      ...options.headers
    },
    body: JSON.stringify(data),
    ...options
  });
  return response.json();
}

/**
 * DELETE request
 */
export async function del(url, options = {}) {
  const response = await makeRequest(url, {
    method: 'DELETE',
    ...options
  });

  // DELETE might not return content
  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    return response.json();
  }
  return null;
}

/**
 * Upload file
 */
export async function upload(url, file, options = {}) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await makeRequest(url, {
    method: 'POST',
    body: formData,
    ...options
  });
  return response.json();
}

/**
 * Download file
 */
export async function download(url, options = {}) {
  const response = await makeRequest(url, {
    method: 'GET',
    ...options
  });
  return response.blob();
}

/**
 * Add authentication token to request headers
 */
export function withAuth(token) {
  return {
    headers: {
      Authorization: `Bearer ${token}`
    }
  };
}

/**
 * Create API client with base configuration
 */
export function createAPIClient(baseConfig = {}) {
  const config = { ...API_CONFIG, ...baseConfig };

  return {
    get: (url, options = {}) => get(`${config.baseURL}${url}`, { ...config, ...options }),
    post: (url, data, options = {}) => post(`${config.baseURL}${url}`, data, { ...config, ...options }),
    put: (url, data, options = {}) => put(`${config.baseURL}${url}`, data, { ...config, ...options }),
    delete: (url, options = {}) => del(`${config.baseURL}${url}`, { ...config, ...options }),
    upload: (url, file, options = {}) => upload(`${config.baseURL}${url}`, file, { ...config, ...options }),
    download: (url, options = {}) => download(`${config.baseURL}${url}`, { ...config, ...options })
  };
}

/**
 * GitHound specific API endpoints
 */
export const ENDPOINTS = {
  // Search
  SEARCH: '/api/search',
  SEARCH_STATUS: id => `/api/search/${id}/status`,
  SEARCH_RESULTS: id => `/api/search/${id}/results`,
  SEARCH_EXPORT: id => `/api/search/${id}/export`,
  SEARCH_CANCEL: id => `/api/search/${id}`,

  // Authentication
  AUTH_LOGIN: '/auth/login',
  AUTH_REGISTER: '/auth/register',
  AUTH_LOGOUT: '/auth/logout',
  AUTH_REFRESH: '/auth/refresh',
  AUTH_CHANGE_PASSWORD: '/auth/change-password',

  // User management
  USER_PROFILE: '/api/user/profile',
  USER_SETTINGS: '/api/user/settings',

  // Admin
  ADMIN_USERS: '/api/admin/users',
  ADMIN_STATS: '/api/admin/stats',
  ADMIN_LOGS: '/api/admin/logs'
};

export default {
  makeRequest,
  get,
  post,
  put,
  delete: del,
  upload,
  download,
  withAuth,
  createAPIClient,
  APIError,
  HTTP_STATUS,
  ENDPOINTS
};
