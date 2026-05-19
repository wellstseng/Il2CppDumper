# Il2CppDumper — AI 分析文件索引

> 本資料夾包含由 AI 輔助產出的專案分析文件。
> 最近更新：2026-05-19（Doomsday S5-E 完成；常駐 strip_stub.py 工具腳本）

---

## 文件清單

| # | 文件 | 涵蓋主題 | 適合場合 |
|---|------|----------|----------|
| 1 | [Project_File_Tree.md](Project_File_Tree.md) | 資料夾結構、模組職責對照 | 「這個檔案在哪？」「這資料夾做什麼？」 |
| 2 | [Architecture.md](Architecture.md) | 整體 pipeline、三大物件關係、資料流、繼承樹 | 「整支程式怎麼跑？」「Init/Dump 在做什麼？」 |
| 3 | [DataModel.md](DataModel.md) | `BinaryStream` 反射讀取、`Il2Cpp*`/`Metadata*` 結構、`[Version]` / `[ArrayLength]` 屬性 | 「這個 struct 怎麼從 bytes 還原？」「`bitfield` 怎麼解？」 |
| 4 | [Loaders_And_Search.md](Loaders_And_Search.md) | 7 種格式 loader 對照、`PlusSearch`/`Search`/`SymbolSearch` 三段式偵測、`SectionHelper`、relocation、dumped 處理 | 「為什麼這個檔案處理失敗？」「PlusSearch 在做什麼？」 |
| 5 | [Outputs.md](Outputs.md) | `dump.cs` / `DummyDll` / `script.json` / `il2cpp.h` 的產生邏輯與 schema | 「輸出的 4 個檔案怎麼來的？」「想改 dump.cs 格式要動哪？」 |
| 6 | [Version_Compatibility.md](Version_Compatibility.md) | IL2CPP v16~31 對應 Unity 版本、`[Version]` 分佈、版本切換內部邏輯 | 「新版 Unity 來了怎麼支援？」「24.2 vs 24.3 差在哪？」 |
| 7 | [Glossary.md](Glossary.md) | 術語表（IL2CPP / metadata / RGCTX / VA/RVA / Adjustor thunk / metadataUsage 等） | 「這縮寫是什麼？」 |
| 8 | [Doomsday_IFix_Hotpatch.md](Doomsday_IFix_Hotpatch.md) | IGG Doomsday 反組譯副作業專用：IFix 熱更框架（PatchManager / VirtualMachine / Call / WrappersManagerImpl / ILFixDynamicMethodWrapper / IDMAP*）解析 | Phase2 翻譯 Annotated→Final 時遇到 `IsPatched/GetPatch/__Gen_Wrap_N` fast-path |
| 9 | [Doomsday_Phase2_Progress.md](Doomsday_Phase2_Progress.md) | **多 agent 平行協調**：Annotated→Final 每 dll 完成狀態、Claude in-flight 範圍、Codex 認領建議、翻譯 SOP 速查、輸出規則 | 多 LLM (Claude + Codex 等) 並行翻譯時避免重複認領、Codex 開工前必讀 |
| 10 | [Doomsday_Phase2_Completion_Plan.md](Doomsday_Phase2_Completion_Plan.md) | Phase2 剩餘 35K 檔的 section / batch 拆分、認領協議、平行啟動順序 | 「怎麼把剩下的派給其他 model？」 |
| 11 | [Token_Cost_Ledger.md](Token_Cost_Ledger.md) | Codex / CLI session token 成本來源、巨量工具輸出事件、成本記錄模板與查詢指令 | 「之前 token 花在哪？」「怎麼建表控成本？」 |
| 12 | [Translation_SOP_TokenSafe.md](Translation_SOP_TokenSafe.md) | Doomsday Phase2 Annotated→Final 的 token-safe 批次流程、工具輸出限制、驗收模板 | 「怎麼翻比較省 token？」「怎麼避免整批返工？」 |
| 13 | [Doomsday_Subagent_Brief.md](Doomsday_Subagent_Brief.md) | Phase2 subagent 派工共用 SOP brief（砍/翻/保留對照、StringLiteral 查表、Token 控制、回報模板） | 派 subagent 時 prompt 引用本檔，避免每次重抄 SOP §2-§4 |

文件間用 `[[name]]` 風格的相對連結互連，從任何一篇都能跳到相關章節。

## 工具腳本（tools/）

| 路徑 | 用途 | 適用 section |
|------|------|--------------|
| [tools/doomsday/strip_stub.py](../tools/doomsday/strip_stub.py) | Doomsday Phase2 Annotated→Final 機械去 IL2CPP/Ghidra/IFix 噪音；參數化 `--dll/--ns`，stdin `--list` | S2-C/D、S5-D/E 起所有 disk-cover 為主的 strip-stub 批次 |

---

## 架構一句話摘要

C# .NET 6/8 主控台工具，將 Unity IL2CPP 二進位（ELF/Mach-O/PE/NSO/WASM）+ `global-metadata.dat` 還原成可讀的 C# dump、DummyDll、以及 IDA/Ghidra/BinaryNinja 反組譯腳本。整支程式是「讀檔 → 反射建模 → 三段式找 Registration → 寫檔」的單向資料管線。

## 技術棧速查

- **Runtime**：.NET 6 / .NET 8（multi-target）
- **語言**：C# 10+
- **主依賴**：[Mono.Cecil 0.11.4](https://github.com/jbevain/cecil)（產生 DummyDll）
- **進入點**：[Il2CppDumper/Program.cs:14](../Il2CppDumper/Program.cs#L14)（`Main`）
- **設定檔**：[Il2CppDumper/config.json](../Il2CppDumper/config.json) → POCO [`Config`](../Il2CppDumper/Config.cs)
- **內嵌資源**：`Resource1.resx` 內含 `Il2CppDummyDll.dll`（DummyDll 樣板）
- **支援範圍**：Unity 5.3 ~ 2022.2（IL2CPP metadata v16 ~ v31）

## 模組職責速查

| 模組 | 角色 | 主要文件 |
|------|------|---------|
| `ExecutableFormats/` | 解析 PE/ELF32/64/Macho32/64/Fat/NSO/WASM | [Loaders_And_Search.md](Loaders_And_Search.md) |
| `Il2Cpp/` | `Il2Cpp`（執行檔抽象基類）、`Metadata`（讀 `global-metadata.dat`）+ 兩個 `*Class.cs` 結構體定義 | [DataModel.md](DataModel.md) |
| `Outputs/` | `Il2CppDecompiler`（dump.cs）、`DummyAssemblyExporter` / `DummyAssemblyGenerator`（DummyDll）、`StructGenerator`（script.json/il2cpp.h/stringliteral.json） | [Outputs.md](Outputs.md) |
| `Utils/` | `Il2CppExecutor`（中介層）、`SectionHelper` / `PELoader` / `SearchSection`（搜尋）、`CustomAttributeDataReader`（v29+ blob） | [Architecture.md](Architecture.md) §3.3, [Loaders_And_Search.md](Loaders_And_Search.md) §3 |
| `IO/` | `BinaryStream`（反射讀取核心） + `Lz4DecoderStream`（給 NSO） | [DataModel.md](DataModel.md) §1 |
| `Extensions/` | `BinaryReader` 擴充（CompressedUInt/Int、ULEB128）、Boyer-Moore-Horspool、字串/hex 小工具 | [Loaders_And_Search.md](Loaders_And_Search.md) §10 |
| `Attributes/` | `[Version]` / `[ArrayLength]` 兩個序列化標記 | [DataModel.md](DataModel.md) §2 |
| `Libraries/` | 內嵌資源 `Il2CppDummyDll.dll`（Cecil 用樣板） | [Outputs.md](Outputs.md) §3.3 |

## 追蹤用途速查

| 我想… | 看哪裡 |
|------|--------|
| 看「我修了什麼 / 何時改的」 | [_CHANGELOG.md](_CHANGELOG.md) |
| 看「資料夾在哪 / 各檔案職責」 | [Project_File_Tree.md](Project_File_Tree.md) |
| 看「整支程式的執行流」 | [Architecture.md](Architecture.md) §2 |
| 看「為什麼這個 binary 抓不到 CodeRegistration」 | [Loaders_And_Search.md](Loaders_And_Search.md) §11 偵錯小抄 |
| 看「Unity 2022.x 為什麼算 v29 / v31」 | [Version_Compatibility.md](Version_Compatibility.md) §2 |
| 看「剩餘 Phase2 怎麼分派」 | [Doomsday_Phase2_Completion_Plan.md](Doomsday_Phase2_Completion_Plan.md) |
| 看「token 花在哪 / 下次怎麼控」 | [Token_Cost_Ledger.md](Token_Cost_Ledger.md) |
| 看「Doomsday 翻譯怎麼省 token」 | [Translation_SOP_TokenSafe.md](Translation_SOP_TokenSafe.md) |
| 看「使用者操作習慣 / 自我校正」 | `.claude/memory/`、`memory/Extra_Efficiently_TokenSafe.md` |

## 風險分級

> 通用分級框架見全域 `~/.claude/CLAUDE.md`。專案特定分級見 [CLAUDE.md](../CLAUDE.md)。
