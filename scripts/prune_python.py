"""Remove only bytecode with an existing source file; keep sourceless modules."""
import importlib.util
import pathlib

count = size = 0
for root in (pathlib.Path("/usr/lib/python3.12"), pathlib.Path("/usr/lib/python3/dist-packages")):
    for path in root.rglob("*.pyc"):
        if not path.is_file():
            continue
        try:
            source = pathlib.Path(importlib.util.source_from_cache(str(path)))
        except ValueError:
            source = path.with_suffix(".py")
        if source.is_file():
            size += path.stat().st_size
            path.unlink()
            count += 1
print(f"Removed regenerable Python bytecode: files={count}, bytes={size}")
