from __future__ import annotations

import argparse
import os
import sys
from typing import Dict, List

from dotenv import load_dotenv

from .compare import compare_across_envs
from .services.env import load_env_configs


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
        default="PRD,STG,DEV,QA",
        help="비교할 환경 목록 (콤마 구분, 기본: PRD,STG,DEV,QA)",
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
    return parser


def _format_result(baseline: str, definitions: Dict[str, object]) -> str:
    lines: List[str] = []
    base_def = definitions[baseline]
    lines.append(f"기준 환경: {baseline} ({base_def.full_name})")
    lines.append("")
    lines.append("환경별 결과:")
    for env_name, proc_def in definitions.items():
        marker = "SAME" if proc_def.digest == base_def.digest else "DIFF"
        lines.append(f"- {env_name}: {marker} (object_id={proc_def.object_id})")
    lines.append("")

    diff_envs = [
        env_name for env_name, proc_def in definitions.items()
        if proc_def.digest != base_def.digest
    ]
    if diff_envs:
        lines.append("차이나는 환경:")
        lines.append(", ".join(diff_envs))
    else:
        lines.append("모든 환경이 동일합니다.")

    return "\n".join(lines)


def main(argv: List[str] | None = None) -> int:
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

    print(_format_result(baseline, definitions))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
