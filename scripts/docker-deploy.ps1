# GitHound Docker Deployment Script for Windows PowerShell
# Supports development, staging, and production deployments

param(
    [Parameter(Position=0)]
    [ValidateSet("deploy", "stop", "restart", "logs", "status", "clean", "build", "update")]
    [string]$Action = "deploy",

    [Parameter()]
    [ValidateSet("development", "staging", "production")]
    [string]$Environment = "development",

    [Parameter()]
    [switch]$Force,

    [Parameter()]
    [switch]$Detach = $true,

    [Parameter()]
    [switch]$Verbose,

    [Parameter()]
    [switch]$Help
)

# Function to write colored output
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Function to show usage
function Show-Usage {
    @"
GitHound Docker Deployment Script for Windows

Usage: .\docker-deploy.ps1 [OPTIONS] [ACTION]

ACTIONS:
    deploy      Deploy the application
    stop        Stop all services
    restart     Restart all services
    logs        Show service logs
    status      Show service status
    clean       Clean up containers and volumes
    build       Build Docker images
    update      Update and redeploy

OPTIONS:
    -Environment ENV    Environment (development|staging|production) [default: development]
    -Force              Force rebuild images
    -Detach             Run in detached mode (default: true)
    -Verbose            Verbose output
    -Help               Show this help

EXAMPLES:
    .\docker-deploy.ps1 deploy                              # Deploy development environment
    .\docker-deploy.ps1 -Environment production deploy      # Deploy production environment
    .\docker-deploy.ps1 -Environment production -Force deploy  # Force rebuild and deploy production
    .\docker-deploy.ps1 logs                                # Show logs for all services
    .\docker-deploy.ps1 -Environment production stop        # Stop production services
    .\docker-deploy.ps1 clean                               # Clean up all containers and volumes

"@
}

# Function to check prerequisites
function Test-Prerequisites {
    Write-Info "Checking prerequisites..."

    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Error "Docker is not installed or not in PATH"
        exit 1
    }

    if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
        Write-Error "Docker Compose is not installed or not in PATH"
        exit 1
    }

    # Check Docker daemon
    try {
        docker info | Out-Null
    }
    catch {
        Write-Error "Docker daemon is not running"
        exit 1
    }

    Write-Success "Prerequisites check passed"
}

# Function to setup environment
function Initialize-Environment {
    Write-Info "Setting up environment: $Environment"

    $script:ComposeFiles = switch ($Environment) {
        "development" { "-f docker-compose.yml -f docker-compose.override.yml" }
        "staging" { "-f docker-compose.yml" }
        "production" { "-f docker-compose.yml -f docker-compose.prod.yml" }
        default {
            Write-Error "Invalid environment: $Environment"
            exit 1
        }
    }

    # Set build arguments
    $buildDate = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    $script:BuildArgs = "--build-arg BUILD_DATE=$buildDate"

    if (Get-Command git -ErrorAction SilentlyContinue) {
        try {
            $vcsRef = git rev-parse --short HEAD
            $script:BuildArgs += " --build-arg VCS_REF=$vcsRef"
        }
        catch {
            # Git not available or not in a git repository
        }
    }

    # Check if .env file exists
    if (-not (Test-Path .env)) {
        Write-Warning ".env file not found, copying from .env.example"
        if (Test-Path .env.example) {
            Copy-Item .env.example .env
            Write-Info "Please edit .env file with your configuration"
        }
        else {
            Write-Error ".env.example file not found"
            exit 1
        }
    }
}

# Function to deploy services
function Start-Deployment {
    Write-Info "Deploying GitHound services..."

    if ($Force) {
        Write-Info "Force building images..."
        Invoke-Expression "docker-compose $ComposeFiles build --no-cache $BuildArgs"
    }
    else {
        Invoke-Expression "docker-compose $ComposeFiles build $BuildArgs"
    }

    if ($Detach) {
        Invoke-Expression "docker-compose $ComposeFiles up -d"
    }
    else {
        Invoke-Expression "docker-compose $ComposeFiles up"
    }

    Write-Success "Deployment completed"
}

# Function to stop services
function Stop-Services {
    Write-Info "Stopping GitHound services..."
    Invoke-Expression "docker-compose $ComposeFiles down"
    Write-Success "Services stopped"
}

# Function to restart services
function Restart-Services {
    Write-Info "Restarting GitHound services..."
    Invoke-Expression "docker-compose $ComposeFiles restart"
    Write-Success "Services restarted"
}

# Function to show logs
function Show-Logs {
    Write-Info "Showing service logs..."
    Invoke-Expression "docker-compose $ComposeFiles logs -f"
}

# Function to show status
function Show-Status {
    Write-Info "Service status:"
    Invoke-Expression "docker-compose $ComposeFiles ps"

    Write-Info "Health checks:"
    try {
        Invoke-Expression "docker-compose $ComposeFiles exec -T githound-web curl -f http://localhost:8000/health"
    }
    catch {
        Write-Warning "Web service health check failed"
    }

    try {
        Invoke-Expression "docker-compose $ComposeFiles exec -T githound-mcp curl -f http://localhost:3000/health"
    }
    catch {
        Write-Warning "MCP service health check failed"
    }
}

# Function to clean up
function Remove-Deployment {
    $response = Read-Host "This will remove all containers, networks, and volumes. Are you sure? (y/N)"
    if ($response -match "^[Yy]$") {
        Write-Info "Cleaning up..."
        Invoke-Expression "docker-compose $ComposeFiles down -v --remove-orphans"
        docker system prune -f
        Write-Success "Cleanup completed"
    }
    else {
        Write-Info "Cleanup cancelled"
    }
}

# Function to build images
function Build-Images {
    Write-Info "Building Docker images..."
    Invoke-Expression "docker-compose $ComposeFiles build $BuildArgs"
    Write-Success "Images built successfully"
}

# Function to update deployment
function Update-Deployment {
    Write-Info "Updating deployment..."
    Invoke-Expression "docker-compose $ComposeFiles pull"
    Invoke-Expression "docker-compose $ComposeFiles up -d"
    Write-Success "Deployment updated"
}

# Main execution
function Main {
    if ($Help) {
        Show-Usage
        return
    }

    if ($Verbose) {
        $VerbosePreference = "Continue"
    }

    Write-Info "GitHound Docker Deployment Script"
    Write-Info "Environment: $Environment"
    Write-Info "Action: $Action"

    Test-Prerequisites
    Initialize-Environment

    switch ($Action) {
        "deploy" { Start-Deployment }
        "stop" { Stop-Services }
        "restart" { Restart-Services }
        "logs" { Show-Logs }
        "status" { Show-Status }
        "clean" { Remove-Deployment }
        "build" { Build-Images }
        "update" { Update-Deployment }
        default {
            Write-Error "Invalid action: $Action"
            Show-Usage
            exit 1
        }
    }
}

# Run main function
Main
