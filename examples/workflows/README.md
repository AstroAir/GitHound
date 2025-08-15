# Workflow Examples

This directory contains end-to-end workflow examples demonstrating complete GitHound usage scenarios.

## Examples Overview

- `complete_analysis.py` - Full repository analysis workflow
- `ci_cd_integration.py` - CI/CD pipeline integration examples
- `automated_reporting.py` - Automated report generation
- `performance_monitoring.py` - Performance analysis workflows
- `code_review_assistance.py` - Code review automation
- `security_analysis.py` - Security-focused analysis workflows
- `migration_analysis.py` - Repository migration assistance

## Workflow Categories

### Complete Analysis Workflows
- Full repository assessment
- Multi-dimensional analysis
- Comprehensive reporting
- Data aggregation and insights

### CI/CD Integration
- Pipeline integration patterns
- Automated quality checks
- Continuous monitoring
- Build-time analysis

### Reporting Workflows
- Automated report generation
- Scheduled analysis runs
- Multi-format output
- Stakeholder communication

### Performance Monitoring
- Performance trend analysis
- Bottleneck identification
- Optimization recommendations
- Historical comparisons

## Running Workflows

Each workflow is designed to be executable:

```bash
python examples/workflows/complete_analysis.py /path/to/repo
python examples/workflows/ci_cd_integration.py
# etc.
```

## Complete Analysis Workflow

### Full Repository Assessment
```python
#!/usr/bin/env python3
"""
Complete repository analysis workflow.
Demonstrates comprehensive GitHound usage for full repository assessment.
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime, timedelta

from githound.git_handler import get_repository, get_repository_metadata
from githound.git_blame import get_author_statistics
from githound.git_diff import compare_branches
from githound.mcp_server import get_mcp_server
from githound.utils.export import ExportManager
from githound.schemas import ExportOptions, OutputFormat

async def complete_repository_analysis(repo_path: str):
    """
    Perform complete repository analysis including:
    - Repository metadata
    - Author statistics
    - Recent activity analysis
    - Branch comparisons
    - Export results in multiple formats
    """
    
    print(f"Starting complete analysis of: {repo_path}")
    
    # 1. Repository Setup
    repo = get_repository(Path(repo_path))
    analysis_results = {
        "analysis_timestamp": datetime.now().isoformat(),
        "repository_path": repo_path
    }
    
    # 2. Repository Metadata
    print("Analyzing repository metadata...")
    repo_metadata = get_repository_metadata(repo)
    analysis_results["repository_metadata"] = repo_metadata
    
    # 3. Author Statistics
    print("Calculating author statistics...")
    author_stats = get_author_statistics(repo)
    analysis_results["author_statistics"] = author_stats
    
    # 4. Recent Activity Analysis (last 30 days)
    print("Analyzing recent activity...")
    recent_date = datetime.now() - timedelta(days=30)
    recent_commits = list(repo.iter_commits(since=recent_date))
    
    recent_activity = {
        "commits_last_30_days": len(recent_commits),
        "active_authors": len(set(commit.author.email for commit in recent_commits)),
        "files_changed": len(set(
            item.a_path or item.b_path 
            for commit in recent_commits 
            for item in commit.stats.files
        ))
    }
    analysis_results["recent_activity"] = recent_activity
    
    # 5. Branch Analysis
    print("Analyzing branches...")
    branches = list(repo.branches)
    branch_analysis = []
    
    for branch in branches[:5]:  # Analyze top 5 branches
        branch_info = {
            "name": branch.name,
            "commit_count": len(list(repo.iter_commits(branch))),
            "last_commit": {
                "hash": branch.commit.hexsha,
                "author": branch.commit.author.name,
                "date": branch.commit.committed_datetime.isoformat(),
                "message": branch.commit.message.strip()
            }
        }
        branch_analysis.append(branch_info)
    
    analysis_results["branch_analysis"] = branch_analysis
    
    # 6. Export Results
    print("Exporting results...")
    export_manager = ExportManager()
    
    # Export as JSON
    json_options = ExportOptions(
        format=OutputFormat.JSON,
        include_metadata=True
    )
    json_output = f"{repo_path.replace('/', '_')}_analysis.json"
    await export_manager.export_data(analysis_results, json_output, json_options)
    
    # Export as YAML
    yaml_options = ExportOptions(
        format=OutputFormat.YAML,
        include_metadata=True
    )
    yaml_output = f"{repo_path.replace('/', '_')}_analysis.yaml"
    await export_manager.export_data(analysis_results, yaml_output, yaml_options)
    
    print(f"Analysis complete! Results exported to:")
    print(f"  JSON: {json_output}")
    print(f"  YAML: {yaml_output}")
    
    return analysis_results

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python complete_analysis.py /path/to/repository")
        sys.exit(1)
    
    repo_path = sys.argv[1]
    asyncio.run(complete_repository_analysis(repo_path))
```

## CI/CD Integration Workflow

### GitHub Actions Integration
```yaml
# .github/workflows/githound-analysis.yml
name: GitHound Repository Analysis

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 2 * * 1'  # Weekly on Monday at 2 AM

jobs:
  analyze:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
      with:
        fetch-depth: 0  # Full history for analysis
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install GitHound
      run: |
        pip install githound
    
    - name: Run Repository Analysis
      run: |
        python examples/workflows/ci_cd_integration.py .
    
    - name: Upload Analysis Results
      uses: actions/upload-artifact@v3
      with:
        name: githound-analysis
        path: analysis_results/
```

### Jenkins Pipeline Integration
```groovy
pipeline {
    agent any
    
    triggers {
        cron('H 2 * * 1')  // Weekly analysis
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Setup') {
            steps {
                sh 'pip install githound'
            }
        }
        
        stage('Analysis') {
            steps {
                sh 'python examples/workflows/ci_cd_integration.py .'
            }
        }
        
        stage('Archive Results') {
            steps {
                archiveArtifacts artifacts: 'analysis_results/**/*'
                publishHTML([
                    allowMissing: false,
                    alwaysLinkToLastBuild: true,
                    keepAll: true,
                    reportDir: 'analysis_results',
                    reportFiles: 'index.html',
                    reportName: 'GitHound Analysis Report'
                ])
            }
        }
    }
}
```

## Automated Reporting Workflow

### Daily Report Generation
```python
#!/usr/bin/env python3
"""
Automated daily reporting workflow.
Generates comprehensive reports and sends them to stakeholders.
"""

import asyncio
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timedelta

async def generate_daily_report(repo_path: str, recipients: list):
    """Generate and send daily repository report."""
    
    # 1. Perform analysis
    analysis = await complete_repository_analysis(repo_path)
    
    # 2. Generate HTML report
    html_report = generate_html_report(analysis)
    
    # 3. Send email report
    await send_email_report(html_report, recipients)
    
    print("Daily report generated and sent successfully!")

def generate_html_report(analysis_data):
    """Generate HTML report from analysis data."""
    html = f"""
    <html>
    <head>
        <title>GitHound Daily Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ background-color: #f0f0f0; padding: 10px; }}
            .metric {{ margin: 10px 0; }}
            .highlight {{ color: #007acc; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>GitHound Repository Analysis Report</h1>
            <p>Generated: {analysis_data['analysis_timestamp']}</p>
            <p>Repository: {analysis_data['repository_path']}</p>
        </div>
        
        <h2>Repository Overview</h2>
        <div class="metric">
            Total Commits: <span class="highlight">{analysis_data['repository_metadata']['total_commits']}</span>
        </div>
        <div class="metric">
            Contributors: <span class="highlight">{len(analysis_data['repository_metadata']['contributors'])}</span>
        </div>
        
        <h2>Recent Activity (Last 30 Days)</h2>
        <div class="metric">
            New Commits: <span class="highlight">{analysis_data['recent_activity']['commits_last_30_days']}</span>
        </div>
        <div class="metric">
            Active Authors: <span class="highlight">{analysis_data['recent_activity']['active_authors']}</span>
        </div>
        
        <h2>Top Contributors</h2>
        <ul>
    """
    
    # Add top contributors
    for author, stats in list(analysis_data['author_statistics'].items())[:5]:
        html += f"<li>{author}: {stats.get('total_commits', 0)} commits</li>"
    
    html += """
        </ul>
    </body>
    </html>
    """
    
    return html
```

## Performance Monitoring Workflow

### Continuous Performance Analysis
```python
#!/usr/bin/env python3
"""
Performance monitoring workflow.
Tracks repository performance metrics over time.
"""

import asyncio
import time
from datetime import datetime
import sqlite3

class PerformanceMonitor:
    def __init__(self, db_path="performance_metrics.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize performance metrics database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                repository_path TEXT NOT NULL,
                operation TEXT NOT NULL,
                duration_seconds REAL NOT NULL,
                memory_usage_mb REAL,
                cpu_usage_percent REAL,
                success BOOLEAN NOT NULL
            )
        """)
        
        conn.commit()
        conn.close()
    
    async def monitor_operation(self, operation_name, operation_func, *args, **kwargs):
        """Monitor performance of a specific operation."""
        start_time = time.time()
        start_memory = self.get_memory_usage()
        
        try:
            result = await operation_func(*args, **kwargs)
            success = True
        except Exception as e:
            result = None
            success = False
            print(f"Operation {operation_name} failed: {e}")
        
        end_time = time.time()
        end_memory = self.get_memory_usage()
        
        duration = end_time - start_time
        memory_delta = end_memory - start_memory
        
        # Record metrics
        self.record_metrics(
            operation_name,
            duration,
            memory_delta,
            success
        )
        
        return result
    
    def get_memory_usage(self):
        """Get current memory usage in MB."""
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    
    def record_metrics(self, operation, duration, memory_usage, success):
        """Record performance metrics to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO performance_metrics 
            (timestamp, repository_path, operation, duration_seconds, memory_usage_mb, success)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            "current_repo",  # Would be dynamic in real usage
            operation,
            duration,
            memory_usage,
            success
        ))
        
        conn.commit()
        conn.close()
```

## Security Analysis Workflow

### Security-Focused Repository Analysis
```python
#!/usr/bin/env python3
"""
Security analysis workflow.
Focuses on security-related patterns and potential issues.
"""

import re
from pathlib import Path

class SecurityAnalyzer:
    def __init__(self):
        self.security_patterns = {
            'secrets': [
                r'password\s*=\s*["\'][^"\']+["\']',
                r'api_key\s*=\s*["\'][^"\']+["\']',
                r'secret\s*=\s*["\'][^"\']+["\']',
                r'token\s*=\s*["\'][^"\']+["\']'
            ],
            'vulnerabilities': [
                r'eval\s*\(',
                r'exec\s*\(',
                r'subprocess\.call\s*\(',
                r'os\.system\s*\('
            ]
        }
    
    async def analyze_security(self, repo_path: str):
        """Perform security-focused analysis."""
        repo = get_repository(Path(repo_path))
        
        security_issues = {
            'secrets_found': [],
            'vulnerabilities_found': [],
            'suspicious_commits': [],
            'large_files': []
        }
        
        # Analyze recent commits for security issues
        for commit in repo.iter_commits(max_count=100):
            commit_issues = self.analyze_commit_security(commit)
            if commit_issues:
                security_issues['suspicious_commits'].append({
                    'hash': commit.hexsha,
                    'author': commit.author.name,
                    'date': commit.committed_datetime.isoformat(),
                    'issues': commit_issues
                })
        
        return security_issues
    
    def analyze_commit_security(self, commit):
        """Analyze a single commit for security issues."""
        issues = []
        
        try:
            for item in commit.stats.files:
                if item.endswith(('.py', '.js', '.php', '.rb')):
                    # Analyze file content for security patterns
                    try:
                        file_content = commit.tree[item].data_stream.read().decode('utf-8')
                        file_issues = self.scan_file_content(file_content, item)
                        issues.extend(file_issues)
                    except:
                        pass  # Skip binary or problematic files
        except:
            pass  # Skip commits with issues
        
        return issues
    
    def scan_file_content(self, content, filename):
        """Scan file content for security patterns."""
        issues = []
        
        for category, patterns in self.security_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    issues.append({
                        'type': category,
                        'pattern': pattern,
                        'file': filename,
                        'line': content[:match.start()].count('\n') + 1,
                        'match': match.group()
                    })
        
        return issues
```
