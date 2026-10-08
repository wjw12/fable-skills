"""Generate or edit an image with gpt-image-2.5. With --image it calls the edits endpoint, otherwise generations."""
import argparse
import base64
import json
import time
from pathlib import Path

from openai import OpenAI

p = argparse.ArgumentParser()
p.add_argument("--prompt")
p.add_argument("--prompt-file")
p.add_argument("--image", action="append", default=[])
p.add_argument("--mask")
p.add_argument("--size", default="auto")
p.add_argument("--background")
p.add_argument("--format", default="png")
p.add_argument("--n", type=int, default=1)
p.add_argument("--out", required=True)
a = p.parse_args()

prompt = a.prompt or Path(a.prompt_file).read_text()
params = dict(model="gpt-image-2.5-sunburst", prompt=prompt, quality="high", size=a.size, output_format=a.format, n=a.n)
if a.background:
    params["background"] = a.background

client = OpenAI()
start = time.time()
if a.image:
    files = [open(f, "rb") for f in a.image]
    if a.mask:
        params["mask"] = open(a.mask, "rb")
    result = client.images.edit(image=files, **params)
else:
    result = client.images.generate(**params)
elapsed = round(time.time() - start, 1)

out = Path(a.out)
out.parent.mkdir(parents=True, exist_ok=True)
paths = [out] if a.n == 1 else [out.with_name(f"{out.stem}-{i + 1}{out.suffix}") for i in range(a.n)]
for path, item in zip(paths, result.data):
    path.write_bytes(base64.b64decode(item.b64_json))
    print(path)

log = {k: v for k, v in params.items() if k != "mask"} | {"images": a.image, "mask": a.mask, "seconds": elapsed}
if result.usage:
    log["usage"] = result.usage.model_dump()
out.with_suffix(".json").write_text(json.dumps(log, indent=2))
print(f"{elapsed}s")
