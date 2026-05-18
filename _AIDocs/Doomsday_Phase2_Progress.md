# Doomsday Phase2 Annotated→Final — 多 agent 平行協調

> 最後更新：2026-05-18 23:45（撤回 Phase2 程式翻譯路線；Final 改回人工/LLM 還原）
> 目的：協調 Claude (judy-cli) + Codex 平行翻譯，避免重複作業
> 權威 SOP：見 §「Codex 必讀清單」

---

## 1. 當前完成狀態（per dll）

| dll | Annotated | Final | 狀態 | 處理者 |
|---|---:|---:|---|---|
| Assembly-CSharp-firstpass | 9 | 9 | ✅ 完成 | Claude Batch-1 |
| Assembly-CSharp | 536 | 5 | 🟡 partial (S1 早期 sample) | — 未認領 |
| behaviac.runtime | 177 | 177 | ✅ 完成 | Claude C3a/b + Codex redo |
| dls.config | 2,946 | 0 | ⬜ 未開始 | — 未認領 |
| dls.framework.common | 234 | 15 | 🟡 partial | — 未認領 |
| dls.framework.unsafe | 4 | 4 | ✅ 完成 | Claude Batch-1 |
| dls.framework | 547 | 2 | 🟡 partial (S1 早期 sample) | — 未認領 |
| dls.game | 7,828 | 45 | 🟡 partial (S1 Launch/Login/MainScene/Cache 已完成) | — 未認領 |
| dls.im | 380 | 374 | ⚠️ 需重檢（先前為程式翻譯產物，不列品質基準） | — 待重新認領 |
| dls.message | 7,867 | 0 | ⬜ 未開始 | — 未認領 |
| dls.plugins.processcontext | 6 | 6 | ✅ 完成 | Claude Batch-1 |
| dls.ui.base | 11,128 | 0 | ⬜ 未開始（最大 dll） | — 未認領 |
| Epic | 1,698 | 0 | ⬜ 未開始 | — 未認領 |
| IFix.Core | 34 | 33 | ✅ 完成（VirtualMachine.cs stub 化，ILSpy 無法解析；Properties/AssemblyInfo.cs skip：build metadata 無業務語意） | Claude IFix-S1+S2 |
| netease | 40 | 40 | ✅ 完成 | Claude C1 |
| sdk.peapod | 10 | 10 | ✅ 完成 | Claude Batch-1 |
| TapticFeedback | 5 | 5 | ✅ 完成 | Claude Batch-1 |
| USDK.Bridge | 62 | 62 | ✅ 完成 | Claude C1 |
| USDK.Foundation | 123 | 123 | ✅ 完成 | Claude C2 + Codex redo |
| USDK.Module.AIGuide | 48 | 48 | ✅ 完成 | Claude Batch-9 |
| USDK.Module.BlacklistedWord.Editor | 51 | 50 | ✅ 完成 (1 skip: n.cs 1610 行) | Claude Batch-10 |
| USDK.Module.CPD.Editor | 40 | 40 | ✅ 完成 | Claude C1 + Codex redo |
| USDK.Module.Operations.Editor | 207 | 25 | 🟡 partial | — 未認領 |
| USDK.Module.Push.Editor | 46 | 46 | ✅ 完成 | Claude Batch-9 |
| USDK.Windows | 1,776 | 0 | ⬜ 未開始 | — 未認領 |

**進度總計**：Annotated 35,802 檔，有效 Final 落地 748 檔（不含 dls.im 先前程式翻譯產物 374 檔）≈ **2.1%**

---

## 2. Claude 當前 in-flight agent（不要碰這些）

| agent | 範圍 | 預估完成 |
|---|---|---|
| Batch-C1 | netease 缺 0 / USDK.Bridge 缺 10 / USDK.Module.CPD.Editor 缺 34 | ~15-20 分鐘 |
| Batch-C2 | USDK.Foundation 缺 66 | ~15-20 分鐘 |
| Batch-C3a | behaviac.runtime 缺檔字母序前 60 | ~15-20 分鐘 |
| Batch-C3b | behaviac.runtime 缺檔字母序後 62 | ~15-20 分鐘 |

> 2026-05-18 14:47 更新：Claude 撞上限前已部分落地；Codex 10:29 補尾產物曾因空殼化退回，14:47 已重做並完成抽樣品質檢查。

**Claude 接下來會啟動的**（仍未啟，可被 Codex 搶）：
- USDK.Module.Operations.Editor 殘 182 檔
- dls.framework.common 殘 219 檔
- dls.im 全 380 檔（小型 IM 模組）
- Assembly-CSharp 殘 531 檔（含 S1 5 個 sample）
- dls.framework 殘 545 檔（含 S1 2 個 sample）

---

## 3. 建議 Codex 認領的 dll（互不衝突）

按優先順序：

1. **dls.im** (380 檔，0 完成) — 中型，純未開始，最容易並行
2. **dls.config** (2,946 檔，0 完成) — 大型但純未開始
3. **USDK.Windows** (1,776 檔，0 完成) — 大型純未開始
4. **Epic** (1,698 檔，0 完成) — 大型純未開始
5. **dls.message** (7,867 檔，0 完成) — 超大但純未開始

避免：dls.game / dls.framework / Assembly-CSharp / behaviac.runtime / USDK.Foundation / USDK.Bridge / netease / USDK.Module.CPD.Editor —— Claude 已在處理或已有 partial 產出，並行容易撞檔。

**Codex 認領後請更新本檔的「處理者」欄**（簡單 string 註記即可，例：`Codex (gpt-5-codex)`）。

---

## 4. Codex 必讀清單（翻譯 SOP）

開工前必讀：
1. `/Users/wellstseng/.claude/memory/_staging/_il2cpp_source_restore.md` — 通用 SOP（「忠實 = 還原 IL2CPP 編譯前的 .NET 源碼」校準）
2. `/Users/wellstseng/project/Il2CppDumper/memory/_staging/Doomsday_Phase2_SOP.md` — 專案 SOP（含 IFix fast-path 處置 §3）
3. `/Users/wellstseng/project/Il2CppDumper/_AIDocs/Doomsday_IFix_Hotpatch.md` — IFix 熱更機制摘要（IFix fast-path 出現時要砍）

**參考 sample**（已完成風格範本）：
- `Input/Doomsday/RestoredSolution/Final/dls.game/IGG.Game.Module.Launch/GameContext.cs`（含已砍 IFix fast-path 範例）
- `Input/Doomsday/RestoredSolution/Final/dls.framework/IGG.Framework.Event/EventListener.cs`
- `Input/Doomsday/RestoredSolution/Final/USDK.Module.AIGuide/`（剛完成 dll，可看整族）
- `Input/Doomsday/RestoredSolution/Final/IFix.Core/IFix.Core/Call.cs`（unsafe 模板化 PushXxx/GetXxx）

---

## 5. 翻譯硬規則速查（給 Codex）

**砍掉**：
- ILSpy attribute（`[Token]` / `[FieldOffset]` / `[Address]`）
- `using Il2CppDummyDll;`
- IFix fast-path 整段（`IsPatched(N) / GetPatch(N) / __Gen_Wrap_N` 三段組合）
- `il2cpp_runtime_class_init` / `FUN_18055b3e0` null-deref trap / `FUN_18055a480` write barrier
- IL2CPP method-info pointer trailing `0`（calling convention noise）
- 靜態 init guard `if (DAT_xxx == '\0') { FUN_xxx(&TypeInfo); DAT_xxx = '\x01'; }`

**翻譯**：
- `thunk_FUN_xxx(TypeInfo) + X__ctor(plVar, args)` → `new X(args)`
- `IsPatched(0xb3d, 0)` 的 trailing `0` 省略
- `*(int*)(arr + 0x18)` → `arr.Length`
- `*(T *)(this + 0xXX)` → 對照 `[FieldOffset]` 翻成 field 名
- demangled symbol → C# instance/static call
- `UnityEngine_Object__op_Inequality(a, b, 0)` → `a != b`

**保留**：
- C# attribute（`[Flags]` / `[Serializable]` / `[MethodImpl]`）
- `unsafe` 指標操作（IFix runtime / Value*/Instruction* 等）

**ILSpy 失敗 stub**：method body 只剩 pseudocode 註解 + `return null` / 空 body —— **不要從 pseudocode 反推**。保留 stub + 加 1 行註解「ILSpy could not decompile; see Annotated L<X>-<Y> Ghidra pseudocode (RVA 0x...) for reference」

**不要**：
- 加 `// Note:` `// Suspicious:` 推測註解
- 發明 helper API（如 `Patches.InvokeVoid`）
- 憑感覺推測 StringLiteral 真值（要查 `script.json` 內 `ScriptString[N-1]`）
- 一次 Read > 1500 行（agent context 撐不住）

---

## 6. 檔案頂部 `// Annotated:` 路徑規則

每檔頂部第一行：
```csharp
// Annotated: <相對路徑回 Annotated 對應檔>
```

計算規則：從 `Final/<dll>/<sub-path>/<File>.cs` 出發，跳到 `RestoredSolution/`，然後接 `Annotated/<dll>/<sub-path>/<File>.cs`。
- 無 sub：`Final/<dll>/Foo.cs` → 2 個 `..` → `../../Annotated/<dll>/Foo.cs`
- 1 層 sub：`Final/<dll>/Sub/Foo.cs` → 3 個 `..` → `../../../Annotated/<dll>/Sub/Foo.cs`
- 2 層 sub → 4 個 `..`
- 例外：`IFix.Core` 因為結構是 `Final/IFix.Core/IFix.Core/Foo.cs`（多一層 wrapper），所以 1 層 sub 用 3 個 `..`

---

## 7. 輸出位置

每檔輸出到鏡像路徑：
- 來源：`/Users/wellstseng/project/Il2CppDumper/Input/Doomsday/RestoredSolution/Annotated/<dll>/<path>/<File>.cs`
- 輸出：`/Users/wellstseng/project/Il2CppDumper/Input/Doomsday/RestoredSolution/Final/<dll>/<path>/<File>.cs`（鏡像結構，`mkdir -p` 確保子目錄存在）

整個 `Input/Doomsday/` 被 `.gitignore` 排除，**不會進 git**，所以 Codex 直接寫磁碟即可，無需 commit。

---

## 8. 完成回報

每 Codex 完成一批後，更新本檔的 §1 表格（更新 Final 計數 + 處理者欄），並追加：

```markdown
## 9. Codex 已完成批次

- 2026-05-18 HH:MM Codex `<batch-name>` — `<dll>` 完成 X/Y 檔，skip Z 個（原因）
```

## 9. Codex 已完成批次

- 2026-05-18 10:29 Codex `Claude-C2-tail` — `USDK.Foundation` 產出 24 檔，但品質不合格：多數 method 未依 Annotated pseudocode 還原，需重做
- 2026-05-18 10:29 Codex `Claude-C1-tail` — `USDK.Module.CPD.Editor` 產出 12 檔，但品質不合格：多數 method 未依 Annotated pseudocode 還原，需重做
- 2026-05-18 10:29 Codex `Claude-C3-tail` — `behaviac.runtime` 產出 35 檔，但品質不合格：多數 method 未依 Annotated pseudocode 還原，需重做
- 2026-05-18 14:47 Codex `Claude-C2-tail-redo` — `USDK.Foundation` 重做 25 檔，完成 123/123；抽查 `GPCUIFramework` / `GPCUIModuleBaseBehaviour` / loader/provider/helper 類，已從空殼改為 field-backed property、singleton、Unity object/component、loader fallback 等可讀 C# 實作
- 2026-05-18 14:47 Codex `Claude-C1-tail-redo` — `USDK.Module.CPD.Editor` 重做 12 檔，完成 40/40；抽查 CPD diagnosis / metric / bridge command 類，已還原 event add/remove、ctor 初始化、scene metric JSON、dispose/lazy init 等邏輯
- 2026-05-18 14:47 Codex `Claude-C3-tail-redo` — `behaviac.runtime` 重做 35 檔，完成 177/177；抽查 `Agent` / `Workspace` / `MiniXmlParser` / behavior task 類，已改為 behaviac runtime 風格實作，剩餘 `return null/default` 為 not found / fallback / disabled path 語意
- 2026-05-18 23:45 Codex `Phase2 rule cleanup` — 撤回程式翻譯路線；dls.im 先前產物改列需重檢，後續 Final 一律回到人工/LLM 依 Annotated 還原
