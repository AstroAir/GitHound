---
type: "always_apply"
---

Complete a full project build process for the GitHound repository, including:

1. **Build the project**: Execute the complete build process using the project's standard build tools and commands (as defined in the Makefile or build configuration)

2. **Build Docker image**: Create a Docker image for the project using the existing Dockerfile, ensuring all dependencies are properly included and the image builds successfully

3. **Package the project**: Generate distribution packages (wheel and sdist) for the GitHound Python package

4. **Fix all encountered issues**: Resolve any errors, warnings, or build failures that occur during the build, Docker image creation, or packaging processes. This includes:
   - Dependency issues
   - Type checking errors
   - Linting errors
   - Build configuration problems
   - Docker build failures
   - Package creation errors

5. **Preserve existing functionality**: Ensure that all fixes and changes maintain backward compatibility and do not break any existing features, tests, or APIs. All existing tests must continue to pass.

**Important constraints**:

- Do NOT modify core functionality or behavior
- Do NOT remove or disable existing tests to make builds pass
- Do NOT introduce breaking changes to public APIs
- Verify that the build artifacts (Docker image and packages) are functional and complete

**Success criteria**:

- Clean build with no errors
- Docker image builds successfully and can be run
- Distribution packages are created without errors
- All existing tests pass
- No regressions in functionality
