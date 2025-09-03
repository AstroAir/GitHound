# GitHub Workflows Documentation

This directory contains the GitHub Actions workflows and configurations for the GitHound project. These workflows provide comprehensive CI/CD automation, code quality checks, security scanning, and deployment capabilities.

## 🚀 Workflows Overview

### Core CI/CD Pipeline (`ci.yml`)

The main CI/CD pipeline that runs on every push and pull request.

**Features:**

- 🎯 **Smart execution**: Path-based filtering to skip unnecessary jobs
- 🏗️ **Multi-platform testing**: Ubuntu, Windows, macOS with Python 3.11 & 3.12
- 📊 **Code quality**: Black, isort, ruff, mypy with caching
- 🧪 **Comprehensive testing**: Unit, integration, and performance tests
- 📈 **Coverage reporting**: Codecov integration with PR comments
- 🔒 **Security scanning**: Safety, bandit with SARIF reporting
- 📦 **Package building**: Automated builds with integrity checks
- 📚 **Documentation**: Auto-build and deploy to GitHub Pages
- 🚀 **PyPI deployment**: Secure publishing on releases

**Optimizations:**

- Advanced caching for pip, mypy, ruff, and other tools
- Conditional job execution based on file changes
- Performance regression detection
- Artifact retention policies
- Failure notifications and auto-issue creation

### Security Analysis (`codeql.yml`)

Advanced security scanning with multiple tools.

**Features:**

- 🔍 **CodeQL analysis**: Semantic code analysis for vulnerabilities
- 🛡️ **Semgrep scanning**: Additional security rule checks
- 📦 **Dependency scanning**: Safety and pip-audit for vulnerabilities
- 📊 **SARIF reporting**: Results integrated into GitHub Security tab
- ⏰ **Scheduled scans**: Weekly security audits

### PR Automation (`pr-automation.yml`)

Intelligent pull request automation and management.

**Features:**

- 🏷️ **Auto-labeling**: Based on file changes and content
- 📏 **Size detection**: Automatic PR size labeling (XS/S/M/L/XL)
- 🔍 **Breaking change detection**: Identifies breaking changes
- 🛡️ **Security change detection**: Flags security-related changes
- 👋 **First-time contributor welcome**: Automated welcome messages
- ⚠️ **Large PR warnings**: Special handling for large changes
- 🔄 **Conflict detection**: Automatic merge conflict detection

### Auto-fix (`auto-fix.yml`)

Automated code formatting and linting fixes.

**Features:**

- 🤖 **Automatic fixes**: Black, isort, and ruff auto-fixes
- 💬 **PR comments**: Notification of applied fixes
- 🏷️ **Auto-labeling**: Marks PRs with auto-fixes applied
- 🔧 **Manual trigger**: Can be triggered via workflow dispatch
- ✅ **Status checks**: Indicates when auto-fix is needed

### Staging Deployment (`staging-deploy.yml`)

Environment-specific deployment automation.

**Features:**

- 🌍 **Multi-environment**: Staging and preview deployments
- 🔄 **Conditional deployment**: Based on branch and labels
- 🧪 **Pre-deployment checks**: Tests before deployment
- 📊 **Deployment status**: GitHub deployment API integration
- 💬 **PR comments**: Deployment notifications with URLs
- 🧹 **Auto-cleanup**: Preview environment cleanup on PR close

## 🔧 Configuration Files

### Dependabot (`dependabot.yml`)

Automated dependency management configuration.

**Features:**

- 📦 **Python dependencies**: Weekly updates with grouping
- 🎬 **GitHub Actions**: Automated action updates
- 🐳 **Docker support**: Ready for container deployments
- 👥 **Auto-assignment**: Automatic reviewer assignment
- 🏷️ **Smart labeling**: Categorized dependency updates
- 🚫 **Ignore rules**: Skip major updates for critical packages

### Code Owners (`CODEOWNERS`)

Automatic reviewer assignment based on file changes.

**Coverage:**

- Core application components
- Critical functionality (search engine, MCP server)
- Configuration and build files
- CI/CD workflows
- Documentation and examples

### Auto-labeling (`labeler.yml`)

Comprehensive labeling rules for automatic PR categorization.

**Categories:**

- Component-based labels (core, search-engine, mcp-server, etc.)
- Type-based labels (tests, documentation, build, etc.)
- Priority levels (high, medium, low)
- Change types (enhancement, bug, refactor, etc.)

### Issue Templates

Structured templates for bug reports and feature requests.

**Templates:**

- 🐛 **Bug Report** (`bug_report.yml`): Comprehensive bug reporting
- ✨ **Feature Request** (`feature_request.yml`): Detailed feature proposals

### PR Template (`pull_request_template.md`)

Comprehensive pull request template with checklists and guidelines.

## 🎯 Workflow Triggers

| Workflow       | Push         | PR  | Schedule    | Manual | Labels              |
| -------------- | ------------ | --- | ----------- | ------ | ------------------- |
| CI/CD          | ✅           | ✅  | ❌          | ✅     | ❌                  |
| CodeQL         | ✅           | ✅  | ✅ (weekly) | ✅     | ❌                  |
| PR Automation  | ❌           | ✅  | ❌          | ❌     | ❌                  |
| Auto-fix       | ❌           | ✅  | ❌          | ✅     | ❌                  |
| Staging Deploy | ✅ (develop) | ❌  | ❌          | ✅     | ✅ (deploy-preview) |

## 🔒 Security Features

- **SARIF Integration**: Security findings in GitHub Security tab
- **Dependency Scanning**: Automated vulnerability detection
- **Secret Scanning**: Built-in GitHub secret detection
- **Code Analysis**: Multi-tool security analysis
- **Trusted Publishing**: Secure PyPI deployment without API tokens

## 📊 Performance Optimizations

- **Smart Caching**: Multi-level caching for dependencies and tools
- **Conditional Execution**: Skip unnecessary jobs based on changes
- **Parallel Execution**: Optimized job dependencies
- **Artifact Management**: Intelligent retention policies
- **Matrix Optimization**: Reduced test matrix for faster feedback

## 🚀 Getting Started

1. **Required Secrets**: Set up the following repository secrets:

   - `PYPI_API_TOKEN`: For PyPI publishing
   - `CODECOV_TOKEN`: For coverage reporting (optional)
   - `SLACK_WEBHOOK_URL`: For failure notifications (optional)
   - `SEMGREP_APP_TOKEN`: For Semgrep scanning (optional)

2. **Branch Protection**: Configure branch protection rules for `main` and `develop`

3. **Environments**: Set up GitHub environments for `production` and `staging`

4. **Labels**: The workflows will automatically create labels as needed

## 🔧 Customization

### Adding New Workflows

1. Create workflow file in `.github/workflows/`
2. Update this documentation
3. Add appropriate triggers and permissions
4. Test with workflow dispatch first

### Modifying Existing Workflows

1. Test changes in a feature branch
2. Use workflow dispatch for testing
3. Monitor workflow runs for issues
4. Update documentation as needed

### Environment-Specific Configuration

- Modify `staging-deploy.yml` for your deployment targets
- Update environment URLs and deployment scripts
- Configure environment-specific secrets

## 📈 Monitoring and Maintenance

- **Workflow Status**: Monitor via GitHub Actions tab
- **Security Alerts**: Check GitHub Security tab regularly
- **Dependency Updates**: Review Dependabot PRs promptly
- **Performance**: Monitor workflow execution times
- **Costs**: Review GitHub Actions usage monthly

## 📋 Workflow Status Badges

Add these badges to your README.md to show workflow status:

```markdown
[![CI/CD](https://github.com/AstroAir/GitHound/actions/workflows/ci.yml/badge.svg)](https://github.com/AstroAir/GitHound/actions/workflows/ci.yml)
[![CodeQL](https://github.com/AstroAir/GitHound/actions/workflows/codeql.yml/badge.svg)](https://github.com/AstroAir/GitHound/actions/workflows/codeql.yml)
[![codecov](https://codecov.io/gh/AstroAir/GitHound/branch/main/graph/badge.svg)](https://codecov.io/gh/AstroAir/GitHound)
```

## 🤝 Contributing

When contributing to workflows:

1. Test changes thoroughly
2. Update documentation
3. Consider backward compatibility
4. Follow security best practices
5. Add appropriate error handling

For questions or issues with workflows, please create an issue with the `ci-cd` label.
