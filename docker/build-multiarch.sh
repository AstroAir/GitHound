#!/bin/bash
# Multi-architecture Docker build script for GitHound
# Supports building for multiple platforms: linux/amd64, linux/arm64

set -euo pipefail

# Configuration
REGISTRY="${REGISTRY:-ghcr.io/astroair}"
IMAGE_NAME="${IMAGE_NAME:-githound}"
VERSION="${VERSION:-latest}"
PLATFORMS="${PLATFORMS:-linux/amd64,linux/arm64}"
PUSH="${PUSH:-false}"
CACHE_FROM="${CACHE_FROM:-}"
CACHE_TO="${CACHE_TO:-}"

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

# Function to check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi

    # Check if buildx is available
    if ! docker buildx version &> /dev/null; then
        log_error "Docker Buildx is not available"
        exit 1
    fi

    # Check if builder exists, create if not
    if ! docker buildx inspect multiarch-builder &> /dev/null; then
        log_info "Creating multiarch builder..."
        docker buildx create --name multiarch-builder --driver docker-container --use
        docker buildx inspect --bootstrap
    else
        log_info "Using existing multiarch builder..."
        docker buildx use multiarch-builder
    fi

    log_success "Prerequisites check completed"
}

# Function to get build metadata
get_build_metadata() {
    BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')

    if command -v git &> /dev/null && git rev-parse --git-dir > /dev/null 2>&1; then
        VCS_REF=$(git rev-parse --short HEAD)
        # Get version from git tag if available
        if git describe --tags --exact-match HEAD &> /dev/null; then
            VERSION=$(git describe --tags --exact-match HEAD)
        fi
    else
        VCS_REF="unknown"
    fi

    log_info "Build metadata:"
    log_info "  Version: ${VERSION}"
    log_info "  VCS Ref: ${VCS_REF}"
    log_info "  Build Date: ${BUILD_DATE}"
}

# Function to build multi-architecture images
build_multiarch() {
    local target="${1:-production}"
    local tag_suffix="${2:-}"

    log_info "Building multi-architecture image for target: ${target}"
    log_info "Platforms: ${PLATFORMS}"

    # Prepare build arguments
    BUILD_ARGS=(
        "--build-arg" "BUILD_DATE=${BUILD_DATE}"
        "--build-arg" "VCS_REF=${VCS_REF}"
        "--build-arg" "GITHOUND_VERSION=${VERSION}"
    )

    # Prepare cache arguments
    if [[ -n "${CACHE_FROM}" ]]; then
        BUILD_ARGS+=("--cache-from" "${CACHE_FROM}")
    fi

    if [[ -n "${CACHE_TO}" ]]; then
        BUILD_ARGS+=("--cache-to" "${CACHE_TO}")
    fi

    # Prepare tags
    FULL_TAG="${REGISTRY}/${IMAGE_NAME}:${VERSION}${tag_suffix}"
    LATEST_TAG="${REGISTRY}/${IMAGE_NAME}:latest${tag_suffix}"

    # Build command
    BUILD_CMD=(
        "docker" "buildx" "build"
        "--platform" "${PLATFORMS}"
        "--target" "${target}"
        "${BUILD_ARGS[@]}"
        "--tag" "${FULL_TAG}"
        "--tag" "${LATEST_TAG}"
        "--file" "Dockerfile"
        "."
    )

    # Add push flag if requested
    if [[ "${PUSH}" == "true" ]]; then
        BUILD_CMD+=("--push")
        log_info "Images will be pushed to registry"
    else
        BUILD_CMD+=("--load")
        log_warning "Images will be loaded locally (single platform only)"
    fi

    log_info "Executing build command..."
    "${BUILD_CMD[@]}"

    log_success "Multi-architecture build completed for target: ${target}"
}

# Function to show usage
show_usage() {
    cat << EOF
Multi-architecture Docker build script for GitHound

Usage: $0 [OPTIONS] [TARGET]

OPTIONS:
    -r, --registry REGISTRY     Container registry (default: ghcr.io/astroair)
    -i, --image IMAGE          Image name (default: githound)
    -v, --version VERSION      Image version (default: latest)
    -p, --platforms PLATFORMS  Target platforms (default: linux/amd64,linux/arm64)
    --push                     Push images to registry
    --cache-from CACHE         Cache source
    --cache-to CACHE           Cache destination
    -h, --help                 Show this help message

TARGETS:
    production                 Build production image (default)
    development               Build development image
    all                       Build all targets

EXAMPLES:
    # Build production image for multiple architectures
    $0 production

    # Build and push to registry
    $0 --push production

    # Build with custom registry and version
    $0 -r myregistry.com -v v1.0.0 production

    # Build with cache
    $0 --cache-from type=registry,ref=myregistry.com/githound:cache production

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -r|--registry)
            REGISTRY="$2"
            shift 2
            ;;
        -i|--image)
            IMAGE_NAME="$2"
            shift 2
            ;;
        -v|--version)
            VERSION="$2"
            shift 2
            ;;
        -p|--platforms)
            PLATFORMS="$2"
            shift 2
            ;;
        --push)
            PUSH="true"
            shift
            ;;
        --cache-from)
            CACHE_FROM="$2"
            shift 2
            ;;
        --cache-to)
            CACHE_TO="$2"
            shift 2
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        production|development|all)
            TARGET="$1"
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Set default target if not specified
TARGET="${TARGET:-production}"

# Main execution
main() {
    log_info "Starting multi-architecture build for GitHound"

    check_prerequisites
    get_build_metadata

    case "${TARGET}" in
        production)
            build_multiarch "production"
            ;;
        development)
            build_multiarch "development" "-dev"
            ;;
        all)
            build_multiarch "production"
            build_multiarch "development" "-dev"
            ;;
        *)
            log_error "Invalid target: ${TARGET}"
            show_usage
            exit 1
            ;;
    esac

    log_success "Multi-architecture build process completed!"
}

# Run main function
main "$@"
