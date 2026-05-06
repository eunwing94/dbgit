"""프로시저/함수 정의 문자열에 대한 공백 무시 줄 단위 diff (Streamlit 비의존)."""

from __future__ import annotations

import difflib
import re
from typing import List, Tuple

ComparableLine = Tuple[int, str, str]  # (원본 줄번호, 원문, 공백 제거)


def build_comparable_lines(definition: str) -> List[ComparableLine]:
    """빈 줄·공백만 있는 줄은 비교에서 제외."""
    lines: List[ComparableLine] = []
    for idx, line in enumerate(definition.splitlines(), start=1):
        normalized = re.sub(r"\s+", "", line)
        if not normalized:
            continue
        lines.append((idx, line, normalized))
    return lines


def format_line_range(lines: List[ComparableLine]) -> str:
    if not lines:
        return "-"
    start = lines[0][0]
    end = lines[-1][0]
    if start == end:
        return f"L{start}"
    return f"L{start}-L{end}"


def _format_chunk(header: str, lines: List[ComparableLine]) -> List[str]:
    output = [header]
    if not lines:
        output.append("(없음)")
        return output
    for line_no, text, _ in lines:
        output.append(f"L{line_no}: {text}")
    return output


def build_diff_text(
    base_lines: List[ComparableLine],
    env_lines: List[ComparableLine],
) -> tuple[str, str]:
    """정규화 줄 기준 SequenceMatcher. 반환: (기준측, 비교측) 텍스트."""
    base_norm = [item[2] for item in base_lines]
    env_norm = [item[2] for item in env_lines]
    matcher = difflib.SequenceMatcher(a=base_norm, b=env_norm, autojunk=False)

    base_out: List[str] = []
    env_out: List[str] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        base_chunk = base_lines[i1:i2]
        env_chunk = env_lines[j1:j2]
        header = (
            f"[{tag}] base {format_line_range(base_chunk)} | env {format_line_range(env_chunk)}"
        )
        base_out.extend(_format_chunk(header, base_chunk))
        env_out.extend(_format_chunk(header, env_chunk))
        base_out.append("")
        env_out.append("")

    return "\n".join(base_out).strip(), "\n".join(env_out).strip()
