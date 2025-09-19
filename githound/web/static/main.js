/**
 * GitHound Web Interface - Main Entry Point
 *
 * This is the new modular entry point for the GitHound web interface.
 * It replaces the monolithic app.js with a component-based architecture.
 */

import { GitHoundApp } from './components/core/app.js';
import eventBus from './components/core/event-bus.js';

// Make eventBus globally available
window.EventBus = eventBus;

// Global functions for HTML onclick handlers (backward compatibility)
window.loadSearchTemplate = function (templateId) {
  eventBus.emit('search:loadTemplate', templateId);
};

window.saveSearchTemplate = function () {
  eventBus.emit('search:saveTemplate');
};

window.clearForm = function () {
  const form = document.getElementById('searchForm');
  if (form) {
    form.reset();
    eventBus.emit('form:cleared');
  }
};

window.showSearchHistory = function () {
  eventBus.emit('search:showHistory');
};

window.loadTemplateById = function (templateId) {
  eventBus.emit('search:loadTemplate', templateId);
};

window.showHelp = function () {
  eventBus.emit('help:show');
};

// Authentication functions
window.showLoginModal = function () {
  const modal = new bootstrap.Modal(document.getElementById('loginModal'));
  modal.show();
};

window.showRegisterModal = function () {
  const modal = new bootstrap.Modal(document.getElementById('registerModal'));
  modal.show();
};

window.logout = function () {
  eventBus.emit('auth:logout');
};

window.showProfile = function () {
  eventBus.emit('auth:showProfile');
};

window.showAdminPanel = function () {
  eventBus.emit('admin:showPanel');
};

// Help modal function
window.showHelpModal = function () {
  const modal = document.createElement('div');
  modal.className = 'modal fade';
  modal.innerHTML = `
    <div class="modal-dialog modal-lg">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">
            <i class="fas fa-question-circle me-2"></i>GitHound Help
          </h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
        </div>
        <div class="modal-body">
          <div class="row">
            <div class="col-md-6">
              <h6><i class="fas fa-keyboard me-2"></i>Keyboard Shortcuts</h6>
              <table class="table table-sm">
                <tr><td><kbd>Ctrl/Cmd + Enter</kbd></td><td>Start search</td></tr>
                <tr><td><kbd>Escape</kbd></td><td>Cancel search</td></tr>
                <tr><td><kbd>Ctrl/Cmd + K</kbd></td><td>Focus search input</td></tr>
                <tr><td><kbd>Ctrl/Cmd + /</kbd></td><td>Show help</td></tr>
              </table>

              <h6 class="mt-3"><i class="fas fa-search me-2"></i>Search Tips</h6>
              <ul class="list-unstyled">
                <li>• Use regular expressions for advanced pattern matching</li>
                <li>• Combine multiple search criteria for better results</li>
                <li>• Use date ranges to narrow down results</li>
                <li>• File patterns support glob syntax (*.js, src/**)</li>
              </ul>
            </div>
            <div class="col-md-6">
              <h6><i class="fas fa-lightbulb me-2"></i>Features</h6>
              <ul class="list-unstyled">
                <li>• <strong>Real-time progress:</strong> Live updates via WebSocket</li>
                <li>• <strong>Export options:</strong> JSON and CSV formats</li>
                <li>• <strong>Search templates:</strong> Save and reuse configurations</li>
                <li>• <strong>Search history:</strong> Access previous searches</li>
                <li>• <strong>Theme toggle:</strong> Light and dark modes</li>
                <li>• <strong>Auto-save:</strong> Form data is automatically saved</li>
              </ul>

              <h6 class="mt-3"><i class="fas fa-code me-2"></i>Regex Examples</h6>
              <ul class="list-unstyled">
                <li>• <code>function.*test</code> - Functions containing "test"</li>
                <li>• <code>\\b(bug|fix|issue)\\b</code> - Bug-related terms</li>
                <li>• <code>TODO|FIXME</code> - Code comments</li>
              </ul>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-primary" data-bs-dismiss="modal">Got it!</button>
        </div>
      </div>
    </div>
  `;

  document.body.appendChild(modal);
  const bsModal = new bootstrap.Modal(modal);
  bsModal.show();

  modal.addEventListener('hidden.bs.modal', () => {
    document.body.removeChild(modal);
  });
};

// Set up help event listener
eventBus.on('help:show', window.showHelpModal);

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', async () => {
  try {
    console.log('🚀 Initializing GitHound Web Interface v2.0');

    // Create and initialize the main application
    window.app = new GitHoundApp();
    await window.app.init();

    console.log('✅ GitHound Web Interface initialized successfully');

    // Show initialization success notification
    setTimeout(() => {
      eventBus.emit('notification:success', 'GitHound initialized successfully');
    }, 1000);
  } catch (error) {
    console.error('❌ Failed to initialize GitHound:', error);

    // Show error notification
    eventBus.emit('notification:error', `Failed to initialize: ${error.message}`);

    // Fallback to legacy app if available
    if (typeof GitHoundApp !== 'undefined') {
      console.log('🔄 Falling back to legacy application...');
      try {
        window.app = new GitHoundApp();
        console.log('✅ Legacy application initialized');
      } catch (legacyError) {
        console.error('❌ Legacy fallback also failed:', legacyError);
      }
    }
  }
});

// Export for debugging
export { GitHoundApp, eventBus };
