"""P1 规范库 — 冲突检测

对 .claude/skills/reg-extractor/scripts/detect_conflicts.py 的封装。
纯 Python 预筛部分直接复用，LLM 语义裁决部分预留接口。
"""

import sys
from pathlib import Path

_scripts_dir = str(Path(__file__).resolve().parent.parent.parent.parent / ".claude" / "skills" / "reg-extractor" / "scripts")
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

from detect_conflicts import (  # noqa: E402
    STRENGTH_LEVELS,
    detect_conflicts,
    extract_numbers,
    extract_strengths,
    numbers_differ,
    strengths_differ,
)


def pre_screen(clauses: list[dict]) -> dict:
    """预筛候选冲突（纯 Python，无 LLM）。

    Args:
        clauses: 条款列表（需包含 clause_id, source_id, category_id, text, strength）

    Returns:
        {
            "total_clauses": N,
            "total_candidates": M,
            "candidates": [...]
        }
    """
    candidates = detect_conflicts(clauses)
    return {
        "total_clauses": len(clauses),
        "total_candidates": len(candidates),
        "candidates": candidates,
    }


# LLM 语义裁决接口（阶段 B 实现）
async def resolve_conflicts(candidates: list[dict], clauses: list[dict], *, llm=None) -> list[dict]:
    """对候选冲突进行语义裁决（需要 LLM）。

    Args:
        candidates: pre_screen 输出的候选冲突
        clauses: 完整条款列表（用于回溯原文上下文）
        llm: BaseLLM 实例

    Returns:
        裁决后的冲突列表
    """
    raise NotImplementedError("阶段 B 实现：LLM 语义裁决")
