#!/usr/bin/env python3
"""Phase 2 Ghidra → C# 保守翻譯器 (Doomsday).

設計原則：**不加油添醋**。只在 100% 可決定性對應時翻譯，否則保留原 Ghidra 註解。

可翻譯模式（白名單）:
  - 框架雜訊：static init guard / IFix fast-path / null-deref trap / write barrier
  - allocation + ctor + offset assign 四步組合 → `_field = new Type();`
  - field 讀：`*(T *)(param_1 + 0xN)` → `_fieldName`（前提 N 在 FieldOffset 表）
  - stdlib symbol（Dictionary/List/string 白名單） → 對應 C# 寫法
  - 局部變數宣告（uVar/lVar/cVar/iVar）→ `var`
  - param_1 → this，param_N (N>=2) → 對應 method 參數名

保留模式（不翻譯）:
  - 未知 demangled symbol
  - 複雜泛型參數 parse 失敗
  - 控制流分支（保留 C 風格 if/else/return，讀者自行判讀）
  - 任何 ambiguous 表達式

輸出：method body 文字（混合 C# 翻譯 + Ghidra 註解殘段）
"""
from __future__ import annotations

import re
from dataclasses import dataclass


# ─────────────────────────────────────────────────────────────────────
# Field offset map 萃取
# ─────────────────────────────────────────────────────────────────────

FIELD_OFFSET_RE = re.compile(
    r"\[(?:Il2CppDummyDll\.)?FieldOffset\(Offset\s*=\s*\"0x([0-9A-Fa-f]+)\"\)\]\s*\n"
    r"\s*(?:public|private|protected|internal)\s+(?:static\s+)?(?:readonly\s+)?"
    r"([\w.<>, ?\[\]]+?)\s+(\w+)\s*[;=]",
    re.MULTILINE,
)


def extract_field_offset_map(annotated_text: str) -> dict[int, tuple[str, str]]:
    """從 Annotated.cs 文字抽 `{offset: (field_name, field_type)}` 映射。"""
    out: dict[int, tuple[str, str]] = {}
    for m in FIELD_OFFSET_RE.finditer(annotated_text):
        offset = int(m.group(1), 16)
        typ = m.group(2).strip()
        name = m.group(3).strip()
        out[offset] = (name, typ)
    return out


# ─────────────────────────────────────────────────────────────────────
# Method 上下文萃取
# ─────────────────────────────────────────────────────────────────────

METHOD_SIG_RE = re.compile(
    r"^\s*(?:public|private|protected|internal)\s+"
    r"(?:(?:static|virtual|override|abstract|sealed|new|async|extern|unsafe)\s+)*"
    # return type optional（ctor 沒有 return type）
    r"(?:([\w<>, ?\[\]]+?)\s+)?"
    r"(\w+)\s*\(([^)]*)\)"
)


@dataclass
class MethodContext:
    return_type: str
    method_name: str
    param_names: list[str]
    is_ctor: bool


def parse_method_signature(sig_line: str, class_name: str) -> MethodContext | None:
    m = METHOD_SIG_RE.match(sig_line)
    if not m:
        return None
    ret = (m.group(1) or "").strip()
    name = m.group(2).strip()
    params = m.group(3).strip()
    param_names: list[str] = []
    if params:
        for p in params.split(","):
            tok = p.strip().rsplit(" ", 1)
            if len(tok) == 2:
                param_names.append(tok[1].strip("[] "))
            else:
                param_names.append(tok[0])
    is_ctor = (name == class_name) or ret == class_name
    return MethodContext(return_type=ret, method_name=name, param_names=param_names, is_ctor=is_ctor)


# ─────────────────────────────────────────────────────────────────────
# Ghidra block 拆解
# ─────────────────────────────────────────────────────────────────────

GHIDRA_BLOCK_RE = re.compile(
    r"/\* === Ghidra pseudocode RVA 0x[0-9A-Fa-f]+ ===\s*\n"
    r"(.*?)"
    r"\s*=== end pseudocode === \*/",
    re.DOTALL,
)


def unwrap_ghidra(ghidra_block: str) -> list[str]:
    """從 `/* === Ghidra... === end pseudocode === */` 取出純粹偽碼行（去除 `* ` 前綴）。"""
    m = GHIDRA_BLOCK_RE.search(ghidra_block)
    if not m:
        return []
    inner = m.group(1)
    lines = []
    for raw in inner.splitlines():
        stripped = raw.lstrip()
        if stripped.startswith("* "):
            lines.append(stripped[2:])
        elif stripped == "*" or stripped == "":
            lines.append("")
        else:
            lines.append(stripped)
    # 去除頭尾空白行
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


# ─────────────────────────────────────────────────────────────────────
# Translation passes（每個 pass 接受 lines 回傳 lines）
# ─────────────────────────────────────────────────────────────────────


def merge_multiline_statements(lines: list[str]) -> list[str]:
    """把跨行 C statement 合併成單行。

    Ghidra 偽碼常把長 expression 換行，例如：
        uVar1 = thunk_FUN_1805e65d0(
                                   System_..._TypeInfo
                                   );
    合併後：
        uVar1 = thunk_FUN_1805e65d0( System_..._TypeInfo );
    """
    out: list[str] = []
    buf: list[str] = []
    paren_depth = 0
    for l in lines:
        s = l.rstrip()
        stripped = s.strip()
        if not stripped:
            if buf:
                out.append(" ".join(buf))
                buf = []
                paren_depth = 0
            out.append("")
            continue
        buf.append(stripped)
        paren_depth += stripped.count("(") - stripped.count(")")
        # statement 完整：括號平衡 AND 結尾為 ; / { / } / : / 純括號
        if paren_depth <= 0 and (
            stripped.endswith(";")
            or stripped.endswith("{")
            or stripped.endswith("}")
            or stripped.endswith(":")
        ):
            out.append(" ".join(buf))
            buf = []
            paren_depth = 0
    if buf:
        out.append(" ".join(buf))
    return out


def strip_function_header(lines: list[str]) -> list[str]:
    """砍掉開頭的 `<RetType> <Name>(<params>)` 與隨後的 `{`/`}` 框，以及局部變數宣告區。

    Ghidra 偽碼開頭結構固定：
        <undefined8> <Type__Method>(longlong param_1, ...)
        {
          <local var decls>;

          <body>
        }
    """
    out = list(lines)
    # 砍掉到第一個 `{` 為止
    while out and out[0].strip() != "{":
        out.pop(0)
    if out and out[0].strip() == "{":
        out.pop(0)
    # 砍掉結尾的 `}`
    while out and not out[-1].strip():
        out.pop()
    if out and out[-1].strip() == "}":
        out.pop()
    # 砍掉局部變數宣告區（從頭連續的 `<type> <name>;` 直到第一個空白行或非宣告行）
    var_decl_re = re.compile(
        r"^\s*(undefined\d*|char|int|uint|longlong|ulonglong|short|ushort|byte|void)\s*\*?\s+\w[\w,\s\*]*;\s*$"
    )
    while out:
        first = out[0].strip()
        if not first:
            out.pop(0)
            continue
        if var_decl_re.match(out[0]):
            out.pop(0)
            continue
        break
    return out


INIT_GUARD_RE = re.compile(r"^\s*if\s*\(DAT_[0-9a-fA-F]+\s*==\s*'\\0'\)\s*\{?\s*$")
INIT_GUARD_SET_RE = re.compile(r"^\s*DAT_[0-9a-fA-F]+\s*=\s*'\\x01';\s*$")


def strip_static_init_guard(lines: list[str]) -> list[str]:
    """砍 `if (DAT_xxx == '\\0') { ... DAT_xxx = '\\x01'; }` 整段。"""
    out: list[str] = []
    i = 0
    while i < len(lines):
        if INIT_GUARD_RE.match(lines[i]):
            # 找對應 `}`
            depth = 1 if "{" in lines[i] else 0
            j = i + 1
            while j < len(lines):
                depth += lines[j].count("{") - lines[j].count("}")
                if depth <= 0:
                    break
                j += 1
            # 跳過整段 [i .. j]
            i = j + 1
            continue
        if INIT_GUARD_SET_RE.match(lines[i]):
            i += 1
            continue
        out.append(lines[i])
        i += 1
    return out


IFIX_DETECT_RE = re.compile(
    r"^\s*(\w+)\s*=\s*IFix_WrappersManagerImpl__IsPatched\(0x([0-9a-fA-F]+),\s*0\);\s*$"
)


def strip_ifix_fastpath(lines: list[str]) -> list[str]:
    """偵測 IFix fast-path 結構：

        cVar1 = IFix_WrappersManagerImpl__IsPatched(0xN, 0);
        if (cVar1 == '\\0') {
            <real body>
        }
        else {
            lVar3 = IFix_WrappersManagerImpl__GetPatch(0xN, 0);
            if (lVar3 != 0) {
                uVar2 = IFix_ILFixDynamicMethodWrapper____Gen_Wrap_<N>(...);
                return uVar2;
            }
        }

    保留 `<real body>`，砍掉其他部分。
    """
    out: list[str] = []
    i = 0
    while i < len(lines):
        m = IFIX_DETECT_RE.match(lines[i])
        if not m:
            out.append(lines[i])
            i += 1
            continue
        var = m.group(1)
        # 預期下一行為 `if (<var> == '\0') {`
        j = i + 1
        if j >= len(lines) or not re.match(
            rf"^\s*if\s*\(\s*{re.escape(var)}\s*==\s*'\\0'\s*\)\s*\{{?\s*$", lines[j]
        ):
            out.append(lines[i])
            i += 1
            continue
        # 找匹配的 `}`：實作分支結束
        depth = 1
        k = j + 1
        real_body_start = k
        while k < len(lines):
            depth += lines[k].count("{") - lines[k].count("}")
            if depth <= 0:
                break
            k += 1
        real_body_end = k  # 該行是 `}`
        # 真實業務分支內容：lines[real_body_start .. real_body_end-1]
        real_body = lines[real_body_start:real_body_end]
        # 檢查後面是不是 `else {`，是的話跳過整段 else
        nxt = real_body_end + 1
        if nxt < len(lines) and re.match(r"^\s*else\s*\{?\s*$", lines[nxt]):
            depth = 1
            m2 = nxt + 1
            while m2 < len(lines):
                depth += lines[m2].count("{") - lines[m2].count("}")
                if depth <= 0:
                    break
                m2 += 1
            nxt = m2 + 1  # 跳過整段 else 與其 `}`
        out.extend(real_body)
        i = nxt
    return out


NULL_TRAP_RE = re.compile(r"^\s*FUN_18055b3e0\(\)\s*;\s*$")
WRITE_BARRIER_RE = re.compile(r"^\s*FUN_18055a480\(.*\)\s*;\s*$")
RUNTIME_INIT_RE = re.compile(r"^\s*FUN_18055b140\(.*\)\s*;\s*$")
THUNK_ALLOC_RE = re.compile(r"^\s*(\w+)\s*=\s*thunk_FUN_1805e65d0\(\s*([\w<>, _]+?)_TypeInfo\s*\)\s*;\s*$")
CLASS_INIT_RE = re.compile(r"^\s*il2cpp_runtime_class_init\(.*\)\s*;\s*$")


def strip_runtime_helpers(lines: list[str]) -> list[str]:
    """砍 IL2CPP runtime helper 行（null-deref trap、write barrier、type init、class init）。"""
    return [l for l in lines if not (
        NULL_TRAP_RE.match(l)
        or WRITE_BARRIER_RE.match(l)
        or RUNTIME_INIT_RE.match(l)
        or CLASS_INIT_RE.match(l)
    )]


# ─────────────────────────────────────────────────────────────────────
# Generic type parsing (Ghidra 用 `_` 分隔逗號後的空白)
# ─────────────────────────────────────────────────────────────────────


def normalize_generic(gh_type: str) -> str:
    """Ghidra 寫 `Dictionary<IMChatTagKey,_IMChatTag>` → C# `Dictionary<IMChatTagKey, IMChatTag>`."""
    return gh_type.replace(",_", ", ")


SYSTEM_PREFIX_RE = re.compile(r"^System_(?:Collections_Generic_|Linq_|Text_)?")


def strip_namespace_prefix(t: str) -> str:
    """`System_Collections_Generic_Dictionary<...>` → `Dictionary<...>`."""
    return SYSTEM_PREFIX_RE.sub("", t)


# ─────────────────────────────────────────────────────────────────────
# Allocation + ctor + offset 四步合併翻譯
# ─────────────────────────────────────────────────────────────────────


CTOR_CALL_RE = re.compile(
    r"^\s*([\w<>, _]+?)___ctor\s*\(\s*(\w+)\s*,\s*Method_[\w<>, _]+__ctor__\s*\)\s*;\s*$"
)
OFFSET_STORE_RE = re.compile(
    r"^\s*\*\(undefined8 \*\)\(param_1\s*\+\s*(0x[0-9a-fA-F]+|\d+)\)\s*=\s*(\w+)\s*;\s*$"
)


def translate_alloc_init_pattern(
    lines: list[str], field_map: dict[int, tuple[str, str]]
) -> list[str]:
    """偵測 4 行組合：

        uVar1 = thunk_FUN_1805e65d0(<TypeInfo>);
        <Type>___ctor(uVar1, <MethodInfo>);
        *(undefined8 *)(param_1 + 0xN) = uVar1;
        FUN_18055a480((undefined8 *)(param_1 + 0xN), uVar1);   ← 已被 strip_runtime_helpers 移除

    翻譯為：`_fieldName = new <Type>();`（前提 0xN 在 field_map）。
    對不上就保留 4 行原文。
    """
    out: list[str] = []
    i = 0
    while i < len(lines):
        m1 = THUNK_ALLOC_RE.match(lines[i])
        if not m1:
            out.append(lines[i])
            i += 1
            continue
        var = m1.group(1)
        gh_type = m1.group(2)
        # 下一行應為 `<SomeType>___ctor(<var>, MethodInfo)`
        if i + 1 >= len(lines):
            out.append(lines[i])
            i += 1
            continue
        m2 = CTOR_CALL_RE.match(lines[i + 1])
        if not m2 or m2.group(2) != var:
            out.append(lines[i])
            i += 1
            continue
        # 下一行應為 `*(undefined8 *)(param_1 + 0xN) = <var>`
        if i + 2 >= len(lines):
            out.append(lines[i])
            i += 1
            continue
        m3 = OFFSET_STORE_RE.match(lines[i + 2])
        if not m3 or m3.group(2) != var:
            out.append(lines[i])
            i += 1
            continue
        offset_str = m3.group(1)
        offset = int(offset_str, 16) if offset_str.startswith("0x") else int(offset_str)
        field = field_map.get(offset)
        if not field:
            # offset 對不上 field_map → 保留原文 3 行
            out.append(lines[i])
            i += 1
            continue
        field_name, field_type = field
        cs_type = normalize_generic(strip_namespace_prefix(gh_type))
        # 輸出單行翻譯
        out.append(f"{field_name} = new {cs_type}();")
        i += 3  # 跳過 3 行
    return out


# ─────────────────────────────────────────────────────────────────────
# Field 讀取翻譯
# ─────────────────────────────────────────────────────────────────────


FIELD_READ_RE = re.compile(
    r"\*\((?:undefined[1248]?|longlong|ulonglong|int|uint|char|short|byte|void)\s*\*?\s*\*\)\s*\(\s*param_1\s*\+\s*(0x[0-9a-fA-F]+|\d+)\s*\)"
)


def translate_field_reads(line: str, field_map: dict[int, tuple[str, str]]) -> str:
    def sub(m: re.Match[str]) -> str:
        off_str = m.group(1)
        off = int(off_str, 16) if off_str.startswith("0x") else int(off_str)
        f = field_map.get(off)
        if not f:
            return m.group(0)  # 不翻
        return f[0]
    return FIELD_READ_RE.sub(sub, line)


# ─────────────────────────────────────────────────────────────────────
# Stdlib symbol 翻譯（白名單）
# ─────────────────────────────────────────────────────────────────────


# 白名單模式：(regex, replacement)。Replacement 用 \g<name> 引用。
STDLIB_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # Dictionary
    (re.compile(
        r"System_Collections_Generic_Dictionary<[\w<>, _]+?>__ContainsKey\s*\(\s*([^,]+?)\s*,\s*([^,]+?)\s*,\s*Method_[\w<>, _]+_ContainsKey__\s*\)"
    ), r"\1.ContainsKey(\2)"),
    (re.compile(
        r"System_Collections_Generic_Dictionary<[\w<>, _]+?>__get_Item\s*\(\s*([^,]+?)\s*,\s*([^,]+?)\s*,\s*Method_[\w<>, _]+_get_Item__\s*\)"
    ), r"\1[\2]"),
    (re.compile(
        r"System_Collections_Generic_Dictionary<[\w<>, _]+?>__Add\s*\(\s*([^,]+?)\s*,\s*([^,]+?)\s*,\s*([^,]+?)\s*,\s*Method_[\w<>, _]+_Add__\s*\)"
    ), r"\1.Add(\2, \3)"),
    (re.compile(
        r"System_Collections_Generic_Dictionary<[\w<>, _]+?>__Remove\s*\(\s*([^,]+?)\s*,\s*([^,]+?)\s*,\s*Method_[\w<>, _]+_Remove__\s*\)"
    ), r"\1.Remove(\2)"),
    (re.compile(
        r"System_Collections_Generic_Dictionary<[\w<>, _]+?>__set_Item\s*\(\s*([^,]+?)\s*,\s*([^,]+?)\s*,\s*([^,]+?)\s*,\s*Method_[\w<>, _]+_set_Item__\s*\)"
    ), r"\1[\2] = \3"),
    (re.compile(
        r"System_Collections_Generic_Dictionary<[\w<>, _]+?>__get_Count\s*\(\s*([^,]+?)\s*,\s*Method_[\w<>, _]+_get_Count__\s*\)"
    ), r"\1.Count"),
    (re.compile(
        r"System_Collections_Generic_Dictionary<[\w<>, _]+?>__Clear\s*\(\s*([^,]+?)\s*,\s*Method_[\w<>, _]+_Clear__\s*\)"
    ), r"\1.Clear()"),
    # List
    (re.compile(
        r"System_Collections_Generic_List<[\w<>, _]+?>__Add\s*\(\s*([^,]+?)\s*,\s*([^,]+?)\s*,\s*Method_[\w<>, _]+_Add__\s*\)"
    ), r"\1.Add(\2)"),
    (re.compile(
        r"System_Collections_Generic_List<[\w<>, _]+?>__Remove\s*\(\s*([^,]+?)\s*,\s*([^,]+?)\s*,\s*Method_[\w<>, _]+_Remove__\s*\)"
    ), r"\1.Remove(\2)"),
    (re.compile(
        r"System_Collections_Generic_List<[\w<>, _]+?>__get_Count\s*\(\s*([^,]+?)\s*,\s*Method_[\w<>, _]+_get_Count__\s*\)"
    ), r"\1.Count"),
    (re.compile(
        r"System_Collections_Generic_List<[\w<>, _]+?>__get_Item\s*\(\s*([^,]+?)\s*,\s*([^,]+?)\s*,\s*Method_[\w<>, _]+_get_Item__\s*\)"
    ), r"\1[\2]"),
    (re.compile(
        r"System_Collections_Generic_List<[\w<>, _]+?>__Clear\s*\(\s*([^,]+?)\s*,\s*Method_[\w<>, _]+_Clear__\s*\)"
    ), r"\1.Clear()"),
    (re.compile(
        r"System_Collections_Generic_List<[\w<>, _]+?>__Contains\s*\(\s*([^,]+?)\s*,\s*([^,]+?)\s*,\s*Method_[\w<>, _]+_Contains__\s*\)"
    ), r"\1.Contains(\2)"),
]


def translate_stdlib(line: str) -> str:
    out = line
    for pat, repl in STDLIB_PATTERNS:
        out = pat.sub(repl, out)
    return out


# ─────────────────────────────────────────────────────────────────────
# 變數名歸一化 + param_N 翻譯
# ─────────────────────────────────────────────────────────────────────


VAR_RE = re.compile(r"\b([culis]Var)(\d+)\b")


def normalize_var_names(line: str) -> str:
    """uVar1 / lVar2 / cVar3 / iVar4 / sVar5 → v1 / v2 / v3 / v4 / v5。"""
    return VAR_RE.sub(lambda m: f"v{m.group(2)}", line)


def translate_params(line: str, param_names: list[str]) -> str:
    """param_1 → this，param_2 → param_names[0]，param_3 → param_names[1]，依此類推。"""
    def repl(m: re.Match[str]) -> str:
        n = int(m.group(1))
        if n == 1:
            return "this"
        idx = n - 2
        if 0 <= idx < len(param_names):
            return param_names[idx]
        return m.group(0)
    return re.sub(r"\bparam_(\d+)\b", repl, line)


# ─────────────────────────────────────────────────────────────────────
# Hex / 字面量翻譯
# ─────────────────────────────────────────────────────────────────────


def translate_literals(line: str, return_type: str) -> str:
    # long/ulong 的 0xffffffffffffffff → -1L
    if re.search(r"\b(?:long|int64)\b", return_type, re.IGNORECASE):
        line = re.sub(r"\b0xffffffffffffffff\b", "-1L", line)
    if return_type in ("int", "Int32"):
        line = re.sub(r"\b0xffffffff\b", "-1", line)
    # Ghidra 寫 '\0' → 0
    line = line.replace("'\\0'", "0")
    return line


# ─────────────────────────────────────────────────────────────────────
# Cleanup: 把未識別的非空行包成 Ghidra 註解
# ─────────────────────────────────────────────────────────────────────


def is_recognized_cs(line: str) -> bool:
    """粗判翻譯後是否已接近合法 C#。用於決定是否包成註解。"""
    s = line.strip()
    if not s:
        return True
    # 純控制流關鍵字：認可
    if re.match(r"^(if|else|else if|return|break|continue|while|for|switch|case|default|\{|\})", s):
        return True
    # 含 thunk_FUN / FUN_ / undefined / param_N / DAT_ / RVA / IFix_ → 未翻乾淨
    if re.search(
        r"thunk_FUN_|FUN_18|\bundefined\d*\b|\bparam_\d+\b|\bDAT_[0-9a-fA-F]+\b|IFix_(?:WrappersManagerImpl|ILFixDynamicMethodWrapper)",
        s,
    ):
        return False
    # 含 Method_ symbol → 未翻乾淨
    if re.search(r"\bMethod_[\w<>, ]+__\b", s):
        return False
    # 含 ___ctor / __get_ / __set_ 等仍是 demangled symbol
    if re.search(r"__(?:ctor|get_|set_|Add|Remove|Contains|Clear)__?", s):
        return False
    return True


def wrap_unknown_as_comments(lines: list[str]) -> list[str]:
    out: list[str] = []
    for l in lines:
        if is_recognized_cs(l):
            out.append(l)
        else:
            stripped = l.strip()
            if stripped:
                out.append(f"// Ghidra: {stripped}")
            else:
                out.append("")
    return out


# ─────────────────────────────────────────────────────────────────────
# 主入口
# ─────────────────────────────────────────────────────────────────────


def translate_method_body(
    ghidra_block_text: str,
    field_map: dict[int, tuple[str, str]],
    method_ctx: MethodContext,
    indent: str = "\t\t",
) -> str:
    """從 `/* === Ghidra... === */` 區塊文字產出翻譯後的 method body 文字。

    輸出不含外層 method 大括號，每行已加 `indent` 縮排。
    """
    lines = unwrap_ghidra(ghidra_block_text)
    if not lines:
        return ""
    lines = strip_function_header(lines)
    lines = merge_multiline_statements(lines)
    lines = strip_static_init_guard(lines)
    lines = strip_ifix_fastpath(lines)
    lines = strip_runtime_helpers(lines)
    lines = translate_alloc_init_pattern(lines, field_map)

    # 逐行 line-level transforms
    out: list[str] = []
    for l in lines:
        x = l
        x = translate_field_reads(x, field_map)
        x = translate_stdlib(x)
        x = normalize_var_names(x)
        x = translate_params(x, method_ctx.param_names)
        x = translate_literals(x, method_ctx.return_type)
        out.append(x)

    out = wrap_unknown_as_comments(out)
    # 去重連續空白行
    deduped: list[str] = []
    prev_blank = False
    for l in out:
        if not l.strip():
            if prev_blank:
                continue
            prev_blank = True
        else:
            prev_blank = False
        deduped.append(l)
    while deduped and not deduped[0].strip():
        deduped.pop(0)
    while deduped and not deduped[-1].strip():
        deduped.pop()
    return "\n".join(indent + l if l.strip() else "" for l in deduped)


# ─────────────────────────────────────────────────────────────────────
# File-level processing：在 preserved C# 內逐 method 替換 Ghidra 區塊
# ─────────────────────────────────────────────────────────────────────


METHOD_START_RE = re.compile(
    r"^(\s*)((?:(?:public|protected|internal|private)\s+)"
    r"(?:(?:static|virtual|override|abstract|sealed|new|async|extern|unsafe)\s+)*"
    r"(?:[\w<>, ?\[\]]+\s+)?\w+\s*\([^)]*\))\s*$",
    re.MULTILINE,
)


def translate_file(
    annotated_text: str,
    preserved_text: str,
    class_name: str,
) -> tuple[str, int, int]:
    """處理整檔。

    Args:
      annotated_text: 原 Annotated.cs 全文（用來抽 field offset map）
      preserved_text: 已 transform 但 needs-llm 保留 Ghidra 在 method body 內的中間文字
      class_name: 主 class 名稱

    Returns:
      (translated_text, methods_translated, methods_total)
    """
    field_map = extract_field_offset_map(annotated_text)

    # 切片：找每個 method 開頭，從 `{` 到匹配的 `}` 區塊
    # 反向處理：先收集所有 match，從後往前替換，避免位置漂移
    text = preserved_text
    total = 0
    translated = 0
    all_matches = list(METHOD_START_RE.finditer(text))

    for m in reversed(all_matches):
        sig_start = m.start()
        sig_end = m.end()
        # 找 method body 的開頭 `{`
        i = sig_end
        while i < len(text) and text[i] in " \t\r\n":
            i += 1
        if i >= len(text) or text[i] != "{":
            continue
        # 找匹配的 `}`
        depth = 1
        j = i + 1
        # 處理字串字面值 & 註解
        in_block_comment = False
        in_line_comment = False
        in_string = False
        in_char = False
        while j < len(text):
            ch = text[j]
            nxt = text[j + 1] if j + 1 < len(text) else ""
            if in_block_comment:
                if ch == "*" and nxt == "/":
                    in_block_comment = False
                    j += 2
                    continue
            elif in_line_comment:
                if ch == "\n":
                    in_line_comment = False
            elif in_string:
                if ch == "\\" and nxt:
                    j += 2
                    continue
                if ch == '"':
                    in_string = False
            elif in_char:
                if ch == "\\" and nxt:
                    j += 2
                    continue
                if ch == "'":
                    in_char = False
            else:
                if ch == "/" and nxt == "*":
                    in_block_comment = True
                    j += 2
                    continue
                elif ch == "/" and nxt == "/":
                    in_line_comment = True
                    j += 2
                    continue
                elif ch == '"':
                    in_string = True
                elif ch == "'":
                    in_char = True
                elif ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        break
            j += 1
        if j >= len(text):
            continue

        body_open = i  # index of '{'
        body_close = j  # index of '}'
        body_inner = text[body_open + 1 : body_close]

        # 抓 body 內第一個 Ghidra 區塊
        gm = GHIDRA_BLOCK_RE.search(body_inner)
        total += 1
        if not gm:
            continue

        # parse sig
        ctx = parse_method_signature(m.group(0), class_name)
        if not ctx:
            continue

        # 翻譯 Ghidra
        translated_body = translate_method_body(
            gm.group(0), field_map, ctx, indent=m.group(1) + "\t"
        )

        # 用翻譯後的 body 取代整個 Ghidra 區塊（含註解前後空白）
        ghidra_start_in_body = gm.start()
        ghidra_end_in_body = gm.end()
        # 也清掉緊隨 Ghidra 後的 `return default(...);` 殘留（transform 留下的）
        trailing_default_re = re.compile(
            r"\s*return\s+default\([^)]*\)\s*;\s*\n?|\s*return\s+null\s*;\s*\n?"
        )
        after = body_inner[ghidra_end_in_body:]
        m_def = trailing_default_re.match(after)
        if m_def:
            ghidra_end_in_body = gm.end() + m_def.end()

        new_inner = (
            body_inner[:ghidra_start_in_body]
            + ("\n" + translated_body + "\n" if translated_body else "")
            + body_inner[ghidra_end_in_body:]
        )
        # 重組整檔
        text = text[: body_open + 1] + new_inner + text[body_close:]
        translated += 1

    return text, translated, total


if __name__ == "__main__":
    import sys
    print(__doc__)
    sys.exit(0)
