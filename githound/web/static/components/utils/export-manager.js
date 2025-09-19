/**
 * Export Manager Component
 *
 * Manages data export functionality for search results.
 */

import { Component } from '../core/component.js';
import eventBus from '../core/event-bus.js';
import stateManager from '../core/state-manager.js';

export class ExportManager extends Component {
  constructor(name, options = {}) {
    super(name, options);

    this.supportedFormats = ['json', 'csv', 'xlsx', 'txt'];
    this.exportHistory = [];
  }

  getDefaultOptions() {
    return {
      ...super.getDefaultOptions(),
      maxHistoryItems: 20,
      defaultFormat: 'json',
      includeMetadata: true,
      autoSaveHistory: true
    };
  }

  async onInit() {
    // Load export history
    this.loadExportHistory();

    // Set up event listeners
    this.setupEventListeners();

    // Update state
    this.updateExportState();

    this.log('info', 'Export manager initialized');
  }

  setupEventListeners() {
    // Listen for export requests
    eventBus.on('export:results', data => {
      this.exportResults(data);
    });

    eventBus.on('export:json', data => {
      this.exportResults({ ...data, format: 'json' });
    });

    eventBus.on('export:csv', data => {
      this.exportResults({ ...data, format: 'csv' });
    });

    eventBus.on('export:xlsx', data => {
      this.exportResults({ ...data, format: 'xlsx' });
    });

    // Set up DOM event listeners
    this.setupDOMEventListeners();
  }

  setupDOMEventListeners() {
    // Export buttons
    const exportJsonBtn = document.getElementById('exportJson');
    if (exportJsonBtn) {
      exportJsonBtn.addEventListener('click', () => {
        this.exportCurrentResults('json');
      });
    }

    const exportCsvBtn = document.getElementById('exportCsv');
    if (exportCsvBtn) {
      exportCsvBtn.addEventListener('click', () => {
        this.exportCurrentResults('csv');
      });
    }
  }

  /**
   * Export search results
   */
  async exportResults(options = {}) {
    const {
      searchId,
      format = this.options.defaultFormat,
      includeMetadata = this.options.includeMetadata,
      filename,
      data
    } = options;

    try {
      this.emit('exportStarted', { format, searchId });
      eventBus.emit('export:started', { format, searchId });

      let exportData;
      let downloadFilename;

      if (data) {
        // Export provided data
        exportData = await this.processDataForExport(data, format, includeMetadata);
        downloadFilename = filename || `githound_export_${Date.now()}.${format}`;
      } else if (searchId) {
        // Export via API
        const result = await this.exportViaAPI(searchId, format, includeMetadata);
        exportData = result.data;
        downloadFilename = result.filename;
      } else {
        throw new Error('No data or search ID provided for export');
      }

      // Download the file
      await this.downloadFile(exportData, downloadFilename, format);

      // Add to export history
      this.addToExportHistory({
        searchId,
        format,
        filename: downloadFilename,
        timestamp: new Date().toISOString(),
        size: this.getDataSize(exportData)
      });

      // Emit success events
      this.emit('exportCompleted', { format, filename: downloadFilename });
      eventBus.emit('export:completed', { format, filename: downloadFilename });
      eventBus.emit('notification:success', `Results exported as ${format.toUpperCase()}`);
    } catch (error) {
      this.log('error', 'Export failed:', error);
      this.emit('exportFailed', { format, error });
      eventBus.emit('export:failed', { format, error });
      eventBus.emit('notification:error', `Export failed: ${error.message}`);
    }
  }

  /**
   * Export current search results
   */
  async exportCurrentResults(format) {
    const state = stateManager.getState();
    const searchId = state.search?.currentSearchId;

    if (!searchId) {
      eventBus.emit('notification:warning', 'No active search to export');
      return;
    }

    await this.exportResults({ searchId, format });
  }

  /**
   * Export via API
   */
  async exportViaAPI(searchId, format, includeMetadata) {
    const exportRequest = {
      search_id: searchId,
      format,
      include_metadata: includeMetadata
    };

    const response = await fetch(`/api/search/${searchId}/export`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(exportRequest)
    });

    if (!response.ok) {
      throw new Error(`Export API failed: ${response.statusText}`);
    }

    const blob = await response.blob();
    const filename = this.getFilenameFromResponse(response) || `githound_results.${format}`;

    return {
      data: blob,
      filename
    };
  }

  /**
   * Process data for export
   */
  async processDataForExport(data, format, includeMetadata) {
    switch (format.toLowerCase()) {
      case 'json':
        return this.exportAsJSON(data, includeMetadata);
      case 'csv':
        return this.exportAsCSV(data, includeMetadata);
      case 'xlsx':
        return this.exportAsXLSX(data, includeMetadata);
      case 'txt':
        return this.exportAsText(data, includeMetadata);
      default:
        throw new Error(`Unsupported export format: ${format}`);
    }
  }

  /**
   * Export as JSON
   */
  exportAsJSON(data, includeMetadata) {
    const exportData = {
      results: data,
      exported_at: new Date().toISOString(),
      format: 'json'
    };

    if (includeMetadata) {
      exportData.metadata = {
        total_results: data.length,
        export_version: '1.0',
        source: 'GitHound'
      };
    }

    const jsonString = JSON.stringify(exportData, null, 2);
    return new Blob([jsonString], { type: 'application/json' });
  }

  /**
   * Export as CSV
   */
  exportAsCSV(data, includeMetadata) {
    if (!Array.isArray(data) || data.length === 0) {
      throw new Error('No data to export');
    }

    // Get all unique keys from the data
    const allKeys = new Set();
    data.forEach(item => {
      Object.keys(this.flattenObject(item)).forEach(key => allKeys.add(key));
    });

    const headers = Array.from(allKeys);
    const csvRows = [];

    // Add metadata as comments if requested
    if (includeMetadata) {
      csvRows.push(`# Exported from GitHound on ${new Date().toISOString()}`);
      csvRows.push(`# Total results: ${data.length}`);
      csvRows.push('');
    }

    // Add headers
    csvRows.push(headers.map(h => this.escapeCSVField(h)).join(','));

    // Add data rows
    data.forEach(item => {
      const flatItem = this.flattenObject(item);
      const row = headers.map(header => {
        const value = flatItem[header] || '';
        return this.escapeCSVField(String(value));
      });
      csvRows.push(row.join(','));
    });

    const csvString = csvRows.join('\n');
    return new Blob([csvString], { type: 'text/csv' });
  }

  /**
   * Export as XLSX (requires external library)
   */
  async exportAsXLSX(data, includeMetadata) {
    // This would require a library like SheetJS
    // For now, fall back to CSV
    this.log('warn', 'XLSX export not implemented, falling back to CSV');
    return this.exportAsCSV(data, includeMetadata);
  }

  /**
   * Export as plain text
   */
  exportAsText(data, includeMetadata) {
    const lines = [];

    if (includeMetadata) {
      lines.push(`GitHound Export - ${new Date().toISOString()}`);
      lines.push(`Total results: ${data.length}`);
      lines.push('=' * 50);
      lines.push('');
    }

    data.forEach((item, index) => {
      lines.push(`Result ${index + 1}:`);
      lines.push(JSON.stringify(item, null, 2));
      lines.push('-' * 30);
    });

    const textString = lines.join('\n');
    return new Blob([textString], { type: 'text/plain' });
  }

  /**
   * Download file
   */
  async downloadFile(data, filename, format) {
    const url = window.URL.createObjectURL(data);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.style.display = 'none';

    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);

    // Clean up the URL object
    setTimeout(() => {
      window.URL.revokeObjectURL(url);
    }, 100);
  }

  /**
   * Get filename from response headers
   */
  getFilenameFromResponse(response) {
    const contentDisposition = response.headers.get('Content-Disposition');
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
      if (filenameMatch) {
        return filenameMatch[1];
      }
    }
    return null;
  }

  /**
   * Flatten nested object for CSV export
   */
  flattenObject(obj, prefix = '') {
    const flattened = {};

    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        const newKey = prefix ? `${prefix}.${key}` : key;

        if (obj[key] !== null && typeof obj[key] === 'object' && !Array.isArray(obj[key])) {
          Object.assign(flattened, this.flattenObject(obj[key], newKey));
        } else {
          flattened[newKey] = obj[key];
        }
      }
    }

    return flattened;
  }

  /**
   * Escape CSV field
   */
  escapeCSVField(field) {
    if (field.includes(',') || field.includes('"') || field.includes('\n')) {
      return `"${field.replace(/"/g, '""')}"`;
    }
    return field;
  }

  /**
   * Get data size in bytes
   */
  getDataSize(data) {
    if (data instanceof Blob) {
      return data.size;
    }
    return new Blob([data]).size;
  }

  /**
   * Add to export history
   */
  addToExportHistory(exportInfo) {
    this.exportHistory.unshift(exportInfo);

    // Keep only last N exports
    if (this.exportHistory.length > this.options.maxHistoryItems) {
      this.exportHistory = this.exportHistory.slice(0, this.options.maxHistoryItems);
    }

    if (this.options.autoSaveHistory) {
      this.saveExportHistory();
    }

    this.updateExportState();
    this.emit('historyUpdated', this.exportHistory);
    eventBus.emit('export:historyUpdated', this.exportHistory);
  }

  /**
   * Load export history from storage
   */
  loadExportHistory() {
    try {
      const history = localStorage.getItem('githound-export-history');
      this.exportHistory = history ? JSON.parse(history) : [];
    } catch (error) {
      this.log('warn', 'Failed to load export history:', error);
      this.exportHistory = [];
    }
  }

  /**
   * Save export history to storage
   */
  saveExportHistory() {
    try {
      localStorage.setItem('githound-export-history', JSON.stringify(this.exportHistory));
    } catch (error) {
      this.log('warn', 'Failed to save export history:', error);
    }
  }

  /**
   * Get supported formats
   */
  getSupportedFormats() {
    return [...this.supportedFormats];
  }

  /**
   * Get export history
   */
  getExportHistory() {
    return [...this.exportHistory];
  }

  /**
   * Clear export history
   */
  clearExportHistory() {
    this.exportHistory = [];
    localStorage.removeItem('githound-export-history');
    this.updateExportState();

    this.emit('historyCleared');
    eventBus.emit('export:historyCleared');
  }

  /**
   * Update export state in global state manager
   */
  updateExportState() {
    stateManager.setState({
      export: {
        supportedFormats: this.supportedFormats,
        history: this.exportHistory,
        historyCount: this.exportHistory.length
      }
    }, 'export-manager');
  }

  /**
   * Get export status
   */
  getStatus() {
    return {
      supportedFormats: this.supportedFormats,
      historyCount: this.exportHistory.length,
      lastExport: this.exportHistory[0] || null
    };
  }
}

export default ExportManager;
