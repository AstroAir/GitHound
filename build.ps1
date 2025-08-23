# GitHound Build Script for Windows PowerShell
# Comprehensive build automation for Windows environments

param(
    [Parameter(Position=0)]
    [string]$Command = "help",

    [switch]$VerboseOutput,
    [switch]$Force
)

# Configuration
$PackageName = "githound"
$SrcDir = "githound"
$TestDir = "tests"
$DocsDir = "docs"
$BuildDir = "build"
$DistDir = "dist"

# Colors for output
$Colors = @{
    Red = "Red"
    Green = "Green"
    Yellow = "Yellow"
    Blue = "Blue"
    Cyan = "Cyan"
    White = "White"
}

function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Colors[$Color]
}

function Show-Help {
    Write-ColorOutput "GitHound Build System for Windows" "Blue"
    Write-ColorOutput "Usage: .\build.ps1 <command> [options]" "White"
    Write-ColorOutput ""
    Write-ColorOutput "Available commands:" "Green"
    Write-ColorOutput "  help              Show this help message" "White"
    Write-ColorOutput "  install           Install package and dependencies" "White"
    Write-ColorOutput "  install-dev       Install development dependencies" "White"
    Write-ColorOutput "  install-test      Install test dependencies only" "White"
    Write-ColorOutput "  format            Format code with black and isort" "White"
    Write-ColorOutput "  lint              Run linting with ruff" "White"
    Write-ColorOutput "  lint-fix          Run linting with automatic fixes" "White"
    Write-ColorOutput "  type-check        Run type checking with mypy" "White"
    Write-ColorOutput "  quality           Run all code quality checks" "White"
    Write-ColorOutput "  test              Run unit tests" "White"
    Write-ColorOutput "  test-unit         Run unit tests only" "White"
    Write-ColorOutput "  test-integration  Run integration tests" "White"
    Write-ColorOutput "  test-performance  Run performance tests" "White"
    Write-ColorOutput "  test-all          Run all tests" "White"
    Write-ColorOutput "  test-fast         Run tests in parallel" "White"
    Write-ColorOutput "  test-cov          Run tests with coverage" "White"
    Write-ColorOutput "  benchmark         Run benchmark tests" "White"
    Write-ColorOutput "  clean             Clean build artifacts" "White"
    Write-ColorOutput "  build             Build package" "White"
    Write-ColorOutput "  build-wheel       Build wheel only" "White"
    Write-ColorOutput "  build-sdist       Build source distribution only" "White"
    Write-ColorOutput "  docs              Build documentation" "White"
    Write-ColorOutput "  docs-serve        Serve documentation locally" "White"
    Write-ColorOutput "  dev-setup         Complete development setup" "White"
    Write-ColorOutput "  check             Run quality checks and unit tests" "White"
    Write-ColorOutput "  ci                Full CI pipeline" "White"
    Write-ColorOutput "  deps-update       Update dependencies" "White"
    Write-ColorOutput "  security-check    Run security checks" "White"
    Write-ColorOutput "  version           Show version information" "White"
    Write-ColorOutput "  env-info          Show environment information" "White"
    Write-ColorOutput ""
    Write-ColorOutput "Options:" "Green"
    Write-ColorOutput "  -VerboseOutput    Enable verbose output" "White"
    Write-ColorOutput "  -Force            Force operations (skip confirmations)" "White"
}

function Test-VirtualEnv {
    return $env:VIRTUAL_ENV -ne $null
}

function Invoke-Command {
    param([string]$Cmd, [string]$Description)
    
    if ($Description) {
        Write-ColorOutput $Description "Blue"
    }
    
    if ($VerboseOutput) {
        Write-ColorOutput "Executing: $Cmd" "Cyan"
    }
    
    Invoke-Expression $Cmd
    if ($LASTEXITCODE -ne 0) {
        Write-ColorOutput "Command failed with exit code $LASTEXITCODE" "Red"
        exit $LASTEXITCODE
    }
}

function Install-Package {
    Invoke-Command "pip install -e ." "Installing GitHound and dependencies..."
}

function Install-DevDependencies {
    Invoke-Command "pip install -e `".[dev,test,docs,build]`"" "Installing development dependencies..."
}

function Install-TestDependencies {
    Invoke-Command "pip install -e `".[test]`"" "Installing test dependencies..."
}

function Format-Code {
    Write-ColorOutput "Formatting code..." "Blue"
    Invoke-Command "black $SrcDir $TestDir"
    Invoke-Command "isort $SrcDir $TestDir"
}

function Run-Linting {
    Invoke-Command "ruff check $SrcDir $TestDir" "Running linter..."
}

function Run-LintingWithFix {
    Invoke-Command "ruff check --fix $SrcDir $TestDir" "Running linter with fixes..."
}

function Run-TypeCheck {
    Invoke-Command "mypy $SrcDir" "Running type checker..."
}

function Run-QualityChecks {
    Format-Code
    Run-Linting
    Run-TypeCheck
}

function Run-Tests {
    Invoke-Command "pytest tests/ -k `"test_`" -v" "Running unit tests..."
}

function Run-UnitTests {
    Invoke-Command "pytest tests/ -k `"test_`" -m `"not integration and not performance`" -v" "Running unit tests..."
}

function Run-IntegrationTests {
    Invoke-Command "pytest $TestDir/integration/ -v" "Running integration tests..."
}

function Run-PerformanceTests {
    Invoke-Command "pytest $TestDir/performance/ -v" "Running performance tests..."
}

function Run-AllTests {
    Invoke-Command "pytest -v" "Running all tests..."
}

function Run-FastTests {
    Invoke-Command "pytest -n auto -v" "Running tests in parallel..."
}

function Run-TestsWithCoverage {
    Invoke-Command "pytest --cov=$SrcDir --cov-report=html --cov-report=term-missing" "Running tests with coverage..."
}

function Run-Benchmarks {
    Invoke-Command "pytest $TestDir/performance/ --benchmark-only" "Running benchmarks..."
}

function Clean-BuildArtifacts {
    Write-ColorOutput "Cleaning build artifacts..." "Blue"
    
    $DirsToRemove = @($BuildDir, $DistDir, "*.egg-info", ".pytest_cache", "htmlcov", ".mypy_cache", ".ruff_cache")
    foreach ($Dir in $DirsToRemove) {
        if (Test-Path $Dir) {
            Remove-Item -Recurse -Force $Dir
            if ($VerboseOutput) {
                Write-ColorOutput "Removed: $Dir" "Cyan"
            }
        }
    }
    
    # Remove __pycache__ directories
    Get-ChildItem -Recurse -Directory -Name "__pycache__" | ForEach-Object {
        Remove-Item -Recurse -Force $_
        if ($VerboseOutput) {
            Write-ColorOutput "Removed: $_" "Cyan"
        }
    }
    
    # Remove .pyc files
    Get-ChildItem -Recurse -File -Name "*.pyc" | ForEach-Object {
        Remove-Item -Force $_
    }
    
    # Remove .coverage file
    if (Test-Path ".coverage") {
        Remove-Item ".coverage"
    }
}

function Build-Package {
    Clean-BuildArtifacts
    Invoke-Command "python -m build" "Building package..."
}

function Build-Wheel {
    Clean-BuildArtifacts
    Invoke-Command "python -m build --wheel" "Building wheel..."
}

function Build-SourceDist {
    Clean-BuildArtifacts
    Invoke-Command "python -m build --sdist" "Building source distribution..."
}

function Build-Documentation {
    Invoke-Command "cd $DocsDir && mkdocs build" "Building documentation..."
}

function Serve-Documentation {
    Write-ColorOutput "Serving documentation at http://localhost:8000" "Blue"
    Invoke-Command "cd $DocsDir && mkdocs serve"
}

function Setup-Development {
    Install-DevDependencies
    Invoke-Command "pre-commit install" "Installing pre-commit hooks..."
}

function Run-Check {
    Run-QualityChecks
    Run-UnitTests
    Write-ColorOutput "All checks passed!" "Green"
}

function Run-CI {
    Run-QualityChecks
    Run-AllTests
    Build-Package
    Write-ColorOutput "CI pipeline completed successfully!" "Green"
}

function Update-Dependencies {
    Write-ColorOutput "Updating dependencies..." "Blue"
    Invoke-Command "pip install --upgrade pip"
    Invoke-Command "pip install --upgrade -e `".[dev,test,docs,build]`""
}

function Run-SecurityCheck {
    Write-ColorOutput "Running security checks..." "Blue"
    Invoke-Command "pip install safety bandit"
    Invoke-Command "safety check"
    Invoke-Command "bandit -r $SrcDir"
}

function Show-Version {
    Write-ColorOutput "Version Information:" "Blue"
    python --version
    pip --version
    pytest --version
}

function Show-EnvInfo {
    Write-ColorOutput "Environment Information:" "Blue"
    Write-ColorOutput "Virtual Environment Active: $(Test-VirtualEnv)" "White"
    Write-ColorOutput "Python: $(python --version)" "White"
    Write-ColorOutput "Pip: $(pip --version)" "White"
    Write-ColorOutput "Working Directory: $(Get-Location)" "White"
    if (Test-VirtualEnv) {
        Write-ColorOutput "Virtual Environment: $env:VIRTUAL_ENV" "White"
    }
}

# Main command dispatcher
switch ($Command.ToLower()) {
    "help" { Show-Help }
    "install" { Install-Package }
    "install-dev" { Install-DevDependencies }
    "install-test" { Install-TestDependencies }
    "format" { Format-Code }
    "lint" { Run-Linting }
    "lint-fix" { Run-LintingWithFix }
    "type-check" { Run-TypeCheck }
    "quality" { Run-QualityChecks }
    "test" { Run-Tests }
    "test-unit" { Run-UnitTests }
    "test-integration" { Run-IntegrationTests }
    "test-performance" { Run-PerformanceTests }
    "test-all" { Run-AllTests }
    "test-fast" { Run-FastTests }
    "test-cov" { Run-TestsWithCoverage }
    "benchmark" { Run-Benchmarks }
    "clean" { Clean-BuildArtifacts }
    "build" { Build-Package }
    "build-wheel" { Build-Wheel }
    "build-sdist" { Build-SourceDist }
    "docs" { Build-Documentation }
    "docs-serve" { Serve-Documentation }
    "dev-setup" { Setup-Development }
    "check" { Run-Check }
    "ci" { Run-CI }
    "deps-update" { Update-Dependencies }
    "security-check" { Run-SecurityCheck }
    "version" { Show-Version }
    "env-info" { Show-EnvInfo }
    default {
        Write-ColorOutput "Unknown command: $Command" "Red"
        Write-ColorOutput "Use '.\build.ps1 help' to see available commands" "Yellow"
        exit 1
    }
}
