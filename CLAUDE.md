# Il2CppDumper — 專案導讀 (Claude Code)

> Unity IL2CPP 二進位反組譯工具。C# .NET 6/8 主控台應用，解析 ELF/Mach-O/PE/NSO/WASM 加 `global-metadata.dat`，產生 dump.cs / DummyDll / 反組譯腳本。

## 風險分級（專案特定）

> 通用分級框架見全域 `~/.claude/CLAUDE.md`。

| 風險等級 | 本專案操作類型 | 驗證要求 |
|---------|--------------|---------|
| **高** | 修改 `ExecutableFormats/*`、`Il2Cpp/Metadata.cs`、`Il2Cpp/Il2Cpp.cs`、`Utils/SearchSection.cs` / `SectionHelper.cs` | 必須先讀 [_AIDocs/Project_File_Tree.md](_AIDocs/Project_File_Tree.md)；對照 Unity IL2CPP 各版本 metadata 結構差異 |
| **高** | 新增 Unity 版本支援（觸碰 `MetadataClass.cs` / `Il2CppClass.cs` 的 `[Version]` 標記） | 必須確認 `[VersionAttribute]` 的 `Min`/`Max` 區間正確，並驗證舊版不被破壞 |
| **高** | 修改 `Outputs/Il2CppDecompiler.cs`、`DummyAssemblyExporter.cs` | 輸出檔案直接被使用者拿去逆向，破壞性變更需先確認 |
| **極高** | 改動 `Il2CppDumper.csproj` `<TargetFrameworks>` / 引用版本 | 必須向使用者確認；目前 multi-target net6.0;net8.0（commit 4741d46 刪掉 net7） |
| **極高** | 任何會改變 `config.json` schema 或預設值的修改 | 必須向使用者確認，因 config 由使用者外部維護 |

## 技術約束

- **multi-target**：`net6.0;net8.0`。新功能避免使用 .NET 8 only API，否則用 `#if NET8_0` 包起來
- **Mono.Cecil 0.11.4**：DummyDll 全靠它，升版需測 `DummyAssemblyGenerator.cs`
- **Windows-only 段落**：`OpenFileDialog.cs`、`FileDialogNative.cs`、`PELoader.cs` 都包在 `RuntimeInformation.IsOSPlatform(OSPlatform.Windows)` 條件下，跨平台時不可移除這層判斷
- **內嵌資源**：`Libraries/Il2CppDummyDll.dll` 透過 `Resource1.resx` 嵌入，改動 DummyDll 需重新 build resx
- **Unity 版本範圍**：5.3 ~ 2022.2（IL2CPP metadata v16 ~ v31）。`[Version(Min=..., Max=...)]` 屬性是版本相容的主要機制
- **Magic 對應表**（[Program.cs:130-180](Il2CppDumper/Program.cs#L130-L180)）：
  - `0x6D736100` → WebAssembly
  - `0x304F534E` → NSO
  - `0x905A4D` → PE
  - `0x464C457F` → ELF（看 byte[4]：1=32-bit, 2=64-bit）
  - `0xCAFEBABE`/`0xBEBAFECA` → Mach-O FAT
  - `0xFEEDFACF` → Mach-O 64
  - `0xFEEDFACE` → Mach-O 32
  - `0xFAB11BAF` → global-metadata.dat magic

## 上游 / Fork 來源

本 repo fork 自 [Perfare/Il2CppDumper](https://github.com/Perfare/Il2CppDumper)。提 PR 給上游前確認是否為 fork-only 改動。
