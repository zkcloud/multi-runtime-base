"""Compare Docker's uncompressed image content size in bytes. Never estimate."""
import json
import subprocess
import sys
import datetime

variant, arch = sys.argv[1:3]
def inspect(tag):
    return json.loads(subprocess.check_output(["docker", "image", "inspect", tag]))[0]
before = inspect("local/" + variant + ":baseline")
after = inspect("local/" + variant + ":test")
report = {
    "variant": variant, "architecture": arch,
    "measured_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "commit": __import__("os").environ.get("GITHUB_SHA", "local"),
    "metric": "docker image inspect .Size (uncompressed image content bytes)",
    "baseline_bytes": before["Size"], "optimized_bytes": after["Size"],
    "saved_bytes": before["Size"] - after["Size"],
    "saved_percent": round((before["Size"]-after["Size"])*100/before["Size"], 3),
    "baseline_id": before["Id"], "optimized_id": after["Id"],
    "compressed_registry_bytes": None,
}
print(json.dumps(report, indent=2))
