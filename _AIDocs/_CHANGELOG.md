# Il2CppDumper — _AIDocs 變更記錄

> 僅記錄 `_AIDocs/` 知識庫的新增 / 修改 / 廢止。原始碼變更請看 `git log`。

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
