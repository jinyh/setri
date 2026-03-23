"""全局配置"""

import os
from enum import Enum
from pathlib import Path

# 项目根目录（pyproject.toml 所在位置）
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# 数据目录
DATA_DIR = PROJECT_ROOT / "data"
REGULATIONS_DIR = DATA_DIR / "regulations"
PROJECTS_DIR = DATA_DIR / "projects"

# 源数据目录
SPECS_DIR = PROJECT_ROOT / "技术规范文件"
TEST_DATA_DIR = PROJECT_ROOT / "项目测试数据"

# Skills 脚本目录（复用现有脚本）
SKILLS_DIR = PROJECT_ROOT / ".claude" / "skills"
REG_SCRIPTS_DIR = SKILLS_DIR / "reg-extractor" / "scripts"


class LLMProvider(str, Enum):
    CLAUDE = "claude"
    GEMINI = "gemini"
    QWEN = "qwen"


# LLM 配置
LLM_PROVIDER = LLMProvider(os.getenv("SETRI_LLM_PROVIDER", "claude"))
LLM_API_KEY = os.getenv("SETRI_LLM_API_KEY", "")
LLM_MODEL = os.getenv("SETRI_LLM_MODEL", "claude-sonnet-4-20250514")

# 文件类型过滤
INCLUDE_EXTENSIONS = {".pdf", ".xlsx", ".xls", ".docx", ".doc", ".pptx", ".ofd"}
EXCLUDE_EXTENSIONS = {".bdd3", ".bpz17", ".DS_Store", ".db", ".tmp"}
EXCLUDE_PATTERNS = {"工程估算书(软件版)"}
