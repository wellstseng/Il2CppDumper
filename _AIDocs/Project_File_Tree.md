# Il2CppDumper — 專案資料夾結構

> 重點摘要，不複製整棵樹。對應 git: `master`，最近 commit `4741d46`（添加.net8刪除.net7）。

## 頂層

```
Il2CppDumper/
├── Il2CppDumper.sln                — 解決方案（單一專案）
├── Il2CppDumper/                   — 主程式碼資料夾
├── README.md / README.zh-CN.md     — 使用說明（含 config 選項解釋）
├── LICENSE                          — MIT
├── .github/                         — CI（AppVeyor 用 .appveyor.yml 在外部）
└── _AIDocs/                         — AI 分析文件（本資料夾）
```

## 主程式碼 `Il2CppDumper/`

```
Il2CppDumper/
├── Il2CppDumper.csproj    — net6.0;net8.0；引用 Mono.Cecil 0.11.4
├── Program.cs             — Main：讀 args → 判斷 magic → dispatch → Dump
├── Config.cs              — POCO，對應 config.json
├── config.json            — 預設輸出開關（複製到 output 目錄）
├── Resource1.resx/.cs     — 內嵌資源（Il2CppDummyDll.dll）
│
├── Attributes/            — 序列化 metadata 用 attr
│   ├── ArrayLengthAttribute.cs
│   └── VersionAttribute.cs
│
├── ExecutableFormats/     — 各格式 loader（magic 對應請看 Program.cs:130-180）
│   ├── ElfBase.cs / Elf.cs / Elf64.cs / ElfClass.cs   — ELF 32/64
│   ├── Macho.cs / Macho64.cs / MachoFat.cs / MachoClass.cs — Mach-O 32/64/FAT
│   ├── PE.cs / PEClass.cs                              — Windows PE
│   ├── NSO.cs / NSOClass.cs                            — Switch NSO（用 LZ4 解壓）
│   └── WebAssembly.cs / WebAssemblyClass.cs / WebAssemblyMemory.cs — wasm
│
├── Il2Cpp/                — 核心資料模型
│   ├── Il2Cpp.cs          — 抽象基底（IsDumped/ImageBase/Search/SymbolSearch）
│   ├── Il2CppClass.cs     — 對應 il2cpp runtime 結構體（Il2CppType, MethodInfo, ...）
│   ├── Metadata.cs        — 解析 global-metadata.dat
│   └── MetadataClass.cs   — Metadata 結構體定義
│
├── IO/
│   ├── BinaryStream.cs    — 主讀寫類別，反射讀取 attribute 標記的結構
│   └── Lz4DecoderStream.cs — 給 NSO 用
│
├── Extensions/
│   ├── BinaryReaderExtensions.cs — Read[U]Int24、ReadStringToNull
│   ├── BoyerMooreHorspool.cs     — bytes 搜尋（給 Search 用）
│   ├── HexExtensions.cs / StringExtensions.cs — 小工具
│
├── Outputs/               — 結果輸出
│   ├── Il2CppDecompiler.cs       — 產生 dump.cs（主輸出）
│   ├── DummyAssemblyExporter.cs  — 產生 DummyDll/ 資料夾
│   ├── ScriptJson.cs             — 產生 script.json（給 ida/ghidra/binja 用）
│   ├── StructGenerator.cs        — 產生 il2cpp.h
│   ├── StructInfo.cs             — struct header 用資料結構
│   ├── HeaderConstants.cs        — il2cpp.h 內固定常數
│   └── Il2CppConstants.cs        — runtime 常數（type enum / flag）
│
├── Il2CppBinaryNinja/     — Python plugin（給 BinaryNinja）
│   ├── __init__.py
│   └── plugin.json
│
├── Libraries/
│   └── Il2CppDummyDll.dll — Mono.Cecil 用的樣板 DLL（內嵌為資源）
│
├── Utils/
│   ├── Il2CppExecutor.cs            — 將 metadata + il2cpp 串起的執行單元
│   ├── DummyAssemblyGenerator.cs    — 用 Mono.Cecil 組裝 DummyDll 內容
│   ├── MyAssemblyResolver.cs        — Cecil resolver
│   ├── CustomAttributeDataReader.cs — CustomAttribute Blob 讀取
│   ├── CustomAttributeReaderVisitor.cs
│   ├── AttributeArgument.cs / BlobValue.cs
│   ├── PELoader.cs                  — 手動載入 PE（auto-search 失敗時備援，僅 Windows）
│   ├── SearchSection.cs / SectionHelper.cs
│   ├── ArmUtils.cs                  — ARM 指令小解析
│   ├── OpenFileDialog.cs / FileDialogNative.cs — Windows 檔案對話框（P/Invoke）
│
└── 根目錄 *.py            — 輸出附帶的反組譯腳本
    ├── ida.py / ida_py3.py / ida_with_struct.py / ida_with_struct_py3.py
    ├── ghidra.py / ghidra_with_struct.py / ghidra_wasm.py
    ├── hopper-py3.py
    ├── il2cpp_header_to_ghidra.py / il2cpp_header_to_binja.py
    (這些檔案被 .csproj 標記 CopyToOutputDirectory)
```

## 主要流程（Program.cs）

1. **讀 `config.json`** → 反序列化為 `Config`
2. **解析參數**：args → 判斷哪個是 il2cpp binary、哪個是 metadata（用 magic `0xFAB11BAF`）、哪個是輸出資料夾
3. **Windows 無參時**：跳 OpenFileDialog 互動選檔
4. **`Init()`**：
   - 讀 metadata 建 `Metadata`
   - 讀 il2cpp 二進位 → 用 magic 分派到對應 `ExecutableFormats/*`
   - `SetProperties(version, metadataUsagesCount)`
   - 判定 dump 檔（`CheckDump`）→ 取得 `ImageBase`
   - `PlusSearch` → `Search` → `SymbolSearch` → 失敗則手動輸入 `CodeRegistration` / `MetadataRegistration`
5. **`Dump()`**：
   - `Il2CppExecutor` 串起 metadata + il2cpp
   - `Il2CppDecompiler.Decompile` → `dump.cs`
   - 依 config：`StructGenerator` → `il2cpp.h`、`DummyAssemblyExporter` → `DummyDll/`

## 注意要點

- **multi-target**：`net6.0;net8.0`，新功能避免用 .NET 8 only API（除非用 `#if NET8_0` 包起來）
- **Windows-only 路徑**：`OpenFileDialog`、`PELoader` 走 `RuntimeInformation.IsOSPlatform(OSPlatform.Windows)` 條件分支
- **內嵌 DLL**：`Il2CppDummyDll.dll` 透過 `Resource1.resx` 內嵌，Cecil 讀為 byte[]
- **Unity 版本範圍**：支援 5.3 ~ 2022.2（v16 ~ v31，最近 commit 加入 v31 支援）
- **NSO LZ4 解壓**：`Lz4DecoderStream` 是 NSO loader 專用
