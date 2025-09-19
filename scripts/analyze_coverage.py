#!/usr/bin/env python3
"""Analyze test coverage and identify gaps for GitHound project."""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Tuple
import sys


def parse_coverage_xml(coverage_file: Path) -> Dict[str, Dict[str, float]]:
    """Parse coverage.xml and extract coverage data."""
    tree = ET.parse(coverage_file)
    root = tree.getroot()
    
    coverage_data = {}
    
    for package in root.findall('.//package'):
        package_name = package.get('name', '')
        
        for class_elem in package.findall('classes/class'):
            filename = class_elem.get('filename', '')
            line_rate = float(class_elem.get('line-rate', 0))
            branch_rate = float(class_elem.get('branch-rate', 0))
            
            # Get line counts
            lines = class_elem.findall('lines/line')
            total_lines = len(lines)
            covered_lines = len([line for line in lines if int(line.get('hits', 0)) > 0])
            
            coverage_data[filename] = {
                'line_rate': line_rate,
                'branch_rate': branch_rate,
                'total_lines': total_lines,
                'covered_lines': covered_lines,
                'missing_lines': total_lines - covered_lines
            }
    
    return coverage_data


def identify_priority_files(coverage_data: Dict[str, Dict[str, float]]) -> List[Tuple[str, Dict[str, float]]]:
    """Identify files that need priority attention for test coverage."""
    priority_files = []
    
    for filename, data in coverage_data.items():
        # Skip test files and __pycache__
        if 'test_' in filename or '__pycache__' in filename:
            continue
            
        # Priority criteria:
        # 1. Low coverage (< 50%)
        # 2. High number of missing lines (> 50)
        # 3. Core modules (cli.py, mcp_server.py, etc.)
        
        line_rate = data['line_rate']
        missing_lines = data['missing_lines']
        
        is_core_module = any(core in filename for core in [
            'cli.py', 'mcp_server.py', 'git_handler.py', 'git_blame.py', 
            'git_diff.py', '__init__.py', 'searcher.py', 'orchestrator.py'
        ])
        
        priority_score = 0
        if line_rate < 0.5:  # Less than 50% coverage
            priority_score += 3
        elif line_rate < 0.8:  # Less than 80% coverage
            priority_score += 2
        
        if missing_lines > 50:
            priority_score += 2
        elif missing_lines > 20:
            priority_score += 1
            
        if is_core_module:
            priority_score += 2
            
        if priority_score >= 3:  # High priority threshold
            priority_files.append((filename, data))
    
    # Sort by priority score (descending) and missing lines (descending)
    priority_files.sort(key=lambda x: (x[1]['missing_lines'], 1 - x[1]['line_rate']), reverse=True)
    
    return priority_files


def generate_coverage_report():
    """Generate a comprehensive coverage analysis report."""
    coverage_file = Path('coverage.xml')
    
    if not coverage_file.exists():
        print("❌ coverage.xml not found. Run tests with coverage first:")
        print("   ./venv/bin/python -m pytest --cov=githound --cov-report=xml")
        return
    
    print("🔍 GitHound Test Coverage Analysis")
    print("=" * 50)
    
    coverage_data = parse_coverage_xml(coverage_file)
    priority_files = identify_priority_files(coverage_data)
    
    # Overall statistics
    total_files = len([f for f in coverage_data.keys() if not ('test_' in f or '__pycache__' in f)])
    total_lines = sum(data['total_lines'] for data in coverage_data.values())
    total_covered = sum(data['covered_lines'] for data in coverage_data.values())
    overall_coverage = (total_covered / total_lines) * 100 if total_lines > 0 else 0
    
    print(f"\n📊 Overall Statistics:")
    print(f"   Total files: {total_files}")
    print(f"   Total lines: {total_lines}")
    print(f"   Covered lines: {total_covered}")
    print(f"   Overall coverage: {overall_coverage:.2f}%")
    print(f"   Target coverage: 90.00%")
    print(f"   Gap to target: {90 - overall_coverage:.2f}%")
    
    print(f"\n🎯 Priority Files for Test Coverage (Top 15):")
    print("-" * 80)
    print(f"{'File':<40} {'Coverage':<10} {'Missing':<8} {'Total':<8}")
    print("-" * 80)
    
    for i, (filename, data) in enumerate(priority_files[:15]):
        coverage_pct = data['line_rate'] * 100
        missing = data['missing_lines']
        total = data['total_lines']
        
        print(f"{filename:<40} {coverage_pct:>6.1f}%   {missing:>6}   {total:>6}")
    
    # Module-specific analysis
    print(f"\n📁 Module-specific Analysis:")
    print("-" * 50)
    
    modules = {
        'CLI': ['cli.py'],
        'MCP Server': ['mcp_server.py', 'mcp/'],
        'Git Operations': ['git_handler.py', 'git_blame.py', 'git_diff.py'],
        'Search Engine': ['search_engine/'],
        'Web API': ['web/'],
        'Utils': ['utils/'],
        'Core': ['__init__.py', 'models.py', 'schemas.py']
    }
    
    for module_name, patterns in modules.items():
        module_files = []
        for filename, data in coverage_data.items():
            if any(pattern in filename for pattern in patterns):
                if not ('test_' in filename or '__pycache__' in filename):
                    module_files.append((filename, data))
        
        if module_files:
            module_total_lines = sum(data['total_lines'] for _, data in module_files)
            module_covered_lines = sum(data['covered_lines'] for _, data in module_files)
            module_coverage = (module_covered_lines / module_total_lines) * 100 if module_total_lines > 0 else 0
            
            print(f"{module_name:<15}: {module_coverage:>6.1f}% ({len(module_files)} files)")
    
    print(f"\n💡 Recommendations:")
    print("   1. Start with CLI module (0% coverage, 694 lines)")
    print("   2. Focus on MCP server components (low coverage, high impact)")
    print("   3. Enhance Git operations tests (core functionality)")
    print("   4. Complete search engine test coverage")
    print("   5. Add comprehensive integration tests")
    
    print(f"\n📋 Next Steps:")
    print("   1. Run: python scripts/analyze_coverage.py")
    print("   2. Create tests for priority files listed above")
    print("   3. Aim for 90% overall coverage")
    print("   4. Focus on meaningful tests, not just line coverage")


if __name__ == "__main__":
    generate_coverage_report()
