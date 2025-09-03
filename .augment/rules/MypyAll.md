---
type: "manual"
---

Run mypy type checking across the entire GitHound project and fix all type-related issues that are discovered. Please follow these steps:

1. First, run mypy on the entire codebase to identify all type checking errors and warnings
2. Analyze the output to understand the specific type issues found
3. For each issue identified:
   - Add appropriate type annotations where missing
   - Fix incorrect type annotations
   - Resolve type compatibility issues
   - Add necessary imports for typing modules
   - Handle any mypy configuration issues if needed
4. After making fixes, re-run mypy to verify all issues have been resolved
5. Ensure the fixes don't break existing functionality by running any available tests
6. If mypy configuration files need to be created or modified, do so appropriately for the project structure

Focus on making the code fully type-compliant while maintaining existing functionality and following Python typing best practices.