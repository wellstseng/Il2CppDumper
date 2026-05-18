# [續接] Doomsday Phase2 — 認領 dls.im 翻譯

## 1. 前置脈絡
- **專案根目錄**：`/Users/wellstseng/project/Il2CppDumper`
- **分支**：`master`（git repo）
- **任務**：Doomsday Phase2 Annotated→Final 翻譯，**本階段認領 `dls.im`**（Annotated 380 檔、Final 0 檔）
- **Why**：使用者在多 dll 並行翻譯流程中（已完成 IFix.Core / USDK.Foundation / USDK.Module.CPD.Editor / behaviac.runtime / netease / USDK.Bridge / USDK.Module.AIGuide / USDK.Module.Push.Editor / USDK.Module.BlacklistedWord.Editor 等），dls.im 是進度檔 §3 建議優先處理的純未開始中型 dll，並行無衝突。

## 2. 已完成 + commit 狀態
- **最後 commit**：`ab44fb4 chore: 加入 Doomsday 還原作業文件`（已 push origin/master）
- **本次 session 變更（尚未 commit，留給本階段一起 commit）**：
  - `_AIDocs/Doomsday_Phase2_Progress.md` L26 IFix.Core 那行加註：「Properties/AssemblyInfo.cs skip：build metadata 無業務語意」
- **本次 session 結論（IFix / VirtualMachine 盤點）**：
  - `IFix.Core` ✅ 完成：Annotated 34 → Final 33 + 1 skip（AssemblyInfo.cs 為 3 行 `[assembly: AssemblyVersion]` build metadata）
  - `VirtualMachine.cs` stub 化是預期行為：Annotated 8477 → Final 342 行（ILSpy 無法反編譯 ~6900 行 Execute switch case）
  - 各業務 dll 的 `IFix/` 子目錄（IDMAP* / ILFixDynamicMethodWrapper / WrappersManagerImpl / ILFixInterfaceBridge）依 SOP §10 整族跳過，0 翻譯是正確設計
- **上 session 完成的 redo**：USDK.Foundation 123/123、USDK.Module.CPD.Editor 40/40、behaviac.runtime 177/177（Claude + Codex redo 通過抽查）

## 3. 權威來源（先讀這些再開工）
1. **進度檔**：`/Users/wellstseng/project/Il2CppDumper/_AIDocs/Doomsday_Phase2_Progress.md`（§1 表 + §3 認領建議 + §9 批次 log）
2. **專案 SOP**：`/Users/wellstseng/project/Il2CppDumper/memory/_staging/Doomsday_Phase2_SOP.md`（**重點看 §0 校準、§3 IFix fast-path 移除、§5 慣用 C#、§8 per-type 工作流**）
3. **通用 SOP**：`/Users/wellstseng/.claude/memory/_staging/_il2cpp_source_restore.md`（「忠實 = 還原 IL2CPP 編譯前的 .NET 源碼」）
4. **IFix 機制摘要**：`/Users/wellstseng/project/Il2CppDumper/_AIDocs/Doomsday_IFix_Hotpatch.md`（**§10 處置表必看**，dls.im 內若有 IFix/ 子目錄整族跳過）
5. **風格範本**（4 個已完成 sample）：
   - `Input/Doomsday/RestoredSolution/Final/dls.game/IGG.Game.Module.Launch/GameContext.cs`（含已砍 IFix fast-path）
   - `Input/Doomsday/RestoredSolution/Final/dls.framework/IGG.Framework.Event/EventListener.cs`
   - `Input/Doomsday/RestoredSolution/Final/USDK.Module.AIGuide/`（剛完成整族）
   - `Input/Doomsday/RestoredSolution/Final/IFix.Core/IFix.Core/Call.cs`（unsafe 模板）

## 4. 產出位置
- **來源**：`Input/Doomsday/RestoredSolution/Annotated/dls.im/<path>/<File>.cs`
- **輸出**：`Input/Doomsday/RestoredSolution/Final/dls.im/<path>/<File>.cs`（鏡像結構，`mkdir -p` 確保子目錄存在）
- **`Input/Doomsday/` 整個被 `.gitignore` 排除**，Final 產物不進 git
- **唯一進 git 的變更**：`_AIDocs/Doomsday_Phase2_Progress.md`（§1 表 + §9 完成批次 log）

## 5. 做法（步驟 + 工具選擇）
1. **開工前**：先用 Edit 把進度檔 §1 表 dls.im 那行的「處理者」標成 `Claude in-flight (next-phase)`
2. **列檔**：`find Input/Doomsday/RestoredSolution/Annotated/dls.im -type f -name "*.cs" | sort` 確認 380 檔分佈
3. **過濾 IFix build artifact**：dls.im 內若有 `IFix/IDMAP*.cs`、`IFix/ILFixDynamicMethodWrapper.cs`、`IFix/WrappersManagerImpl.cs`、`IFix/ILFixInterfaceBridge.cs`、`Properties/AssemblyInfo.cs` → **整族 skip**（記在 §9 batch log）
4. **切批並行**：剩餘檔案按 namespace 切批，每批 8-12 檔，spawn Agent（`subagent_type: general-purpose`）並行處理。每個 agent prompt 必須包含：
   - 開工前必讀清單（§3 那 5 項）
   - 該批檔案絕對路徑清單
   - 風格範本路徑
   - 硬規則（§4 砍 / §5 翻 / §6 不要）
   - **強制要求**：每檔 Write 前列出該檔翻譯重點摘要（30 字內），方便驗證
5. **每檔處理流程**（per file）：
   - Read Annotated 原檔（>1500 行時分段讀）
   - 砍：ILSpy attribute（`[Token]`/`[FieldOffset]`/`[Address]`）、`using Il2CppDummyDll;`、IFix fast-path（`IsPatched(X)/GetPatch(X)/__Gen_Wrap_N` 三段）、`il2cpp_runtime_class_init`、`FUN_18055b3e0` null trap、`FUN_18055a480` write barrier、static init guard
   - 翻：`thunk_FUN_xxx + X__ctor` → `new X(args)`、`*(int*)(arr + 0x18)` → `arr.Length`、demangled symbol → C# instance/static call、`UnityEngine_Object__op_Inequality(a,b,0)` → `a != b`、`IsPatched(0xb3d, 0)` trailing `0` 省略
   - 留：C# 真 attribute（`[Flags]`/`[Serializable]`/`[MethodImpl]`）、`unsafe` 指標操作
   - 頂部第一行：`// Annotated: <相對路徑回 Annotated>`（路徑層數計算見進度檔 §6）
   - Write 到鏡像 Final 路徑
6. **完成驗證**（自動掃描 + 抽查）：
   - 檔數對齊：`comm -23 <(find Annotated/dls.im -name "*.cs" | sed 's|Annotated/||' | sort) <(find Final/dls.im -name "*.cs" | sed 's|Final/||' | sort)` 結果為空（或只剩明確 skip 檔）
   - Marker 清除：`grep -rE "Il2CppDummyDll|\[Token\(|\[Address\(|\[FieldOffset\(|/\* === Ghidra|FUN_180|StringLiteral_" Final/dls.im/` 無命中
   - **抽查 10 檔**：隨機挑 10 個 method 確認有實質翻譯（不是 `return null;` 空殼化——這是 10:29 Codex 失敗模式）
7. **更新進度檔**：§1 表 dls.im → Final 計數、狀態 ✅；§9 追加 `2026-05-18 HH:MM Claude <batch-name> — dls.im 完成 X/Y 檔，skip Z（理由）`
8. **上 GIT**：`git add _AIDocs/Doomsday_Phase2_Progress.md` + commit（**中文 commit message**，例：`chore(doomsday): dls.im Phase2 翻譯完成 X/380（含 IFix.Core AssemblyInfo skip 註記）`）+ push

## 6. 決策依據 / 已知坑
- **為什麼選 dls.im**：進度檔 §3 列為 Codex 認領建議第 1 名（中型 380 檔、純未開始 Final 0、無 Claude in-flight 衝突）
- **為什麼用 subagent 切批**：之前 Claude C1/C2/C3 撞 context limit 留下尾段是 partial 完成原因（10:29 Codex redo 又出空殼化），subagent 限制單一 agent 範圍可避免兩種失敗
- **拒絕的 alternatives**：
  - dls.config (2,946) / USDK.Windows (1,776) / Epic (1,698) / dls.message (7,867)：規模過大，本階段先做完中型再放大
  - dls.game / dls.framework / Assembly-CSharp / dls.framework.common：已有 Claude partial 產出，並行容易撞檔
  - USDK.Foundation / USDK.Module.CPD.Editor / behaviac.runtime：本次 session 已確認 Codex redo 完成（見進度檔 §9）
- **已知坑**：
  - **空殼化是硬性紅線**：method body 不可用 `return null;` / `return default(...)` / 空 setter 假裝完成。真的無法可靠還原才保留 stub + 一行註解「ILSpy could not decompile; see Annotated L<X>-<Y> Ghidra pseudocode (RVA 0x...) for reference」
  - **不要從 pseudocode 反推 ILSpy stub method**：Annotated 內若 method body 已是 ILSpy stub（pseudocode 註解 + `return null`），保留 stub 不要憑感覺反推
  - **StringLiteral 真值**：要查 `script.json` 內 `ScriptString[N-1]`（1-based），不要憑感覺猜
  - **單次 Read ≤ 1500 行**：agent context 撐不住
  - **進度檔位置 Guardian 警告**：`_AIDocs/Doomsday_Phase2_Progress.md` 屬於進行中協調文件，SOP 規定該放 `memory/_staging/`。**本階段先不搬位置**，等 Phase2 整個收尾再一次性歸檔（避免搬遷期間多 session 引用路徑混亂）

## 7. 完成條件
- `dls.im` Final 檔數 = Annotated 檔數（扣除明確 skip）
- `comm -23` 缺檔為 0
- grep 無硬性 marker 命中
- 抽樣 10 method 通過實質內容檢查
- `_AIDocs/Doomsday_Phase2_Progress.md` §1 + §9 更新
- 進度檔 commit + push 到 origin/master（中文 message）

---
完成後執行：驗證 → 上 GIT → 若使用者要繼續，再下一個 dll（建議 dls.config 或 USDK.Windows）寫新的 handoff prompt。
