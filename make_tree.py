"""
ساختار درختی تمیز پروژه را در فایل خروجی می‌نویسد.
اجرا: python make_tree.py
      python make_tree.py 4        # با عمق دلخواه
خروجی: project_tree.txt در ریشه‌ی پروژه
"""
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "project_tree.txt")

EXCLUDE_DIRS = {
    "__pycache__", ".git", ".venv", "venv", "env",
    "node_modules", ".pytest_cache", ".mypy_cache",
    ".ruff_cache", ".idea",
}
EXCLUDE_FILES_EXT = {".pyc", ".pyo", ".log"}

# پوشه‌هایی که می‌خواهیم کلاً نادیده گرفته شوند (بزرگ / بی‌ربط به ساختار)
SKIP_SUBTREES = {
    "logs",
    os.path.join("data", "backups"),
    "سوابق کد",
}


def _is_skipped_subtree(rel_path: str) -> bool:
    """بررسی می‌کند آیا مسیر نسبی داخل یکی از SKIP_SUBTREES است."""
    rel_path = rel_path.replace("\\", "/")
    for skip in SKIP_SUBTREES:
        skip_norm = skip.replace("\\", "/")
        if rel_path == skip_norm or rel_path.startswith(skip_norm + "/"):
            return True
    return False


def _should_skip_dir(name: str) -> bool:
    return name in EXCLUDE_DIRS


def _should_skip_file(name: str) -> bool:
    _, ext = os.path.splitext(name)
    return ext.lower() in EXCLUDE_FILES_EXT


def write_tree(root: str, rel_root: str, prefix: str, fh,
               max_depth: int, depth: int = 0) -> None:
    if depth > max_depth:
        return

    try:
        entries = sorted(os.listdir(root))
    except PermissionError:
        return

    # جدا کردن دایرکتوری‌ها و فایل‌ها با فیلترهای شفاف
    dirs = []
    files = []
    for name in entries:
        full = os.path.join(root, name)
        rel = os.path.join(rel_root, name) if rel_root else name

        if os.path.isdir(full):
            if _should_skip_dir(name):
                continue
            if _is_skipped_subtree(rel):
                continue
            dirs.append((name, full, rel))
        else:
            if _should_skip_file(name):
                continue
            files.append(name)

    all_items = dirs + [(f, None, None) for f in files]

    for i, item in enumerate(all_items):
        is_last = (i == len(all_items) - 1)
        connector = "└── " if is_last else "├── "
        name = item[0]
        fh.write(prefix + connector + name + "\n")

        if item[1] is not None:  # دایرکتوری
            extension = "    " if is_last else "│   "
            write_tree(item[1], item[2], prefix + extension, fh,
                       max_depth, depth + 1)


def main() -> None:
    max_depth = 6
    if len(sys.argv) > 1:
        try:
            max_depth = int(sys.argv[1])
        except ValueError:
            pass

    with open(OUTPUT_FILE, "w", encoding="utf-8") as fh:
        fh.write(f"# ساختار درختی پروژه (max_depth={max_depth})\n")
        fh.write("# پوشه‌های حذف‌شده: logs, data/backups, سوابق کد\n")
        fh.write(".\n")
        write_tree(PROJECT_ROOT, "", "", fh, max_depth)

    print(f"✓ خروجی در: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()