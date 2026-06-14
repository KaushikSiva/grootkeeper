from __future__ import annotations

import importlib
import sys
from pathlib import Path

from config import settings
from system_checks import LIKELY_GROOT_MODULES, check_groot_repo


def main() -> int:
    print(f"GROOT_REPO_DIR={settings.groot_repo_dir}")
    print(f"GROOT_CHECKPOINT={settings.groot_checkpoint}")

    repo_ok, repo_note = check_groot_repo()
    print(repo_note)
    if not repo_ok:
        print("Debug next: set GROOT_REPO_DIR correctly and clone Isaac-GR00T there.")
        return 1

    repo_dir = str(Path(settings.groot_repo_dir).expanduser())
    if repo_dir not in sys.path:
        sys.path.insert(0, repo_dir)

    import_errors: list[str] = []
    for module_name in LIKELY_GROOT_MODULES:
        try:
            importlib.import_module(module_name)
            print(f"Imported GR00T module candidate successfully: {module_name}")
            print("GR00T import smoke test passed.")
            return 0
        except Exception as exc:
            import_errors.append(f"{module_name}: {exc}")

    print("GR00T import smoke test failed.")
    print("Tried modules:")
    for error in import_errors:
        print(f"  - {error}")
    print("Debug next:")
    print("  1. Follow the official Isaac-GR00T install instructions exactly.")
    print("  2. Verify the Python interpreter matches the GR00T install environment.")
    print("  3. Confirm any editable installs or exported PYTHONPATH entries are active.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
