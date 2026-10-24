"""Check all ELF executables/shared objects, including dlopen-loaded JDK libraries."""
import os
import pathlib
import subprocess
import sys

failures = []
checked = 0
for root in ("/opt/java/openjdk", "/usr/local", "/usr/lib", "/usr/bin", "/bin", "/lib"):
    for parent, _, names in os.walk(root):
        for name in names:
            p = pathlib.Path(parent, name)
            try:
                with p.open("rb") as f:
                    if f.read(4) != b"\x7fELF":
                        continue
            except (OSError, PermissionError):
                continue
            # libjvm is resolved by the JVM loader relative to JAVA_HOME.
            env = dict(os.environ, LD_LIBRARY_PATH="/opt/java/openjdk/lib:/opt/java/openjdk/lib/server")
            r = subprocess.run(["ldd", str(p)], text=True, capture_output=True, env=env)
            checked += 1
            out = r.stdout + r.stderr
            if "not found" in out or (r.returncode and "not a dynamic executable" not in out and "statically linked" not in out):
                failures.append((str(p), out))
print(f"ELF objects checked: {checked}")
for path, output in failures:
    print(path, output)
if not checked:
    raise SystemExit("ERROR: no ELF objects checked")
sys.exit(bool(failures))
