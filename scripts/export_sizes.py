"""Read real compressed layer sizes from single-platform OCI exports."""
import json
import pathlib
import sys
rows=[]
for name in ("baseline-gzip6","optimized-gzip9","optimized-zstd19"):
    root=pathlib.Path(sys.argv[1])/name
    def blob(d):
        algorithm,digest=d["digest"].split(":")
        return json.loads((root/"blobs"/algorithm/digest).read_text())
    def manifests(index):
        for d in index["manifests"]:
            obj=blob(d)
            if "manifests" in obj: yield from manifests(obj)
            elif "layers" in obj: yield obj
    images=list(manifests(json.loads((root/"index.json").read_text())))
    assert len(images)==1
    layers=images[0]["layers"]
    rows.append({"profile":name,"compressed_layer_bytes":sum(x["size"] for x in layers),
      "layers":[{"digest":x["digest"],"size":x["size"],"mediaType":x["mediaType"]} for x in layers]})
print(json.dumps({"metric":"actual local OCI compressed layer sizes; not registry download","results":rows},indent=2))
