#!/usr/bin/env python3
"""Doomsday Phase2 strip-stub.

Reused by S2-C/D (dls.framework / Assembly-CSharp), S5-D (IGG.Game.Helper),
and onwards. Mechanically removes IL2CPP / Ghidra / IFix noise from
Annotated source and writes a stub-form Final file with correct header.

Steps:
- strip [Token(...)] / [Address(...)] / [FieldOffset(...)] / [MetadataOffset(...)]
  attribute lines, including `Il2CppDummyDll.` qualified prefix.
- strip `using Il2CppDummyDll;`
- strip embedded Ghidra pseudocode blocks
  (delimited by `/* === Ghidra pseudocode ... === end pseudocode === */`)
- strip inline `Il2CppDummyDll.` qualifier prefix
- prepend correct `// Annotated:` header based on namespace depth
- collapse runs of blank lines to <=1

Usage:
  python3 tools/doomsday/strip_stub.py --dll <dll> --ns <namespace> <file1.cs> ...
  echo file1.cs ... | python3 tools/doomsday/strip_stub.py --dll <dll> --ns <namespace> --list
"""
import argparse
import os
import re
import sys

ATTR_LINE = re.compile(
    r'^\s*\['
    r'(?:Il2CppDummyDll\.)?'
    r'(Token|Address|FieldOffset|MetadataOffset|FieldOffsetAttribute|TokenAttribute|AddressAttribute|MetadataOffsetAttribute)'
    r'\([^)]*\)\s*\]\s*$'
)

USING_LINE = re.compile(r'^\s*using\s+Il2CppDummyDll\s*;\s*$')

GHIDRA_BLOCK_START = re.compile(r'^\s*/\*\s*===\s*Ghidra\s+pseudocode', re.IGNORECASE)
GHIDRA_BLOCK_END = re.compile(r'^\s*\*?\s*===\s*end\s+pseudocode\s*===\s*\*/', re.IGNORECASE)

IL2CPP_QUAL = re.compile(r'Il2CppDummyDll\.')

ANN_ROOT = 'Input/Doomsday/RestoredSolution/Annotated'
FIN_ROOT = 'Input/Doomsday/RestoredSolution/Final'


def header_for(dll: str, ns: str, fname: str) -> str:
    # Final/<dll>/<ns>/<File>.cs → 3 ups → ../../../Annotated/<dll>/<ns>/<File>.cs
    # For sub-paths inside ns (a/b/c) the caller passes the relative path under ns.
    depth = 2 + len(ns.split('/')) if ns else 2
    ups = '/'.join(['..'] * depth)
    return f"// Annotated: {ups}/Annotated/{dll}/{ns}/{fname}\n" if ns else f"// Annotated: {ups}/Annotated/{dll}/{fname}\n"


def strip(text: str) -> str:
    lines = text.splitlines(keepends=False)
    out = []
    in_ghidra = False
    for ln in lines:
        if in_ghidra:
            if GHIDRA_BLOCK_END.search(ln):
                in_ghidra = False
            continue
        if GHIDRA_BLOCK_START.match(ln):
            in_ghidra = True
            # one-line Ghidra block edge case
            if GHIDRA_BLOCK_END.search(ln):
                in_ghidra = False
            continue
        if USING_LINE.match(ln):
            continue
        if ATTR_LINE.match(ln):
            continue
        if ln.startswith('// Annotated:'):
            continue
        ln = IL2CPP_QUAL.sub('', ln)
        out.append(ln)
    collapsed = []
    blanks = 0
    for ln in out:
        if ln.strip() == '':
            blanks += 1
            if blanks <= 1:
                collapsed.append(ln)
        else:
            blanks = 0
            collapsed.append(ln)
    return '\n'.join(collapsed) + '\n'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dll', required=True, help='dll name, e.g. dls.game')
    ap.add_argument('--ns', default='', help='namespace path under dll, e.g. IGG.Game.Helper')
    ap.add_argument('--list', action='store_true', help='read filenames from stdin')
    ap.add_argument('files', nargs='*', help='filenames (relative to <dll>/<ns>/)')
    args = ap.parse_args()

    if args.list:
        files = [ln.strip() for ln in sys.stdin if ln.strip()]
    else:
        files = args.files
    if not files:
        ap.error('no files (use args or pipe with --list)')

    ann_dir = os.path.join(ANN_ROOT, args.dll, args.ns) if args.ns else os.path.join(ANN_ROOT, args.dll)
    fin_dir = os.path.join(FIN_ROOT, args.dll, args.ns) if args.ns else os.path.join(FIN_ROOT, args.dll)

    written = 0
    missing = 0
    for f in files:
        src = os.path.join(ann_dir, f)
        if not os.path.exists(src):
            print(f"MISSING: {src}", file=sys.stderr)
            missing += 1
            continue
        with open(src, 'r', encoding='utf-8', errors='replace') as fh:
            raw = fh.read()
        stripped = strip(raw)
        out_path = os.path.join(fin_dir, f)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, 'w', encoding='utf-8') as fh:
            fh.write(header_for(args.dll, args.ns, f))
            fh.write(stripped)
        written += 1
    print(f'WROTE {written} stub files to {fin_dir}'
          + (f' (MISSING {missing})' if missing else ''))


if __name__ == '__main__':
    main()
