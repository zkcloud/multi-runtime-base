"""Measure frozen previous-main, compact and stripped candidates."""
import datetime
import json
import os
import subprocess
import sys
variant, arch = sys.argv[1:3]
def inspect(tag):
    return json.loads(subprocess.check_output(["docker","image","inspect",tag]))[0]
def packages(tag):
    return sorted(subprocess.check_output(["docker","run","--rm",tag,"dpkg-query","-W"],text=True).splitlines())
tags = {p:f"local/{variant}:{p}" for p in ("baseline","compact","test")}
images = {p:inspect(t) for p,t in tags.items()}
for p in ("compact","test"):
    if packages(tags[p]) != packages(tags["baseline"]):
        raise SystemExit("Package versions differ: " + p)
base = images["baseline"]["Size"]
profiles = {p:{"bytes":v["Size"],"image_id":v["Id"],"saved_bytes":base-v["Size"],
              "saved_percent":round(100*(base-v["Size"])/base,3)} for p,v in images.items()}
if profiles["test"]["bytes"] > profiles["compact"]["bytes"]:
    raise SystemExit("Strip candidate grew; select compact instead")
print(json.dumps({"variant":variant,"architecture":arch,
 "measured_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "commit":os.environ.get("GITHUB_SHA","local"),
 "reference_source":"07d82c08a3c740311897bb47d35e01c763a79e1a",
 "reference":"Dockerfile.reference, previous main TRIM=1",
 "metric":"docker image inspect .Size, uncompressed bytes",
 "package_versions_equal":True,"profiles":profiles,"selected":"test",
 "compressed_registry_bytes":None},indent=2))
