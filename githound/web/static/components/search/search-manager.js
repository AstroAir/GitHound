/**
 * Search Manager Component
 *
 * Manages search operations, history, and templates.
 */

import { Component } from '../core/component.js';
import eventBus from '../core/event-bus.js';
import stateManager from '../core/state-manager.js';

export class SearchManager extends Component {
  constructor(name, options = {}) {
    super(name, options);

    this.currentSearchId = null;
    this.isSearching = false;
    this.searchResults = [];
    this.searchHistory = [];
    this.searchTemplates = {};
  }

  getDefaultOptions() {
    return {
      ...super.getDefaultOptions(),
      maxHistoryItems: 50,
      autoSaveHistory: true,
      autoSaveTemplates: true
    };
  }

  async onInit() {
    // Load saved data
    this.loadSearchHistory();
    this.loadSearchTemplates();

    // Set up event listeners
    this.setupEventListeners();

    // Initialize state
    this.updateSearchState();

    this.log('info', 'Search manager initialized');
  }

  setupEventListeners() {
    // Listen for WebSocket messages
    eventBus.on('websocket:message', message => {
      this.handleWebSocketMessage(message);
    });

    // Listen for form submissions
    eventBus.on('search:start', searchRequest => {
      this.startSearch(searchRequest);
    });

    eventBus.on('search:cancel', () => {
      this.cancelSearch();
    });

    // Listen for template operations
    eventBus.on('search:loadTemplate', templateId => {
      this.loadTemplate(templateId);
    });

    eventBus.on('search:saveTemplate', templateData => {
      this.saveTemplate(templateData);
    });
  }

  /**
   * Start a new search
   */
  async startSearch(searchRequest) {
    if (this.isSearching) {
      this.emit('error', 'A search is already in progress');
      return;
    }

    try {
      this.isSearching = true;
      this.searchResults = [];
      this.updateSearchState();

      // Validate search request
      if (!this.validateSearchRequest(searchRequest)) {
        throw new Error('Invalid search request');
      }

      // Add to search history
      this.addToSearchHistory(searchRequest);

      // Emit search started event
      this.emit('searchStarted', searchRequest);
      eventBus.emit('search:started', searchRequest);

      // Make API request
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

      // Update state with search ID
      this.updateSearchState();

      // Emit search ID received event
      this.emit('searchIdReceived', result.search_id);
      eventBus.emit('search:idReceived', result.search_id);

      // Connect to WebSocket for real-time updates
      eventBus.emit('websocket:connectForSearch', result.search_id);
    } catch (error) {
      this.log('error', 'Search failed:', error);
      this.isSearching = false;
      this.updateSearchState();

      this.emit('searchFailed', error);
      eventBus.emit('search:failed', error);
    }
  }

  /**
   * Cancel current search
   */
  async cancelSearch() {
    if (!this.currentSearchId) {
      return;
    }

    try {
      const response = await fetch(`/api/search/${this.currentSearchId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        this.emit('searchCancelled');
        eventBus.emit('search:cancelled');
      }
    } catch (error) {
      this.log('error', 'Cancel failed:', error);
    }

    this.stopSearch();
  }

  /**
   * Stop current search
   */
  stopSearch() {
    this.isSearching = false;
    this.currentSearchId = null;
    this.updateSearchState();

    this.emit('searchStopped');
    eventBus.emit('search:stopped');
  }

  /**
   * Handle WebSocket messages related to search
   */
  handleWebSocketMessage(message) {
    const { type, data } = message;

    switch (type) {
      case 'progress':
        this.handleSearchProgress(data);
        break;

      case 'result':
        this.handleSearchResult(data);
        break;

      case 'completed':
        this.handleSearchCompletion(data);
        break;

      case 'error':
        this.handleSearchError(data);
        break;
    }
  }

  /**
   * Handle search progress updates
   */
  handleSearchProgress(data) {
    this.emit('searchProgress', data);
    eventBus.emit('search:progress', data);
  }

  /**
   * Handle individual search results
   */
  handleSearchResult(data) {
    this.searchResults.push(data.result);
    this.updateSearchState();

    this.emit('searchResult', data.result);
    eventBus.emit('search:result', data.result);
  }

  /**
   * Handle search completion
   */
  handleSearchCompletion(data) {
    this.isSearching = false;
    this.updateSearchState();

    this.emit('searchCompleted', data);
    eventBus.emit('search:completed', data);
  }

  /**
   * Handle search errors
   */
  handleSearchError(data) {
    this.isSearching = false;
    this.updateSearchState();

    this.emit('searchError', data);
    eventBus.emit('search:error', data);
  }

  /**
   * Validate search request
   */
  validateSearchRequest(request) {
    if (!request.repo_path || !request.repo_path.trim()) {
      return false;
    }

    // Check if at least one search criterion is provided
    const criteria = [
      'content_pattern',
      'commit_hash',
      'author_pattern',
      'message_pattern',
      'file_path_pattern',
      'file_extensions',
      'date_from',
      'date_to'
    ];

    return criteria.some(field => {
      const value = request[field];
      return value && (typeof value === 'string' ? value.trim() : true);
    });
  }

  /**
   * Add search to history
   */
  addToSearchHistory(searchRequest) {
    const historyItem = {
      id: Date.now(),
      timestamp: new Date().toISOString(),
      request: searchRequest,
      name: this.generateSearchName(searchRequest)
    };

    this.searchHistory.unshift(historyItem);

    // Keep only last N searches
    if (this.searchHistory.length > this.options.maxHistoryItems) {
      this.searchHistory = this.searchHistory.slice(0, this.options.maxHistoryItems);
    }

    if (this.options.autoSaveHistory) {
      this.saveSearchHistory();
    }

    this.emit('historyUpdated', this.searchHistory);
    eventBus.emit('search:historyUpdated', this.searchHistory);
  }

  /**
   * Generate a descriptive name for a search
   */
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

  /**
   * Load search template
   */
  loadTemplate(templateId) {
    const template = this.searchTemplates[templateId];
    if (template) {
      this.emit('templateLoaded', template);
      eventBus.emit('search:templateLoaded', template);
      return template;
    }
    return null;
  }

  /**
   * Save search template
   */
  saveTemplate(templateData) {
    const { name, description, config } = templateData;
    const templateId = name.toLowerCase().replace(/\s+/g, '-');

    this.searchTemplates[templateId] = {
      name,
      description,
      config,
      created: new Date().toISOString()
    };

    if (this.options.autoSaveTemplates) {
      this.saveSearchTemplates();
    }

    this.emit('templateSaved', { templateId, template: this.searchTemplates[templateId] });
    eventBus.emit('search:templateSaved', { templateId, template: this.searchTemplates[templateId] });
  }

  /**
   * Load search history from localStorage
   */
  loadSearchHistory() {
    try {
      const history = localStorage.getItem('githound-search-history');
      this.searchHistory = history ? JSON.parse(history) : [];
    } catch (error) {
      this.log('warn', 'Failed to load search history:', error);
      this.searchHistory = [];
    }
  }

  /**
   * Save search history to localStorage
   */
  saveSearchHistory() {
    try {
      localStorage.setItem('githound-search-history', JSON.stringify(this.searchHistory));
    } catch (error) {
      this.log('warn', 'Failed to save search history:', error);
    }
  }

  /**
   * Load search templates from localStorage
   */
  loadSearchTemplates() {
    try {
      const templates = localStorage.getItem('githound-search-templates');
      this.searchTemplates = templates ? JSON.parse(templates) : this.getDefaultTemplates();
    } catch (error) {
      this.log('warn', 'Failed to load search templates:', error);
      this.searchTemplates = this.getDefaultTemplates();
    }
  }

  /**
   * Save search templates to localStorage
   */
  saveSearchTemplates() {
    try {
      localStorage.setItem('githound-search-templates', JSON.stringify(this.searchTemplates));
    } catch (error) {
      this.log('warn', 'Failed to save search templates:', error);
    }
  }

  /**
   * Get default search templates
   */
  getDefaultTemplates() {
    return {
      'recent-commits': {
        name: 'Recent Commits',
        description: 'Find commits from the last 7 days',
        config: {
          date_from: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
          date_to: new Date().toISOString().split('T')[0]
        }
      },
      'bug-fixes': {
        name: 'Bug Fixes',
        description: 'Find commits that fix bugs',
        config: {
          message_pattern: '(fix|bug|issue|resolve)',
          case_sensitive: false
        }
      },
      'code-changes': {
        name: 'Code Changes',
        description: 'Find code changes in specific file types',
        config: {
          file_extensions: 'js,ts,py,java,cpp,c',
          content_pattern: '(function|class|method)'
        }
      }
    };
  }

  /**
   * Update search state in global state manager
   */
  updateSearchState() {
    stateManager.setState({
      search: {
        isSearching: this.isSearching,
        currentSearchId: this.currentSearchId,
        resultsCount: this.searchResults.length,
        history: this.searchHistory,
        templates: this.searchTemplates
      }
    }, 'search-manager');
  }

  /**
   * Get current search status
   */
  getStatus() {
    return {
      isSearching: this.isSearching,
      currentSearchId: this.currentSearchId,
      resultsCount: this.searchResults.length,
      historyCount: this.searchHistory.length,
      templatesCount: Object.keys(this.searchTemplates).length
    };
  }

  onDestroy() {
    if (this.isSearching) {
      this.cancelSearch();
    }
  }
}

export default SearchManager;
