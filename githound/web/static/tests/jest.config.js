/**
 * Jest configuration for GitHound frontend component testing
 */

module.exports = {
  // Test environment
  testEnvironment: 'jsdom',

  // Test file patterns
  testMatch: [
    '<rootDir>/tests/**/*.test.js',
    '<rootDir>/tests/**/*.spec.js'
  ],

  // Module file extensions
  moduleFileExtensions: ['js', 'json'],

  // Module name mapping for ES6 imports
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',
    '^@components/(.*)$': '<rootDir>/components/$1',
    '^@utils/(.*)$': '<rootDir>/utils/$1',
    '^@styles/(.*)$': '<rootDir>/styles/$1'
  },

  // Setup files
  setupFilesAfterEnv: [
    '<rootDir>/tests/setup.js'
  ],

  // Transform configuration
  transform: {
    '^.+\\.js$': 'babel-jest'
  },

  // Coverage configuration
  collectCoverage: true,
  collectCoverageFrom: [
    'components/**/*.js',
    'utils/**/*.js',
    '!components/**/README.md',
    '!**/node_modules/**',
    '!**/tests/**'
  ],

  coverageDirectory: 'tests/coverage',

  coverageReporters: [
    'text',
    'text-summary',
    'html',
    'lcov',
    'json'
  ],

  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    }
  },

  // Test timeout
  testTimeout: 10000,

  // Verbose output
  verbose: true,

  // Clear mocks between tests
  clearMocks: true,

  // Restore mocks after each test
  restoreMocks: true,

  // Error handling
  errorOnDeprecated: true,

  // Globals
  globals: {
    window: {},
    document: {},
    navigator: {},
    location: {}
  },

  // Mock modules
  modulePathIgnorePatterns: [
    '<rootDir>/node_modules/'
  ],

  // Test reporters
  reporters: [
    'default',
    ['jest-html-reporters', {
      publicPath: './tests/reports',
      filename: 'test-report.html',
      expand: true
    }]
  ],

  // Watch mode configuration
  watchPathIgnorePatterns: [
    '<rootDir>/node_modules/',
    '<rootDir>/tests/coverage/',
    '<rootDir>/tests/reports/'
  ]
};
