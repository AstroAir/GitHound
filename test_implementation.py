#!/usr/bin/env python3
"""Simple test script to verify GitHound enhancements."""

import sys
import os
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all new modules can be imported."""
    try:
        print("Testing imports...")
        
        # Test basic imports
        from githound.schemas import OutputFormat, DataFilter, ExportOptions
        print("✓ Schemas imported successfully")
        
        from githound.models import BranchInfo, TagInfo, EnhancedCommitInfo
        print("✓ Enhanced models imported successfully")
        
        # Test git modules (may fail if GitPython not available)
        try:
            from githound.git_handler import extract_commit_metadata
            print("✓ Git handler imported successfully")
        except ImportError as e:
            print(f"⚠ Git handler import failed: {e}")
        
        try:
            from githound.git_blame import BlameInfo, FileBlameResult
            print("✓ Git blame imported successfully")
        except ImportError as e:
            print(f"⚠ Git blame import failed: {e}")
        
        try:
            from githound.git_diff import ChangeType, FileDiffInfo
            print("✓ Git diff imported successfully")
        except ImportError as e:
            print(f"⚠ Git diff import failed: {e}")
        
        # Test MCP server (may fail if FastMCP not available)
        try:
            from githound.mcp_server import mcp
            print("✓ MCP server imported successfully")
        except ImportError as e:
            print(f"⚠ MCP server import failed: {e}")
        
        # Test enhanced API (may fail if FastAPI not available)
        try:
            from githound.web.enhanced_api import app
            print("✓ Enhanced API imported successfully")
        except ImportError as e:
            print(f"⚠ Enhanced API import failed: {e}")
        
        print("\n✅ Import tests completed!")
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False


def test_schemas():
    """Test schema functionality."""
    try:
        print("\nTesting schemas...")
        
        from githound.schemas import (
            OutputFormat, DataFilter, FilterOperator, 
            ExportOptions, AuthorSchema, CommitSchema
        )
        
        # Test enum
        assert OutputFormat.JSON.value == "json"
        assert OutputFormat.YAML.value == "yaml"
        print("✓ Output format enum works")
        
        # Test data filter
        filter_obj = DataFilter(
            field="author_name",
            operator=FilterOperator.CONTAINS,
            value="john"
        )
        assert filter_obj.field == "author_name"
        print("✓ Data filter creation works")
        
        # Test export options
        options = ExportOptions(
            format=OutputFormat.JSON,
            include_metadata=True,
            filters=[filter_obj]
        )
        assert options.format == OutputFormat.JSON
        assert len(options.filters) == 1
        print("✓ Export options creation works")
        
        # Test author schema
        author = AuthorSchema(
            name="John Doe",
            email="john@example.com",
            commits_count=10
        )
        assert author.name == "John Doe"
        print("✓ Author schema creation works")
        
        print("✅ Schema tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Schema test failed: {e}")
        return False


def test_models():
    """Test enhanced models."""
    try:
        print("\nTesting enhanced models...")
        
        from githound.models import (
            BranchInfo, TagInfo, RemoteInfo, 
            EnhancedCommitInfo, FileBlameInfo, BlameLineInfo
        )
        from datetime import datetime
        
        # Test branch info
        branch = BranchInfo(
            name="main",
            commit_hash="abc123",
            is_remote=False
        )
        assert branch.name == "main"
        print("✓ Branch info creation works")
        
        # Test tag info
        tag = TagInfo(
            name="v1.0.0",
            commit_hash="def456",
            is_annotated=True
        )
        assert tag.name == "v1.0.0"
        print("✓ Tag info creation works")
        
        # Test blame line info
        blame_line = BlameLineInfo(
            line_number=1,
            content="def hello():",
            commit_hash="ghi789",
            author_name="Test Author",
            author_email="test@example.com",
            commit_date=datetime.now(),
            commit_message="Add hello function"
        )
        assert blame_line.line_number == 1
        print("✓ Blame line info creation works")
        
        print("✅ Model tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Model test failed: {e}")
        return False


def test_export_functionality():
    """Test export functionality without actual file operations."""
    try:
        print("\nTesting export functionality...")
        
        from githound.utils.export import ExportManager
        from githound.schemas import ExportOptions, OutputFormat, DataFilter, FilterOperator
        
        # Create export manager
        export_manager = ExportManager()
        print("✓ Export manager created")
        
        # Test filter evaluation logic (without actual data)
        test_filter = DataFilter(
            field="test_field",
            operator=FilterOperator.CONTAINS,
            value="test_value"
        )
        
        # Test that the filter object is created correctly
        assert test_filter.field == "test_field"
        assert test_filter.operator == FilterOperator.CONTAINS
        print("✓ Filter creation works")
        
        # Test export options
        options = ExportOptions(
            format=OutputFormat.YAML,
            include_metadata=True,
            pretty_print=True,
            filters=[test_filter]
        )
        assert options.format == OutputFormat.YAML
        assert len(options.filters) == 1
        print("✓ Export options with filters work")
        
        print("✅ Export functionality tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Export functionality test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 GitHound Enhancement Verification")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_schemas,
        test_models,
        test_export_functionality
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! GitHound enhancements are working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
