#!/bin/bash
# GitHound Multi-Architecture Docker Build Setup
# This script sets up Docker Buildx for multi-architecture builds

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed and running
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    if ! docker info &> /dev/null; then
        log_error "Docker is not running. Please start Docker first."
        exit 1
    fi

    log_success "Docker is installed and running"
}

# Check if Docker Buildx is available
check_buildx() {
    if ! docker buildx version &> /dev/null; then
        log_error "Docker Buildx is not available. Please update Docker to a newer version."
        exit 1
    fi

    log_success "Docker Buildx is available"
}

# Create or update the multi-arch builder
setup_builder() {
    local builder_name="githound-multiarch"
    
    log_info "Setting up multi-architecture builder: $builder_name"
    
    # Check if builder already exists
    if docker buildx inspect "$builder_name" &> /dev/null; then
        log_info "Builder '$builder_name' already exists, updating..."
        docker buildx rm "$builder_name" || true
    fi
    
    # Create new builder with multi-arch support
    docker buildx create \
        --name "$builder_name" \
        --driver docker-container \
        --platform linux/amd64,linux/arm64 \
        --use
    
    # Bootstrap the builder
    log_info "Bootstrapping the builder..."
    docker buildx inspect --bootstrap
    
    log_success "Multi-architecture builder '$builder_name' is ready"
}

# List available platforms
list_platforms() {
    log_info "Available platforms:"
    docker buildx inspect --bootstrap | grep "Platforms:" || true
}

# Test multi-arch build capability
test_build() {
    log_info "Testing multi-architecture build capability..."
    
    # Create a simple test Dockerfile
    cat > /tmp/test-multiarch.Dockerfile << 'EOF'
FROM alpine:latest
RUN echo "Architecture: $(uname -m)" > /arch.txt
CMD cat /arch.txt
EOF
    
    # Test build for multiple architectures
    if docker buildx build \
        --platform linux/amd64,linux/arm64 \
        --file /tmp/test-multiarch.Dockerfile \
        --tag githound-test:multiarch \
        /tmp; then
        log_success "Multi-architecture build test passed"
        
        # Clean up test image
        docker rmi githound-test:multiarch &> /dev/null || true
    else
        log_error "Multi-architecture build test failed"
        exit 1
    fi
    
    # Clean up test file
    rm -f /tmp/test-multiarch.Dockerfile
}

# Main execution
main() {
    log_info "GitHound Multi-Architecture Docker Build Setup"
    echo
    
    check_docker
    check_buildx
    setup_builder
    list_platforms
    test_build
    
    echo
    log_success "Multi-architecture build setup completed successfully!"
    echo
    log_info "You can now build GitHound for multiple architectures using:"
    echo "  docker buildx build --platform linux/amd64,linux/arm64 -t githound:latest ."
    echo
    log_info "To push to a registry, add --push flag:"
    echo "  docker buildx build --platform linux/amd64,linux/arm64 -t your-registry/githound:latest --push ."
}

# Run main function
main "$@"
