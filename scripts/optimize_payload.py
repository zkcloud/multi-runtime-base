"""Minimize payload while retaining every JDK module, tool, header and JMOD entry."""
import hashlib
import io
import json
import pathlib
import shutil
import subprocess
import sys
import zipfile

java, node = map(pathlib.Path, sys.argv[1:3])
strip_node = sys.argv[3] == "1"
report_dir = java.parent / "optimization"
report_dir.mkdir(exist_ok=True)
def run(*args):
    return subprocess.check_output([str(a) for a in args], text=True)
def size(root):
    return sum(p.stat().st_size for p in root.rglob("*") if p.is_file() and not p.is_symlink())
def modules(binary):
    return sorted(run(binary, "--list-modules").splitlines())

before = {"java": size(java), "node": size(node)}
expected = modules(java / "bin/java")
# Use the exact vendor/version JMODs and preserve all modules, including JDK tools.
linked = pathlib.Path("/tmp/linked-jdk")
subprocess.run([str(java / "bin/jlink"), "--module-path", str(java / "jmods"),
                "--add-modules", "ALL-MODULE-PATH", "--compress=zip-9",
                "--output", str(linked)], check=True)
assert modules(linked / "bin/java") == expected, "jlink lost a JDK module"
# Only the runtime resource image changes; vendor native libraries, tools and headers stay.
shutil.copyfile(linked / "lib/modules", java / "lib/modules")
subprocess.run([str(java / "bin/jimage"), "verify", str(java / "lib/modules")], check=True)
assert modules(java / "bin/java") == expected

jmods_before = jmods_after = entries = 0
for path in sorted((java / "jmods").glob("*.jmod")):
    original = path.read_bytes()
    assert original[:4] == b"JM\x01\x00", f"Unexpected JMOD header: {path}"
    archive = io.BytesIO()
    digests = {}
    with zipfile.ZipFile(path) as src, zipfile.ZipFile(archive, "w",
            compression=zipfile.ZIP_DEFLATED, compresslevel=9) as dst:
        for info in src.infolist():
            data = src.read(info)
            digests[info.filename] = hashlib.sha256(data).hexdigest()
            dst.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    compressed = original[:4] + archive.getvalue()
    if len(compressed) < len(original):
        path.write_bytes(compressed)
    # Verify full decompressed payload, not just archive filenames or CRC.
    with zipfile.ZipFile(path) as check:
        assert {i.filename: hashlib.sha256(check.read(i)).hexdigest()
                for i in check.infolist()} == digests
    subprocess.run([str(java / "bin/jmod"), "describe", str(path)],
                   check=True, stdout=subprocess.DEVNULL)
    jmods_before += len(original)
    jmods_after += path.stat().st_size
    entries += len(digests)

# Pre-generated CDS archives depend on the original module image.
# CDS remains available: users can regenerate an archive with java -Xshare:dump.
cds_bytes = 0
for path in (java / "lib").rglob("*.jsa"):
    cds_bytes += path.stat().st_size
    path.unlink()
# Node's dynamic exports remain; optional native symbol table/debugging tradeoff.
node_binary = node / "bin/node"
if strip_node:
    before_exports = run("nm", "-D", "--defined-only", node_binary)
    subprocess.run(["strip", "--strip-unneeded", str(node_binary)], check=True)
    assert run("nm", "-D", "--defined-only", node_binary) == before_exports
    assert run(node_binary, "--version").startswith("v24.")
after = {"java": size(java), "node": size(node)}
report = {"before_bytes": before, "after_bytes": after,
          "node_native_symbols_stripped": strip_node,
          "jdk_modules": expected, "jdk_module_count": len(expected),
          "jmod_entries_sha256_verified": entries,
          "jmods_before_bytes": jmods_before, "jmods_after_bytes": jmods_after,
          "regenerable_cds_removed_bytes": cds_bytes}
(report_dir / "payload.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report))
shutil.rmtree(linked)
