import importlib.util
import sys
from pathlib import Path
import types


def load_module_from_path(module_name: str, file_path: str):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


def test_run_mcp_tests_import_and_coverage_returncode(checker=True):
    """
    Verifies scripts/run_mcp_tests.py imports successfully.
    Then ensures run_coverage_report returns an int and does not crash.
    Prior to the fix, import failed due to 'Optionalny' typo and 'result.returncode = = 0'.
    """
    path = str(Path("scripts/run_mcp_tests.py"))
    module = load_module_from_path("run_mcp_tests_module", path)
    assert isinstance(module, types.ModuleType)

    runner = module.MCPTestRunner()
    # We don't actually run pytest here; ensure method can be invoked and returns an int.
    # The subprocess call will execute; we accept any return code, focus on no SyntaxError.
    rc = runner.run_coverage_report()
    assert isinstance(rc, int)