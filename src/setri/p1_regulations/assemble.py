"""P1 规范库 — 输出组装

对 .claude/skills/reg-extractor/scripts/assemble_output.py 的封装。
"""

import sys
from pathlib import Path

_scripts_dir = str(Path(__file__).resolve().parent.parent.parent.parent / ".claude" / "skills" / "reg-extractor" / "scripts")
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

from assemble_output import assemble, validate_references  # noqa: E402


def assemble_regulations(
    input_dir: str | Path,
    subject: str,
    slug: str,
    keywords: str = "",
) -> tuple[dict, list[str]]:
    """组装 regulations.json 并校验。

    Args:
        input_dir: 中间文件目录
        subject: 专题名称
        slug: 输出目录名
        keywords: 逗号分隔的关键词

    Returns:
        (regulations_dict, validation_errors)
    """
    result = assemble(str(input_dir), subject, slug, keywords)
    errors = validate_references(result)
    return result, errors
