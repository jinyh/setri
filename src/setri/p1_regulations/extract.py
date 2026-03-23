"""P1 规范库 — 条款提取（LLM）

阶段 B 实现。当前为占位模块。
"""


async def extract_clauses(pdf_path: str, scan_result: dict, *, llm=None) -> list[dict]:
    """从 PDF 中提取结构化条款（需要 LLM）。"""
    raise NotImplementedError("阶段 B 实现：LLM 条款提取")
