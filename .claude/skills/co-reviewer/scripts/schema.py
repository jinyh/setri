"""Co-Reviewer 三元关联数据结构定义"""

from dataclasses import dataclass, field, asdict
from typing import Optional
import json


@dataclass
class Opinion:
    """专家意见"""
    text: str
    type: str = ""          # 材料选型|工程量|技术标准|造价|形式审查
    severity: str = "info"  # error|warning|info
    review_stage: str = ""  # 预审|正式评审|收口评审
    expert_name: str = ""
    expert_role: str = ""


@dataclass
class DocumentRef:
    """设计文件引用"""
    file: str = ""
    page: int = 0
    section: str = ""
    snippet: str = ""
    doc_type: str = ""  # 初设报告|设计图纸|工程概算书


@dataclass
class RegulationRef:
    """规范引用"""
    standard_id: str = ""
    standard_name: str = ""
    clause: str = ""
    text: str = ""
    category: str = ""  # 政策类|管理类|技术类


@dataclass
class Metadata:
    """标注元数据"""
    confidence: float = 0.0
    confidence_doc: float = 0.0
    confidence_reg: float = 0.0
    source: str = "ai_draft"  # seed|ai_draft|reviewed
    notes: str = ""


@dataclass
class Annotation:
    """三元关联标注记录"""
    project_id: str
    opinion_id: str
    opinion: Opinion
    document: DocumentRef = field(default_factory=DocumentRef)
    regulation: RegulationRef = field(default_factory=RegulationRef)
    metadata: Metadata = field(default_factory=Metadata)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Annotation":
        return cls(
            project_id=d["project_id"],
            opinion_id=d["opinion_id"],
            opinion=Opinion(**d["opinion"]),
            document=DocumentRef(**d.get("document", {})),
            regulation=RegulationRef(**d.get("regulation", {})),
            metadata=Metadata(**d.get("metadata", {})),
        )


@dataclass
class AnnotationSet:
    """一个项目的完整标注集"""
    project_id: str
    project_name: str = ""
    annotations: list = field(default_factory=list)  # List[Annotation]

    def to_json(self, path: str):
        data = {
            "project_id": self.project_id,
            "project_name": self.project_name,
            "total": len(self.annotations),
            "annotations": [a.to_dict() for a in self.annotations],
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, path: str) -> "AnnotationSet":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        annotations = [Annotation.from_dict(a) for a in data.get("annotations", [])]
        return cls(
            project_id=data["project_id"],
            project_name=data.get("project_name", ""),
            annotations=annotations,
        )
