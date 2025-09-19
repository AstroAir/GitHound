# Frontend Components

This directory contains modular JavaScript components for the GitHound web interface.

## Structure

```
components/
├── core/           # Core system components
│   ├── app.js      # Main application controller
│   ├── component.js # Base component class
│   └── registry.js # Component registration system
├── auth/           # Authentication components
│   ├── auth-manager.js
│   ├── login-form.js
│   └── user-profile.js
├── search/         # Search functionality
│   ├── search-form.js
│   ├── search-results.js
│   └── search-progress.js
├── ui/             # UI components
│   ├── theme-manager.js
│   ├── notification.js
│   └── modal.js
├── websocket/      # WebSocket components
│   └── websocket-manager.js
└── utils/          # Utility components
    ├── export.js
    └── helpers.js
```

## Component Guidelines

1. Each component should extend the base Component class
2. Components should be self-contained and reusable
3. Use event-driven communication between components
4. Follow the established naming conventions
5. Include proper error handling and logging

## Usage

Components are automatically registered and initialized by the registry system.
See the main app.js for initialization order and dependencies.
