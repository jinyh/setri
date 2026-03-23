"""P1 规范库 — 分类归纳（LLM）

阶段 B 实现。当前为占位模块。
"""


async def classify_clauses(clauses: list[dict], *, llm=None) -> tuple[list[dict], list[dict]]:
    """对条款进行分类归纳（需要 LLM）。

    Returns:
        (categories, updated_clauses)
    """
    raise NotImplementedError("阶段 B 实现：LLM 分类归纳")
