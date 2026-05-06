"""`python -m dbgit` 실행 시 CLI 진입점."""

from .cli import main


if __name__ == "__main__":
    raise SystemExit(main())
