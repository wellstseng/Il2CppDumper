# Doomsday Phase 2 — LLM 翻譯 SOP

> Phase 1 已完成：`RestoredSolution/Annotated/` 含 35,802 個 .cs（ILSpy skeleton + 嵌入 Ghidra pseudocode）。
> Phase 2 目的：把 `Annotated/<dll>/<...>.cs` 翻譯成 `Final/<dll>/<...>.cs`（**還原成 IL2CPP 編譯前的 .NET 源碼**），可被 VS / VS Code OmniSharp 導覽。

---

## 0. 校準：什麼叫「忠實」

「忠實」≠「忠於反組譯 pseudocode 的中間表示」。
「忠實」=「**還原成 IL2CPP 編譯前的 .NET 源碼**」——也就是程式設計師當初寫的 C# 程式，被 IL2CPP/IFix/Mono.Cecil 工具鏈處理過後留下的中間痕跡都要清掉。

> **判斷標準**：問自己「.NET 源碼會這樣寫嗎？」
> - 是 → 保留
> - 否 → 是 IL2CPP / IFix / runtime 注入的噪音 → 移除或翻譯回原始 idiom

---

## 1. 邏輯層（保留）

逐行對應 pseudocode 的：
- 賦值順序 / 條件判斷 / 迴圈結構 / return path
- 業務 API 呼叫順序（Ghidra demangled 過的 `Namespace_Type__Method` symbol → C# instance/static call）
- 算術運算（含 packed-int64 `CONCAT44(hi, lo)` 拆解）

---

## 2. 命名 / 包裝層（翻譯成人話）

| Ghidra raw | 翻譯成 | 原因 |
|---|---|---|
| `FUN_18055b3e0()`（標 "Subroutine does not return"） | `throw new Exception();` 或**整段省略** | IL2CPP null-deref defensive trap，.NET 源碼不寫 |
| `FUN_18055a480(ref field, value)` | **完全省略** | IL2CPP managed write barrier，C# 內 implicit |
| `il2cpp_runtime_class_init()` | **完全省略** | 靜態 class init lazy guard，C# runtime 處理 |
| `il2cpp_value_box(T_TypeInfo, &val)` | **完全省略**（或 `(object)val`） | C# auto-box |
| `il2cpp_object_unbox` | C# unbox cast `(T)obj` | |
| `thunk_FUN_1805e65d0(X_TypeInfo)` + `X__ctor(plVar3, args)` | `new X(args)`（合成兩步） | IL2CPP 物件配置拆成 alloc + ctor，C# 一行 |
| `IsPatched(0xb3d, 0)` 的 trailing `0` | **省略**（只留 `IsPatched(0xb3d)`） | IL2CPP method-info pointer，calling convention noise |
| `stream.vtable_338(args)` | 推測對應 .NET API（FileStream.SetLength / Write / Read 等） | vtable slot 對應實際方法；不確定時保留 raw + 短註解 |
| `*(int*)(arr + 0x18)` | `arr.Length` | IL2CPP managed array length 在 +0x18 |
| `*(undefined? *)(this + 0xXX)` | 對照 `[FieldOffset(Offset="0xXX")]` 翻成 field 名 | |
| `Method_Singleton<T>_get_Inst__` + `IGG_Framework_Singleton<object>__get_Inst(...)` | `Singleton<T>.Inst` | |
| `UnityEngine_Object__op_Inequality(a, b, 0)` | `a != b` | |
| `System_String__Format(StringLiteral_N, ...)` | `string.Format("...", ...)`，**查 ScriptString 取真值** | |

---

## 3. 框架注入（整段移除）

`Annotated` 內每個 method 都會有的 boilerplate，**Final 內整段砍掉**：

### IFix 熱更 fast-path
```c
if (IFix.WrappersManagerImpl.IsPatched(0xb3d, 0)) {
    var patch = IFix.WrappersManagerImpl.GetPatch(0xb3d, 0);
    if (patch != 0) return ILFixDynamicMethodWrapper.__Gen_Wrap_N(patch, args);
    FUN_18055b3e0();
}
```
**理由**：IFix 是 build-time CIL injection，原 .NET 源碼從不寫這段。

### Null-deref defensive trap
原 .NET source 不寫 `if (foo == null) throw new NullReferenceException();`——C# runtime 自動處理。IL2CPP 之所以有是因為 `il2cpp_codegen_raise_null_reference_exception` helper inline。

### 靜態 init guard
```c
if (DAT_18b62b17b == '\0') {
    FUN_18055b140(&Some_TypeInfo);
    DAT_18b62b17b = '\x01';
}
```
這是 IL2CPP runtime 對 static type initialization 的 lazy guard，**完全省略**。

---

## 4. ILSpy attribute（全砍）

`Annotated` 內每個 type/field/method 都帶這些（ILSpy IL2CPP-marker），**Final 砍掉**：
- `[Token(Token = "0x...")]` — IL token id
- `[FieldOffset(Offset = "0x...")]` — IL2CPP runtime offset 信息
- `[Address(RVA = "...", Offset = "...", VA = "...")]` — 反組譯位址
- `using Il2CppDummyDll;` — ILSpy 的 namespace import

**例外**：C# 本身的 attribute（`[Flags]`、`[Serializable]`、`[MethodImpl]` 等）保留。

---

## 5. 慣用 C# 用回來

| Pseudocode 醜寫 | C# 寫法 |
|---|---|
| `var x = foo(...); if (x == null) return null; return x.bar;` | `return foo(...)?.bar;` |
| `if (obj != null) { var t = (T)obj; if (t.X == this.X) return true; } return false;` | `obj is T t && t.X == this.X` |
| 多個 explicit `using { ... .Dispose(); }` 巢狀 | `using var stream = ...;` |
| Constructor body 內 3 個賦值對應 `[FieldOffset]` 順序 | constructor body 保留賦值（不要搬到 field initializer） |
| 空 `override OnGraphStart(...)` / `PrepareFrame(...)` 等 base 預設 | **省略**（Unity Timeline 慣例） |

---

## 6. 不確定時的處理

- **不查就不要推測**：StringLiteral_N 一定查 `script.json` 的 ScriptString[N-1]（1-based）
- **真不知道的 vtable**：保留 `stream.vtable_348(args)` + 短行尾註解 `// best guess / unknown slot`
- **Symbol collision**（Ghidra base ctor 解析成不相關的 type）：當作隱式 base call，不寫不註解。pseudocode 註解區塊整體保留在 `Annotated/`，Final 不需要重複
- **腳本工具翻譯時的例外**（**前提：用 `tools/restore_phase2.py` + `phase2_ghidra_translator.py` 機械工具，非 LLM**）：
  - 工具走**保守白名單翻譯**：100% 可決定性對應的模式（field offset 表查得到、stdlib symbol 在白名單、IFix/init guard/null trap 框架雜訊）→ 翻成 C# 寫法
  - 工具**無法翻譯**的行（未知 demangled symbol / 複雜泛型 / 控制流變體 / 不確定語義）→ **保留原 Ghidra pseudocode** 以 `// Ghidra: <原文>` 行內註解形式，不發明、不推測
  - 不能加油添醋：寧可保留 Ghidra 註解，不要編造看似合理但無依據的 C# 邏輯
  - 在檔案 header 加一行：`// Note: Method bodies auto-translated from Ghidra pseudocode by tools/phase2_ghidra_translator.py (conservative whitelist; untranslated parts retained as // Ghidra: comments).`
  - 不適用 LLM 翻譯：LLM 仍應依 §5 嘗試從 demangled symbol 還原業務 API，不要把整段 Ghidra 抄進去

---

## 7. 檔案結構規約

### Final/ 目錄鏡像 _raw/ 結構
```
RestoredSolution/Final/
├── Doomsday.Restored.csproj
├── Assembly-CSharp/
│   └── *.cs
├── dls.game/
│   ├── IGG.Game.Helper/
│   ├── IGG.Game.Module.*/
│   └── ...
└── dls.framework/
    └── ...
```

### 每個 .cs 頂部第一行
```csharp
// Annotated: ../../Annotated/<dll>/<namespace>/<TypeName>.cs
```
（相對路徑從當前 .cs 所在目錄出發。讓人類 + 工具能跳回原始 Ghidra-annotated 版對照）

### Doomsday.Restored.csproj 關鍵設定
- `<TargetFramework>net8.0</TargetFramework>`
- `<Nullable>disable</Nullable>` + `<ImplicitUsings>disable</ImplicitUsings>`
- Reference 用 **path-form Include**（**不能** simple-name + HintPath，會 unresolved）：
  ```xml
  <Reference Include="..\..\output\DummyDll\Assembly-CSharp.dll" />
  ```
- 不能用 wildcard / `@()` expansion in `<Reference Include>` — 必須**列每個 dll**
- 路徑算層數：csproj 在 `Final/` → DummyDll 在 `../../output/DummyDll/`

---

## 8. 工作流（per type）

1. 讀 `Annotated/<path>/<Type>.cs`（含 pseudocode）
2. 對每個 method body：
   a. 識別 IFix patch fast-path → 整段移除
   b. 識別 null defensive trap / write barrier / class_init → 整段移除
   c. 識別 thunk + ctor → 合成 `new X(...)`
   d. demangled symbol → C# call
   e. magic offset → field 名（對照 `[FieldOffset]`）
   f. StringLiteral_N → 查 ScriptString[N-1] 取真值
3. 移除 ILSpy attribute
4. 用 C# idiom 重寫（pattern match / using var / null-conditional）
5. 寫到 `Final/<path>/<Type>.cs`，頂部加 `// Annotated:` 註解

---

## 9. 已產出 sample 對照

驗證過此 SOP 的 6 個 sample（涵蓋從簡單到複雜）：

| Final 檔 | Annotated 行數 | Final 行數 | 性質 |
|---|---|---|---|
| `Final/Assembly-CSharp/TroopFormater.cs` | 44 | 18 | MonoBehaviour + 簡單 init |
| `Final/Assembly-CSharp/PlayAudio.cs` | 108 | 13 | Unity Timeline + Singleton call |
| `Final/Assembly-CSharp/GuideTimelineMessageBehaviour.cs` | 141 | 15 | Timeline + 多層 navigation |
| `Final/dls.framework/IGG.Framework.Helper/PosAxisHelper.cs` | 157 | 13 | bitflag extensions |
| `Final/dls.framework/IGG.Framework.Event/EventListener.cs` | 230 | 60 | Disposable event listener |
| `Final/dls.game/IGG.Game.Helper/BytesHelper.cs` | 295 | 57 | File I/O with player path |
| `Final/dls.game/HexCoord.cs` | 355 | 65 | 完整 struct（16 method：ctor / operators / Equals / GetHashCode） |

平均壓縮比 **~5x**（Annotated → Final），核心業務邏輯保留 100%。

---

## 10. 規模 / 成本估（按需執行）

| 模型 | 全 27.9 萬 method 翻譯估價 | 時程 |
|---|---|---|
| Haiku 4.5 | ~$1,100 | 1-2 天（10 並行 agent） |
| Sonnet 4.6 | ~$2,500 | 1-3 天 |
| Opus 4.7 | ~$15,000 | 5-10 天 |

> **建議**：按 namespace 增量做。先選 1-2 個高價值 namespace（戰鬥 / 任務 / 經濟系統等）試水，再決定要不要全量。
