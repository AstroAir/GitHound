# Frontend Styles

This directory contains modular CSS styles for the GitHound web interface.

## Structure

```
styles/
├── base/           # Base styles
│   ├── reset.css   # CSS reset/normalize
│   ├── variables.css # CSS custom properties
│   └── typography.css # Typography styles
├── components/     # Component-specific styles
│   ├── auth.css    # Authentication components
│   ├── search.css  # Search components
│   ├── ui.css      # UI components
│   └── websocket.css # WebSocket status
├── layout/         # Layout styles
│   ├── grid.css    # Grid system
│   ├── header.css  # Header/navigation
│   └── footer.css  # Footer
├── themes/         # Theme variations
│   ├── light.css   # Light theme
│   └── dark.css    # Dark theme
└── utilities/      # Utility classes
    ├── spacing.css # Margin/padding utilities
    ├── colors.css  # Color utilities
    └── animations.css # Animation utilities
```

## Guidelines

1. Use CSS custom properties for theming
2. Follow BEM naming convention
3. Keep component styles scoped
4. Use mobile-first responsive design
5. Minimize specificity conflicts

## Usage

Styles are automatically loaded in the correct order by the build system.
Component-specific styles are loaded with their respective components.
