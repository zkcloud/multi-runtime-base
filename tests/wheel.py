import base64
import hashlib
import io
import zipfile
import csv

files = {
    "smoke_pkg/__init__.py": b"def answer(): return 42\n",
    "smoke_pkg-1.0.dist-info/METADATA": b"Metadata-Version: 2.1\nName: smoke-pkg\nVersion: 1.0\n",
    "smoke_pkg-1.0.dist-info/WHEEL": b"Wheel-Version: 1.0\nGenerator: smoke\nRoot-Is-Purelib: true\nTag: py3-none-any\n",
}
record = io.StringIO()
writer = csv.writer(record)
for name, value in files.items():
    digest = base64.urlsafe_b64encode(hashlib.sha256(value).digest()).rstrip(b"=").decode()
    writer.writerow([name, "sha256=" + digest, len(value)])
writer.writerow(["smoke_pkg-1.0.dist-info/RECORD", "", ""])
files["smoke_pkg-1.0.dist-info/RECORD"] = record.getvalue().encode()
with zipfile.ZipFile("/tmp/smoke_pkg-1.0-py3-none-any.whl", "w") as wheel:
    for name, value in files.items():
        wheel.writestr(name, value)
