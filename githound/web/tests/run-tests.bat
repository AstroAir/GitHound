@echo off
REM GitHound Web Frontend Test Runner for Windows
REM Comprehensive test execution script for local development and CI/CD

setlocal enabledelayedexpansion

REM Default values
set BROWSER=chromium
set HEADLESS=true
set WORKERS=4
set RETRIES=1
set TIMEOUT=30000
set OUTPUT_DIR=test-results
set COVERAGE=false
set PERFORMANCE=false
set ACCESSIBILITY=false
set VISUAL=false
set LOAD_TEST=false
set VERBOSE=false
set CLEAN=false

REM Function to show usage
:show_usage
echo GitHound Web Frontend Test Runner
echo.
echo Usage: %~nx0 [OPTIONS]
echo.
echo Options:
echo     -b, --browser BROWSER       Browser to use (chromium, firefox, webkit, all) [default: chromium]
echo     -h, --headless              Run in headless mode [default: true]
echo     -w, --workers WORKERS       Number of parallel workers [default: 4]
echo     -r, --retries RETRIES       Number of retries for failed tests [default: 1]
echo     -t, --timeout TIMEOUT       Test timeout in milliseconds [default: 30000]
echo     -o, --output OUTPUT_DIR     Output directory for test results [default: test-results]
echo     -c, --coverage              Generate coverage reports
echo     -p, --performance           Run performance tests
echo     -a, --accessibility         Run accessibility tests
echo     -v, --visual                Run visual regression tests
echo     -l, --load                  Run load tests
echo     --verbose                   Enable verbose output
echo     --clean                     Clean output directory before running
echo     --help                      Show this help message
echo.
echo Examples:
echo     %~nx0                          # Run basic tests with default settings
echo     %~nx0 -b all -c -p            # Run all browsers with coverage and performance
echo     %~nx0 --accessibility --visual # Run accessibility and visual tests
echo     %~nx0 --load --verbose         # Run load tests with verbose output
echo     %~nx0 --clean -o custom-results # Clean and use custom output directory
echo.
goto :eof

REM Parse command line arguments
:parse_args
if "%~1"=="" goto :start_tests
if "%~1"=="-b" (
    set BROWSER=%~2
    shift
    shift
    goto :parse_args
)
if "%~1"=="--browser" (
    set BROWSER=%~2
    shift
    shift
    goto :parse_args
)
if "%~1"=="-h" (
    set HEADLESS=true
    shift
    goto :parse_args
)
if "%~1"=="--headless" (
    set HEADLESS=true
    shift
    goto :parse_args
)
if "%~1"=="-w" (
    set WORKERS=%~2
    shift
    shift
    goto :parse_args
)
if "%~1"=="--workers" (
    set WORKERS=%~2
    shift
    shift
    goto :parse_args
)
if "%~1"=="-r" (
    set RETRIES=%~2
    shift
    shift
    goto :parse_args
)
if "%~1"=="--retries" (
    set RETRIES=%~2
    shift
    shift
    goto :parse_args
)
if "%~1"=="-t" (
    set TIMEOUT=%~2
    shift
    shift
    goto :parse_args
)
if "%~1"=="--timeout" (
    set TIMEOUT=%~2
    shift
    shift
    goto :parse_args
)
if "%~1"=="-o" (
    set OUTPUT_DIR=%~2
    shift
    shift
    goto :parse_args
)
if "%~1"=="--output" (
    set OUTPUT_DIR=%~2
    shift
    shift
    goto :parse_args
)
if "%~1"=="-c" (
    set COVERAGE=true
    shift
    goto :parse_args
)
if "%~1"=="--coverage" (
    set COVERAGE=true
    shift
    goto :parse_args
)
if "%~1"=="-p" (
    set PERFORMANCE=true
    shift
    goto :parse_args
)
if "%~1"=="--performance" (
    set PERFORMANCE=true
    shift
    goto :parse_args
)
if "%~1"=="-a" (
    set ACCESSIBILITY=true
    shift
    goto :parse_args
)
if "%~1"=="--accessibility" (
    set ACCESSIBILITY=true
    shift
    goto :parse_args
)
if "%~1"=="-v" (
    set VISUAL=true
    shift
    goto :parse_args
)
if "%~1"=="--visual" (
    set VISUAL=true
    shift
    goto :parse_args
)
if "%~1"=="-l" (
    set LOAD_TEST=true
    shift
    goto :parse_args
)
if "%~1"=="--load" (
    set LOAD_TEST=true
    shift
    goto :parse_args
)
if "%~1"=="--verbose" (
    set VERBOSE=true
    shift
    goto :parse_args
)
if "%~1"=="--clean" (
    set CLEAN=true
    shift
    goto :parse_args
)
if "%~1"=="--help" (
    call :show_usage
    exit /b 0
)
echo [ERROR] Unknown option: %~1
call :show_usage
exit /b 1

:start_tests
REM Validate browser option
if not "%BROWSER%"=="chromium" if not "%BROWSER%"=="firefox" if not "%BROWSER%"=="webkit" if not "%BROWSER%"=="all" (
    echo [ERROR] Invalid browser: %BROWSER%. Must be one of: chromium, firefox, webkit, all
    exit /b 1
)

REM Clean output directory if requested
if "%CLEAN%"=="true" (
    echo [INFO] Cleaning output directory: %OUTPUT_DIR%
    if exist "%OUTPUT_DIR%" rmdir /s /q "%OUTPUT_DIR%"
)

REM Create output directory
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

REM Set environment variables
set HEADLESS=%HEADLESS%
set WORKERS=%WORKERS%
set RETRIES=%RETRIES%
set TIMEOUT=%TIMEOUT%
set VERBOSE=%VERBOSE%

echo [INFO] Starting GitHound Web Frontend Tests
echo [INFO] Browser: %BROWSER%
echo [INFO] Headless: %HEADLESS%
echo [INFO] Workers: %WORKERS%
echo [INFO] Output: %OUTPUT_DIR%

REM Check if we're in the correct directory
if not exist "playwright.config.js" (
    echo [ERROR] playwright.config.js not found. Please run this script from the githound/web/tests directory.
    exit /b 1
)

REM Install dependencies if needed
if not exist "node_modules" (
    echo [INFO] Installing dependencies...
    call npm install
)

REM Function to run tests for a specific browser
:run_browser_tests
set browser=%~1
echo [INFO] Running tests for %browser%

REM Base test command
set cmd=playwright test --project=%browser% --output-dir=%OUTPUT_DIR%/%browser%

REM Add reporters
set cmd=%cmd% --reporter=html:%OUTPUT_DIR%/%browser%/html-report
set cmd=%cmd% --reporter=junit:%OUTPUT_DIR%/%browser%/results.xml
set cmd=%cmd% --reporter=./utils/custom-reporter.js:%OUTPUT_DIR%/%browser%/custom

REM Add specific test filters based on options
set test_filters=

if "%PERFORMANCE%"=="true" (
    set test_filters=%test_filters% --grep=@performance
)

if "%ACCESSIBILITY%"=="true" (
    set test_filters=%test_filters% --grep=@accessibility
)

if "%VISUAL%"=="true" (
    set test_filters=%test_filters% --grep=@visual
)

if "%LOAD_TEST%"=="true" (
    set test_filters=%test_filters% --grep=@load
)

REM If no specific tests selected, run core tests
if "%test_filters%"=="" (
    set test_filters=--grep=@unit^|@integration^|@ui
)

REM Execute the test command
%cmd% %test_filters%
if %errorlevel% equ 0 (
    echo [SUCCESS] Tests completed successfully for %browser%
    exit /b 0
) else (
    echo [ERROR] Tests failed for %browser%
    exit /b 1
)

REM Main execution
set exit_code=0

REM Run tests based on browser selection
if "%BROWSER%"=="all" (
    call :run_browser_tests chromium
    if !errorlevel! neq 0 set exit_code=1

    call :run_browser_tests firefox
    if !errorlevel! neq 0 set exit_code=1

    call :run_browser_tests webkit
    if !errorlevel! neq 0 set exit_code=1
) else (
    call :run_browser_tests %BROWSER%
    if !errorlevel! neq 0 set exit_code=1
)

REM Generate coverage if requested
if "%COVERAGE%"=="true" (
    echo [INFO] Generating coverage reports

    node -e "const CoverageReporter = require('./utils/coverage-reporter.js'); const reporter = new CoverageReporter({ outputDir: '%OUTPUT_DIR%/coverage', generateHtml: true, threshold: { statements: 75, branches: 70, functions: 75, lines: 75 } }); reporter.generateReports();"

    if !errorlevel! equ 0 (
        echo [SUCCESS] Coverage reports generated in %OUTPUT_DIR%/coverage
    ) else (
        echo [WARNING] Failed to generate coverage reports
    )
)

REM Generate summary
echo [INFO] Generating test summary

set summary_file=%OUTPUT_DIR%/summary.md

echo # GitHound Web Frontend Test Summary > "%summary_file%"
echo. >> "%summary_file%"
echo **Generated:** %date% %time% >> "%summary_file%"
echo **Browser(s):** %BROWSER% >> "%summary_file%"
echo **Configuration:** >> "%summary_file%"
echo - Headless: %HEADLESS% >> "%summary_file%"
echo - Workers: %WORKERS% >> "%summary_file%"
echo - Retries: %RETRIES% >> "%summary_file%"
echo. >> "%summary_file%"
echo ## Test Categories Run >> "%summary_file%"
echo. >> "%summary_file%"

if "%PERFORMANCE%"=="true" (
    echo - ⚡ Performance Tests >> "%summary_file%"
)

if "%ACCESSIBILITY%"=="true" (
    echo - ♿ Accessibility Tests >> "%summary_file%"
)

if "%VISUAL%"=="true" (
    echo - 👁️ Visual Regression Tests >> "%summary_file%"
)

if "%LOAD_TEST%"=="true" (
    echo - 🔥 Load Tests >> "%summary_file%"
)

if "%COVERAGE%"=="true" (
    echo - 📊 Coverage Analysis >> "%summary_file%"
)

echo. >> "%summary_file%"
echo ## Results >> "%summary_file%"
echo. >> "%summary_file%"
echo Test results are available in the following locations: >> "%summary_file%"
echo - HTML Reports: `%OUTPUT_DIR%/*/html-report/` >> "%summary_file%"
echo - JUnit XML: `%OUTPUT_DIR%/*/results.xml` >> "%summary_file%"
echo - Custom Reports: `%OUTPUT_DIR%/*/custom/` >> "%summary_file%"

if "%COVERAGE%"=="true" (
    echo - Coverage Reports: `%OUTPUT_DIR%/coverage/` >> "%summary_file%"
)

echo [SUCCESS] Test summary generated: %summary_file%

if %exit_code% equ 0 (
    echo [SUCCESS] All tests completed successfully!
    echo [INFO] Results available in: %OUTPUT_DIR%
) else (
    echo [ERROR] Some tests failed. Check the reports for details.
)

exit /b %exit_code%

REM Parse arguments and start
call :parse_args %*
