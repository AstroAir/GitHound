---
type: "manual"
---

Update the .gitignore file at .gitignore to properly exclude files and directories that should not be tracked in version control. Please:

1. First examine the current project structure to understand what files and directories exist
2. Review the existing .gitignore file to see what is currently being ignored
3. Identify common files that should be excluded based on the project type (e.g., build artifacts, dependency directories, IDE files, temporary files, logs, etc.)
4. Update the .gitignore file to include appropriate ignore patterns for:
   - Language-specific build outputs and dependencies
   - IDE and editor configuration files
   - Operating system generated files
   - Temporary and cache files
   - Any project-specific files that shouldn't be version controlled
5. Ensure the patterns are specific enough to avoid accidentally ignoring important project files
6. Test that the updated .gitignore works correctly by checking git status

The goal is to have a comprehensive .gitignore that prevents unnecessary files from being committed while ensuring all important project files remain tracked.