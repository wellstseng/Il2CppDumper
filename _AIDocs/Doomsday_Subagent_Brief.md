# Doomsday Phase2 Subagent Brief

> 用途：S2/S5/S6 各 batch 派 subagent 時的共用 SOP brief。每個派工 prompt 引用本檔，不再逐字重複 §2-§4。
> 對應規則：`memory/_staging/Doomsday_Phase2_SOP.md`（§2 命名翻譯、§3 框架注入、§4 ILSpy attribute、§6 不確定處理）

---

## 1. 來源 / 輸出

- 讀：`Input/Doomsday/RestoredSolution/Annotated/<dll>/<namespace>/<File>.cs`
- 寫：`Input/Doomsday/RestoredSolution/Final/<dll>/<namespace>/<File>.cs`
- 每檔頂部第一行：`// Annotated: <相對路徑回 Annotated>`
  - 算層數：`Final/<dll>/<sub-path>/<File>.cs` → 跳到 `RestoredSolution/` 再接 `Annotated/<dll>/<sub-path>/<File>.cs`
  - 例：`Final/dls.game/IGG.Game.Helper/X.cs` → 3 個 `..` → `../../../Annotated/dls.game/IGG.Game.Helper/X.cs`

## 2. 砍（IL2CPP / IFix / Ghidra 噪音）

- ILSpy attribute（含 `Il2CppDummyDll.` qualified prefix）：
  - `[Token(Token = "0x...")]`
  - `[Address(RVA = "...", Offset = "...", VA = "...")]`
  - `[FieldOffset(Offset = "0x...")]`
  - `[MetadataOffset(Offset = "...")]`
- `using Il2CppDummyDll;`
- IFix fast-path 整段：
  ```c
  if (IFix.WrappersManagerImpl.IsPatched(0xXXX, 0)) {
      var p = IFix.WrappersManagerImpl.GetPatch(0xXXX, 0);
      if (p != 0) return IFix.ILFixDynamicMethodWrapper.__Gen_Wrap_N(p, args);
  }
  ```
- `il2cpp_runtime_class_init(...)` / `FUN_18055b3e0()` null-deref trap / `FUN_18055a480(ref ...)` write barrier
- 靜態 init guard：`if (DAT_xxx == '\0') { FUN_18055b140(&Type_TypeInfo); DAT_xxx = '\x01'; }`
- 嵌入 Ghidra pseudocode block：`/* === Ghidra pseudocode RVA 0x... === ... === end pseudocode === */`
- IL2CPP method-info pointer trailing `0`（calling convention noise）：`IsPatched(0xb3d, 0)` 的 `0`、`new X(args, 0)` 的尾 `0`

## 3. 翻（pseudocode → C# idiom）

| Ghidra 寫法 | C# 寫法 |
|---|---|
| `thunk_FUN_xxx(TypeInfo) + X__ctor(plVar, args)` | `new X(args)` |
| demangled `Namespace_Type__Method(this, args)` | `this.Method(args)` |
| `*(int*)(arr + 0x18)` | `arr.Length`（managed array len 在 +0x18） |
| `*(T *)(this + 0xXX)` | 對照 `[FieldOffset]` 翻成 field 名 |
| `UnityEngine_Object__op_Inequality(a, b, 0)` | `a != b` |
| `UnityEngine_Object__op_Equality(a, b, 0)` | `a == b` |
| `IGG_Framework_Singleton<object>__get_Inst(Method_..._get_Inst__)` | `Singleton<T>.Inst` |
| `IGG_Framework_Config_BaseDao<object,uint,object>__get_Inst(...)` | `BaseDao<T, TKey, TCfg>.Inst` |
| `BaseDao<...>__GetCfg(inst, key, 0, ...)` | `inst.GetCfg(key)` |
| `System_String__Format(StringLiteral_N, args, 0)` | `string.Format("<查 ScriptString[N-1]>", args)` |
| `System_String__Concat(StringLiteral_A, x, StringLiteral_B, 0)` | `"<A>" + x + "<B>"` 或 `string.Concat(...)` |
| `System_String__StartsWith(s, StringLiteral_N, 0)` | `s.StartsWith("<查 ScriptString[N-1]>")` |
| `UnityEngine_Component__GetComponent<object>(go, Method_..._GetComponent<T>__)` | `go.GetComponent<T>()` |
| `UnityEngine_Transform__GetParent(t, 0)` | `t.parent` |
| packed-int64 `CONCAT44(hi, lo)` | `((long)hi << 32) \| lo` |

## 4. 保留（C# 原生）

- C# attribute：`[Flags]`, `[Serializable]`, `[MethodImpl(MethodImplOptions.AggressiveInlining)]`, `[Conditional]`, `[Obsolete]`, `[DllImport]`
- `unsafe` block（IFix runtime / pointer arithmetic 需要時）
- `partial` modifier
- explicit interface impl 簽名（除非 Roslyn 衝突，見 §6）

## 5. StringLiteral 查表（必查）

```bash
jq -r '.ScriptString[N-1].Value' Input/Doomsday/output/script.json
```

**1-based！**Annotated 寫 `StringLiteral_4422` → 查 `ScriptString[4421]`。批次查多個：

```bash
jq -r '[.ScriptString[4421], .ScriptString[83699], .ScriptString[10210]] | map(.Value) | .[]' Input/Doomsday/output/script.json
```

不查就不要猜。

## 6. 不確定 / 邊界

| 情境 | 處理 |
|---|---|
| ILSpy 抓不到 method body（只剩 IFix fast-path + `return default`） | 保留空 stub + 1 行：`// ILSpy could not decompile; only IFix fast-path visible at RVA 0x...` |
| pseudocode 出現 `vtable_348(args)` 不知 slot 對應 | 保留 `obj.vtable_348(args)` + 行尾 `// best guess / unknown slot` |
| field offset 不在 `[FieldOffset]` 表（如 `+0x78` 沒對應） | 命名按上下文 best-guess + 行尾 `// best guess: offset 0x78` |
| pseudocode 顯式 Roslyn 衝突的 explicit-interface impl（多個同簽名） | 砍 explicit-interface impl，保留 base method；註記「IFix.Core 反射查找受影響部分留 dedicated pass」 |
| Symbol collision（Ghidra base ctor 解析成不相關 type） | 當隱式 base call，不寫不註解 |
| Annotated nested class 與 outer method 同名（IL 結構） | 留待 dedicated pass rename，先 stub |

## 7. 不要

- 加 `// Note:` / `// Suspicious:` 推測註解
- 發明 helper API（如 `Patches.InvokeVoid` / `IL2CppHelper.SafeCall`）
- 從 pseudocode 反推不存在的 .NET source（pseudocode 看不到就是看不到，stub 即可）
- 一次 Read > 1500 行單檔（agent context 撐不住，改分 method/property 讀 200-400 行）
- 動已 Final 的 sample 檔（dll-specific 列表見派工 prompt）
- 把 disk-coverage 當 effective completed（disk-covered 是手段，effective = 業務邏輯被還原）

## 8. Token 控制

- 用到 60% 預算停手，回報已完成 / skip 清單，**不要硬撐**
- 大檔（>500 行）優先 stub-first：保留 type/member skeleton + 空 body + `// ILSpy stub` 註解
- IFix wrapper 大檔（`ILFixDynamicMethodWrapper.cs`）抄 `dls.framework.common` Final 範本
- Skip 檔不要產空檔，留主執行緒 strip-stub 補位

## 9. 完成回報模板

```
Sub-X done
完成 X/Y
Skip Z: <檔名 + 原因>
Marker grep: rg -n "Il2CppDummyDll|\[Token|\[Address|\[FieldOffset|=== Ghidra|FUN_180|StringLiteral_" <本批檔案> → <hits 數 / clean>
亮點: <1-2 個 pattern：Singleton 用法、跨 dll dep、StringLiteral 查表特殊發現等>
```

## 10. 已驗證範本（按複雜度）

| 範本 | 性質 |
|---|---|
| `Final/dls.game/IGG.Game.Helper/BytesHelper.cs` | File I/O + Singleton + `using var stream`（SOP §9 標準） |
| `Final/dls.game/IGG.Game.Helper/SelectionHelper.cs` | `while parent != null + GetComponent<T>` 模式 |
| `Final/dls.game/IGG.Game.Helper/TransformHelp.cs` | 遞迴 childCount loop + name 比對 |
| `Final/dls.framework/IGG.Framework.Event/EventListener.cs` | Disposable + event listener |
| `Final/dls.game/HexCoord.cs` | struct + operators + Equals + GetHashCode |
| `Final/IFix.Core/IFix.Core/Call.cs` | unsafe PushXxx/GetXxx 模板 |

---

## 派工 prompt 引用本檔的方式

```
你是 Doomsday Phase2 S{section}-{batch} Sub-{N}。
按 `_AIDocs/Doomsday_Subagent_Brief.md` SOP，翻譯下列 N 個 `<dll>/<namespace>` 檔（{lines} 行）：
<檔名清單>

【dll-specific 補充】
- 已 Final 的 sample（不要碰）：<list>
- 範本：<最相關的 1-2 個 sample 路徑>

【Skip 條件 dll-specific 補充】
<根據 dll 性質列 1-3 條，如「obfuscated 過密」「protobuf nested message」「IFix nested >3 層」>

開工，60% 預算停手，回報用 §9 模板。
```
