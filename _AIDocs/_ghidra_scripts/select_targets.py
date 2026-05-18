#!/usr/bin/env python3
"""From script.json ScriptMethod, pick only Assembly-CSharp / firstpass / __Generated user methods.
Excludes BCL (System/Microsoft/Mono), Unity, SevenZip, Newtonsoft, and compiler-generated stubs.
Output: _target_rvas.tsv (one RVA per line, decimal)."""
import json, re
from pathlib import Path

src = Path("/Users/wellstseng/project/Il2CppDumper/Input/output/script.json")
out = src.parent / "_target_rvas.tsv"
data = json.load(open(src))

EXCLUDE_PREFIXES = (
    "System.", "Microsoft.", "Mono.", "UnityEngine.", "UnityEditor.",
    "Newtonsoft.", "SevenZip", "Interop.", "FxResources.",
    "MS.Internal.", "MS.", "Windows.",
    "DG.Tweening", "Unity.Collections", "Unity.Burst", "Unity.Jobs",
)

# Compiler-generated indicators (lambda/iterator/async)
GENERATED_RE = re.compile(r"<[^>]+>[dceuib]?__|<>c|<>1__|<>2__|<>4__|kStateMachine|__InvokeMethod__|invoke_")

# IL2CPP method delimiter
DELIM = "$$"

kept = 0
total = 0
samples = {}
with open(out, "w") as f:
    for m in data["ScriptMethod"]:
        total += 1
        name = m["Name"]
        addr = m["Address"]
        # Strip leading "Method$" if present (ScriptMetadataMethod has it; ScriptMethod usually doesn't)
        n = name
        if n.startswith("Method$"):
            n = n[len("Method$"):]
        # Excluded namespaces
        if any(n.startswith(p) for p in EXCLUDE_PREFIXES):
            continue
        # Compiler-generated
        if GENERATED_RE.search(n):
            continue
        # Keep
        f.write(f"{addr}\n")
        kept += 1
        # Track sample by top-level namespace token
        ns = n.split(DELIM, 1)[0].rsplit(".", 1)[0] if "." in n.split(DELIM, 1)[0] else "(global)"
        samples[ns] = samples.get(ns, 0) + 1

print(f"total ScriptMethod: {total}")
print(f"kept (Assembly-CSharp系，非 generated): {kept}")
print(f"output: {out}")
print(f"\n=== 命中 namespace 分布 (前 20) ===")
for ns, c in sorted(samples.items(), key=lambda x: -x[1])[:20]:
    print(f"  {c:6d}  {ns}")
