"""环境检查 + 依赖安装提示"""

import importlib
import sys

REQUIRED = {
    "xlrd": "xlrd",
    "pdfplumber": "pdfplumber",
    "openpyxl": "openpyxl",
}


def check_dependencies():
    missing = []
    for module_name, pip_name in REQUIRED.items():
        try:
            importlib.import_module(module_name)
            print(f"  ✓ {module_name}")
        except ImportError:
            print(f"  ✗ {module_name} — 未安装")
            missing.append(pip_name)

    if missing:
        print(f"\n缺少依赖，请运行：")
        print(f"  pip install {' '.join(missing)}")
        return False

    print("\n所有依赖已就绪。")
    return True


def check_python_version():
    v = sys.version_info
    print(f"Python 版本: {v.major}.{v.minor}.{v.micro}")
    if v.major < 3 or (v.major == 3 and v.minor < 8):
        print("  ✗ 需要 Python 3.8+")
        return False
    print("  ✓ 版本满足要求")
    return True


def main():
    print("=" * 40)
    print("Co-Reviewer 环境检查")
    print("=" * 40)

    print("\n[1/2] Python 版本检查")
    py_ok = check_python_version()

    print("\n[2/2] 依赖检查")
    dep_ok = check_dependencies()

    if py_ok and dep_ok:
        print("\n✓ 环境检查全部通过")
        sys.exit(0)
    else:
        print("\n✗ 环境检查未通过，请修复上述问题")
        sys.exit(1)


if __name__ == "__main__":
    main()
