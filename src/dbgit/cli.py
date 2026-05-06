"""명령줄에서 프로시저/함수 환경 비교."""

from __future__ import annotations

import argparse
import os
import sys
from typing import List

from dotenv import load_dotenv

from .compare import compare_across_envs
from .config import load_env_configs
from .constants import DEFAULT_ENVS
from .logging_setup import configure_logging
from .output_format import OutputFormat, format_proc_comparison


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="환경별 프로시저/함수 정의 차이를 확인합니다.",
    )
    parser.add_argument(
        "proc",
        help="프로시저/함수 object_id 또는 이름 (schema.name 권장)",
    )
    parser.add_argument(
        "--envs",
        default=",".join(DEFAULT_ENVS),
        help=f"비교할 환경 목록 (콤마 구분, 기본: {','.join(DEFAULT_ENVS)})",
    )
    parser.add_argument(
        "--baseline",
        default="PRD",
        help="기준 환경 (기본: PRD)",
    )
    parser.add_argument(
        "--dotenv",
        default=".env",
        help="환경변수 파일 경로 (기본: .env)",
    )
    parser.add_argument(
        "--output",
        "-o",
        choices=("text", "json", "markdown"),
        default="text",
        help="출력 형식 (기본: text)",
    )
    return parser


def main(argv: List[str] | None = None) -> int:
    configure_logging()
    parser = _build_parser()
    args = parser.parse_args(argv)

    if os.path.exists(args.dotenv):
        load_dotenv(args.dotenv)

    env_list = [item.strip().upper() for item in args.envs.split(",") if item.strip()]
    baseline = args.baseline.strip().upper()
    if baseline not in env_list:
        parser.error("baseline 환경이 envs 목록에 포함되어야 합니다.")

    try:
        configs = load_env_configs(env_list)
        definitions = compare_across_envs(configs, args.proc)
    except Exception as exc:
        print(f"오류: {exc}", file=sys.stderr)
        return 1

    out: OutputFormat = args.output
    text = format_proc_comparison(baseline, definitions, out)
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
