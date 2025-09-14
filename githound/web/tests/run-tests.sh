#!/bin/bash

# GitHound Web Frontend Test Runner
# Comprehensive test execution script for local development and CI/CD

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
BROWSER="chromium"
HEADLESS="true"
WORKERS="4"
RETRIES="1"
TIMEOUT="30000"
OUTPUT_DIR="test-results"
COVERAGE="false"
PERFORMANCE="false"
ACCESSIBILITY="false"
VISUAL="false"
LOAD_TEST="false"
VERBOSE="false"
CLEAN="false"

# Function to print colored output
print_status() {
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
GitHound Web Frontend Test Runner

Usage: $0 [OPTIONS]

Options:
    -b, --browser BROWSER       Browser to use (chromium, firefox, webkit, all) [default: chromium]
    -h, --headless              Run in headless mode [default: true]
    -w, --workers WORKERS       Number of parallel workers [default: 4]
    -r, --retries RETRIES       Number of retries for failed tests [default: 1]
    -t, --timeout TIMEOUT       Test timeout in milliseconds [default: 30000]
    -o, --output OUTPUT_DIR     Output directory for test results [default: test-results]
    -c, --coverage              Generate coverage reports
    -p, --performance           Run performance tests
    -a, --accessibility         Run accessibility tests
    -v, --visual                Run visual regression tests
    -l, --load                  Run load tests
    --verbose                   Enable verbose output
    --clean                     Clean output directory before running
    --help                      Show this help message

Examples:
    $0                          # Run basic tests with default settings
    $0 -b all -c -p            # Run all browsers with coverage and performance
    $0 --accessibility --visual # Run accessibility and visual tests
    $0 --load --verbose         # Run load tests with verbose output
    $0 --clean -o custom-results # Clean and use custom output directory

Test Categories:
    - Unit tests: Fast, isolated component tests
    - Integration tests: API and service integration tests
    - UI tests: User interface and interaction tests
    - Performance tests: Load time and responsiveness tests
    - Accessibility tests: WCAG compliance and screen reader tests
    - Visual tests: Screenshot comparison and layout tests
    - Load tests: Concurrent user and stress tests

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -b|--browser)
            BROWSER="$2"
            shift 2
            ;;
        -h|--headless)
            HEADLESS="true"
            shift
            ;;
        -w|--workers)
            WORKERS="$2"
            shift 2
            ;;
        -r|--retries)
            RETRIES="$2"
            shift 2
            ;;
        -t|--timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -c|--coverage)
            COVERAGE="true"
            shift
            ;;
        -p|--performance)
            PERFORMANCE="true"
            shift
            ;;
        -a|--accessibility)
            ACCESSIBILITY="true"
            shift
            ;;
        -v|--visual)
            VISUAL="true"
            shift
            ;;
        -l|--load)
            LOAD_TEST="true"
            shift
            ;;
        --verbose)
            VERBOSE="true"
            shift
            ;;
        --clean)
            CLEAN="true"
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate browser option
if [[ "$BROWSER" != "chromium" && "$BROWSER" != "firefox" && "$BROWSER" != "webkit" && "$BROWSER" != "all" ]]; then
    print_error "Invalid browser: $BROWSER. Must be one of: chromium, firefox, webkit, all"
    exit 1
fi

# Clean output directory if requested
if [[ "$CLEAN" == "true" ]]; then
    print_status "Cleaning output directory: $OUTPUT_DIR"
    rm -rf "$OUTPUT_DIR"
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Set environment variables
export HEADLESS="$HEADLESS"
export WORKERS="$WORKERS"
export RETRIES="$RETRIES"
export TIMEOUT="$TIMEOUT"
export VERBOSE="$VERBOSE"

print_status "Starting GitHound Web Frontend Tests"
print_status "Browser: $BROWSER"
print_status "Headless: $HEADLESS"
print_status "Workers: $WORKERS"
print_status "Output: $OUTPUT_DIR"

# Function to run tests for a specific browser
run_browser_tests() {
    local browser=$1
    print_status "Running tests for $browser"
    
    # Base test command
    local cmd="playwright test --project=$browser --output-dir=$OUTPUT_DIR/$browser"
    
    # Add reporters
    cmd="$cmd --reporter=html:$OUTPUT_DIR/$browser/html-report"
    cmd="$cmd --reporter=junit:$OUTPUT_DIR/$browser/results.xml"
    cmd="$cmd --reporter=./utils/custom-reporter.js:$OUTPUT_DIR/$browser/custom"
    
    # Add specific test filters based on options
    local test_filters=""
    
    if [[ "$PERFORMANCE" == "true" ]]; then
        test_filters="$test_filters --grep=@performance"
    fi
    
    if [[ "$ACCESSIBILITY" == "true" ]]; then
        test_filters="$test_filters --grep=@accessibility"
    fi
    
    if [[ "$VISUAL" == "true" ]]; then
        test_filters="$test_filters --grep=@visual"
    fi
    
    if [[ "$LOAD_TEST" == "true" ]]; then
        test_filters="$test_filters --grep=@load"
    fi
    
    # If no specific tests selected, run core tests
    if [[ -z "$test_filters" ]]; then
        test_filters="--grep=@unit|@integration|@ui"
    fi
    
    # Execute the test command
    if eval "$cmd $test_filters"; then
        print_success "Tests completed successfully for $browser"
        return 0
    else
        print_error "Tests failed for $browser"
        return 1
    fi
}

# Function to generate coverage report
generate_coverage() {
    if [[ "$COVERAGE" == "true" ]]; then
        print_status "Generating coverage reports"
        
        node -e "
            const CoverageReporter = require('./utils/coverage-reporter.js');
            const reporter = new CoverageReporter({
                outputDir: '$OUTPUT_DIR/coverage',
                generateHtml: true,
                threshold: { statements: 75, branches: 70, functions: 75, lines: 75 }
            });
            reporter.generateReports();
        "
        
        if [[ $? -eq 0 ]]; then
            print_success "Coverage reports generated in $OUTPUT_DIR/coverage"
        else
            print_warning "Failed to generate coverage reports"
        fi
    fi
}

# Function to generate summary report
generate_summary() {
    print_status "Generating test summary"
    
    local summary_file="$OUTPUT_DIR/summary.md"
    
    cat > "$summary_file" << EOF
# GitHound Web Frontend Test Summary

**Generated:** $(date)
**Browser(s):** $BROWSER
**Configuration:**
- Headless: $HEADLESS
- Workers: $WORKERS
- Retries: $RETRIES

## Test Categories Run

EOF
    
    if [[ "$PERFORMANCE" == "true" ]]; then
        echo "- ⚡ Performance Tests" >> "$summary_file"
    fi
    
    if [[ "$ACCESSIBILITY" == "true" ]]; then
        echo "- ♿ Accessibility Tests" >> "$summary_file"
    fi
    
    if [[ "$VISUAL" == "true" ]]; then
        echo "- 👁️ Visual Regression Tests" >> "$summary_file"
    fi
    
    if [[ "$LOAD_TEST" == "true" ]]; then
        echo "- 🔥 Load Tests" >> "$summary_file"
    fi
    
    if [[ "$COVERAGE" == "true" ]]; then
        echo "- 📊 Coverage Analysis" >> "$summary_file"
    fi
    
    cat >> "$summary_file" << EOF

## Results

Test results are available in the following locations:
- HTML Reports: \`$OUTPUT_DIR/*/html-report/\`
- JUnit XML: \`$OUTPUT_DIR/*/results.xml\`
- Custom Reports: \`$OUTPUT_DIR/*/custom/\`

EOF
    
    if [[ "$COVERAGE" == "true" ]]; then
        echo "- Coverage Reports: \`$OUTPUT_DIR/coverage/\`" >> "$summary_file"
    fi
    
    print_success "Test summary generated: $summary_file"
}

# Main execution
main() {
    local exit_code=0
    
    # Check if we're in the correct directory
    if [[ ! -f "playwright.config.js" ]]; then
        print_error "playwright.config.js not found. Please run this script from the githound/web/tests directory."
        exit 1
    fi
    
    # Install dependencies if needed
    if [[ ! -d "node_modules" ]]; then
        print_status "Installing dependencies..."
        npm install
    fi
    
    # Run tests based on browser selection
    if [[ "$BROWSER" == "all" ]]; then
        for browser in chromium firefox webkit; do
            if ! run_browser_tests "$browser"; then
                exit_code=1
            fi
        done
    else
        if ! run_browser_tests "$BROWSER"; then
            exit_code=1
        fi
    fi
    
    # Generate coverage if requested
    generate_coverage
    
    # Generate summary
    generate_summary
    
    if [[ $exit_code -eq 0 ]]; then
        print_success "All tests completed successfully!"
        print_status "Results available in: $OUTPUT_DIR"
    else
        print_error "Some tests failed. Check the reports for details."
    fi
    
    exit $exit_code
}

# Run main function
main "$@"
