#!/usr/bin/env python3
"""把 script.json 拆成 3 個 TSV 給 Java GhidraScript 讀（繞開 PyGhidra SIGBUS）"""
import json, sys
from pathlib import Path

src = Path("/Users/wellstseng/project/Il2CppDumper/Input/output/script.json")
out_dir = src.parent
data = json.load(open(src))

def sanitize(s: str) -> str:
    return s.replace("\t", " ").replace("\n", " ").replace("\r", " ")

methods = out_dir / "_methods.tsv"
with open(methods, "w") as f:
    for m in data.get("ScriptMethod", []):
        f.write(f"{m['Address']}\t{sanitize(m['Name'])}\n")
print(f"methods: {len(data.get('ScriptMethod', []))} -> {methods}")

strings = out_dir / "_strings.tsv"
with open(strings, "w") as f:
    for s in data.get("ScriptString", []):
        f.write(f"{s['Address']}\t{sanitize(s['Value'])}\n")
print(f"strings: {len(data.get('ScriptString', []))} -> {strings}")

metadata = out_dir / "_metadata.tsv"
with open(metadata, "w") as f:
    for m in data.get("ScriptMetadata", []):
        f.write(f"{m['Address']}\t{sanitize(m['Name'])}\n")
print(f"metadata: {len(data.get('ScriptMetadata', []))} -> {metadata}")

mmethods = out_dir / "_metadata_methods.tsv"
with open(mmethods, "w") as f:
    for m in data.get("ScriptMetadataMethod", []):
        f.write(f"{m['Address']}\t{sanitize(m['Name'])}\n")
print(f"metadata methods: {len(data.get('ScriptMetadataMethod', []))} -> {mmethods}")

addresses = out_dir / "_addresses.tsv"
with open(addresses, "w") as f:
    for a in data.get("Addresses", []):
        f.write(f"{a}\n")
print(f"addresses: {len(data.get('Addresses', []))} -> {addresses}")
