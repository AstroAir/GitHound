# Frontend Utilities

This directory contains utility functions and helper modules for the GitHound web interface.

## Structure

```
utils/
├── api.js          # API communication utilities
├── dom.js          # DOM manipulation helpers
├── events.js       # Event system utilities
├── storage.js      # Local storage management
├── validation.js   # Form validation utilities
├── formatters.js   # Data formatting functions
└── constants.js    # Application constants
```

## Guidelines

1. Keep utilities pure functions when possible
2. Avoid side effects in utility functions
3. Use consistent naming conventions
4. Include JSDoc comments for all functions
5. Write unit tests for all utilities

## Usage

Import utilities as needed in components:

```javascript
import { formatDate, escapeHtml } from '../utils/formatters.js';
import { validateEmail } from '../utils/validation.js';
```
