// GitHound Web Interface JavaScript

class GitHoundApp {
    constructor() {
        this.currentSearchId = null;
        this.websocket = null;
        this.searchResults = [];
        this.isSearching = false;
        
        this.initializeEventListeners();
        this.updateConnectionStatus('disconnected');
    }
    
    initializeEventListeners() {
        // Form submission
        document.getElementById('searchForm').addEventListener('submit', (e) => {
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
        
        // Fuzzy threshold slider
        const fuzzyThreshold = document.getElementById('fuzzyThreshold');
        const fuzzyThresholdValue = document.getElementById('fuzzyThresholdValue');
        fuzzyThreshold.addEventListener('input', (e) => {
            fuzzyThresholdValue.textContent = e.target.value;
        });
        
        // Enable/disable fuzzy threshold based on checkbox
        document.getElementById('fuzzySearch').addEventListener('change', (e) => {
            fuzzyThreshold.disabled = !e.target.checked;
        });
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
            
            // Start search
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
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
            this.updateUI('idle');
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
        
        this.websocket = new WebSocket(wsUrl);
        
        this.websocket.onopen = () => {
            console.log('WebSocket connected');
            this.updateConnectionStatus('connected');
        };
        
        this.websocket.onmessage = (event) => {
            const message = JSON.parse(event.data);
            this.handleWebSocketMessage(message);
        };
        
        this.websocket.onclose = () => {
            console.log('WebSocket disconnected');
            this.updateConnectionStatus('disconnected');
        };
        
        this.websocket.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.updateConnectionStatus('disconnected');
        };
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
            file_path_pattern: document.getElementById('filePathPattern').value || null,
            case_sensitive: document.getElementById('caseSensitive').checked,
            fuzzy_search: document.getElementById('fuzzySearch').checked,
            fuzzy_threshold: parseFloat(document.getElementById('fuzzyThreshold').value),
            max_results: parseInt(document.getElementById('maxResults').value) || null,
            max_file_size: parseInt(document.getElementById('maxFileSize').value) || null,
            timeout_seconds: parseInt(document.getElementById('timeoutSeconds').value) || 300
        };
        
        // Handle date fields
        const dateFrom = document.getElementById('dateFrom').value;
        const dateTo = document.getElementById('dateTo').value;
        if (dateFrom) request.date_from = dateFrom + 'T00:00:00';
        if (dateTo) request.date_to = dateTo + 'T23:59:59';
        
        // Handle comma-separated lists
        const fileExtensions = document.getElementById('fileExtensions').value;
        if (fileExtensions) {
            request.file_extensions = fileExtensions.split(',').map(ext => ext.trim()).filter(ext => ext);
        }
        
        const includeGlobs = document.getElementById('includeGlobs').value;
        if (includeGlobs) {
            request.include_globs = includeGlobs.split(',').map(glob => glob.trim()).filter(glob => glob);
        }
        
        const excludeGlobs = document.getElementById('excludeGlobs').value;
        if (excludeGlobs) {
            request.exclude_globs = excludeGlobs.split(',').map(glob => glob.trim()).filter(glob => glob);
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
            'contentPattern', 'commitHash', 'authorPattern', 'messagePattern',
            'filePathPattern', 'fileExtensions', 'dateFrom', 'dateTo'
        ];
        
        const hasAnyCriteria = criteria.some(id => {
            const value = document.getElementById(id).value;
            return value && value.trim();
        });
        
        if (!hasAnyCriteria) {
            this.showAlert('At least one search criterion must be provided', 'danger');
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
                searchButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Searching...';
                cancelButton.style.display = 'inline-block';
                progressCard.style.display = 'block';
                resultsCard.style.display = 'none';
                this.clearResults();
                break;
                
            case 'idle':
                searchButton.disabled = false;
                searchButton.innerHTML = '<i class="fas fa-search"></i> Start Search';
                cancelButton.style.display = 'none';
                progressCard.style.display = 'none';
                break;
                
            case 'completed':
                searchButton.disabled = false;
                searchButton.innerHTML = '<i class="fas fa-search"></i> Start Search';
                cancelButton.style.display = 'none';
                progressCard.style.display = 'none';
                resultsCard.style.display = 'block';
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
                statusEl.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Connecting...';
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
        div.className = 'result-item';

        const searchTypeBadge = `<span class="badge search-type-${result.search_type}">${result.search_type.replace('_', ' ')}</span>`;
        const scoreBadge = `<span class="result-score">${(result.relevance_score * 100).toFixed(0)}%</span>`;

        let contentHtml = '';
        if (result.matching_line) {
            contentHtml = `
                <div class="result-content">
                    ${this.escapeHtml(result.matching_line)}
                    ${result.line_number ? `<small class="text-muted ms-2">Line ${result.line_number}</small>` : ''}
                </div>
            `;
        }

        let metaHtml = '';
        if (result.author_name || result.commit_date || result.commit_message) {
            metaHtml = `
                <div class="result-meta">
                    ${result.author_name ? `<span class="badge bg-secondary">${this.escapeHtml(result.author_name)}</span>` : ''}
                    ${result.commit_date ? `<span class="badge bg-info">${new Date(result.commit_date).toLocaleDateString()}</span>` : ''}
                    ${result.commit_message ? `<div class="mt-1"><small>${this.escapeHtml(result.commit_message.substring(0, 100))}${result.commit_message.length > 100 ? '...' : ''}</small></div>` : ''}
                </div>
            `;
        }

        div.innerHTML = `
            <div class="result-header">
                <div>
                    <span class="result-commit">${result.commit_hash.substring(0, 8)}</span>
                    ${searchTypeBadge}
                </div>
                ${scoreBadge}
            </div>
            <div class="result-file">
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
                format: format,
                include_metadata: true
            };

            const response = await fetch(`/api/search/${this.currentSearchId}/export`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(exportRequest)
            });

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

                this.showAlert(`Results exported as ${format.toUpperCase()}`, 'success');
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
        this.showAlert(`Search completed! Found ${data.total_results} results.`, 'success');
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
            const response = await fetch(`/api/search/${this.currentSearchId}/status`);

            if (response.ok) {
                const status = await response.json();

                // Update UI elements
                document.getElementById('searchStatus').textContent = status.status;
                document.getElementById('searchId').textContent = this.currentSearchId.substring(0, 8);

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
                        this.updateProgress(status.progress, status.message, status.results_count);
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
            const response = await fetch(`/api/search/${this.currentSearchId}/results?include_metadata=true`);

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
                    <strong>Duration:</strong> ${(data.search_duration_ms / 1000).toFixed(2)}s
                </div>
            </div>
        `;

        container.insertBefore(summaryDiv, container.firstChild);
    }

    addResult(result) {
        // Add new result to the list (for real-time updates)
        this.searchResults.push(result);

        const container = document.getElementById('resultsContainer');
        const resultEl = this.createResultElement(result, this.searchResults.length - 1);
        resultEl.classList.add('new-result');

        container.appendChild(resultEl);

        // Update results count
        document.getElementById('resultsCount').textContent = this.searchResults.length;
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.gitHoundApp = new GitHoundApp();
});
