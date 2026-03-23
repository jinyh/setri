"""Pydantic 数据模型"""

from datetime import date, datetime

from pydantic import BaseModel, Field


# ─── P1 规范库模型 ───


class ScanHit(BaseModel):
    """单个关键词命中"""
    keyword: str
    page: int
    position: int
    context: str


class ScanResult(BaseModel):
    """单个 PDF 的扫描结果"""
    file: str
    path: str
    total_chars: int = 0
    is_image_only: bool = False
    total_hits: int = 0
    hit_pages: list[int] = Field(default_factory=list)
    keyword_counts: dict[str, int] = Field(default_factory=dict)
    hits: list[ScanHit] = Field(default_factory=list)
    error: str | None = None


class Source(BaseModel):
    """规范来源"""
    source_id: str
    standard_id: str = ""
    standard_name: str = ""
    year: int = 0
    pdf_filename: str = ""


class Clause(BaseModel):
    """规范条款"""
    clause_id: str
    source_id: str
    source_clause_ref: str = ""
    category_id: str = ""
    subject: str = ""
    text: str
    strength: str = ""
    domain_tags: dict[str, str] = Field(default_factory=dict)
    page: int = 0


class Category(BaseModel):
    """条款分类"""
    id: str
    name: str
    description: str = ""


class ConflictResolution(BaseModel):
    """冲突裁决"""
    effective_clause_id: str = ""
    effective_source: str = ""
    rationale: str = ""


class Conflict(BaseModel):
    """冲突记录"""
    conflict_id: str
    category_id: str = ""
    subject: str = ""
    involved_clauses: list[str] = Field(default_factory=list)
    description: str = ""
    resolution: ConflictResolution | None = None


class RegulationsOutput(BaseModel):
    """P1 最终输出"""

    class Metadata(BaseModel):
        subject: str
        slug: str
        keywords: list[str] = Field(default_factory=list)
        generated_at: str = Field(default_factory=lambda: date.today().isoformat())
        total_clauses: int = 0
        total_conflicts: int = 0
        sources_count: int = 0

    metadata: Metadata
    sources: list[Source] = Field(default_factory=list)
    categories: list[Category] = Field(default_factory=list)
    clauses: list[Clause] = Field(default_factory=list)
    conflicts: list[Conflict] = Field(default_factory=list)


# ─── P2 文件整理模型 ───


class FileMapping(BaseModel):
    """单条文件映射"""
    source: str  # 源路径（相对于项目测试数据）
    target: str  # 目标路径（相对于 data/projects/{project_id}）
    file_count: int = 0
    note: str = ""  # [未匹配] / [歧义] / [跳过]


class ProjectMeta(BaseModel):
    """项目元数据"""
    project_id: str
    project_name: str
    short_name: str
    imported_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    source_paths: dict[str, str] = Field(default_factory=dict)
    file_type_filter: list[str] = Field(
        default_factory=lambda: ["pdf", "xlsx", "xls", "docx", "doc", "pptx", "ofd"]
    )
    path_mapping: list[FileMapping] = Field(default_factory=list)
