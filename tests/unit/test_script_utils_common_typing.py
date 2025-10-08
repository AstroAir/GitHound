import types
import importlib.util
from pathlib import Path


def load_module_from_path(module_name: str, file_path: str):
    """Load a Python module directly from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


def test_import_scripts_script_utils_common_success():
    """
    This test verifies that scripts/script_utils/common.py can be imported successfully
    directly from its path. Before the fix, importing the module raises due to invalid
    typing imports. After the fix, import should succeed and basic functions should work.
    """
    file_path = str(Path("scripts/script_utils/common.py"))
    module = load_module_from_path("script_utils_common", file_path)
    assert isinstance(module, types.ModuleType)

    # Smoke-check a simple function to ensure module is usable
    assert module.format_bytes(1023) == "1023.0 B"
    assert module.format_bytes(1024) == "1.0 KB"