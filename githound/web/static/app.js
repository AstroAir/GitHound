// GitHound Web Interface JavaScript - Enhanced Version

class WebSocketManager {
  constructor() {
    this.websocket = null;
    this.isConnectedFlag = false;
    this.isAuthenticatedFlag = false;
    this.messageHandlers = [];
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000;
  }

  isConnected() {
    return this.isConnectedFlag && this.websocket && this.websocket.readyState === WebSocket.OPEN;
  }

  isAuthenticated() {
    return this.isAuthenticatedFlag;
  }

  onMessage(handler) {
    this.messageHandlers.push(handler);
  }

  connect(url, authToken = null) {
    if (this.websocket) {
      this.websocket.close();
    }

    this.websocket = new WebSocket(url);

    this.websocket.onopen = () => {
      this.isConnectedFlag = true;
      this.reconnectAttempts = 0;

      // Send authentication if token provided
      if (authToken) {
        this.websocket.send(JSON.stringify({
          type: 'auth',
          token: authToken
        }));
      }
    };

    this.websocket.onmessage = event => {
      try {
        const message = JSON.parse(event.data);

        // Handle authentication response
        if (message.type === 'auth_success') {
          this.isAuthenticatedFlag = true;
        } else if (message.type === 'auth_failed') {
          this.isAuthenticatedFlag = false;
        }

        // Notify all handlers
        this.messageHandlers.forEach(handler => {
          try {
            handler(message);
          } catch (error) {
            console.error('Error in WebSocket message handler:', error);
          }
        });
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    this.websocket.onclose = () => {
      this.isConnectedFlag = false;
      this.isAuthenticatedFlag = false;

      // Attempt reconnection
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        this.reconnectAttempts++;
        setTimeout(() => {
          this.connect(url, authToken);
        }, this.reconnectDelay * this.reconnectAttempts);
      }
    };

    this.websocket.onerror = error => {
      console.error('WebSocket error:', error);
    };
  }

  send(message) {
    if (this.isConnected()) {
      this.websocket.send(JSON.stringify(message));
    }
  }

  close() {
    if (this.websocket) {
      this.websocket.close();
      this.websocket = null;
    }
    this.isConnectedFlag = false;
    this.isAuthenticatedFlag = false;
  }
}

class GitHoundApp {
  constructor() {
    this.currentSearchId = null;
    this.websocket = null;
    this.searchResults = [];
    this.isSearching = false;
    this.searchHistory = this.loadSearchHistory();
    this.searchTemplates = this.loadSearchTemplates();
    this.currentUser = null;
    this.authToken = null;
    this.stats = {
      totalSearches: 0,
      activeSearches: 0,
      totalResults: 0,
      lastSearchTime: null
    };

    this.initializeEventListeners();
    this.initializeTheme();
    this.initializeAuth();
    this.loadStats();
    this.updateConnectionStatus('disconnected');
    this.updateDashboard();
    this.loadQuickActions();
  }

  initializeEventListeners() {
    // Form submission
    document.getElementById('searchForm').addEventListener('submit', e => {
      e.preventDefault();
      this.startSearch();
    });

    // Cancel button
    document.getElementById('cancelButton').addEventListener('click', () => {
      this.cancelSearch();
    });

    // Export buttons
    document.getElementById('exportJson').addEventListener('click', () => {
      this.exportResults('json');
    });

    document.getElementById('exportCsv').addEventListener('click', () => {
      this.exportResults('csv');
    });

    // Authentication event listeners
    document.getElementById('loginForm').addEventListener('submit', e => {
      e.preventDefault();
      this.handleLogin();
    });

    document.getElementById('registerForm').addEventListener('submit', e => {
      e.preventDefault();
      this.handleRegistration();
    });

    // Profile event listeners
    document.getElementById('changePasswordForm').addEventListener('submit', e => {
      e.preventDefault();
      this.handlePasswordChange();
    });

    // Fuzzy threshold slider
    const fuzzyThreshold = document.getElementById('fuzzyThreshold');
    const fuzzyThresholdValue = document.getElementById('fuzzyThresholdValue');
    fuzzyThreshold.addEventListener('input', e => {
      fuzzyThresholdValue.textContent = e.target.value;
    });

    // Enable/disable fuzzy threshold based on checkbox
    document.getElementById('fuzzySearch').addEventListener('change', e => {
      fuzzyThreshold.disabled = !e.target.checked;
    });

    // Theme toggle
    document.getElementById('themeToggle').addEventListener('click', () => {
      this.toggleTheme();
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', e => {
      this.handleKeyboardShortcuts(e);
    });

    // Auto-save form data
    this.setupAutoSave();
  }

  initializeTheme() {
    const savedTheme = localStorage.getItem('githound-theme') || 'light';
    this.setTheme(savedTheme);
  }

  toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    this.setTheme(newTheme);
  }

  setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('githound-theme', theme);

    const themeIcon = document.getElementById('themeIcon');
    if (theme === 'dark') {
      themeIcon.className = 'fas fa-sun';
    } else {
      themeIcon.className = 'fas fa-moon';
    }
  }

  handleKeyboardShortcuts(e) {
    // Ctrl/Cmd + Enter: Start search
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      this.startSearch();
    }

    // Escape: Cancel search
    if (e.key === 'Escape' && this.isSearching) {
      this.cancelSearch();
    }

    // Ctrl/Cmd + K: Focus search input
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      e.preventDefault();
      document.getElementById('contentPattern').focus();
    }
  }

  setupAutoSave() {
    const formInputs = document.querySelectorAll('#searchForm input, #searchForm select');
    formInputs.forEach(input => {
      input.addEventListener('input', () => {
        this.saveFormState();
      });
    });

    // Load saved form state
    this.loadFormState();
  }

  saveFormState() {
    const formData = new FormData(document.getElementById('searchForm'));
    const formState = {};
    for (const [key, value] of formData.entries()) {
      formState[key] = value;
    }
    localStorage.setItem('githound-form-state', JSON.stringify(formState));
  }

  loadFormState() {
    const savedState = localStorage.getItem('githound-form-state');
    if (savedState) {
      try {
        const formState = JSON.parse(savedState);
        Object.keys(formState).forEach(key => {
          const element = document.getElementById(key);
          if (element) {
            element.value = formState[key];
          }
        });
      } catch (e) {
        console.warn('Failed to load form state:', e);
      }
    }
  }

  loadSearchHistory() {
    const history = localStorage.getItem('githound-search-history');
    return history ? JSON.parse(history) : [];
  }

  saveSearchHistory() {
    localStorage.setItem('githound-search-history', JSON.stringify(this.searchHistory));
  }

  loadSearchTemplates() {
    const templates = localStorage.getItem('githound-search-templates');
    return templates ? JSON.parse(templates) : this.getDefaultTemplates();
  }

  saveSearchTemplates() {
    localStorage.setItem('githound-search-templates', JSON.stringify(this.searchTemplates));
  }

  getDefaultTemplates() {
    return {
      'recent-commits': {
        name: 'Recent Commits',
        description: 'Find commits from the last 7 days',
        config: {
          dateFrom: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
          dateTo: new Date().toISOString().split('T')[0]
        }
      },
      'bug-fixes': {
        name: 'Bug Fixes',
        description: 'Find commits that fix bugs',
        config: {
          messagePattern: '(fix|bug|issue|resolve)',
          caseSensitive: false
        }
      },
      'code-changes': {
        name: 'Code Changes',
        description: 'Find code changes in specific file types',
        config: {
          fileExtensions: 'js,ts,py,java,cpp,c',
          contentPattern: '(function|class|method)'
        }
      }
    };
  }

  updateDashboard() {
    document.getElementById('totalSearches').textContent = this.stats.totalSearches;
    document.getElementById('activeSearches').textContent = this.stats.activeSearches;
    document.getElementById('totalResults').textContent = this.stats.totalResults;

    if (this.stats.lastSearchTime) {
      const timeAgo = this.getTimeAgo(this.stats.lastSearchTime);
      document.getElementById('lastSearchTime').textContent = timeAgo;
    }

    // Save stats to localStorage
    this.saveStats();
  }

  saveStats() {
    localStorage.setItem('githound-stats', JSON.stringify(this.stats));
  }

  loadStats() {
    const savedStats = localStorage.getItem('githound-stats');
    if (savedStats) {
      try {
        const stats = JSON.parse(savedStats);
        this.stats = { ...this.stats, ...stats };
        // Reset active searches on page load
        this.stats.activeSearches = 0;
      } catch (e) {
        console.warn('Failed to load stats:', e);
      }
    }
  }

  getTimeAgo(timestamp) {
    const now = new Date();
    const searchTime = new Date(timestamp);
    const diffMs = now - searchTime;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) { return 'Just now'; }
    if (diffMins < 60) { return `${diffMins}m ago`; }
    if (diffHours < 24) { return `${diffHours}h ago`; }
    return `${diffDays}d ago`;
  }

  loadQuickActions() {
    // Quick actions are already defined in HTML
    // This method can be used to dynamically update them if needed
  }

  async startSearch() {
    if (this.isSearching) {
      this.showAlert('A search is already in progress', 'warning');
      return;
    }

    // Validate form
    if (!this.validateForm()) {
      return;
    }

    // Prepare search request
    const searchRequest = this.buildSearchRequest();

    try {
      this.isSearching = true;
      this.updateUI('searching');

      // Update stats
      this.stats.totalSearches++;
      this.stats.activeSearches++;
      this.stats.lastSearchTime = new Date().toISOString();
      this.updateDashboard();

      // Save to search history
      this.addToSearchHistory(searchRequest);

      // Start search
      const response = await fetch('/api/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(searchRequest)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      this.currentSearchId = result.search_id;

      // Connect to WebSocket for real-time updates
      this.connectWebSocket(this.currentSearchId);

      // Start polling for status updates (fallback)
      this.startStatusPolling();
    } catch (error) {
      console.error('Search failed:', error);
      this.showAlert(`Search failed: ${error.message}`, 'danger');
      this.isSearching = false;
      this.stats.activeSearches--;
      this.updateDashboard();
      this.updateUI('idle');
    }
  }

  addToSearchHistory(searchRequest) {
    const historyItem = {
      id: Date.now(),
      timestamp: new Date().toISOString(),
      request: searchRequest,
      name: this.generateSearchName(searchRequest)
    };

    this.searchHistory.unshift(historyItem);

    // Keep only last 50 searches
    if (this.searchHistory.length > 50) {
      this.searchHistory = this.searchHistory.slice(0, 50);
    }

    this.saveSearchHistory();
  }

  generateSearchName(searchRequest) {
    const parts = [];

    if (searchRequest.content_pattern) {
      parts.push(`Content: "${searchRequest.content_pattern}"`);
    }
    if (searchRequest.commit_hash) {
      parts.push(`Commit: ${searchRequest.commit_hash}`);
    }
    if (searchRequest.author_pattern) {
      parts.push(`Author: ${searchRequest.author_pattern}`);
    }
    if (searchRequest.message_pattern) {
      parts.push(`Message: "${searchRequest.message_pattern}"`);
    }
    if (searchRequest.file_path_pattern) {
      parts.push(`Files: ${searchRequest.file_path_pattern}`);
    }

    return parts.length > 0 ? parts.join(', ') : 'General Search';
  }

  loadSearchTemplate(templateId) {
    if (templateId && this.searchTemplates[templateId]) {
      const template = this.searchTemplates[templateId];
      this.applySearchConfig(template.config);
      this.showAlert(`Loaded template: ${template.name}`, 'success');
    } else {
      this.showSearchTemplateDialog();
    }
  }

  showSearchTemplateDialog() {
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.innerHTML = `
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">
              <i class="fas fa-folder-open me-2"></i>Load Search Template
            </h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body">
            <div class="list-group">
              ${Object.entries(this.searchTemplates).map(([id, template]) => `
                <button type="button" class="list-group-item list-group-item-action" onclick="app.loadTemplateById('${id}')">
                  <div class="d-flex justify-content-between align-items-start">
                    <div>
                      <h6 class="mb-1">${template.name}</h6>
                      <small class="text-muted">${template.description}</small>
                    </div>
                    <small class="text-muted">Template</small>
                  </div>
                </button>
              `).join('')}
            </div>
            ${Object.keys(this.searchTemplates).length === 0
    ? '<p class="text-muted text-center">No templates available. Create one by saving your current search configuration.</p>'
    : ''
}
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
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
  }

  loadTemplateById(templateId) {
    const template = this.searchTemplates[templateId];
    if (template) {
      this.applySearchConfig(template.config);
      this.showAlert(`Loaded template: ${template.name}`, 'success');

      // Close modal
      const modal = document.querySelector('.modal.show');
      if (modal) {
        bootstrap.Modal.getInstance(modal).hide();
      }
    }
  }

  applySearchConfig(config) {
    Object.keys(config).forEach(key => {
      const element = document.getElementById(key);
      if (element) {
        if (element.type === 'checkbox') {
          element.checked = config[key];
        } else {
          element.value = config[key];
        }
      }
    });
  }

  saveSearchTemplate() {
    const name = prompt('Enter template name:');
    if (!name) { return; }

    const config = this.getCurrentSearchConfig();
    const templateId = name.toLowerCase().replace(/\s+/g, '-');

    this.searchTemplates[templateId] = {
      name,
      description: `Custom template: ${name}`,
      config
    };

    this.saveSearchTemplates();
    this.showAlert(`Template "${name}" saved successfully`, 'success');
  }

  getCurrentSearchConfig() {
    const config = {};
    const formInputs = document.querySelectorAll('#searchForm input, #searchForm select');

    formInputs.forEach(input => {
      if (input.id && input.value) {
        if (input.type === 'checkbox') {
          config[input.id] = input.checked;
        } else {
          config[input.id] = input.value;
        }
      }
    });

    return config;
  }

  clearForm() {
    document.getElementById('searchForm').reset();
    document.getElementById('repoPath').value = '.';
    this.showAlert('Form cleared', 'info');
  }

  showSearchHistory() {
    if (this.searchHistory.length === 0) {
      this.showAlert('No search history available', 'info');
      return;
    }

    // Create and show search history modal
    this.showSearchHistoryModal();
  }

  showSearchHistoryModal() {
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.innerHTML = `
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Search History</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body">
            <div class="list-group">
              ${this.searchHistory.map(item => `
                <div class="list-group-item">
                  <div class="d-flex justify-content-between align-items-start">
                    <div>
                      <h6 class="mb-1">${item.name}</h6>
                      <small class="text-muted">${new Date(item.timestamp).toLocaleString()}</small>
                    </div>
                    <button class="btn btn-sm btn-outline-primary" onclick="app.loadHistoryItem(${item.id})">
                      Load
                    </button>
                  </div>
                </div>
              `).join('')}
            </div>
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
  }

  loadHistoryItem(itemId) {
    const item = this.searchHistory.find(h => h.id === itemId);
    if (item) {
      this.applySearchConfig(item.request);
      this.showAlert('Search configuration loaded from history', 'success');

      // Close modal
      const modal = document.querySelector('.modal.show');
      if (modal) {
        bootstrap.Modal.getInstance(modal).hide();
      }
    }
  }

  async cancelSearch() {
    if (!this.currentSearchId) {
      return;
    }

    try {
      const response = await fetch(`/api/search/${this.currentSearchId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        this.showAlert('Search cancelled', 'info');
      }
    } catch (error) {
      console.error('Cancel failed:', error);
    }

    this.stopSearch();
  }

  connectWebSocket(searchId) {
    // Close existing connection
    if (this.websocket) {
      this.websocket.close();
    }

    // Create WebSocket connection
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/${searchId}`;

    // Use the global WebSocket manager
    if (window.websocketManager) {
      window.websocketManager.connect(wsUrl, this.authToken);

      // Set up message handler for search updates
      window.websocketManager.onMessage(message => {
        this.handleWebSocketMessage(message);
      });

      this.updateConnectionStatus('connecting');

      // Check connection status periodically
      const checkConnection = () => {
        if (window.websocketManager.isConnected()) {
          this.updateConnectionStatus('connected');
        } else {
          setTimeout(checkConnection, 100);
        }
      };
      checkConnection();
    } else {
      // Fallback to direct WebSocket connection
      this.websocket = new WebSocket(wsUrl);

      this.websocket.onopen = () => {
        console.log('WebSocket connected');
        this.updateConnectionStatus('connected');
      };

      this.websocket.onmessage = event => {
        const message = JSON.parse(event.data);
        this.handleWebSocketMessage(message);
      };

      this.websocket.onclose = () => {
        console.log('WebSocket disconnected');
        this.updateConnectionStatus('disconnected');
      };

      this.websocket.onerror = error => {
        console.error('WebSocket error:', error);
        this.updateConnectionStatus('disconnected');
      };
    }
  }

  handleWebSocketMessage(message) {
    const { type, data } = message;

    switch (type) {
      case 'connected':
        console.log('WebSocket connection confirmed');
        break;

      case 'progress':
        this.updateProgress(data.progress, data.message, data.results_count);
        break;

      case 'result':
        this.addResult(data.result);
        break;

      case 'completed':
        this.handleSearchCompletion(data);
        break;

      case 'error':
        this.handleSearchError(data.error);
        break;

      case 'ping':
        // Respond to ping
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
          this.websocket.send(JSON.stringify({ type: 'pong' }));
        }
        break;

      default:
        console.log('Unknown WebSocket message type:', type);
    }
  }

  buildSearchRequest() {
    const request = {
      repo_path: document.getElementById('repoPath').value,
      branch: document.getElementById('branch').value || null,
      content_pattern: document.getElementById('contentPattern').value || null,
      commit_hash: document.getElementById('commitHash').value || null,
      author_pattern: document.getElementById('authorPattern').value || null,
      message_pattern: document.getElementById('messagePattern').value || null,
      file_path_pattern:
        document.getElementById('filePathPattern').value || null,
      case_sensitive: document.getElementById('caseSensitive').checked,
      fuzzy_search: document.getElementById('fuzzySearch').checked,
      fuzzy_threshold: parseFloat(
        document.getElementById('fuzzyThreshold').value
      ),
      max_results:
        parseInt(document.getElementById('maxResults').value) || null,
      max_file_size:
        parseInt(document.getElementById('maxFileSize').value) || null,
      timeout_seconds:
        parseInt(document.getElementById('timeoutSeconds').value) || 300
    };

    // Handle date fields
    const dateFrom = document.getElementById('dateFrom').value;
    const dateTo = document.getElementById('dateTo').value;
    if (dateFrom) { request.date_from = `${dateFrom}T00:00:00`; }
    if (dateTo) { request.date_to = `${dateTo}T23:59:59`; }

    // Handle comma-separated lists
    const fileExtensions = document.getElementById('fileExtensions').value;
    if (fileExtensions) {
      request.file_extensions = fileExtensions
        .split(',')
        .map(ext => ext.trim())
        .filter(ext => ext);
    }

    const includeGlobs = document.getElementById('includeGlobs').value;
    if (includeGlobs) {
      request.include_globs = includeGlobs
        .split(',')
        .map(glob => glob.trim())
        .filter(glob => glob);
    }

    const excludeGlobs = document.getElementById('excludeGlobs').value;
    if (excludeGlobs) {
      request.exclude_globs = excludeGlobs
        .split(',')
        .map(glob => glob.trim())
        .filter(glob => glob);
    }

    return request;
  }

  validateForm() {
    const repoPath = document.getElementById('repoPath').value;
    if (!repoPath.trim()) {
      this.showAlert('Repository path is required', 'danger');
      return false;
    }

    // Check if at least one search criterion is provided
    const criteria = [
      'contentPattern',
      'commitHash',
      'authorPattern',
      'messagePattern',
      'filePathPattern',
      'fileExtensions',
      'dateFrom',
      'dateTo'
    ];

    const hasAnyCriteria = criteria.some(id => {
      const { value } = document.getElementById(id);
      return value && value.trim();
    });

    if (!hasAnyCriteria) {
      this.showAlert(
        'At least one search criterion must be provided',
        'danger'
      );
      return false;
    }

    return true;
  }

  updateUI(state) {
    const searchButton = document.getElementById('searchButton');
    const cancelButton = document.getElementById('cancelButton');
    const progressCard = document.getElementById('progressCard');
    const resultsCard = document.getElementById('resultsCard');

    switch (state) {
      case 'searching':
        searchButton.disabled = true;
        searchButton.innerHTML
          = '<i class="fas fa-spinner fa-spin"></i> Searching...';
        searchButton.classList.add('pulse');
        cancelButton.classList.remove('d-none');
        progressCard.classList.remove('d-none');
        resultsCard.classList.add('d-none');
        this.clearResults();
        break;

      case 'idle':
        searchButton.disabled = false;
        searchButton.innerHTML = '<i class="fas fa-search"></i> Start Search';
        searchButton.classList.remove('pulse');
        cancelButton.classList.add('d-none');
        progressCard.classList.add('d-none');
        this.isSearching = false;
        this.stats.activeSearches = Math.max(0, this.stats.activeSearches - 1);
        this.updateDashboard();
        break;

      case 'completed':
        searchButton.disabled = false;
        searchButton.innerHTML = '<i class="fas fa-search"></i> Start Search';
        searchButton.classList.remove('pulse');
        cancelButton.classList.add('d-none');
        progressCard.classList.add('d-none');
        resultsCard.classList.remove('d-none');
        this.isSearching = false;
        this.stats.activeSearches = Math.max(0, this.stats.activeSearches - 1);
        this.updateDashboard();
        break;
    }
  }

  updateProgress(progress, message, resultsCount = 0) {
    const progressBar = document.getElementById('progressBar');
    const progressMessage = document.getElementById('progressMessage');
    const resultsCountEl = document.getElementById('resultsCount');

    const percentage = Math.round(progress * 100);
    progressBar.style.width = `${percentage}%`;
    progressBar.setAttribute('aria-valuenow', percentage);

    progressMessage.textContent = message;
    resultsCountEl.textContent = resultsCount;
  }

  showAlert(message, type = 'info') {
    // Create alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

    // Insert at top of container
    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
      if (alertDiv.parentNode) {
        alertDiv.remove();
      }
    }, 5000);
  }

  updateConnectionStatus(status) {
    let statusEl = document.querySelector('.connection-status');

    if (!statusEl) {
      statusEl = document.createElement('div');
      statusEl.className = 'connection-status';
      document.body.appendChild(statusEl);
    }

    statusEl.className = `connection-status ${status}`;

    switch (status) {
      case 'connected':
        statusEl.innerHTML = '<i class="fas fa-wifi"></i> Connected';
        break;
      case 'disconnected':
        statusEl.innerHTML = '<i class="fas fa-wifi"></i> Disconnected';
        break;
      case 'connecting':
        statusEl.innerHTML
          = '<i class="fas fa-spinner fa-spin"></i> Connecting...';
        break;
    }

    // Hide after 3 seconds if connected
    if (status === 'connected') {
      setTimeout(() => {
        if (statusEl.classList.contains('connected')) {
          statusEl.style.display = 'none';
        }
      }, 3000);
    } else {
      statusEl.style.display = 'block';
    }
  }

  clearResults() {
    this.searchResults = [];
    const container = document.getElementById('resultsContainer');
    container.innerHTML = '';
  }

  displayResults(results) {
    this.searchResults = results;
    const container = document.getElementById('resultsContainer');

    if (results.length === 0) {
      container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-search"></i>
                    <h5>No results found</h5>
                    <p>Try adjusting your search criteria or using fuzzy search.</p>
                </div>
            `;
      return;
    }

    container.innerHTML = '';

    results.forEach((result, index) => {
      const resultEl = this.createResultElement(result, index);
      container.appendChild(resultEl);
    });
  }

  createResultElement(result, index) {
    const div = document.createElement('div');
    div.className = 'result-item fade-in-up';
    div.style.animationDelay = `${index * 0.1}s`;
    div.setAttribute('data-testid', 'result-card');

    const searchTypeBadge = `<span class="badge search-type-${
      result.search_type
    }">${result.search_type.replace('_', ' ')}</span>`;
    const scoreBadge = `<span class="result-score">${(
      result.relevance_score * 100
    ).toFixed(0)}%</span>`;

    let contentHtml = '';
    if (result.matching_line) {
      contentHtml = `
                <div class="result-content" data-testid="code-content">
                    ${this.escapeHtml(result.matching_line)}
                    ${
  result.line_number
    ? `<small class="text-muted ms-2" data-testid="line-number">Line ${result.line_number}</small>`
    : ''
}
                </div>
            `;
    }

    let metaHtml = '';
    if (result.author_name || result.commit_date || result.commit_message) {
      metaHtml = `
                <div class="result-meta" data-testid="commit-info">
                    ${
  result.author_name
    ? `<span class="badge bg-secondary">${this.escapeHtml(
      result.author_name
    )}</span>`
    : ''
}
                    ${
  result.commit_date
    ? `<span class="badge bg-info">${new Date(
      result.commit_date
    ).toLocaleDateString()}</span>`
    : ''
}
                    ${
  result.commit_message
    ? `<div class="mt-1"><small>${this.escapeHtml(
      result.commit_message.substring(0, 100)
    )}${
      result.commit_message.length > 100 ? '...' : ''
    }</small></div>`
    : ''
}
                </div>
            `;
    }

    div.innerHTML = `
            <div class="result-header">
                <div>
                    <span class="result-commit">${result.commit_hash.substring(
    0,
    8
  )}</span>
                    ${searchTypeBadge}
                </div>
                ${scoreBadge}
            </div>
            <div class="result-file" data-testid="file-path">
                <i class="fas fa-file"></i> ${this.escapeHtml(result.file_path)}
            </div>
            ${contentHtml}
            ${metaHtml}
        `;

    return div;
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  async exportResults(format) {
    if (!this.currentSearchId || this.searchResults.length === 0) {
      this.showAlert('No results to export', 'warning');
      return;
    }

    try {
      const exportRequest = {
        search_id: this.currentSearchId,
        format,
        include_metadata: true
      };

      const response = await fetch(
        `/api/search/${this.currentSearchId}/export`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(exportRequest)
        }
      );

      if (response.ok) {
        // Trigger download
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `githound_results.${format}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);

        this.showAlert(
          `Results exported as ${format.toUpperCase()}`,
          'success'
        );
      } else {
        throw new Error(`Export failed: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Export failed:', error);
      this.showAlert(`Export failed: ${error.message}`, 'danger');
    }
  }

  stopSearch() {
    this.isSearching = false;
    this.currentSearchId = null;

    if (this.websocket) {
      this.websocket.close();
      this.websocket = null;
    }

    this.updateUI('idle');
  }

  handleSearchCompletion(data) {
    this.showAlert(
      `Search completed! Found ${data.total_results} results.`,
      'success'
    );

    // Update stats
    this.stats.totalResults += data.total_results || 0;
    this.updateDashboard();

    this.loadSearchResults();
    this.stopSearch();
    this.updateUI('completed');
  }

  handleSearchError(errorMessage) {
    this.showAlert(`Search failed: ${errorMessage}`, 'danger');
    this.stopSearch();
  }

  async startStatusPolling() {
    if (!this.currentSearchId || !this.isSearching) {
      return;
    }

    try {
      const response = await fetch(
        `/api/search/${this.currentSearchId}/status`
      );

      if (response.ok) {
        const status = await response.json();

        // Update UI elements
        document.getElementById('searchStatus').textContent = status.status;
        document.getElementById('searchId').textContent
          = this.currentSearchId.substring(0, 8);

        if (status.status === 'completed') {
          await this.loadSearchResults();
          this.handleSearchCompletion({ total_results: status.results_count });
        } else if (status.status === 'error') {
          this.handleSearchError(status.message);
        } else if (status.status === 'cancelled') {
          this.showAlert('Search was cancelled', 'warning');
          this.stopSearch();
        } else {
          // Update progress if not getting WebSocket updates
          if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
            this.updateProgress(
              status.progress,
              status.message,
              status.results_count
            );
          }

          // Continue polling
          setTimeout(() => this.startStatusPolling(), 1000);
        }
      }
    } catch (error) {
      console.error('Status polling failed:', error);
      setTimeout(() => this.startStatusPolling(), 2000);
    }
  }

  async loadSearchResults() {
    if (!this.currentSearchId) {
      return;
    }

    try {
      const response = await fetch(
        `/api/search/${this.currentSearchId}/results?include_metadata=true`
      );

      if (response.ok) {
        const data = await response.json();
        this.displayResults(data.results);
        this.showResultsSummary(data);
      }
    } catch (error) {
      console.error('Failed to load results:', error);
      this.showAlert('Failed to load search results', 'danger');
    }
  }

  showResultsSummary(data) {
    const container = document.getElementById('resultsContainer');

    const summaryDiv = document.createElement('div');
    summaryDiv.className = 'results-summary mb-3';
    summaryDiv.innerHTML = `
            <h6><i class="fas fa-chart-bar"></i> Search Summary</h6>
            <div class="row">
                <div class="col-md-3">
                    <strong>Total Results:</strong> ${data.total_count}
                </div>
                <div class="col-md-3">
                    <strong>Commits Searched:</strong> ${data.commits_searched}
                </div>
                <div class="col-md-3">
                    <strong>Files Searched:</strong> ${data.files_searched}
                </div>
                <div class="col-md-3">
                    <strong>Duration:</strong> ${(
    data.search_duration_ms / 1000
  ).toFixed(2)}s
                </div>
            </div>
        `;

    container.insertBefore(summaryDiv, container.firstChild);
  }

  addResult(result) {
    // Add new result to the list (for real-time updates)
    this.searchResults.push(result);

    const container = document.getElementById('resultsContainer');
    const resultEl = this.createResultElement(
      result,
      this.searchResults.length - 1
    );
    resultEl.classList.add('new-result');

    container.appendChild(resultEl);

    // Update results count
    document.getElementById('resultsCount').textContent
      = this.searchResults.length;
  }

  // Authentication methods
  initializeAuth() {
    // Check for existing auth token
    this.authToken = localStorage.getItem('access_token');
    this.currentUser = JSON.parse(localStorage.getItem('current_user') || 'null');

    this.updateAuthUI();
  }

  updateAuthUI() {
    const loginButton = document.querySelector('[data-testid="login-button"]');
    const registerButton = document.querySelector('[data-testid="register-button"]');
    const userMenu = document.querySelector('[data-testid="user-menu"]');
    const usernameDisplay = document.querySelector('[data-testid="username-display"]');
    const adminPanelLink = document.querySelector('[data-testid="admin-panel-link"]');

    if (this.currentUser && this.authToken) {
      // User is logged in
      if (loginButton) { loginButton.style.display = 'none'; }
      if (registerButton) { registerButton.style.display = 'none'; }
      if (userMenu) { userMenu.style.display = 'block'; }
      if (usernameDisplay) { usernameDisplay.textContent = this.currentUser.username; }

      // Show admin panel link if user is admin
      if (adminPanelLink && this.currentUser.roles && this.currentUser.roles.includes('admin')) {
        adminPanelLink.style.display = 'block';
      }
    } else {
      // User is not logged in
      if (loginButton) { loginButton.style.display = 'inline-block'; }
      if (registerButton) { registerButton.style.display = 'inline-block'; }
      if (userMenu) { userMenu.style.display = 'none'; }
      if (adminPanelLink) { adminPanelLink.style.display = 'none'; }
    }
  }

  async handleLogin() {
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;
    const errorElement = document.querySelector('[data-testid="login-error"]');

    // Clear previous errors
    this.clearValidationErrors('login');

    if (!username || !password) {
      this.showValidationError('login', 'username', 'Username is required');
      this.showValidationError('login', 'password', 'Password is required');
      return;
    }

    try {
      const response = await fetch('/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, password })
      });

      const data = await response.json();

      if (response.ok) {
        // Store auth data
        this.authToken = data.access_token;
        this.currentUser = {
          user_id: data.user_id,
          username,
          roles: data.roles || ['user']
        };

        localStorage.setItem('access_token', this.authToken);
        localStorage.setItem('current_user', JSON.stringify(this.currentUser));

        // Update UI
        this.updateAuthUI();

        // Close modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('loginModal'));
        modal.hide();

        this.showAlert('Login successful!', 'success');
      } else {
        errorElement.textContent = data.detail || 'Invalid username or password';
        errorElement.classList.remove('d-none');
      }
    } catch (error) {
      console.error('Login failed:', error);
      errorElement.textContent = 'Login failed. Please try again.';
      errorElement.classList.remove('d-none');
    }
  }

  async handleRegistration() {
    const username = document.getElementById('registerUsername').value;
    const email = document.getElementById('registerEmail').value;
    const password = document.getElementById('registerPassword').value;
    const confirmPassword = document.getElementById('registerConfirmPassword').value;

    const successElement = document.querySelector('[data-testid="registration-success"]');
    const errorElement = document.querySelector('[data-testid="registration-error"]');

    // Clear previous messages
    this.clearValidationErrors('register');
    successElement.classList.add('d-none');
    errorElement.classList.add('d-none');

    // Validate form
    let hasErrors = false;

    if (!username) {
      this.showValidationError('register', 'username', 'Username is required');
      hasErrors = true;
    }

    if (!email) {
      this.showValidationError('register', 'email', 'Email is required');
      hasErrors = true;
    }

    if (!password) {
      this.showValidationError('register', 'password', 'Password is required');
      hasErrors = true;
    }

    if (password !== confirmPassword) {
      this.showValidationError('register', 'password-mismatch', 'Passwords do not match');
      hasErrors = true;
    }

    if (hasErrors) { return; }

    try {
      const response = await fetch('/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, email, password })
      });

      const data = await response.json();

      if (response.ok) {
        successElement.classList.remove('d-none');
        // Clear form
        document.getElementById('registerForm').reset();
      } else {
        errorElement.textContent = data.detail || 'Registration failed. Please try again.';
        errorElement.classList.remove('d-none');
      }
    } catch (error) {
      console.error('Registration failed:', error);
      errorElement.textContent = 'Registration failed. Please try again.';
      errorElement.classList.remove('d-none');
    }
  }

  logout() {
    // Clear auth data
    this.authToken = null;
    this.currentUser = null;
    localStorage.removeItem('access_token');
    localStorage.removeItem('current_user');

    // Update UI
    this.updateAuthUI();

    this.showAlert('Logged out successfully', 'info');
  }

  clearValidationErrors(formType) {
    const prefix = formType === 'login' ? 'login' : 'register';
    const errors = document.querySelectorAll(`#${prefix}Form .invalid-feedback`);
    errors.forEach(error => {
      error.textContent = '';
      error.previousElementSibling.classList.remove('is-invalid');
    });
  }

  showValidationError(formType, field, message) {
    const prefix = formType === 'login' ? 'login' : 'register';
    let fieldName = field;

    if (formType === 'register') {
      if (field === 'username') { fieldName = 'registerUsername'; } else if (field === 'email') { fieldName = 'registerEmail'; } else if (field === 'password') { fieldName = 'registerPassword'; } else if (field === 'password-mismatch') { fieldName = 'registerConfirmPassword'; }
    } else {
      if (field === 'username') { fieldName = 'loginUsername'; } else if (field === 'password') { fieldName = 'loginPassword'; }
    }

    const input = document.getElementById(fieldName);
    const errorElement = input.nextElementSibling;

    if (input && errorElement && errorElement.classList.contains('invalid-feedback')) {
      input.classList.add('is-invalid');
      errorElement.textContent = message;
    }
  }

  showProfile() {
    // Load user profile data
    const profileUsername = document.getElementById('profileUsername');
    const profileEmail = document.getElementById('profileEmail');
    const profileRole = document.getElementById('profileRole');

    if (this.currentUser) {
      profileUsername.value = this.currentUser.username;
      profileEmail.value = this.currentUser.email || '';
      profileRole.value = this.currentUser.roles ? this.currentUser.roles.join(', ') : 'user';
    }

    // Show the modal
    const modal = new bootstrap.Modal(document.getElementById('profileModal'));
    modal.show();

    // Show password change button when on password tab
    const passwordTab = document.getElementById('change-password-tab');
    const passwordButton = document.querySelector('[data-testid="submit-password-change"]');

    passwordTab.addEventListener('shown.bs.tab', () => {
      passwordButton.style.display = 'inline-block';
    });

    document.getElementById('profile-info-tab').addEventListener('shown.bs.tab', () => {
      passwordButton.style.display = 'none';
    });
  }

  async handlePasswordChange() {
    const currentPassword = document.getElementById('currentPassword').value;
    const newPassword = document.getElementById('newPassword').value;
    const confirmNewPassword = document.getElementById('confirmNewPassword').value;

    const successElement = document.querySelector('[data-testid="password-change-success"]');
    const errorElement = document.querySelector('[data-testid="password-change-error"]');

    // Clear previous messages
    this.clearPasswordChangeErrors();
    successElement.classList.add('d-none');
    errorElement.classList.add('d-none');

    // Validate form
    let hasErrors = false;

    if (!currentPassword) {
      this.showPasswordChangeError('current-password', 'Current password is required');
      hasErrors = true;
    }

    if (!newPassword) {
      this.showPasswordChangeError('new-password', 'New password is required');
      hasErrors = true;
    }

    if (newPassword !== confirmNewPassword) {
      this.showPasswordChangeError('confirm-new-password', 'Passwords do not match');
      hasErrors = true;
    }

    if (hasErrors) { return; }

    try {
      const response = await fetch('/auth/change-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${this.authToken}`
        },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword
        })
      });

      const data = await response.json();

      if (response.ok) {
        successElement.classList.remove('d-none');
        // Clear form
        document.getElementById('changePasswordForm').reset();
      } else {
        errorElement.textContent = data.detail || 'Failed to change password. Please try again.';
        errorElement.classList.remove('d-none');
      }
    } catch (error) {
      console.error('Password change failed:', error);
      errorElement.textContent = 'Failed to change password. Please try again.';
      errorElement.classList.remove('d-none');
    }
  }

  clearPasswordChangeErrors() {
    const errors = document.querySelectorAll('#changePasswordForm .invalid-feedback');
    errors.forEach(error => {
      error.textContent = '';
      error.previousElementSibling.classList.remove('is-invalid');
    });
  }

  showPasswordChangeError(field, message) {
    const input = document.getElementById(field === 'current-password' ? 'currentPassword'
      : field === 'new-password' ? 'newPassword' : 'confirmNewPassword');
    const errorElement = input.nextElementSibling;

    if (input && errorElement && errorElement.classList.contains('invalid-feedback')) {
      input.classList.add('is-invalid');
      errorElement.textContent = message;
    }
  }

  showAdminPanel() {
    // Check if user has admin role
    if (!this.currentUser || !this.currentUser.roles || !this.currentUser.roles.includes('admin')) {
      this.showAlert('Access denied. Admin privileges required.', 'danger');
      return;
    }

    // Show the admin modal
    const modal = new bootstrap.Modal(document.getElementById('adminModal'));
    modal.show();
  }
}

// Global functions for HTML onclick handlers
function loadSearchTemplate(templateId) {
  if (window.app) {
    window.app.loadSearchTemplate(templateId);
  }
}

function saveSearchTemplate() {
  if (window.app) {
    window.app.saveSearchTemplate();
  }
}

function clearForm() {
  if (window.app) {
    window.app.clearForm();
  }
}

function showSearchHistory() {
  if (window.app) {
    window.app.showSearchHistory();
  }
}

function loadTemplateById(templateId) {
  if (window.app) {
    window.app.loadTemplateById(templateId);
  }
}

function showHelp() {
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
}

// Authentication functions
function showLoginModal() {
  const modal = new bootstrap.Modal(document.getElementById('loginModal'));
  modal.show();
}

function showRegisterModal() {
  const modal = new bootstrap.Modal(document.getElementById('registerModal'));
  modal.show();
}

function logout() {
  if (window.app) {
    window.app.logout();
  }
}

function showProfile() {
  if (window.app) {
    window.app.showProfile();
  }
}

function showAdminPanel() {
  if (window.app) {
    window.app.showAdminPanel();
  }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  window.app = new GitHoundApp();
  window.websocketManager = new WebSocketManager();

  // Load highlight.js if available
  if (typeof hljs !== 'undefined') {
    hljs.configure({
      languages: ['javascript', 'python', 'java', 'cpp', 'html', 'css', 'json', 'xml', 'markdown', 'yaml', 'bash', 'sql']
    });
  }

  // Add some initial animations
  setTimeout(() => {
    document.querySelectorAll('.fade-in-up').forEach((el, index) => {
      el.style.animationDelay = `${index * 0.1}s`;
      el.classList.add('animate');
    });
  }, 100);
});
