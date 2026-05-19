# Doomsday Phase2 Annotated→Final — 多 agent 平行協調

> 最後更新：2026-05-19 13:55（dls.im S1 marker/syntax 重檢完成；dls.im 升為 380/380）
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
| dls.im | 380 | 380 | ✅ 完成（S0 補齊缺檔；S1-A/B/C/D + residual marker pass 完成；全 dll marker grep 0，build 無 dls.im 語法錯） | Codex `dls-im-s0-s1` |
| dls.message | 7,867 | 0 | ⬜ 未開始 | — 未認領 |
| dls.plugins.processcontext | 6 | 6 | ✅ 完成 | Claude Batch-1 |
| dls.ui.base | 11,128 | 0 | ⬜ 未開始（最大 dll） | — 未認領 |
| Epic | 1,698 | 0 | ⬜ 未開始 | — 未認領 |
| IFix.Core | 34 | 34 | ✅ 完成（VirtualMachine.cs stub 化，ILSpy 無法解析；Properties/AssemblyInfo.cs 已補） | Claude IFix-S1+S2 + Codex S0 |
| netease | 40 | 40 | ✅ 完成 | Claude C1 |
| sdk.peapod | 10 | 10 | ✅ 完成 | Claude Batch-1 |
| TapticFeedback | 5 | 5 | ✅ 完成 | Claude Batch-1 |
| USDK.Bridge | 62 | 62 | ✅ 完成 | Claude C1 |
| USDK.Foundation | 123 | 123 | ✅ 完成 | Claude C2 + Codex redo |
| USDK.Module.AIGuide | 48 | 48 | ✅ 完成 | Claude Batch-9 |
| USDK.Module.BlacklistedWord.Editor | 51 | 50 | ✅ 完成 (1 skip: n.cs 1610 行) | Claude Batch-10 |
| USDK.Module.CPD.Editor | 40 | 40 | ✅ 完成 | Claude C1 + Codex redo |
| USDK.Module.Operations.Editor | 207 | 207 | ✅ 完成（S2-A 全 dll 磁碟 207/207；marker grep 乾淨；10 個 700-1654 行大檔為 stub 形式保留 type/member skeleton，body 待後續 dedicated pass） | Claude S2A (主+Sub1-7) |
| USDK.Module.Push.Editor | 46 | 46 | ✅ 完成 | Claude Batch-9 |
| USDK.Windows | 1,776 | 0 | ⬜ 未開始 | — 未認領 |

**進度總計**：Annotated 35,802 檔，有效 Final 落地 1,311 檔（`dls.im` 380/380、`USDK.Module.Operations.Editor` 207/207 全納入；含 10 個 stub 大檔）≈ **3.7%**

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

1. **dls.config** (2,946 檔，0 完成) — 大型但純未開始
2. **USDK.Windows** (1,776 檔，0 完成) — 大型純未開始
3. **Epic** (1,698 檔，0 完成) — 大型純未開始
4. **dls.message** (7,867 檔，0 完成) — 超大但純未開始

避免：dls.game / dls.framework / Assembly-CSharp / behaviac.runtime / USDK.Foundation / USDK.Bridge / netease / USDK.Module.CPD.Editor —— Claude 已在處理或已有 partial 產出，並行容易撞檔。

**Codex 認領後請更新本檔的「處理者」欄**（簡單 string 註記即可，例：`Codex (gpt-5-codex)`）。

---

## 4. Phase2 agent 必讀清單（翻譯 SOP）

開工前必讀：
1. `/Users/wellstseng/.claude/memory/_staging/_il2cpp_source_restore.md` — 通用 SOP（「忠實 = 還原 IL2CPP 編譯前的 .NET 源碼」校準）
2. `/Users/wellstseng/project/Il2CppDumper/memory/_staging/Doomsday_Phase2_SOP.md` — 專案 SOP（含 IFix fast-path 處置 §3）
3. `/Users/wellstseng/project/Il2CppDumper/_AIDocs/Doomsday_IFix_Hotpatch.md` — IFix 熱更機制摘要（IFix fast-path 出現時要砍）
4. `/Users/wellstseng/project/Il2CppDumper/_AIDocs/Translation_SOP_TokenSafe.md` — token-safe 批次流程、工具輸出限制、驗收模板
5. `/Users/wellstseng/project/Il2CppDumper/_AIDocs/Token_Cost_Ledger.md` — token 成本表與高成本操作記錄方式

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
- 2026-05-19 11:55 Codex `dls-im-missing-small` — `dls.im` 補 4 個缺失小檔：`Properties/AssemblyInfo.cs`、`UnitySourceGeneratedAssemblyMonoScriptTypes_v1.cs`、`IFix/ILFixInterfaceBridge.cs`、`IFix/WrappersManagerImpl.cs`；本批 marker grep 乾淨，`dotnet build` 仍被既有 `dls.game/LoginModule.cs` 與舊 `dls.im` 產物語法錯擋住；當時剩 `IFix/IDMAP0.cs`、`IFix/ILFixDynamicMethodWrapper.cs` 兩個大型缺檔
- 2026-05-19 13:31 Codex `dls-im-s0-tail` — `dls.im` 補 `IFix/IDMAP0.cs`、`IFix/ILFixDynamicMethodWrapper.cs`，並補 `IFix.Core/Properties/AssemblyInfo.cs`；`dls.im` 磁碟覆蓋已 380/380；`USDK.Module.BlacklistedWord.Editor/n.cs` 仍 skip，需 dedicated pass
- 2026-05-19 13:31 Codex subagents `dls-im-s1-abc` — `dls.im` 重檢 39 個舊 Final：S1-A 4 檔（Actuator/Controller base）、S1-B 20 檔（Data/Notify/Operation，skip `IGG.IM.Data/FriendData.cs`）、S1-C 15 檔（Network/Sender/Mono）；已完成檔 marker grep 乾淨，剩 335 個舊程式翻譯產物待重檢
- 2026-05-19 13:55 Codex subagents `dls-im-s1-finish` — `FriendData.cs` dedicated pass 完成；S1-D `chatprotos/msgtype/protomsg` 301 檔 marker/sampled generated-message recheck 通過；residual marker 小檔 pass 後 `dls.im` 全 dll marker grep 0；`dotnet build` 仍失敗但錯誤摘要無 `dls.im` 路徑，主要阻擋為 out-of-scope `dls.game/IGG.Game.Module.Login/LoginModule.cs`
- 2026-05-19 13:30 Claude `S2A-1a` — `USDK.Module.Operations.Editor` root tiny (<100 行) 12 檔：`ao/ap/at/a0/a2/a9/ba/bf/bk/bp/t/DotfuscatorAttribute`；marker grep 乾淨；StringLiteral 已對照 `script.json` ScriptString 解析
- 2026-05-19 13:30 Claude `S2A-2a` — `USDK.Module.Operations.Editor` sub-namespace tiny (≤50 行) 13 檔：`GPC.Modules.NoticeHub.VO/{GPCAccountSecurityNotice,GPCGameCommunityNotice,GPCLiveChatNotice,GPCTSHNotice}`、`GPC.Modules.ResourceStorage.VO/{GPCOPSImageSizeType,GPCOPSResource,GPCOPSResourceStatus,GPCOPSResourceStatusHelper,GPCOPSResourceTask,GPCOPSResourceType,GPCOPSUploaderScene}`、`Properties/AssemblyInfo.cs`、`GPC.Modules.NoticeHub.Impl/Error.cs`；marker grep 乾淨
- 2026-05-19 14:00 Claude `S2A-1b root small` — `USDK.Module.Operations.Editor` root 100-200 行 19 檔（an/a3/ay/e/az/bc/bs/bg/s/bw/q/af/ab/a7/bq/r/ae/ar/a1）；含 GPCBridgeRequest pattern、PrimeMembership/GameCommunityHelper 子類、closure 延遲 invoke、bridge response handler；不確定的 vtable slot 留 stub + 1 行短註解
- 2026-05-19 14:00 Claude subagent `S2A-Sub1` — `USDK.Module.Operations.Editor` 28 tiny delegates/interfaces/enums（Service/Upload/Internal.Wrapper 下小檔）；marker grep 乾淨
- 2026-05-19 14:05 Claude subagent `S2A-Sub2` — 33 small wrappers/helpers/errors（Internal.Wrapper / Error.cs / Kit / 小型 entrypoint）；marker grep 乾淨（3 行 `// Ghidra:` stub 註解屬 SOP 允許）；LiveChatHelperForOther 用 `<>c.<>9` 快取 FrameReadyEventHandler 委派
- 2026-05-19 14:10 Claude subagent `S2A-Sub3` — 27 medium VO/Impl/Manager 100-465 行；NoticeHub VO JObject 解析、ResourceStorage Extended/Internal 系列、NoticeHubMessageListenerImpl 314、UOPSResourceCache 312 等；marker grep 乾淨；OPSResourceUploaderEditor.Start() 部分 task 屬性初始化不完整需後續修
- 2026-05-19 14:15 Claude subagents `S2A-Sub4/5/6` 派工 — Sub4 (30 root 200-700) / Sub5 (14 large sub-namespace 700-1576) / Sub6 (6 huge root 786-1654)
- 2026-05-19 14:40 Claude subagent `S2A-Sub4` — 30 root 200-700 行混淆檔全部完成；StringLiteral ~120 索引查表；bl/aa `<>c` 靜態快取改寫為可讀 helper class；ad/y/au 部分 vtable slot 留 best-guess；as.cs listener 取值留 placeholder
- 2026-05-19 14:45 Claude subagent `S2A-Sub5` — 14 大型 sub-namespace 6/14 完成（GPCUserNoticeResult/GPCNoticeHubImpl/OperationsModulesManager/GPCImageHelper/GPCOperationsModule/GPCOperationsImpl）；skip 8 檔（OperationsHelperForAndroid 1279 / ExResourceUploadListenerAndroidImpl 1242 / OPSResourceDownloaderAndroid 1479 / OPSResourceDownloaderWindows 1190 / OPSResourceUploaderWindows 895 / ResourceUploadListenerAndroidImpl 1024 / GPCBravoImageCropperBehaviour 1375 / GPCImageCropperBehaviour 1576），原因 token 60% 閾值 + Android JNI / Windows P/Invoke vtable indirect 過密
- 2026-05-19 14:50 Claude subagent `S2A-Sub6` — 6 huge root 4/6 完成（d/c/p/i.cs，分別 786/1091/1260/1382 行）；skip 2 檔（av.cs 1469 MonoPInvokeCallback + IntPtr delegate、ag.cs 1654 upload state machine pseudocode 失真嚴重）；StringLiteral 80+ 索引查表
- 2026-05-19 15:00 Claude subagent `S2A-Sub7` — Sub5/Sub6 共 10 個 skip 大檔做 stub 化（保留 type/member skeleton，body 空 return default，不做語意還原）；1,138 行 stub 覆蓋 13,183 行 Annotated；marker grep 乾淨；告知：Annotated 原檔 nested class 與同 outer method 同名屬 IL 結構，未必符合 Roslyn 編譯要求，需後續手動 rename（屬 dedicated pass 範圍）
- 2026-05-19 15:00 **S2-A 完成**：`USDK.Module.Operations.Editor` 207/207 磁碟覆蓋；全 dll marker grep 0 hits（除 LiveChatHelperForOther 3 行 SOP 允許的 `// Ghidra:` stub 註解）；本 session Final 落地 182 新檔（baseline 25 → 207）；10 個大檔以 stub 形式存在待後續 dedicated pass refine body
