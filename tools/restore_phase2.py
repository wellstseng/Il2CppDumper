#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from collections import Counter, defaultdict
from pathlib import Path


ARTIFACT_NAMES = {
    "ILFixDynamicMethodWrapper.cs",
    "ILFixInterfaceBridge.cs",
    "WrappersManagerImpl.cs",
    "AssemblyInfo.cs",
    "UnitySourceGeneratedAssemblyMonoScriptTypes_v1.cs",
}


ATTR_RE = re.compile(r"^\s*\[(?:Il2CppDummyDll\.)?(?:Token|Address|FieldOffset)\([^\n]*\)\]\s*\n", re.MULTILINE)
GHIDRA_RE = re.compile(r"\n?\s*/\* === Ghidra pseudocode RVA .*?=== end pseudocode === \*/", re.DOTALL)
IL2CPP_USING_RE = re.compile(r"^using Il2CppDummyDll;\n", re.MULTILINE)
BLANK3_RE = re.compile(r"\n{3,}")
CLASS_RE = re.compile(r"public sealed class\s+(\w+)\s*:\s*(.+?)\n\{", re.DOTALL)
NAMESPACE_RE = re.compile(r"^namespace\s+([^;]+);", re.MULTILINE)
USING_RE = re.compile(r"^using\s+[^;]+;", re.MULTILINE)
FIELD_RE = re.compile(
    r"^\s*(public|private|protected|internal)\s+(static\s+readonly\s+|readonly\s+|const\s+)?([\w.<>, ?\[\]]+)\s+(\w+)(?:\s*=\s*[^;]+)?;",
    re.MULTILINE,
)


MARKERS = [
    "Il2CppDummyDll",
    "[Token(",
    "[Address(",
    "[FieldOffset(",
    "/* === Ghidra",
    "FUN_180",
    "StringLiteral_",
    "IFix_WrappersManagerImpl__IsPatched",
    "IFix_ILFixDynamicMethodWrapper__",
]
ENUM_TYPES: set[str] = set()


def should_skip(path: Path) -> str | None:
    parts = set(path.parts)
    if "IFix" in parts and (path.name.startswith("IDMAP") or path.name in ARTIFACT_NAMES):
        return "IFix build artifact"
    if path.name in ARTIFACT_NAMES:
        return "build metadata/artifact"
    return None


def annotated_line(rel: Path) -> str:
    depth = len(rel.parts)
    prefix = "../" * (depth + 1)
    return f"// Annotated: {prefix}Annotated/{rel.as_posix()}\n"


def transform(text: str, rel: Path, restore_unhandled: bool = True) -> str:
    preserved = IL2CPP_USING_RE.sub("", text)
    preserved = ATTR_RE.sub("", preserved)
    preserved = BLANK3_RE.sub("\n\n", preserved).lstrip()

    stripped = GHIDRA_RE.sub("", preserved)
    stripped = BLANK3_RE.sub("\n\n", stripped).lstrip()
    stripped = enhance_simple_members(stripped)
    if restore_unhandled:
        stripped = restore_unhandled_blocks(stripped, preserved)
    return annotated_line(rel) + stripped


def norm_name(name: str) -> str:
    name = name.lstrip("_")
    if name.startswith("m_"):
        name = name[2:]
    return re.sub(r"[^a-z0-9]", "", name.lower())


def enhance_simple_members(text: str) -> str:
    cls = re.search(r"\b(?:class|struct)\s+(\w+)", text)
    if not cls:
        return text
    class_name = cls.group(1)
    fields = []
    for m in FIELD_RE.finditer(text):
        visibility, modifier, typ, name = m.groups()
        modifier = modifier or ""
        if "const" in modifier or "static" in modifier:
            continue
        fields.append((typ.strip(), name))

    field_by_norm = {norm_name(name): name for _, name in fields}

    def replace_ctor(m: re.Match[str]) -> str:
        sig, args = m.group(1), m.group(2)
        assigns = []
        for arg in [a.strip() for a in args.split(",") if a.strip()]:
            arg_name = arg.split()[-1]
            field = field_by_norm.get(norm_name(arg_name))
            if field:
                assigns.append(f"\t\t{field} = {arg_name};")
        if not assigns:
            return m.group(0)
        return f"{sig}({args})\n\t{{\n" + "\n".join(assigns) + "\n\t}"

    ctor_re = re.compile(rf"((?:public|protected|internal|private)\s+{class_name})\(([^)]*)\)\n\t\{{\n\t\}}")
    text = ctor_re.sub(replace_ctor, text)

    method_re = re.compile(r"((?:public|protected|internal|private)\s+void\s+\w+)\(([^)]*)\)\n\t\{\n\t\}")
    text = method_re.sub(replace_single_assignment_method, text)

    for prop in re.finditer(r"public\s+([\w\[\].<>, ?]+)\s+(\w+)\s*\n\t\{\n\t\t(private\s+)?get\n\t\t\{\n\t\t\treturn null;\n\t\t\}\n\t\tset\n\t\t\{\n\t\t\}\n\t\}", text):
        typ, prop_name, private_get = prop.groups()
        backing = field_by_norm.get(norm_name(prop_name))
        if not backing:
            continue
        get_kw = "private get" if private_get else "get"
        replacement = (
            f"public {typ} {prop_name}\n\t{{\n"
            f"\t\t{get_kw} => {backing};\n"
            f"\t\tset => {backing} = value;\n"
            "\t}"
        )
        text = text.replace(prop.group(0), replacement)

    text = restore_common_array_helpers(text)
    text = restore_common_bool_helpers(text)
    return text


def replace_single_assignment_method(m: re.Match[str]) -> str:
    sig, args = m.group(1), m.group(2)
    parts = [a.strip() for a in args.split(",") if a.strip()]
    if len(parts) != 1:
        return m.group(0)
    arg_name = parts[0].split()[-1]
    method_text = m.string
    fields = []
    for fm in FIELD_RE.finditer(method_text):
        visibility, modifier, typ, name = fm.groups()
        modifier = modifier or ""
        if "const" not in modifier and "static" not in modifier:
            fields.append(name)
    for field in fields:
        if norm_name(field) == norm_name(arg_name) or norm_name(field).endswith(norm_name(arg_name)):
            return f"{sig}({args})\n\t{{\n\t\t{field} = {arg_name};\n\t}}"
    return m.group(0)


def restore_common_array_helpers(text: str) -> str:
    replacements = {
        "public string GetResult()": "return ResultText != null && ResultText.Length > 0 ? ResultText[0] : string.Empty;",
        "public List<string> GetResultList()": "return ResultText != null ? new List<string>(ResultText) : new List<string>();",
        "public string GetSourceLanguage()": "return SourceLanguage != null && SourceLanguage.Length > 0 ? SourceLanguage[0] : string.Empty;",
        "public List<string> GetSourceLanguageList()": "return SourceLanguage != null ? new List<string>(SourceLanguage) : new List<string>();",
    }
    for sig, body in replacements.items():
        text = re.sub(
            re.escape(sig) + r"\n\t\{\n\t\treturn null;\n\t\}",
            sig + "\n\t{\n\t\t" + body + "\n\t}",
            text,
        )
    return text


def restore_common_bool_helpers(text: str) -> str:
    if "_localCacheCleaner" in text:
        text = re.sub(
            r"protected bool NeedClearLocalCache\(\)\n\t\{\n\t\treturn default\(bool\);\n\t\}",
            "protected bool NeedClearLocalCache()\n\t{\n\t\treturn _localCacheCleaner != null && _localCacheCleaner.NeedClean();\n\t}",
            text,
        )
    return text


def extract_method_blocks(text: str) -> dict[str, str]:
    lines = text.splitlines()
    blocks: dict[str, str] = {}
    i = 0
    sig_re = re.compile(r"^\t(?:public|protected|internal|private).*?\)\s*$")
    while i < len(lines) - 1:
        if sig_re.match(lines[i]) and lines[i + 1].strip() == "{":
            sig = lines[i].strip()
            start = i
            depth = 0
            in_comment = False
            j = i + 1
            while j < len(lines):
                line = lines[j]
                scan = line
                if "/*" in scan:
                    in_comment = True
                    scan = scan.split("/*", 1)[0]
                if not in_comment:
                    depth += scan.count("{") - scan.count("}")
                if "*/" in line:
                    in_comment = False
                if depth == 0 and j > i + 1:
                    blocks[sig] = "\n".join(lines[start:j + 1])
                    i = j
                    break
                j += 1
        i += 1
    return blocks


def restore_unhandled_blocks(stripped: str, preserved: str) -> str:
    preserved_blocks = extract_method_blocks(preserved)
    stripped_blocks = extract_method_blocks(stripped)
    for sig, block in stripped_blocks.items():
        if sig not in preserved_blocks:
            continue
        if re.search(r"\{\n\t\}", block) or re.search(r"\{\n\t\t\}", block) or "return null;" in block or "return default(" in block:
            stripped = stripped.replace(block, preserved_blocks[sig])
    return stripped


def parse_fields(cleaned: str) -> list[dict[str, str | bool]]:
    fields: list[dict[str, str | bool]] = []
    for m in FIELD_RE.finditer(cleaned):
        visibility, modifier, typ, name = m.groups()
        modifier = modifier or ""
        if "const" in modifier or "static" in modifier:
            continue
        fields.append({
            "visibility": visibility,
            "readonly": "readonly" in modifier,
            "type": typ.strip(),
            "name": name,
            "repeated": typ.strip().startswith("RepeatedField<"),
        })
    return fields


def wire_type(typ: str) -> tuple[str, str]:
    if typ in ENUM_TYPES:
        return "WriteEnum", "ComputeEnumSize"
    if typ == "string":
        return "WriteString", "ComputeStringSize"
    if typ == "ByteString":
        return "WriteBytes", "ComputeBytesSize"
    if typ in {"uint", "uint32"}:
        return "WriteUInt32", "ComputeUInt32Size"
    if typ in {"ulong", "uint64"}:
        return "WriteUInt64", "ComputeUInt64Size"
    if typ in {"int", "int32"}:
        return "WriteInt32", "ComputeInt32Size"
    if typ in {"long", "int64"}:
        return "WriteInt64", "ComputeInt64Size"
    if typ == "bool":
        return "WriteBool", "ComputeBoolSize"
    if typ == "float":
        return "WriteFloat", "ComputeFloatSize"
    if typ == "double":
        return "WriteDouble", "ComputeDoubleSize"
    return "WriteMessage", "ComputeMessageSize"


def non_default_expr(name: str, typ: str, repeated: bool) -> str:
    if repeated:
        return f"{name}.Count != 0"
    if typ == "string":
        return f"{name}.Length != 0"
    if typ == "ByteString":
        return f"{name}.Length != 0"
    if typ in {"float", "double"}:
        return f"{name} != 0D"
    if typ == "bool":
        return name
    if typ[0].isupper() and typ not in ENUM_TYPES and typ not in {"uint", "ulong"}:
        return f"{name} != null"
    return f"{name} != 0"


def default_value(typ: str) -> str | None:
    if typ == "string":
        return '""'
    if typ == "ByteString":
        return "ByteString.Empty"
    return None


def generate_protobuf(text: str, rel: Path) -> str:
    cleaned = transform(text, rel)
    ns = NAMESPACE_RE.search(cleaned)
    cls = CLASS_RE.search(cleaned)
    if not ns or not cls:
        return cleaned
    class_name = cls.group(1)
    bases = " ".join(cls.group(2).split())
    usings = USING_RE.findall(cleaned)
    fields = parse_fields(cleaned)
    codec_by_type: dict[str, str] = {}
    for m in re.finditer(r"FieldCodec<([^>]+)>\s+(\w+);", cleaned):
        codec_by_type[m.group(1).strip()] = m.group(2)
    static_and_consts = []
    for m in FIELD_RE.finditer(cleaned):
        line = m.group(0).strip()
        modifier = m.group(2) or ""
        if "const" in modifier or "static" in modifier:
            static_and_consts.append(line)
    field_lines = []
    for f in fields:
        ro = "readonly " if f["readonly"] else ""
        field_lines.append(f"\t{f['visibility']} {ro}{f['type']} {f['name']};")

    init_lines = []
    copy_lines = []
    equals_terms = []
    hash_lines = ["\t\tint hash = 1;"]
    write_lines = []
    size_lines = ["\t\tint size = 0;"]
    merge_lines = ["\t\tif (other == null) return;"]
    input_lines = ["\t\twhile (input.ReadTag() != 0)", "\t\t{", "\t\t\tinput.SkipLastField();", "\t\t}"]

    for f in fields:
        typ = str(f["type"])
        name = str(f["name"])
        repeated = bool(f["repeated"])
        if repeated:
            elem = typ[len("RepeatedField<"):-1]
            codec = codec_by_type.get(elem, f"_repeated_{name}_codec")
            init_lines.append(f"\t\t{name} = new RepeatedField<{elem}>();")
            copy_lines.append(f"\t\t{name} = other.{name}.Clone();")
            equals_terms.append(f"{name}.Equals(other.{name})")
            hash_lines.append(f"\t\thash ^= {name}.GetHashCode();")
            write_lines.append(f"\t\t{name}.WriteTo(output, {codec});")
            size_lines.append(f"\t\tsize += {name}.CalculateSize({codec});")
            merge_lines.append(f"\t\t{name}.Add(other.{name});")
            continue
        dv = default_value(typ)
        if dv is not None:
            init_lines.append(f"\t\t{name} = {dv};")
        copy_lines.append(f"\t\t{name} = other.{name};")
        equals_terms.append(f"EqualityComparer<{typ}>.Default.Equals({name}, other.{name})")
        cond = non_default_expr(name, typ, repeated)
        hash_lines.append(f"\t\tif ({cond}) hash ^= {name}.GetHashCode();")
        writer, sizer = wire_type(typ)
        value_expr = f"(int){name}" if typ in ENUM_TYPES else name
        write_lines.extend([f"\t\tif ({cond})", "\t\t{", f"\t\t\toutput.{writer}({value_expr});", "\t\t}"])
        size_lines.extend([f"\t\tif ({cond}) size += CodedOutputStream.{sizer}({value_expr});"])
        merge_lines.extend([f"\t\tif ({non_default_expr('other.' + name, typ, repeated)}) {name} = other.{name};"])

    body = [
        annotated_line(rel).rstrip(),
        *usings,
        "using System.Collections.Generic;",
        "",
        f"namespace {ns.group(1)};",
        "",
        "// Generated by tools/restore_phase2.py from IL2CPP Annotated output.",
        f"public sealed class {class_name} : {bases}",
        "{",
    ]
    body += [f"\t{x}" for x in static_and_consts]
    if static_and_consts and field_lines:
        body.append("")
    body += field_lines
    body += [
        "",
        "\tprivate string pb_003A_003AGoogle_002EProtobuf_002EIMessage_002EFullName => FullName;",
        "",
        f"\tpublic {class_name}()",
        "\t{",
        *(init_lines or ["\t\t"]),
        "\t}",
        "",
        f"\tpublic {class_name}({class_name} other) : this()",
        "\t{",
        "\t\tif (other == null) return;",
        *copy_lines,
        "\t}",
        "",
        f"\tpublic {class_name} Clone() => new {class_name}(this);",
        "",
        f"\tpublic override bool Equals(object other) => Equals(other as {class_name});",
        "",
        f"\tpublic bool Equals({class_name} other)",
        "\t{",
        "\t\tif (ReferenceEquals(other, null)) return false;",
        "\t\tif (ReferenceEquals(other, this)) return true;",
        f"\t\treturn {' && '.join(equals_terms) if equals_terms else 'true'};",
        "\t}",
        "",
        "\tpublic override int GetHashCode()",
        "\t{",
        *hash_lines,
        "\t\treturn hash;",
        "\t}",
        "",
        "\tpublic void WriteTo(CodedOutputStream output)",
        "\t{",
        *(write_lines or ["\t\t"]),
        "\t}",
        "",
        "\tpublic int CalculateSize()",
        "\t{",
        *size_lines,
        "\t\treturn size;",
        "\t}",
        "",
        f"\tpublic void MergeFrom({class_name} other)",
        "\t{",
        *merge_lines,
        "\t}",
        "",
        "\tpublic void MergeFrom(CodedInputStream input)",
        "\t{",
        *input_lines,
        "\t}",
        "}",
        "",
    ]
    return "\n".join(body)


def classify(src: str, out: str) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if "IMessage<" in src and "Google.Protobuf" in src:
        return "mechanical-protobuf-stub", ["protobuf-generated-template"]
    if "enum " in src and "/* === Ghidra" not in src:
        return "mechanical-ok", reasons
    if "interface " in src and "/* === Ghidra" not in src:
        return "mechanical-ok", reasons

    if "/* === Ghidra" in src:
        reasons.append("has-ghidra-pseudocode")
    if re.search(r"return\s+default\(", out) or re.search(r"return\s+default\s*;", out):
        reasons.append("default-return-remains")
    if re.search(r"return\s+null\s*;", out):
        reasons.append("null-return-remains")
    has_method_decl = re.search(r"^\s*(public|protected|internal|private)\s+(?!(?:static\s+)?(?:readonly\s+|const\s+)?[\w.<>, ?\[\]]+\s+\w+\s*[;=])[^\n]*\([^\n]*\)\s*$", out, re.MULTILINE)
    if re.search(r"\{\s*\}", out) and has_method_decl:
        reasons.append("empty-body-remains")

    remaining = [m for m in MARKERS if m in out]
    if remaining:
        reasons.extend(f"marker:{m}" for m in remaining[:5])

    if not reasons:
        return "mechanical-ok", reasons
    if reasons == ["has-ghidra-pseudocode"] and "return" not in out:
        return "mechanical-review", reasons
    return "needs-llm", reasons


def main() -> int:
    parser = argparse.ArgumentParser(description="Doomsday Phase2 mechanical restore dry-run")
    parser.add_argument("dll", help="dll folder name under RestoredSolution/Annotated, e.g. dls.im")
    parser.add_argument("--root", default="Input/Doomsday/RestoredSolution")
    parser.add_argument("--preview-dir", default="")
    parser.add_argument("--write-preview", action="store_true")
    parser.add_argument("--apply", action="store_true",
                        help="Write mechanical-ok/protobuf-stub/review outputs directly to Final/<dll>/; skip needs-llm and skip files")
    args = parser.parse_args()

    root = Path(args.root)
    annotated_root = root / "Annotated" / args.dll
    final_root = root / "Final" / args.dll
    if not annotated_root.exists():
        raise SystemExit(f"Annotated dll not found: {annotated_root}")

    global ENUM_TYPES
    ENUM_TYPES = set()
    for enum_path in annotated_root.rglob("*.cs"):
        enum_text = enum_path.read_text(encoding="utf-8-sig", errors="ignore")
        m = re.search(r"public enum\s+(\w+)", enum_text)
        if m:
            ENUM_TYPES.add(m.group(1))

    preview_root = Path(args.preview_dir) if args.preview_dir else Path("memory/_staging/phase2_mechanical_preview") / args.dll
    counter: Counter[str] = Counter()
    namespaces: dict[str, Counter[str]] = defaultdict(Counter)
    samples: dict[str, list[str]] = defaultdict(list)
    existing = 0
    missing_counter: Counter[str] = Counter()
    APPLY_STATUSES = {"mechanical-ok", "mechanical-protobuf-stub", "mechanical-review"}
    APPLY_LLM_NOTE = (
        "// Note: ILSpy could not decompile method bodies for this class. "
        "Bodies retained empty per SOP §5; see Annotated source for Ghidra pseudocode reference."
    )
    applied_counter: Counter[str] = Counter()
    needs_llm_paths: list[str] = []

    for src_path in sorted(annotated_root.rglob("*.cs")):
        rel = src_path.relative_to(annotated_root)
        ns = rel.parts[0] if len(rel.parts) > 1 else "."
        final_exists = (final_root / rel).exists()
        if final_exists:
            existing += 1

        reason = should_skip(rel)
        if reason:
            status = "skip"
            reasons = [reason]
            out = ""
        else:
            src = src_path.read_text(encoding="utf-8-sig")
            if "IMessage<" in src and "Google.Protobuf" in src:
                out = generate_protobuf(src, Path(args.dll) / rel)
            else:
                out = transform(src, Path(args.dll) / rel)
            status, reasons = classify(src, out)
            if args.write_preview:
                dst = preview_root / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_text(out, encoding="utf-8")
            if args.apply and status in APPLY_STATUSES:
                dst = final_root / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_text(out, encoding="utf-8")
                applied_counter[status] += 1
            elif args.apply and status == "needs-llm":
                clean_out = transform(src, Path(args.dll) / rel, restore_unhandled=False)
                lines = clean_out.splitlines()
                insert_at = 1 if lines and lines[0].startswith("// Annotated:") else 0
                lines.insert(insert_at, APPLY_LLM_NOTE)
                dst = final_root / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_text("\n".join(lines) + "\n", encoding="utf-8")
                applied_counter[status] += 1

        if status == "needs-llm":
            needs_llm_paths.append(rel.as_posix())

        counter[status] += 1
        if not final_exists:
            missing_counter[status] += 1
        namespaces[ns][status] += 1
        if len(samples[status]) < 12:
            samples[status].append(f"{rel.as_posix()} ({'; '.join(reasons)})")

    total = sum(counter.values())
    print(f"dll: {args.dll}")
    print(f"annotated: {total}")
    print(f"existing final: {existing}")
    for key in ["mechanical-ok", "mechanical-protobuf-stub", "mechanical-review", "needs-llm", "skip"]:
        print(f"{key}: {counter[key]}")

    print("\nmissing final only:")
    for key in ["mechanical-ok", "mechanical-protobuf-stub", "mechanical-review", "needs-llm", "skip"]:
        print(f"{key}: {missing_counter[key]}")

    print("\nby namespace:")
    for ns, counts in sorted(namespaces.items()):
        print(
            f"- {ns}: ok={counts['mechanical-ok']}, review={counts['mechanical-review']}, "
            f"protobuf={counts['mechanical-protobuf-stub']}, llm={counts['needs-llm']}, skip={counts['skip']}"
        )

    print("\nsamples:")
    for key in ["mechanical-ok", "mechanical-protobuf-stub", "mechanical-review", "needs-llm", "skip"]:
        print(f"[{key}]")
        for item in samples[key]:
            print(f"  - {item}")

    if args.write_preview:
        print(f"\npreview written: {preview_root}")
    if args.apply:
        print("\napplied (written to Final):")
        for key in ["mechanical-ok", "mechanical-protobuf-stub", "mechanical-review", "needs-llm"]:
            print(f"  {key}: {applied_counter[key]}")
        print(f"\nneeds-llm files (written with ILSpy-undecompiled header note): {len(needs_llm_paths)}")
        for p in needs_llm_paths:
            print(f"  - {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
