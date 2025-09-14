/**
 * Page Object Models index file for GitHound web tests.
 * Exports all page objects for easy importing in test files.
 */

const BasePage = require('./base-page');
const LoginPage = require('./login-page');
const SearchPage = require('./search-page');
const ResultsPage = require('./results-page');
const ExportPage = require('./export-page');
const AdminPage = require('./admin-page');

module.exports = {
  BasePage,
  LoginPage,
  SearchPage,
  ResultsPage,
  ExportPage,
  AdminPage
};
