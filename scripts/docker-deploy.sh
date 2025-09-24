#!/bin/bash
# GitHound Docker Deployment Script
# Supports development, staging, and production deployments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="development"
ACTION="deploy"
COMPOSE_FILES="-f docker-compose.yml"
BUILD_ARGS=""

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    cat << EOF
GitHound Docker Deployment Script

Usage: $0 [OPTIONS] ACTION

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
    -e, --env ENV       Environment (development|staging|production) [default: development]
    -f, --force         Force rebuild images
    -d, --detach        Run in detached mode
    -v, --verbose       Verbose output
    -h, --help          Show this help

EXAMPLES:
    $0 deploy                           # Deploy development environment
    $0 -e production deploy             # Deploy production environment
    $0 -e production -f deploy          # Force rebuild and deploy production
    $0 logs                             # Show logs for all services
    $0 -e production stop               # Stop production services
    $0 clean                            # Clean up all containers and volumes

EOF
}

# Function to check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."

    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed or not in PATH"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed or not in PATH"
        exit 1
    fi

    # Check Docker daemon
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running"
        exit 1
    fi

    print_success "Prerequisites check passed"
}

# Function to setup environment
setup_environment() {
    print_info "Setting up environment: $ENVIRONMENT"

    case $ENVIRONMENT in
        development)
            COMPOSE_FILES="-f docker-compose.yml -f docker-compose.override.yml"
            ;;
        staging)
            COMPOSE_FILES="-f docker-compose.yml"
            ;;
        production)
            COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod.yml"
            ;;
        *)
            print_error "Invalid environment: $ENVIRONMENT"
            exit 1
            ;;
    esac

    # Set build arguments
    BUILD_ARGS="--build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
    if command -v git &> /dev/null && git rev-parse --git-dir > /dev/null 2>&1; then
        BUILD_ARGS="$BUILD_ARGS --build-arg VCS_REF=$(git rev-parse --short HEAD)"
    fi

    # Check if .env file exists
    if [[ ! -f .env ]]; then
        print_warning ".env file not found, copying from .env.example"
        if [[ -f .env.example ]]; then
            cp .env.example .env
            print_info "Please edit .env file with your configuration"
        else
            print_error ".env.example file not found"
            exit 1
        fi
    fi
}

# Function to deploy services
deploy_services() {
    print_info "Deploying GitHound services..."

    if [[ "$FORCE_BUILD" == "true" ]]; then
        print_info "Force building images..."
        docker-compose $COMPOSE_FILES build --no-cache $BUILD_ARGS
    else
        docker-compose $COMPOSE_FILES build $BUILD_ARGS
    fi

    if [[ "$DETACHED" == "true" ]]; then
        docker-compose $COMPOSE_FILES up -d
    else
        docker-compose $COMPOSE_FILES up
    fi

    print_success "Deployment completed"
}

# Function to stop services
stop_services() {
    print_info "Stopping GitHound services..."
    docker-compose $COMPOSE_FILES down
    print_success "Services stopped"
}

# Function to restart services
restart_services() {
    print_info "Restarting GitHound services..."
    docker-compose $COMPOSE_FILES restart
    print_success "Services restarted"
}

# Function to show logs
show_logs() {
    print_info "Showing service logs..."
    docker-compose $COMPOSE_FILES logs -f
}

# Function to show status
show_status() {
    print_info "Service status:"
    docker-compose $COMPOSE_FILES ps

    print_info "Health checks:"
    docker-compose $COMPOSE_FILES exec -T githound-web curl -f http://localhost:8000/health || print_warning "Web service health check failed"
    docker-compose $COMPOSE_FILES exec -T githound-mcp curl -f http://localhost:3000/health || print_warning "MCP service health check failed"
}

# Function to clean up
clean_up() {
    print_warning "This will remove all containers, networks, and volumes. Are you sure? (y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        print_info "Cleaning up..."
        docker-compose $COMPOSE_FILES down -v --remove-orphans
        docker system prune -f
        print_success "Cleanup completed"
    else
        print_info "Cleanup cancelled"
    fi
}

# Function to build images
build_images() {
    print_info "Building Docker images..."
    docker-compose $COMPOSE_FILES build $BUILD_ARGS
    print_success "Images built successfully"
}

# Function to update deployment
update_deployment() {
    print_info "Updating deployment..."
    docker-compose $COMPOSE_FILES pull
    docker-compose $COMPOSE_FILES up -d
    print_success "Deployment updated"
}

# Parse command line arguments
FORCE_BUILD="false"
DETACHED="true"
VERBOSE="false"

while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -f|--force)
            FORCE_BUILD="true"
            shift
            ;;
        -d|--detach)
            DETACHED="true"
            shift
            ;;
        -v|--verbose)
            VERBOSE="true"
            set -x
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        deploy|stop|restart|logs|status|clean|build|update)
            ACTION="$1"
            shift
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Main execution
main() {
    print_info "GitHound Docker Deployment Script"
    print_info "Environment: $ENVIRONMENT"
    print_info "Action: $ACTION"

    check_prerequisites
    setup_environment

    case $ACTION in
        deploy)
            deploy_services
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        logs)
            show_logs
            ;;
        status)
            show_status
            ;;
        clean)
            clean_up
            ;;
        build)
            build_images
            ;;
        update)
            update_deployment
            ;;
        *)
            print_error "Invalid action: $ACTION"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
