/**
 * Development Debug Panel for GitHound
 * Provides component inspection, state monitoring, and debugging tools
 */

import { Component } from '../core/component.js';

export class DebugPanel extends Component {
  constructor() {
    super('debug-panel');
    this.isVisible = false;
    this.selectedComponent = null;
    this.stateHistory = [];
    this.eventHistory = [];
    this.performanceMetrics = new Map();
    this.maxHistorySize = 100;

    // Only enable in development
    this.enabled = this.isDevelopment();
  }

  async init() {
    if (!this.enabled) {
      return;
    }

    await super.init();

    this.setupKeyboardShortcuts();
    this.setupEventListeners();
    this.startPerformanceMonitoring();

    // Auto-show on errors in development
    window.addEventListener('error', () => {
      this.show();
    });
  }

  render() {
    if (!this.enabled) {
      return document.createElement('div');
    }

    const panel = document.createElement('div');
    panel.className = 'debug-panel';
    panel.innerHTML = `
      <div class="debug-panel-header">
        <h3>GitHound Debug Panel</h3>
        <div class="debug-panel-controls">
          <button class="debug-btn" data-action="clear">Clear</button>
          <button class="debug-btn" data-action="export">Export</button>
          <button class="debug-btn debug-close" data-action="close">×</button>
        </div>
      </div>
      
      <div class="debug-panel-tabs">
        <button class="debug-tab active" data-tab="components">Components</button>
        <button class="debug-tab" data-tab="state">State</button>
        <button class="debug-tab" data-tab="events">Events</button>
        <button class="debug-tab" data-tab="performance">Performance</button>
        <button class="debug-tab" data-tab="console">Console</button>
      </div>
      
      <div class="debug-panel-content">
        <div class="debug-tab-content active" data-content="components">
          <div class="component-tree"></div>
          <div class="component-details"></div>
        </div>
        
        <div class="debug-tab-content" data-content="state">
          <div class="state-viewer">
            <div class="current-state"></div>
            <div class="state-history"></div>
          </div>
        </div>
        
        <div class="debug-tab-content" data-content="events">
          <div class="event-filter">
            <input type="text" placeholder="Filter events..." class="event-filter-input">
            <button class="debug-btn" data-action="clear-events">Clear Events</button>
          </div>
          <div class="event-list"></div>
        </div>
        
        <div class="debug-tab-content" data-content="performance">
          <div class="performance-metrics"></div>
          <div class="performance-charts"></div>
        </div>
        
        <div class="debug-tab-content" data-content="console">
          <div class="console-output"></div>
          <div class="console-input">
            <input type="text" placeholder="Execute JavaScript..." class="console-command">
            <button class="debug-btn" data-action="execute">Execute</button>
          </div>
        </div>
      </div>
    `;

    this.setupPanelEvents(panel);
    this.updateComponentTree();
    this.updateStateViewer();
    this.updateEventList();
    this.updatePerformanceMetrics();

    return panel;
  }

  setupKeyboardShortcuts() {
    document.addEventListener('keydown', event => {
      // Ctrl+Shift+D to toggle debug panel
      if (event.ctrlKey && event.shiftKey && event.key === 'D') {
        event.preventDefault();
        this.toggle();
      }

      // Escape to close
      if (event.key === 'Escape' && this.isVisible) {
        this.hide();
      }
    });
  }

  setupEventListeners() {
    // Monitor component registry events
    if (typeof EventBus !== 'undefined') {
      EventBus.on('component:*', (eventName, data) => {
        this.addEventToHistory(eventName, data);
      });

      EventBus.on('state:*', (eventName, data) => {
        this.addStateToHistory(eventName, data);
      });
    }

    // Monitor global state changes
    if (typeof StateManager !== 'undefined') {
      StateManager.subscribe('*', (state, oldState) => {
        this.addStateToHistory('state:changed', { state, oldState });
      });
    }
  }

  setupPanelEvents(panel) {
    // Tab switching
    panel.addEventListener('click', event => {
      if (event.target.classList.contains('debug-tab')) {
        this.switchTab(event.target.dataset.tab);
      }

      if (event.target.dataset.action) {
        this.handleAction(event.target.dataset.action, event);
      }
    });

    // Component selection
    panel.addEventListener('click', event => {
      if (event.target.classList.contains('component-item')) {
        this.selectComponent(event.target.dataset.component);
      }
    });

    // Console input
    const consoleInput = panel.querySelector('.console-command');
    if (consoleInput) {
      consoleInput.addEventListener('keydown', event => {
        if (event.key === 'Enter') {
          this.executeConsoleCommand(consoleInput.value);
          consoleInput.value = '';
        }
      });
    }

    // Event filtering
    const eventFilter = panel.querySelector('.event-filter-input');
    if (eventFilter) {
      eventFilter.addEventListener('input', event => {
        this.filterEvents(event.target.value);
      });
    }
  }

  switchTab(tabName) {
    // Update tab buttons
    this.element.querySelectorAll('.debug-tab').forEach(tab => {
      tab.classList.toggle('active', tab.dataset.tab === tabName);
    });

    // Update tab content
    this.element.querySelectorAll('.debug-tab-content').forEach(content => {
      content.classList.toggle('active', content.dataset.content === tabName);
    });

    // Refresh content for active tab
    switch (tabName) {
      case 'components':
        this.updateComponentTree();
        break;
      case 'state':
        this.updateStateViewer();
        break;
      case 'events':
        this.updateEventList();
        break;
      case 'performance':
        this.updatePerformanceMetrics();
        break;
    }
  }

  handleAction(action, event) {
    switch (action) {
      case 'close':
        this.hide();
        break;
      case 'clear':
        this.clearAll();
        break;
      case 'export':
        this.exportDebugData();
        break;
      case 'clear-events':
        this.clearEvents();
        break;
      case 'execute':
        const input = this.element.querySelector('.console-command');
        this.executeConsoleCommand(input.value);
        input.value = '';
        break;
    }
  }

  updateComponentTree() {
    const treeContainer = this.element?.querySelector('.component-tree');
    if (!treeContainer) { return; }

    const components = this.getRegisteredComponents();

    treeContainer.innerHTML = `
      <h4>Registered Components (${components.length})</h4>
      <div class="component-list">
        ${components.map(comp => `
          <div class="component-item ${comp.initialized ? 'initialized' : 'not-initialized'}" 
               data-component="${comp.name}">
            <span class="component-name">${comp.name}</span>
            <span class="component-status">${comp.initialized ? '✓' : '○'}</span>
          </div>
        `).join('')}
      </div>
    `;
  }

  updateStateViewer() {
    const stateContainer = this.element?.querySelector('.current-state');
    if (!stateContainer) { return; }

    const currentState = this.getCurrentState();

    stateContainer.innerHTML = `
      <h4>Current State</h4>
      <pre class="state-json">${JSON.stringify(currentState, null, 2)}</pre>
    `;

    // Update state history
    const historyContainer = this.element?.querySelector('.state-history');
    if (historyContainer) {
      historyContainer.innerHTML = `
        <h4>State History (${this.stateHistory.length})</h4>
        <div class="history-list">
          ${this.stateHistory.slice(-10).map((entry, index) => `
            <div class="history-item">
              <span class="history-time">${new Date(entry.timestamp).toLocaleTimeString()}</span>
              <span class="history-event">${entry.event}</span>
            </div>
          `).join('')}
        </div>
      `;
    }
  }

  updateEventList() {
    const eventContainer = this.element?.querySelector('.event-list');
    if (!eventContainer) { return; }

    eventContainer.innerHTML = `
      <h4>Event History (${this.eventHistory.length})</h4>
      <div class="event-items">
        ${this.eventHistory.slice(-20).map(event => `
          <div class="event-item">
            <span class="event-time">${new Date(event.timestamp).toLocaleTimeString()}</span>
            <span class="event-name">${event.name}</span>
            <span class="event-data">${JSON.stringify(event.data).substring(0, 50)}...</span>
          </div>
        `).join('')}
      </div>
    `;
  }

  updatePerformanceMetrics() {
    const perfContainer = this.element?.querySelector('.performance-metrics');
    if (!perfContainer) { return; }

    const metrics = this.getPerformanceMetrics();

    perfContainer.innerHTML = `
      <h4>Performance Metrics</h4>
      <div class="metrics-grid">
        ${Object.entries(metrics).map(([key, value]) => `
          <div class="metric-item">
            <span class="metric-label">${key}</span>
            <span class="metric-value">${value}</span>
          </div>
        `).join('')}
      </div>
    `;
  }

  selectComponent(componentName) {
    this.selectedComponent = componentName;

    const detailsContainer = this.element?.querySelector('.component-details');
    if (!detailsContainer) { return; }

    const component = this.getComponentDetails(componentName);

    detailsContainer.innerHTML = `
      <h4>Component Details: ${componentName}</h4>
      <div class="component-info">
        <div class="info-section">
          <h5>Properties</h5>
          <pre>${JSON.stringify(component.properties, null, 2)}</pre>
        </div>
        <div class="info-section">
          <h5>State</h5>
          <pre>${JSON.stringify(component.state, null, 2)}</pre>
        </div>
        <div class="info-section">
          <h5>Methods</h5>
          <ul>
            ${component.methods.map(method => `<li>${method}</li>`).join('')}
          </ul>
        </div>
      </div>
    `;
  }

  executeConsoleCommand(command) {
    const output = this.element?.querySelector('.console-output');
    if (!output) { return; }

    try {
      const result = eval(command);
      this.addConsoleOutput(command, result, 'success');
    } catch (error) {
      this.addConsoleOutput(command, error.message, 'error');
    }
  }

  addConsoleOutput(command, result, type) {
    const output = this.element?.querySelector('.console-output');
    if (!output) { return; }

    const entry = document.createElement('div');
    entry.className = `console-entry console-${type}`;
    entry.innerHTML = `
      <div class="console-command">> ${command}</div>
      <div class="console-result">${JSON.stringify(result, null, 2)}</div>
    `;

    output.appendChild(entry);
    output.scrollTop = output.scrollHeight;
  }

  // Utility methods
  isDevelopment() {
    return location.hostname === 'localhost'
           || location.hostname === '127.0.0.1'
           || location.search.includes('debug=true');
  }

  getRegisteredComponents() {
    if (typeof ComponentRegistry === 'undefined') { return []; }

    return ComponentRegistry.listComponents().map(name => ({
      name,
      initialized: ComponentRegistry.get(name) !== undefined
    }));
  }

  getCurrentState() {
    if (typeof StateManager === 'undefined') { return {}; }
    return StateManager.getState();
  }

  getComponentDetails(componentName) {
    if (typeof ComponentRegistry === 'undefined') { return {}; }

    const component = ComponentRegistry.get(componentName);
    if (!component) { return {}; }

    return {
      properties: {
        name: component.name,
        initialized: component.initialized,
        destroyed: component.destroyed
      },
      state: component.state || {},
      methods: Object.getOwnPropertyNames(Object.getPrototypeOf(component))
        .filter(name => typeof component[name] === 'function')
    };
  }

  getPerformanceMetrics() {
    const metrics = {};

    if (performance.memory) {
      metrics['Memory Used'] = `${Math.round(performance.memory.usedJSHeapSize / 1024 / 1024)}MB`;
      metrics['Memory Total'] = `${Math.round(performance.memory.totalJSHeapSize / 1024 / 1024)}MB`;
    }

    metrics['Components Loaded'] = this.getRegisteredComponents().length;
    metrics['Events Fired'] = this.eventHistory.length;
    metrics['State Changes'] = this.stateHistory.length;

    return metrics;
  }

  addEventToHistory(eventName, data) {
    this.eventHistory.push({
      name: eventName,
      data,
      timestamp: Date.now()
    });

    if (this.eventHistory.length > this.maxHistorySize) {
      this.eventHistory.shift();
    }
  }

  addStateToHistory(event, data) {
    this.stateHistory.push({
      event,
      data,
      timestamp: Date.now()
    });

    if (this.stateHistory.length > this.maxHistorySize) {
      this.stateHistory.shift();
    }
  }

  startPerformanceMonitoring() {
    setInterval(() => {
      if (performance.memory) {
        this.performanceMetrics.set('memory', performance.memory.usedJSHeapSize);
      }
    }, 1000);
  }

  show() {
    if (!this.enabled) { return; }

    if (!this.element) {
      this.element = this.render();
      document.body.appendChild(this.element);
    }

    this.element.style.display = 'block';
    this.isVisible = true;
  }

  hide() {
    if (this.element) {
      this.element.style.display = 'none';
    }
    this.isVisible = false;
  }

  toggle() {
    if (this.isVisible) {
      this.hide();
    } else {
      this.show();
    }
  }

  clearAll() {
    this.eventHistory = [];
    this.stateHistory = [];
    this.updateEventList();
    this.updateStateViewer();
  }

  clearEvents() {
    this.eventHistory = [];
    this.updateEventList();
  }

  filterEvents(filter) {
    // Implementation for event filtering
    const eventItems = this.element?.querySelectorAll('.event-item');
    if (!eventItems) { return; }

    eventItems.forEach(item => {
      const eventName = item.querySelector('.event-name').textContent;
      const visible = eventName.toLowerCase().includes(filter.toLowerCase());
      item.style.display = visible ? 'block' : 'none';
    });
  }

  exportDebugData() {
    const data = {
      timestamp: new Date().toISOString(),
      components: this.getRegisteredComponents(),
      state: this.getCurrentState(),
      eventHistory: this.eventHistory,
      stateHistory: this.stateHistory,
      performance: this.getPerformanceMetrics()
    };

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = `githound-debug-${Date.now()}.json`;
    a.click();

    URL.revokeObjectURL(url);
  }
}

// Auto-initialize in development
if (typeof window !== 'undefined') {
  window.addEventListener('DOMContentLoaded', () => {
    const debugPanel = new DebugPanel();
    debugPanel.init();

    // Make available globally for console access
    window.GitHoundDebug = debugPanel;
  });
}
