"""
Basic test script to verify the utility infrastructure works.
This script uses only standard library modules.
"""

import sys
from pathlib import Path

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent))


def test_utils_import() -> None:
    """Test that utils can be imported."""
    try:
        from utils.common import check_python_version, get_project_root
        from utils.platform import get_platform_info, is_windows

        print("✅ Utils modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import utils: {e}")
        return False


def test_project_root() -> None:
    """Test project root detection."""
    try:
        from utils.common import get_project_root

        root = get_project_root()
        print(f"✅ Project root detected: {root}")

        # Check if pyproject.toml exists
        if (root / "pyproject.toml").exists():
            print("✅ pyproject.toml found")
        else:
            print("❌ pyproject.toml not found")

        return True
    except Exception as e:
        print(f"❌ Project root detection failed: {e}")
        return False


def test_platform_detection() -> None:
    """Test platform detection."""
    try:
        from utils.platform import get_platform_info, is_windows

        print("✅ Platform detection works")
        print(f"   Windows: {is_windows()}")

        info = get_platform_info()
        print(f"   System: {info.get('system', 'unknown')}")
        print(f"   Python: {info.get('python_version', 'unknown')}")

        return True
    except Exception as e:
        print(f"❌ Platform detection failed: {e}")
        return False


def test_python_version() -> None:
    """Test Python version check."""
    try:
        from utils.common import check_python_version

        # Test current version (should pass)
        current_ok = check_python_version((3, 8))
        print(f"✅ Python version check: {current_ok}")

        # Test impossible version (should fail)
        future_ok = check_python_version((4, 0))
        print(f"✅ Future version check (should be False): {future_ok}")

        return True
    except Exception as e:
        print(f"❌ Python version check failed: {e}")
        return False


def main() -> None:
    """Run basic tests."""
    print("🧪 GitHound Utility Scripts - Basic Test")
    print("=" * 50)

    tests = [
        ("Utils Import", test_utils_import),
        ("Project Root", test_project_root),
        ("Platform Detection", test_platform_detection),
        ("Python Version Check", test_python_version),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n📋 Testing: {test_name}")
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")

    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All basic tests passed! The utility infrastructure is working.")
        print("\n💡 Next steps:")
        print("   1. Install dependencies: pip install typer rich")
        print("   2. Run full setup: python scripts/quick-start.py setup")
        print("   3. Test services: python scripts/services.py status")
        return 0
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
