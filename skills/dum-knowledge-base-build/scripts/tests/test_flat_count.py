import importlib.util
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "update_docs_index.py"


def _load():
    spec = importlib.util.spec_from_file_location("udi", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_flat_count_excludes_readme_and_subdirs():
    mod = _load()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        td = root / "tech-design"
        (td / "auth").mkdir(parents=True)
        (td / "README.md").write_text("# x", encoding="utf-8")
        (td / "auth" / "20260101-A.md").write_text("# a", encoding="utf-8")
        for i in range(3):
            (td / f"2026010{i}-flat.md").write_text("# f", encoding="utf-8")
        mod.DOCS_ROOT = root
        assert mod.flat_count("tech-design") == 3  # README + 子目录文件不计


def test_banner_appears_over_threshold():
    mod = _load()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        td = root / "tech-design"
        td.mkdir(parents=True)
        for i in range(20):
            (td / f"202601{i:02d}-x.md").write_text("# x", encoding="utf-8")
        mod.DOCS_ROOT = root
        mod.SUBDIR_THRESHOLDS = {"tech-design": 20}
        text = mod.build_index_text()
        assert "⚠️" in text and "tech-design" in text and "20" in text
