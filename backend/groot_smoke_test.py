try:
    from .config import settings
    from .groot_client import get_groot_status, groot_available
except ImportError:
    from config import settings
    from groot_client import get_groot_status, groot_available


def main() -> int:
    print(f"GROOT_REPO_DIR={settings.groot_repo_dir}")
    print(f"GROOT_CHECKPOINT={settings.groot_checkpoint}")
    print(
        f"GROOT_SERVER=tcp://{settings.groot_server_host}:{settings.groot_server_port}"
    )

    available, note = groot_available()
    print(note)
    if available:
        print("GR00T policy server smoke test passed.")
        print(get_groot_status())
        return 0

    print("GR00T policy server smoke test failed.")
    print("Debug next:")
    print("  1. Start ./scripts/08a_run_groot_policy_server.sh on the GB10.")
    print("  2. Confirm the server embodiment tag matches your checkpoint or modality config.")
    print("  3. Re-run ./scripts/09_test_backend_status.sh and verify groot_server_ok=true.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
