# WebSocket API

GitHound provides real-time WebSocket API for streaming search results, repository analysis updates, and live notifications. The WebSocket API enables efficient real-time communication for long-running operations and live data feeds.

## Connection

### WebSocket Endpoint

```text
ws://localhost:8000/ws/{connection_id}
```

### Authentication

WebSocket connections support the same authentication methods as the REST API:

```javascript
// Connect with JWT token
const ws = new WebSocket('ws://localhost:8000/ws/my-connection', [], {
    headers: {
        'Authorization': 'Bearer your-jwt-token'
    }
});

// Or pass token as query parameter
const ws = new WebSocket('ws://localhost:8000/ws/my-connection?token=your-jwt-token');
```

### Connection Management

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/search-session-123');

ws.onopen = function(event) {
    console.log('WebSocket connected');

    // Send initial subscription
    ws.send(JSON.stringify({
        type: 'subscribe',
        data: {
            events: ['search_progress', 'search_results', 'analysis_complete']
        }
    }));
};

ws.onclose = function(event) {
    console.log('WebSocket disconnected:', event.code, event.reason);
};

ws.onerror = function(error) {
    console.error('WebSocket error:', error);
};
```

## Message Format

All WebSocket messages follow a consistent JSON format:

```json
{
    "type": "message_type",
    "data": {
        "key": "value"
    },
    "timestamp": "2023-12-01T10:00:00Z",
    "request_id": "optional-request-id"
}
```

### Message Types

#### Client to Server Messages

- `subscribe` - Subscribe to event types
- `unsubscribe` - Unsubscribe from event types
- `search` - Start streaming search
- `analysis` - Start streaming analysis
- `ping` - Keep-alive ping

#### Server to Client Messages

- `connected` - Connection established
- `subscribed` - Subscription confirmed
- `search_started` - Search operation started
- `search_progress` - Search progress update
- `search_result` - Individual search result
- `search_complete` - Search operation completed
- `analysis_progress` - Analysis progress update
- `analysis_complete` - Analysis operation completed
- `error` - Error occurred
- `pong` - Response to ping

## Event Subscriptions

### Subscribe to Events

```javascript
ws.send(JSON.stringify({
    type: 'subscribe',
    data: {
        events: ['search_progress', 'search_results'],
        filters: {
            repo_path: '/path/to/repo',
            search_id: 'optional-search-id'
        }
    }
}));
```

### Unsubscribe from Events

```javascript
ws.send(JSON.stringify({
    type: 'unsubscribe',
    data: {
        events: ['search_progress']
    }
}));
```

## Streaming Search

### Start Streaming Search

```javascript
ws.send(JSON.stringify({
    type: 'search',
    data: {
        repo_path: '/path/to/repo',
        query: {
            content_pattern: 'function',
            author_pattern: 'john',
            fuzzy_search: true,
            fuzzy_threshold: 0.8
        },
        options: {
            max_results: 100,
            stream_results: true
        }
    },
    request_id: 'search-123'
}));
```

### Receive Search Updates

```javascript
ws.onmessage = function(event) {
    const message = JSON.parse(event.data);

    switch(message.type) {
        case 'search_started':
            console.log('Search started:', message.data.search_id);
            break;

        case 'search_progress':
            console.log('Progress:', message.data.progress + '%');
            console.log('Files searched:', message.data.files_searched);
            console.log('Commits searched:', message.data.commits_searched);
            break;

        case 'search_result':
            console.log('New result:', message.data.result);
            // Process individual result
            displaySearchResult(message.data.result);
            break;

        case 'search_complete':
            console.log('Search completed');
            console.log('Total results:', message.data.total_results);
            console.log('Duration:', message.data.duration_ms + 'ms');
            break;

        case 'error':
            console.error('Search error:', message.data.error);
            break;
    }
};
```

## Streaming Analysis

### Repository Analysis

```javascript
ws.send(JSON.stringify({
    type: 'analysis',
    data: {
        repo_path: '/path/to/repo',
        analysis_type: 'repository',
        options: {
            detailed: true,
            include_blame: true,
            include_history: true
        }
    },
    request_id: 'analysis-456'
}));
```

### File Blame Analysis

```javascript
ws.send(JSON.stringify({
    type: 'analysis',
    data: {
        repo_path: '/path/to/repo',
        analysis_type: 'blame',
        file_path: 'src/main.py',
        options: {
            line_range: [1, 100]
        }
    },
    request_id: 'blame-789'
}));
```

### Analysis Progress Updates

```javascript
ws.onmessage = function(event) {
    const message = JSON.parse(event.data);

    if (message.type === 'analysis_progress') {
        console.log('Analysis progress:', message.data.progress + '%');
        console.log('Current operation:', message.data.current_operation);
        console.log('Files processed:', message.data.files_processed);
    }

    if (message.type === 'analysis_complete') {
        console.log('Analysis completed:', message.data.results);
    }
};
```

## Real-time Notifications

### Repository Events

Subscribe to repository change notifications:

```javascript
ws.send(JSON.stringify({
    type: 'subscribe',
    data: {
        events: ['repository_updated', 'new_commits', 'branch_created'],
        filters: {
            repo_path: '/path/to/repo'
        }
    }
}));
```

### System Events

Subscribe to system-wide events:

```javascript
ws.send(JSON.stringify({
    type: 'subscribe',
    data: {
        events: ['server_status', 'maintenance_mode', 'rate_limit_warning']
    }
}));
```

## Error Handling

### Error Message Format

```json
{
    "type": "error",
    "data": {
        "code": "SEARCH_FAILED",
        "message": "Search operation failed",
        "details": {
            "repo_path": "/invalid/path",
            "reason": "Repository not found"
        }
    },
    "timestamp": "2023-12-01T10:00:00Z",
    "request_id": "search-123"
}
```

### Common Error Codes

- `CONNECTION_FAILED` - WebSocket connection failed
- `AUTHENTICATION_REQUIRED` - Authentication token required
- `SUBSCRIPTION_FAILED` - Event subscription failed
- `SEARCH_FAILED` - Search operation failed
- `ANALYSIS_FAILED` - Analysis operation failed
- `RATE_LIMIT_EXCEEDED` - Too many requests
- `INVALID_MESSAGE` - Invalid message format

### Reconnection Strategy

```javascript
class GitHoundWebSocket {
    constructor(url, options = {}) {
        this.url = url;
        this.options = options;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.connect();
    }

    connect() {
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
            console.log('Connected to GitHound WebSocket');
            this.reconnectAttempts = 0;
            this.resubscribe();
        };

        this.ws.onclose = (event) => {
            if (this.reconnectAttempts < this.maxReconnectAttempts) {
                setTimeout(() => {
                    this.reconnectAttempts++;
                    console.log(`Reconnecting... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
                    this.connect();
                }, this.reconnectDelay * this.reconnectAttempts);
            }
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        this.ws.onmessage = (event) => {
            this.handleMessage(JSON.parse(event.data));
        };
    }

    resubscribe() {
        // Re-establish subscriptions after reconnection
        if (this.subscriptions) {
            this.subscribe(this.subscriptions);
        }
    }

    subscribe(events) {
        this.subscriptions = events;
        this.send({
            type: 'subscribe',
            data: { events }
        });
    }

    send(message) {
        if (this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        }
    }

    handleMessage(message) {
        // Handle incoming messages
        console.log('Received:', message);
    }
}

// Usage
const ws = new GitHoundWebSocket('ws://localhost:8000/ws/my-session');
ws.subscribe(['search_progress', 'search_results']);
```
