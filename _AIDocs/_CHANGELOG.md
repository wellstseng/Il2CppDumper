# Il2CppDumper — _AIDocs 變更記錄

> 僅記錄 `_AIDocs/` 知識庫的新增 / 修改 / 廢止。原始碼變更請看 `git log`。

## 2026-05-19

### 更新 — Doomsday Phase2 S2-C 完成 dls.framework 547/547 磁碟覆蓋（strip-stub only）

- 更新：`Doomsday_Phase2_Progress.md` — `dls.framework` 由 2/547 baseline 升至 547/547 disk-covered；effective 6（2 sample + IFix runtime 4 抄 dls.framework.common Final 範本）；其餘 541 為 strip-stub placeholder；§9 補 S2C-ifix-template + S2C-strip-stub + S2-C 完成總結；進度總計 effective 由 1,560 升至 1,566
- 更新：`Doomsday_Phase2_Completion_Plan.md` — §0 Final exists 7,983→8,528 / Disk missing 27,819→27,274 / Effective completed 1,560→1,566；§5 S2-C 改列「disk-covered 547/547；effective 6；其餘 541 placeholder」
- 更新：`Token_Cost_Ledger.md` — 新增 `s2c-strip-stub-only` 批次（~150K 主執行緒 token，0 LLM subagent，是 s2b-full 的 12%）
- 策略亮點：全程 python regex 機械處理，**0 LLM subagent**；IFix 4 大檔（ILFixDynamicMethodWrapper.cs 39429 行）走「抄 common Final infrastructure + 解析 Annotated method signature 自動生成 dispatch wrapper」批次配方，744 wrappers / 85 個含 ref/out 全自動生成；驗證「能用知識庫/Annotated 機械處理就不要派 LLM」token-safe 原則
- 驗證：`dls.framework` 全 dll marker grep 0（`Il2CppDummyDll` / `[Token` / `[Address` / `[FieldOffset` / `=== Ghidra pseudocode` / `FUN_180` / `StringLiteral_` / `return default;` / `NotImplementedException` 全 0 命中）；body 留待後續 dedicated pass refine

### S4 Redo — Epic.OnlineServices.Sanctions

- 更新：`Input/Doomsday/RestoredSolution/Final/Epic/Epic.OnlineServices.Sanctions/` — 13 檔改列 effective；重作 options/internal/player/callback/interface，補 `Helper.Set/Get/Dispose`、`EOS_Sanctions_*` binding、callback add/remove/invoke flow
- 更新：`Doomsday_Phase2_Progress.md` / `Doomsday_Phase2_Completion_Plan.md` / `Token_Cost_Ledger.md` — effective completed 1,547 → 1,560；S4 effective remaining 3,474 → 3,461；Epic remaining 1,698 → 1,685
- 驗證：`Epic.OnlineServices.Sanctions` marker/default grep clean；全專案 build 仍被既有 `dls.game/IGG.Game.Module.Login/LoginModule.cs` 語法錯擋住

### 更新 — Doomsday Phase2 dls.im S1 收斂

- 更新：`Doomsday_Phase2_Progress.md` — `dls.im` 從需重檢改列完成；記錄 S0 補齊 380/380、S1-A/B/C/D/residual marker pass、`FriendData.cs` dedicated pass、全 dll marker grep 0、build 摘要無 `dls.im` 語法錯
- 更新：`Doomsday_Phase2_Completion_Plan.md` — S1 改列 done，下一波建議回到 S2/S3/S4/S5/S6
- 更新：`Token_Cost_Ledger.md` — 新增 `dls-im-s1-finish` 批次成本記錄

### 更新 — Doomsday Phase2 S3-A dls.config 起始批次

- 更新：`Doomsday_Phase2_Progress.md` — `dls.config` 由未開始改為 12/2946 partial；`dls.message` 標註 protobuf 暫跳過
- 更新：`Doomsday_Phase2_Completion_Plan.md` — S3-A remaining 改為 2,934；S3-B protobuf 依使用者指示跳過
- 更新：`Token_Cost_Ledger.md` — 新增 `s3a-config-seed` 批次成本記錄

### 更新 — Doomsday Phase2 S3-A dls.config 擴批

- 更新：`Doomsday_Phase2_Progress.md` — `dls.config` 由 12/2946 推進到 30/2946；記錄 build 摘要無 `dls.config` 路徑錯誤
- 更新：`Doomsday_Phase2_Completion_Plan.md` — S3-A remaining 改為 2,916，並刷新 Final exists / missing / effective counts
- 更新：`Token_Cost_Ledger.md` — 新增 `s3a-config-seed-continue` 批次成本記錄

### 更新 — Doomsday Phase2 S3-A BattlePass lite 批次

- 更新：`Doomsday_Phase2_Progress.md` — `dls.config` 由 30/2946 推進到 39/2946；`ActivityBattlePassReward*` / `GuildReward*` 標記留 dedicated 批次
- 更新：`Doomsday_Phase2_Completion_Plan.md` — S3-A remaining 改為 2,907
- 更新：`Token_Cost_Ledger.md` — 新增 `s3a-battlepass-lite` 批次成本記錄

### 更新 — Doomsday Phase2 S3-A BattlePass Reward dedicated 批次

- 更新：`Doomsday_Phase2_Progress.md` — `dls.config` 由 39/2946 推進到 45/2946；`ActivityBattlePassReward*` / `ActivityBattlePassGuildReward*` 6 檔完成，RewardDao helper 已還原
- 更新：`Doomsday_Phase2_Completion_Plan.md` — S3-A remaining 改為 2,901，並刷新 Final exists / missing / effective counts
- 更新：`Token_Cost_Ledger.md` — 新增 `s3a-battlepass-reward` 批次成本記錄

### 更新 — Doomsday Phase2 S3-A dls.config 磁碟覆蓋完成

- 更新：`Doomsday_Phase2_Progress.md` — `dls.config` 由 45/2946 推進到 2946/2946；marker grep 0，build 摘要無 `dls.config` 路徑錯；complex Dao helper 多為 stub-first
- 更新：`Doomsday_Phase2_Completion_Plan.md` — S3-A remaining 改為 0；全域 Final exists / missing / effective counts 刷新
- 更新：`Token_Cost_Ledger.md` — 新增 `s3a-full-template-stub` 批次成本記錄

### 更新 — Doomsday Phase2 S4 External SDK wrappers 完成

- 更新：`Doomsday_Phase2_Progress.md` — `Epic` 1698/1698、`USDK.Windows` 1776/1776 改列完成；marker grep 0，build 摘要無 S4 路徑錯
- 更新：`Doomsday_Phase2_Completion_Plan.md` — S4 remaining 改為 0；全域 Final exists / missing / effective counts 刷新
- 更新：`Token_Cost_Ledger.md` — 新增 `s4-sdk-stub` 批次成本記錄

### 更正 — 撤回 S3/S4 stub 完成口徑

- 更正：`s3a-full-template-stub` / `s4-sdk-stub` 只能算 disk coverage / placeholder，不算 Annotated→Final 翻譯完成
- 更新：`Doomsday_Phase2_Progress.md` — effective completed 回退到 1,547；`dls.config` 只承認 45 effective；`Epic` / `USDK.Windows` 改回未完成但已有 placeholder
- 更新：`Doomsday_Phase2_Completion_Plan.md` — S3-A effective remaining 2,901，S4 effective remaining 3,474
- 更新：`Token_Cost_Ledger.md` — 標記兩批為 0 effective，避免後續 agent 誤判完成

### 更新 — Doomsday Phase2 S2-B 完成 dls.framework.common 234/234

- 更新：`Doomsday_Phase2_Progress.md` — `dls.framework.common` 由 15/234 partial 升至 234/234 ✅ 完成；§9 補 S2B-warmup + Sub-A/B/C/D/F/H + stub-strip + 完成總結；進度總計從 1,323 升至 1,514
- 更新：`Token_Cost_Ledger.md` — 新增 `s2b-full` 批次成本記錄（主執行緒 ~1.2M tokens + 8 個 subagent 平行 ~200K 最大）
- 策略亮點：兩 dll 共用 IFix runtime 時直接抄已驗證 Final 範本（dls.im → dls.framework.common）；25+ 個 ≥500 行大檔走 python regex 批次去 IL2CPP marker，stub 化保留 type/member skeleton；marker grep 全 dll 0 hits

### 新增 — Token 成本追蹤與 token-safe 翻譯流程

- 新增：`Token_Cost_Ledger.md` — 記錄 Codex / CLI session token usage 觀察、高成本事件、工具輸出預算與 jq 聚合查詢方式
- 新增：`Translation_SOP_TokenSafe.md` — 規範 Doomsday Phase2 Annotated→Final 的批次大小、禁止模式、驗收項目與 batch 記錄模板
- 新增：`Doomsday_Phase2_Completion_Plan.md` — 將剩餘 Phase2 翻譯拆成 S0~S6 section，供多 model / agent 認領
- 更新：`_INDEX.md` — 新增 completion plan / token ledger / token-safe SOP 入口與追蹤用途速查
- 更新：`Doomsday_Phase2_Progress.md` — Phase2 必讀清單改為 agent 共用入口，並記錄 `dls-im-missing-small` 小批次

## 2026-05-18（晚）

### Doomsday Phase 2 — 撤回程式翻譯路線

- 更新：`Doomsday_Phase2_Progress.md` §1 / §9，dls.im 先前程式翻譯產物改列需重檢，不列有效完成數
- 更新：`memory/_staging/Doomsday_Phase2_SOP.md` §6，明確規定 Phase2 不走程式/腳本翻譯，Final 回到人工/LLM 依 Annotated 還原
- 移除：程式翻譯工具與其 preview ignore 規則，避免後續 agent 誤用

commit `a697ab6` 的程式翻譯方向已撤回；後續以本段規則為準。

## 2026-05-18

### Doomsday Phase 2 — IFix-S1 完成（無 _AIDocs 文件變更）

IFix.Core runtime 32 檔翻譯完成（Annotated 8,833 行 → Final 2,547 行，壓縮 ~3.5x），VirtualMachine.cs（8,477 行）留 IFix-S2 單獨處理。本次無 _AIDocs 內容變動：既有 `Doomsday_IFix_Hotpatch.md` §1-11 機制摘要仍是 runtime 的權威說明，無需改寫。

- 翻譯成果落地於 `Input/Doomsday/RestoredSolution/Final/IFix.Core/`（被 `.gitignore` 排除，不入 repo）
- S1 完成清單、uncertain 段落、IFix-S2 prompt 寫在 `memory/_staging/next-phase.md`
- fix-on-discovery：`AnonymousStorey.unmanagedFields / managedFields` 由 private 改 internal（讓 `EvaluationStackOperation` ChainFieldReference 分支可透過 `fixed (Value* p = &anon.unmanagedFields[0])` 取址）

## 2026-05-17（補充）

### 新增 — Doomsday 副作業專用知識

- 新增：`Doomsday_IFix_Hotpatch.md` — 解析 Tencent IFix 熱更框架（PatchManager / VirtualMachine / Call / WrappersManagerImpl / ILFixDynamicMethodWrapper / IDMAP*），用於 Phase2 翻譯 Annotated→Final 時識別並砍掉每個 method 入口的 IFix fast-path boilerplate
- 更新：`_INDEX.md` — 文件清單擴充為 8 篇

## 2026-05-17

### 建立（初始骨架）

透過 `/init-project` 初始化知識庫，掃描專案結構並產出模組職責速查。

- 新增：`_INDEX.md`、`_CHANGELOG.md`、`Project_File_Tree.md`

### 擴充（完整深度知識庫）

第二輪 `/init-project`，深度閱讀所有核心檔案（Il2Cpp/Metadata/BinaryStream/Executor/SectionHelper/各 ExecutableFormats/Decompiler/StructGenerator 等）後產出完整分析。所有引用都附 `file:line` 連結，可被驗證。

- 新增：`Architecture.md` — pipeline、三大物件關係、資料流、繼承樹
- 新增：`DataModel.md` — `BinaryStream` 反射讀取機制、`Il2Cpp*`/`Metadata*` 結構、`[Version]` / `[ArrayLength]` 屬性
- 新增：`Loaders_And_Search.md` — 7 種格式 loader、三段式偵測（PlusSearch/Search/SymbolSearch）、`SectionHelper`、relocation、dumped 處理
- 新增：`Outputs.md` — `dump.cs` / `DummyDll` / `script.json` / `il2cpp.h` 四種輸出產物 schema 與產生邏輯
- 新增：`Version_Compatibility.md` — IL2CPP v16~31 對應 Unity 版本、`[Version]` 屬性分佈、變體偵測內部邏輯
- 新增：`Glossary.md` — 術語表（IL2CPP / metadata / RGCTX / VA/RVA / Adjustor thunk / metadataUsage 等）
- 更新：`_INDEX.md` — 文件清單擴充為 7 篇，加入追蹤用途速查表

### 補完盲區（Tier 1~4）

第三輪 `/init-project`，把先前推論的部分讀完整檔後驗證並補上細節。

- 更新 `Loaders_And_Search.md`：
  - 新增 §4.3 ARM 指令解碼公式（`DecodeMov` / `DecodeAdr` / `DecodeAdrp` / `DecodeAdd` / `IsAdr`）
  - 新增 §4.4 Macho64 ARM64 用法範例
  - 新增 §4.5 Macho 32-bit Thumb Search（含 LSB 修正）
  - 新增 §4.6 Elf 32-bit ARM Search（含 GOT/PC-relative 兩種偏移）
  - 新增 §11 32-bit vs 64-bit ELF / Macho 差異總覽表
- 更新 `DataModel.md`：
  - 新增 §7.1~7.6 v29+ CustomAttribute blob 完整 schema（Count + ctorIndex 陣列 + 三類 named args + EncodedTypeEnum + visitor 模式）
  - 新增 §8 執行檔格式結構體（`PEClass.cs` / `ElfClass.cs` / `MachoClass.cs` / `NSOClass.cs` / `WebAssemblyClass.cs` + 完整 `ElfConstants` 常數）
- 更新 `Outputs.md`：
  - §3.6~3.11 補完 DummyDll 細節（Method body IL stub、AddressAttribute、FieldOffset、三段式遍歷、GenericParameter、AssemblyResolver）
  - §6.3~6.10 補完 `il2cpp.h` schema（完整 ParseType 對照、StructInfo 巢狀、版本對應 HeaderVxx、`*_o/_c/_Fields/_VTable/_RGCTXs/_StaticFields` 結構、MethodInfo 版本變化、MetadataUsage 兩條路徑、script.json 五大區段、FixName 規則）
  - §4.3~4.5 補完 Python 反組譯腳本（10 個檔對照表 + 通用流程 + BinaryNinja plugin 三段式說明）
