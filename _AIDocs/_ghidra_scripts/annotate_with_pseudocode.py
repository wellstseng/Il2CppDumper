#!/usr/bin/env python3
"""Step 2: pseudocode 對應貼回 ILSpy 反編檔 (Annotated 版本).

對每個 .cs 中的 method（用 [Address(RVA=...)] 識別），找對應的 pseudocode/*.c，
把 pseudocode 用 /* ... */ 區塊註解貼在 method body 內最前面，不改動其它內容。
"""
import re, shutil
from pathlib import Path

SRC_DIR = Path("/Users/wellstseng/project/Il2CppDumper/RestoredSolution/_raw")
DST_DIR = Path("/Users/wellstseng/project/Il2CppDumper/RestoredSolution/Annotated")
PSEUDO_DIR = Path("/Users/wellstseng/project/Il2CppDumper/Input/output/pseudocode")

if DST_DIR.exists():
    shutil.rmtree(DST_DIR)
DST_DIR.mkdir(parents=True)

# Index pseudocode by RVA (8-digit hex prefix of filename)
pseudo_by_rva = {}
for p in PSEUDO_DIR.iterdir():
    if not p.is_file() or not p.name.endswith(".c"): continue
    rva_hex = p.name.split("__", 1)[0]
    try:
        rva = int(rva_hex, 16)
    except ValueError:
        continue
    # Read pseudocode body (skip our 4-line header)
    raw = p.read_text(encoding="utf-8", errors="replace").splitlines()
    body = "\n".join(raw[4:]) if len(raw) > 4 else "\n".join(raw)
    pseudo_by_rva[rva] = body
print(f"loaded pseudocode: {len(pseudo_by_rva)} methods")

# Regex: [Address(RVA = "0x251E80", Offset = "0x250A80", VA = "0x180251E80")]
ADDR_RE = re.compile(r'\[Address\(RVA\s*=\s*"0x([0-9A-Fa-f]+)"')

annotated_methods = 0
annotated_files = 0
skipped_files = 0

def find_method_body_open(text: str, start: int) -> int:
    """From start index, find the next '{' that opens the method body (skip attrs and signature)."""
    depth = 0
    i = start
    while i < len(text):
        c = text[i]
        if c == '{':
            return i
        elif c == ';':
            # abstract / extern / interface signature ; no body
            return -1
        i += 1
    return -1

def make_comment_block(pseudo: str, rva_hex: str) -> str:
    safe = pseudo.replace("*/", "* /")
    lines = ["/* === Ghidra pseudocode RVA 0x" + rva_hex + " ==="]
    for ln in safe.splitlines():
        lines.append(" * " + ln)
    lines.append(" * === end pseudocode === */")
    return "\n".join(lines)

for src in SRC_DIR.rglob("*.cs"):
    rel = src.relative_to(SRC_DIR)
    text = src.read_text(encoding="utf-8", errors="replace")

    matches = list(ADDR_RE.finditer(text))
    if not matches:
        # Copy verbatim
        dst = DST_DIR / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(text, encoding="utf-8")
        skipped_files += 1
        continue

    pieces = []
    last = 0
    file_anno_count = 0
    for m in matches:
        rva_hex = m.group(1).lower()
        rva = int(rva_hex, 16)
        if rva not in pseudo_by_rva:
            continue
        # Find next '{' after this attribute
        brace = find_method_body_open(text, m.end())
        if brace < 0:
            continue
        # Append everything up to and including '{'
        pieces.append(text[last:brace + 1])
        # Indent: detect leading whitespace on the line containing '{'
        line_start = text.rfind('\n', 0, brace) + 1
        indent = ""
        for ch in text[line_start:brace]:
            if ch in (" ", "\t"): indent += ch
            else: break
        body_indent = indent + "\t"
        # Insert comment block (then a newline) right after '{'
        comment = make_comment_block(pseudo_by_rva[rva], rva_hex)
        commented = "\n" + "\n".join(body_indent + ln for ln in comment.splitlines())
        pieces.append(commented)
        last = brace + 1
        file_anno_count += 1
        annotated_methods += 1
    pieces.append(text[last:])

    if file_anno_count == 0:
        # No matches actually had pseudocode -- copy verbatim
        dst = DST_DIR / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(text, encoding="utf-8")
        skipped_files += 1
        continue

    dst = DST_DIR / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text("".join(pieces), encoding="utf-8")
    annotated_files += 1

print(f"annotated files: {annotated_files}")
print(f"skipped files (no pseudocode hit): {skipped_files}")
print(f"annotated methods: {annotated_methods}")
print(f"output: {DST_DIR}")
