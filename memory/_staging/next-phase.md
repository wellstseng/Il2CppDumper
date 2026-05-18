# Doomsday Phase 2 — S1 進度與接續 Handoff

> **日期**：2026-05-17（S1 完成 + 增量 session 補修 2 個 uncertain + IFix 熱更摘要）
> **Session ID（catclaw judy-cli）**：`0fbd3b92-cc36-48e1-9244-7aa1aaefd12a`（S1 主體）；本檔最新更新由後續 session 完成
> **Channel**：`1491754414325764148`
> **Project cwd**：`/Users/wellstseng/project/Il2CppDumper`
>
> **判斷接續方式**：本檔 Session ID 是否仍對應 `~/.catclaw/cli-bridges.json` 內 `1491754414325764148` channel 的 `sessionId`？
> - 是 → resume 同 session（context 連續）
> - 否 → 新 session，讀本檔 + `Doomsday_Phase2_SOP.md` + global `_il2cpp_source_restore.md` 接手

## S1 狀態：**45/45 ✅ 全完成**

### 完成的範圍（遊戲啟動相關）

| Namespace | Files | 處理 batch | 標 `[uncertain]` |
|---|---|---|---|
| `dls.game/IGG.Game.Module.Launch/` | 14 | batch-1, batch-2 | GameLaunch.cs（vtable 3 處）, GameContext.cs（CONCAT44 1 處）|
| `dls.game/IGG.Game.Module.Login/` | 5 | batch-2 | — |
| `dls.game/IGG.Game.Module.Login.View/` | 13 | batch-2 含 CivilizationDefPanel.cs, PreLoading.cs | — |
| `dls.game/IGG.Game.Module.MainScene/` | 7 | batch-3 | MainSceneModule.cs（OnInit/OnEnterBindScene 等 ~2000 行 pseudocode 留 stub）|
| `dls.game/IGG.Game.Data.Cache.Launch/` | 1 | batch-3 | — |
| `dls.game/IGG.Game.Data.Cache.Login/` | 11 | batch-3, batch-4, batch-5 | SerStorage.cs（binary chunk layout 留骨架）, ConfigPreloadInfo.cs（BitConverter 語意推測）, LoginCache.cs（輕度）|
| `dls.game/IGG.Game.Data.Cache.MainScene/` | 5 | batch-5 | MainSceneCache.cs（~100 個 MagicLamp helper proto unpack 推測）|
| `Assembly-CSharp/IGG.Game.Module.Launch/` | 1 (GameLaunchProxy) | batch-5 | — |
| `Assembly-CSharp/IGG.Game.Module.Login.Comp/` | 1 (CgVideoProxy) | batch-5 | — |

特別大型檔（agent 標明 partial coverage）：
- **LoginModule.cs** (9631→1737 lines): 約 65% method 完整還原，其餘以方法呼叫關係推斷或留 stub
- **MainSceneModule.cs** OnInit 等大型 method 留 stub

### Handoff 內 uncertain file 統計（**剩 5 個**，原 7 個）

剩 5 個（皆為大檔，須單 agent + 多輪 SendMessage）：
1. `Final/dls.game/IGG.Game.Module.Launch/GameLaunch.cs`（Final 709 / Anno 2852，vtable 3 處）
2. `Final/dls.game/IGG.Game.Module.Login/LoginModule.cs`（Final 1737 / Anno 9631，~65% 完整）
3. `Final/dls.game/IGG.Game.Module.MainScene/MainSceneModule.cs`（Final 422 / Anno 8574，OnInit/OnEnterBindScene 留 stub）
4. `Final/dls.game/IGG.Game.Data.Cache.Login/SerStorage.cs`（Final 693 / Anno 5463，binary chunk 留骨架）
5. `Final/dls.game/IGG.Game.Data.Cache.MainScene/MainSceneCache.cs`（Final 1844 / Anno 15545，~100 MagicLamp helper proto unpack 推測）

已修完（移出 uncertain 名單）：
- ~~`GameContext.cs`~~（2026-05-17 增量 session）：CampId getter 修正 — `CampInfo` struct 是 `{ uint CurId@0x0, uint OriginalId@0x4 }` **無 ctor**，原寫 `new CampInfo(p2.CampId, p2.CampId2)` 編譯不過；正確還原為 `new CampInfo { CurId = data.CampId, OriginalId = data.OriginalCampId }`（`PlayerData.OriginalCampId` 而非 `CampId2`，欄位定義在 `Protomsg/MsgGS2CLPlayerBaseNotice.cs` +0xB4）。順手清掉 WorldId getter 內冗餘的 IL2CPP 二次取值。
- ~~`ConfigPreloadInfo.cs`~~（2026-05-17 增量 session）：逐行對照 pseudocode 後 BitConverter Write/Read 語意全對，**無需修改**，移出 uncertain 名單。

## 全專案進度

| Sprint | 範圍 | Files | 狀態 |
|---|---|---|---|
| S0 | Annotated/（ILSpy + Ghidra pseudocode 合併） | 31,941 | ✅ |
| **S1** | **遊戲啟動（Launch+Login+MainScene+Cache）** | **45** | **✅** |
| S2 | （未定，使用者決定）| ~31,896 待選 | ⏳ |

## Token 用量估算（Sonnet 4.6 actual）

S1 batch-2~5 (35 files) 並行 4 agent：
- batch-2: 295K tokens (含 LoginModule 9631 行)
- batch-3: 257K tokens (含 MainSceneCache 15545 行)
- batch-4: 59K tokens (純 enum/struct)
- batch-5: 190K tokens
- 合計 **~800K tokens × Sonnet 4.6 ($3/M input + $15/M output)** ≈ **~$8 USD**

外加 batch-1（單 agent，10 files）135K tokens ≈ $1.5。

**S1 全部成本 ≈ $10 USD**。比預估的 ~$2 高 5 倍——主因是某些 file 超大（GameLaunch 2800 行、LoginModule 9631、MainSceneCache 15545）導致 agent context 吃重。

實際 throughput：
- 簡單 file（enum / struct / interface）：1-2 分鐘
- 中等 file（commander / cache）：5-10 分鐘
- 大型 MonoBehaviour（Launch / Login / Scene module）：30-60 分鐘
- **大檔不會線性 scale 4 agent**——同檔內無平行性

## 下次接續方法

### 增量 session（2026-05-17）已產出 ⚠ **未上 git**

> 使用者決定本批 working tree 變更不 commit，留給下個 session 接續看完整脈絡。git log 查不到，必須靠本檔與 `_AIDocs/Doomsday_IFix_Hotpatch.md` 重建脈絡。

- **`Input/Doomsday/RestoredSolution/Final/dls.game/IGG.Game.Module.Launch/GameContext.cs`**（dirty） — CampId getter 修正 + WorldId getter 清冗餘（注：`Input/Doomsday/` 似乎被 .gitignore 排除，本就不會 commit）
- **`_AIDocs/Doomsday_IFix_Hotpatch.md`**（新檔，untracked） — IFix 熱更框架完整解析。Phase2 任何 dll 翻譯遇到 `IsPatched/GetPatch/__Gen_Wrap_N` fast-path 都查這份；解釋為什麼 SOP §3 要砍那段、IDMAP*/ILFixDynamicMethodWrapper/WrappersManagerImpl/PatchManager/VirtualMachine 五大角色職責、為什麼 `dls.game/IFix/ILFixDynamicMethodWrapper.cs` 會爆 463K 行。
- `_AIDocs/_INDEX.md`（dirty） 擴充為 8 篇
- `_AIDocs/_CHANGELOG.md`（dirty）加 2026-05-17 補充段
- `memory/_staging/next-phase.md`（dirty，即本檔）

---

## IFix.Core/ 完整還原 sprint plan

**目標**：把 Tencent IFix runtime（`Input/Doomsday/RestoredSolution/Annotated/IFix.Core/`）翻譯成 .NET 源碼級 `Final/IFix.Core/`，補完 `_AIDocs/Doomsday_IFix_Hotpatch.md` 留下的「機制摘要」變成「可閱讀的源碼」。

**為什麼分兩 sprint**：`VirtualMachine.cs` 8477 行內含單 method `Execute` ~6900 行，按 S1 已知坑 4「大檔不要硬塞單 agent」必須單獨處理；其他檔可一 sprint 解掉。

### IFix-S1：**✅ 完成（2026-05-18）**

| Agent | 範圍 | 檔數 | Annotated 行 | Final 行 |
|---|---|---:|---:|---:|
| A | 14 個微型 attribute/marker（IFix/* 4 + IFix.Core/* 9 + Option.cs） | 14 | 280 | 138 |
| B | 10 個小型 class（ExceptionHandler/AnonymousStoreyInfo/RuntimeException/ObjectClone/Il2CppSetOptionAttribute/ThreadStackInfo/Cleanner/GenericDelegate/Utils/SimpleVirtualMachineBuilder）| 10 | 1,548 | 446 |
| C | 5 個中型（Code/GenericDelegateFactory/NewFieldInfo/ReflectionMethodInvoker/AnonymousStorey） | 5 | 2,867 | 696 |
| D | Call.cs + EvaluationStackOperation.cs | 2 | 2,382 | 734 |
| E | PatchManager.cs（分段 Read） | 1 | 2,135 | 598 |
| **合計** | | **32** | **8,833** (含 ThreadStackInfo 等 partial 已落地) | **2,547** (壓縮 ~3.5x) |

**跳過**：`Properties/AssemblyInfo.cs` 3 行（按 SOP 跳過）

**結構** (`Final/IFix.Core/`)：
- `IFix/`（4 attribute）
- `IFix.Core/`（27 主要 runtime 檔，**不含 VirtualMachine.cs**）
- `Unity.IL2CPP.CompilerServices/`（2 attribute/enum）

**Uncertain / best-guess 段落清單**（VirtualMachine 完成後一併複查）：
- `GenericDelegateFactory.cs`：保留 `m__0..m__4` LINQ closure 命名痕跡；非 generic Action 路徑標 best guess
- `ReflectionMethodInvoker.cs`：Nullable get_Value 分支留空 + 註解（pseudocode 走 fall-through 但無明確賦值）
- `AnonymousStorey.cs`：ctor 內 `virtualMachine.externTypes[t-1]` 標 best guess（VM 內 `externTypes` 為 private，原作者可能用 internal accessor）
- `EvaluationStackOperation.cs:255`：`virtualMachine.objectClone.Clone(obj)` 標 best guess
- `PatchManager.cs`：`readMethod` ctor path generic placeholder 解析、`MakeGenericMethod` vtable 對應、`GetInterfaceMap` 段、`_LoadAnonStorey2._m__0/_m__1` cleanup body、IDMAP 命名格式 5 處 best guess
- `SimpleVirtualMachineBuilder.cs`：16 條 Instruction 的 Code enum 值直接用 cast 數字（未查 Code.cs 對應名）；packed int64 拆解可能要互換高/低 4 byte
- `Utils.TryAdapterToDelegate`：`delegateAdptCache` 初始化（未找到 cctor）
- `GenericDelegate.Action()`：`extraArgNum` 設為 `anonObj != null ? 1 : 0`（未交叉驗證）

**Fix-on-discovery 已順手修**：`AnonymousStorey.unmanagedFields / managedFields` private → internal（讓 `EvaluationStackOperation` 用 `fixed (Value* p = &anon.unmanagedFields[0])` 訪問）

**S2 也要做的**：5 個 dll 的 `WrappersManagerImpl.cs`（都很小，但跨 dll 重複；做完一個其他模仿）

### IFix-S2：VirtualMachine.cs 單獨處理

- **必須單 agent**，多輪 SendMessage 追加 Read 範圍
- 策略：
  1. 第一輪：Read L1-500（class 頭、fields、ctor、checkCctorExecute、store、copy、Execute 簡單 overload）
  2. 第二輪：Read L500-1300（Execute overload + arrayGet/arraySet + throwRuntimeException + getExceptionHandler）
  3. 第三輪起：Read L1284-8205 巨無霸 Execute method，按 1000-1500 行一段切，每段內按 opcode group 翻譯（ldarg/stloc/load-store 一組、arithmetic 一組、call/callvirt/newobj 一組、conv.* 一組、branch 一組、box/unbox/cast 一組、throw/exception 一組、互鎖/原子 一組）
  4. 最後：Read L8205-end（Sweep、Statistics、Set/Get/Initialize/Replace/RemoveGlobal）
- **不要試圖一輪 Read 整檔**；agent context 一定不夠
- **產出格式**：`Final/IFix.Core/IFix.Core/VirtualMachine.cs`，Execute 內按 region 註解切（`#region Opcodes: Load/Store` 等），便於人類導覽
- **跨檔依賴提醒**（S1 已對應，S2 寫 VirtualMachine 時要對齊）：
  - `VirtualMachine.externTypes` 應為 `internal`（AnonymousStorey ctor 訪問）
  - `VirtualMachine.objectClone` 應為 `public`/`internal` 欄位（EvaluationStackOperation ToObject 訪問）
  - `VirtualMachine.Execute(int methodId, ref Call, int argsCount)` 簽名定型（已從 AnonymousStorey/GenericDelegate/PatchManager 三檔交叉驗證）
  - `VirtualMachine.global` 為 static，可 `SetGlobal/GetGlobal/InitializeGlobal(Stream)/ReplaceGlobal(Stream)/RemoveGlobal()` 操作（PatchManager 內呼叫）

### 接續 prompt（複製貼上給新 session 執行 IFix-S2）

```
讀以下檔當權威來源：
- /Users/wellstseng/project/Il2CppDumper/memory/_staging/next-phase.md（IFix-S1 結果 + IFix-S2 plan 在 §「IFix-S2: VirtualMachine.cs 單獨處理」）
- /Users/wellstseng/project/Il2CppDumper/_AIDocs/Doomsday_IFix_Hotpatch.md（IFix 機制摘要 §8 VirtualMachine 章節必讀）
- /Users/wellstseng/project/Il2CppDumper/memory/_staging/Doomsday_Phase2_SOP.md（Phase2 翻譯 SOP）
- /Users/wellstseng/.claude/memory/_staging/_il2cpp_source_restore.md（通用 SOP）

⚠ IFix-S1 已完成（32 檔翻譯成果在 `Input/Doomsday/RestoredSolution/Final/IFix.Core/`，被 .gitignore 排除不在 repo）。權威進度與 uncertain 清單在 next-phase.md。

任務：執行 IFix-S2（VirtualMachine.cs 單檔）。

**檔案**：
- 輸入 `/Users/wellstseng/project/Il2CppDumper/Input/Doomsday/RestoredSolution/Annotated/IFix.Core/IFix.Core/VirtualMachine.cs` (8477 行)
- 輸出 `/Users/wellstseng/project/Il2CppDumper/Input/Doomsday/RestoredSolution/Final/IFix.Core/IFix.Core/VirtualMachine.cs`
- 頂部：`// Annotated: ../../../Annotated/IFix.Core/IFix.Core/VirtualMachine.cs`（3 個 ../，注意：S1 第一輪曾踩 2 個 ../ 範本錯誤）

**做法（必讀，否則 agent context 必爆）**：
- **必須單 agent**（不要平行；同檔無平行性）
- 分段 Read：
  1. L1-500（class 頭、fields、ctor、checkCctorExecute、store、copy、Execute 簡單 overload）
  2. L500-1300（Execute overload + arrayGet/arraySet + throwRuntimeException + getExceptionHandler）
  3. L1284-8205 巨無霸 Execute method，按 1000-1500 行一段切；每段按 IL opcode group 翻譯（load/store / arithmetic / call/callvirt/newobj / conv.* / branch / box/unbox/cast / throw/exception / 互鎖 一組）
  4. L8205-end（Sweep、Statistics、Set/Get/Initialize/Replace/RemoveGlobal）
- **不要試圖一輪 Read 整檔**
- Execute 內用 `#region Opcodes: Load/Store` 等註解區塊，便於人類導覽

**跨檔依賴對齊**（S1 已落地，VirtualMachine 寫的時候要對齊欄位 visibility）：
- `externTypes` 為 `internal`（S1 AnonymousStorey 內 `virtualMachine.externTypes[t-1]` 已假設可訪問）
- `objectClone` 為 `internal`（S1 EvaluationStackOperation ToObject `virtualMachine.objectClone.Clone(obj)` 已假設可訪問）
- `Execute(int methodId, ref Call, int argsCount)` 簽名定型（AnonymousStorey/GenericDelegate/PatchManager 三檔已對齊）
- `static SetGlobal/GetGlobal/InitializeGlobal(Stream)/ReplaceGlobal(Stream)/RemoveGlobal()`（PatchManager 內呼叫）

**校準**（同 IFix-S1）：
- 砍 `[Token]/[FieldOffset]/[Address]` / `using Il2CppDummyDll;` / `il2cpp_runtime_class_init` / null-deref trap / write barrier / IL2CPP method-info pointer trailing `0`
- 保留 `unsafe` 指標（Value*/Instruction*）
- 不加 `// Note:` `// Suspicious:` 推測註解
- 不發明 helper API
- 不確定 → 保留 raw + 行尾 `// best guess`

完成 IFix-S2 後給「執驗上P」收尾報告：列出 Execute 內已覆蓋 vs 未覆蓋的 opcode、uncertain 清單、跨檔欄位對齊狀況；然後產 IFix-S1 + S2 一併的「IFix 全 Restore」commit 訊息草案（含中文 body）。

git remote 狀態：origin = `git@github.com:wellstseng/Il2CppDumper.git` (fork)，upstream = `git@github.com:Perfare/Il2CppDumper.git`。IFix-S2 完成的文件更新（_CHANGELOG/next-phase.md）push 到 origin master 即可。Final/IFix.Core/ 翻譯成果本身被 .gitignore 排除不入 repo。
```

### 接續 prompt（複製貼上）

```
讀以下三份檔當權威來源：
- /Users/wellstseng/project/Il2CppDumper/memory/_staging/next-phase.md  ← 本檔（含 5 個剩餘 uncertain + 已完成清單）
- /Users/wellstseng/project/Il2CppDumper/memory/_staging/Doomsday_Phase2_SOP.md
- /Users/wellstseng/.claude/memory/_staging/_il2cpp_source_restore.md
- /Users/wellstseng/project/Il2CppDumper/_AIDocs/Doomsday_IFix_Hotpatch.md  ← 熱更機制（新增，必讀）

S1 已完成 45/45，2 個小 uncertain 已補（GameContext + ConfigPreloadInfo）。下一步請選：

A. 修精剩餘 5 個 uncertain 大檔（建議單 agent 一檔，多輪 SendMessage 追加 Read 範圍）
   - GameLaunch.cs（vtable 3 處）
   - LoginModule.cs（9631 行，~65%）
   - MainSceneModule.cs（8574 行，OnInit stub）
   - SerStorage.cs（5463 行，binary chunk）
   - MainSceneCache.cs（15545 行，~100 helper）

B. 開始 S2 framework 基礎層（IGG.Framework.* ~150 files，預估 ~$33）
   - 多為小型 helper/enum/struct/interface，適合 4 agent 並行
   - 完成後 dls.framework 整族可被 S2 戰鬥/UI 直接呼叫，是優先依賴項

C. 開始 S2 戰鬥/遊戲核心（IGG.Game.Module.March + Battle + Combat ~500 files，預估 ~$110）

D. 開始 S2 UI 系統（IGG.Game.UI.* ~2000 files，預估 ~$440）

E. 其他 namespace（你指定）

開工前先 ls /Users/wellstseng/project/Il2CppDumper/Input/Doomsday/RestoredSolution/Final/dls.game/ 與 dls.framework/ 確認 namespace 已動過範圍。
```

### 全專案剩餘規模
S1 完成後，全 `Annotated/` 內待翻譯：~31,896 files（35,802 - 35,802×0% 已翻 + 35802 - 31941 純 attribute = 略不準確）

實際 grep：
```bash
find /Users/wellstseng/project/Il2CppDumper/Input/Doomsday/RestoredSolution/Annotated -name "*.cs" | wc -l   # = 35802
find /Users/wellstseng/project/Il2CppDumper/Input/Doomsday/RestoredSolution/Final -name "*.cs" | wc -l      # 含 sample + S1
```

### 預算 / 時程估算
按 S1 真實成本外推（$10 / 45 files = $0.22/file 平均）：
- **全 32K files 全做：~$7,000 USD（Sonnet 4.6）**
- 比預估的 $2,500 高 ~3 倍（因大檔開銷）

更務實做法：分 sprint 逐步驗收。每 sprint < $50 控制風險。

## 已開不會丟的東西（持久化）

- `~/.claude/memory/_staging/_il2cpp_source_restore.md` — 通用 SOP（跨專案重用）
- `Il2CppDumper/memory/_staging/Doomsday_Phase2_SOP.md` — 專案 SOP
- `Il2CppDumper/_AIDocs/plan/Doomsday_Restore.md` — 總計畫
- `Il2CppDumper/memory/_staging/Doomsday_S1_progress.md` ← **本檔**
- `Input/Doomsday/RestoredSolution/Final/_progress/S1_pending.txt` + `S1_remaining.txt` + `S1_ba/bb/bc/bd`（batch 切分明細）
- 所有 sample（手寫 7 個 + S1 翻譯 45 個）都在 `Final/`

## 已知坑（下次別重踩）
1. **csproj reference**：path-form Include，不能 simple-name + HintPath，路徑層數 `..\..\output\DummyDll\` 從 Final 算
2. **StringLiteral**: 用 `script.json` 內 `ScriptString[N-1]`（1-based），絕對不要憑感覺推測 format string
3. **空 override** 省略（base 預設行為，如 Unity Timeline 空 PrepareFrame）
4. **超大 file** 不要硬塞單 agent — agent context 不夠會 partial cover，下次處理 LoginModule 級的 9000+ 行檔建議**單獨開一個 agent 只做一個檔**，並用 SendMessage 多輪追加 Read 範圍

## Cron / 背景 process 狀態
- 無 in-flight Ghidra pipeline（S0 已完成）
- 無 in-flight subagent（4 agent 全部已 return）
- session-only cron 跨 session 會丟（之前測過）
