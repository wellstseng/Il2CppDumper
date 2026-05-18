# Architecture — Il2CppDumper

> 整體架構、資料流、Pipeline 與類別關係。所有引用點都附 `file:line`，方便驗證。

---

## 1. 一句話定位

> 把 Unity IL2CPP 編譯產生的 **原生二進位**（`libil2cpp.so`、`GameAssembly.dll`、`UserAssembly.so` 等）+ **`global-metadata.dat`** 兩個檔案，還原成可讀的 C# 偽碼（`dump.cs`）、可被 .NET 反組譯工具讀取的 **DummyDll**、以及 IDA / Ghidra / BinaryNinja 用的腳本。

無資料庫、無網路、無 DI 容器。整支程式是「讀檔 → 建模 → 解析 → 寫檔」的單向資料管線。

---

## 2. Pipeline 總覽

```
┌────────────────────────────────────────────────────────────────────────────────┐
│ Program.Main (Program.cs:14)                                                   │
│                                                                                │
│   ① 讀 config.json → Config POCO                                                │
│   ② 解析 argv：用 magic 判斷誰是 il2cpp / metadata / outputDir                  │
│   ③ Init(il2cppPath, metadataPath, out metadata, out il2Cpp)                    │
│        ├─ new Metadata(stream)             ← Metadata.cs:43                    │
│        ├─ switch (magic) { new PE | Elf | Elf64 | Macho | Macho64 | NSO | … }  │
│        ├─ il2Cpp.SetProperties(version, metadataUsagesCount)                    │
│        ├─ il2Cpp.CheckDump()  → IsDumped & ImageBase                            │
│        ├─ PlusSearch → Search → SymbolSearch → 手動 (任一成功就停)              │
│        └─ AutoPlusInit / Init(codeRegistration, metadataRegistration)           │
│                                                                                │
│   ④ Dump(metadata, il2Cpp, outputDir)                                           │
│        ├─ new Il2CppExecutor(metadata, il2Cpp)                                  │
│        ├─ Il2CppDecompiler.Decompile           → dump.cs                        │
│        ├─ (config.GenerateStruct)  StructGenerator.WriteScript                  │
│        │      → script.json + stringliteral.json + il2cpp.h                     │
│        └─ (config.GenerateDummyDll) DummyAssemblyExporter.Export                │
│               → DummyDll/*.dll                                                  │
└────────────────────────────────────────────────────────────────────────────────┘
```

### 2.1 三個階段，三組類別

| 階段 | 角色 | 主要參與 |
|------|------|----------|
| **載入** | 「我要把這堆 byte 解讀成結構」 | `Metadata`、`Il2Cpp` 的具體子類（PE/ELF/Macho/NSO/WASM）、底層 `BinaryStream` |
| **解析** | 「在原生 binary 裡找出 CodeRegistration / MetadataRegistration 兩個錨點，把整張表展開」 | `SectionHelper`、各 loader 的 `PlusSearch`/`Search`/`SymbolSearch`、`Il2Cpp.Init`、`Il2CppExecutor` |
| **輸出** | 「把建好的模型轉成人類 / 工具能讀的格式」 | `Il2CppDecompiler`、`StructGenerator`、`DummyAssemblyGenerator` |

---

## 3. 三個核心物件

### 3.1 `Metadata`（[Il2Cpp/Metadata.cs](../Il2CppDumper/Il2Cpp/Metadata.cs)）

讀取 `global-metadata.dat` 後的純資料容器。

- **入口**：建構子驗證 `0xFAB11BAF` magic（[Metadata.cs:46](../Il2CppDumper/Il2Cpp/Metadata.cs#L46)）
- **版本檢查**：只支援 v16 ~ v31（[Metadata.cs:55-58](../Il2CppDumper/Il2Cpp/Metadata.cs#L55-L58)）。v24 內部還會細分 24 / 24.1 / 24.2 / 24.4
- **內容**：`imageDefs` / `assemblyDefs` / `typeDefs` / `methodDefs` / `fieldDefs` / `parameterDefs` / `propertyDefs` / `eventDefs` / `genericContainers` / `genericParameters` / `stringLiterals` / `attributeTypeRanges`（v21~27.2）/ `attributeDataRanges`（v29+）/ `metadataUsageDic`（v19~24.5）
- **繼承**：`Metadata : BinaryStream`，所有「按結構讀」都透過 [BinaryStream.ReadClass](../Il2CppDumper/IO/BinaryStream.cs#L109) 反射

### 3.2 `Il2Cpp`（抽象基類，[Il2Cpp/Il2Cpp.cs](../Il2CppDumper/Il2Cpp/Il2Cpp.cs)）

代表已載入的「原生執行檔」。每種格式（PE / Elf / Elf64 / Macho / Macho64 / NSO / WebAssemblyMemory）有對應的子類，各自負責：

| 抽象方法 | 用途 |
|---------|------|
| `MapVATR(addr)` | Virtual Address → file offset / Raw Address |
| `MapRTVA(addr)` | file offset → Virtual Address（反向） |
| `Search()` | 用 ARM 指令樣式 / mod_init_func 等啟發式找 Registration |
| `PlusSearch(...)` | 用 `SectionHelper` + `mscorlib.dll` 字串特徵找 Registration |
| `SymbolSearch()` | 從 dynsym 直接找 `g_CodeRegistration` / `g_MetadataRegistration` |
| `GetSectionHelper(...)` | 用該格式的 section/segment 資訊建 `SectionHelper` |
| `CheckDump()` | 判定這份檔案是不是「記憶體 dump」 |

子類繼承 `Il2Cpp : BinaryStream`，所以也擁有 `ReadClass<T>` 等反射讀取能力。

### 3.3 `Il2CppExecutor`（[Utils/Il2CppExecutor.cs](../Il2CppDumper/Utils/Il2CppExecutor.cs)）

把 `Metadata` 和 `Il2Cpp` 兩個容器**串起來**的查詢中介層。負責：

- **型別名稱組裝**：[`GetTypeName`](../Il2CppDumper/Utils/Il2CppExecutor.cs#L61) / [`GetTypeDefName`](../Il2CppDumper/Utils/Il2CppExecutor.cs#L149)，遞迴處理 `IL2CPP_TYPE_ARRAY` / `SZARRAY` / `PTR` / `VAR` / `MVAR` / `CLASS` / `VALUETYPE` / `GENERICINST`
- **泛型解析**：[`GetGenericInstParams`](../Il2CppDumper/Utils/Il2CppExecutor.cs#L181) / [`GetGenericContainerParams`](../Il2CppDumper/Utils/Il2CppExecutor.cs#L193) / [`GetGenericClassTypeDefinition`](../Il2CppDumper/Utils/Il2CppExecutor.cs#L275)
- **RGCTX 查表**：[`GetRGCTXDefinition`](../Il2CppDumper/Utils/Il2CppExecutor.cs#L239)（v24.2+ 用 `il2Cpp.rgctxsDictionary`，舊版用 `metadata.rgctxEntries`）
- **Blob 預設值**：[`TryGetDefaultValue`](../Il2CppDumper/Utils/Il2CppExecutor.cs#L326) + [`GetConstantValueFromBlob`](../Il2CppDumper/Utils/Il2CppExecutor.cs#L343)，給欄位 / 參數 default value（`= "abc"`、`= 42`）
- **dumped 檔案的特殊查表路徑**：[`GetTypeDefinitionFromIl2CppType`](../Il2CppDumper/Utils/Il2CppExecutor.cs#L293) 在 v27+ 且 `IsDumped` 時用 `typeHandle - ImageBase - typeDefinitionsOffset` 算 index，而不是 `klassIndex`
- **CustomAttribute 指標表**：v27~28 從 `codeGenModule.customAttributeCacheGenerator` 收集，v<27 直接用 `il2Cpp.customAttributeGenerators`（[Il2CppExecutor.cs:41-58](../Il2CppDumper/Utils/Il2CppExecutor.cs#L41-L58)）

---

## 4. 為什麼需要 CodeRegistration / MetadataRegistration？

兩者是 IL2CPP runtime 在原生 binary 裡的「索引根」：

- **`Il2CppCodeRegistration`**：所有 method pointer、invoker、reverse PInvoke wrapper、customAttribute generator、codeGenModule 的進入點（[Il2CppClass.cs:5-66](../Il2CppDumper/Il2Cpp/Il2CppClass.cs#L5-L66)）
- **`Il2CppMetadataRegistration`**：所有 type、generic inst、generic method、field offset、metadata usage 的進入點（[Il2CppClass.cs:68-94](../Il2CppDumper/Il2Cpp/Il2CppClass.cs#L68-L94)）

只要找到這兩個位址，再呼叫 [`Il2Cpp.Init(codeRegistration, metadataRegistration)`](../Il2CppDumper/Il2Cpp/Il2Cpp.cs#L120)，整張 IL2CPP 的型別圖、方法指標表、泛型實例表就會被全部展開到 `Il2Cpp` 物件的欄位中。

Search 三段式（[Program.cs:222-237](../Il2CppDumper/Program.cs#L222-L237)）：

```
if (!PlusSearch)   ← SectionHelper + mscorlib.dll 字串
    if (!Search)   ← ARM 指令樣式（只 Macho64/Macho 實作；ELF/PE/NSO/WASM 都 return false）
        if (!SymbolSearch) ← ELF 從 dynsym 取 g_CodeRegistration（只 Elf64/Elf 有；PE/Macho/NSO/WASM return false）
            手動讓使用者輸入兩個位址
```

Windows-only 額外路徑（[Program.cs:213-219](../Il2CppDumper/Program.cs#L213-L219)）：PlusSearch 失敗時，PE 會走 [`PELoader.Load`](../Il2CppDumper/Utils/PELoader.cs#L14) 用 `LoadLibrary` 把 PE 載到記憶體再讀一次（繞過部分 packer 對檔案 raw 表的破壞）。

---

## 5. 類別繼承關係

```
BinaryStream  (IO/BinaryStream.cs)
├── Metadata           (Il2Cpp/Metadata.cs)
├── MachoFat           (ExecutableFormats/MachoFat.cs)   ← 不是 Il2Cpp，只負責 Fat dispatcher
├── WebAssembly        (ExecutableFormats/WebAssembly.cs) ← 不是 Il2Cpp，產出 WebAssemblyMemory
└── Il2Cpp (abstract)  (Il2Cpp/Il2Cpp.cs)
    ├── PE             (ExecutableFormats/PE.cs)
    ├── Macho          (ExecutableFormats/Macho.cs)
    ├── Macho64        (ExecutableFormats/Macho64.cs)
    ├── NSO            (ExecutableFormats/NSO.cs)
    ├── WebAssemblyMemory (ExecutableFormats/WebAssemblyMemory.cs)
    └── ElfBase (abstract) (ExecutableFormats/ElfBase.cs)
        ├── Elf        (ExecutableFormats/Elf.cs)
        └── Elf64      (ExecutableFormats/Elf64.cs)
```

`ElfBase` 多了一個 `Reload()` / `CheckSection()`，讓 dumped ELF 檔可以重做 program header fix。

---

## 6. 主要資料流

### 6.1 `Init` 階段（讀 metadata）

```
File.ReadAllBytes(metadataPath)
  → new Metadata(MemoryStream)
       → 驗 magic 0xFAB11BAF
       → 讀 header (Il2CppGlobalMetadataHeader)，依 v24 變體調整 Version
       → 一口氣讀完所有 *Defs[] / *Indices[] / stringLiterals[]
       → 建 dictionary 給 default value / attribute range
       → v19~24.5 額外：ProcessingMetadataUsage 把 (destinationIndex → decodedIndex) 灌進 metadataUsageDic
```

### 6.2 `Init` 階段（讀 il2cpp binary）

```
File.ReadAllBytes(il2cppPath)
  → 看 magic 選 loader：
     0x6D736100 → new WebAssembly → .CreateMemory() → WebAssemblyMemory
     0x304F534E → new NSO → .UnCompress() → 解開 LZ4 後重 new NSO
     0x905A4D   → new PE
     0x464C457F → new Elf / Elf64（看 byte[4] 是 1 還 2）
     0xCAFEBABE / 0xBEBAFECA → new MachoFat → 提示使用者選 32/64bit → 跳對應 case
     0xFEEDFACF → new Macho64
     0xFEEDFACE → new Macho

  → il2Cpp.SetProperties(version, metadataUsagesCount)
  → il2Cpp.CheckDump() 為 true 時：
       詢問 dump address 或 0
       設 il2Cpp.ImageBase, il2Cpp.IsDumped = true
       (Elf 還會 elf.Reload())

  → PlusSearch / Search / SymbolSearch / 手動 → 得到 codeRegistration / metadataRegistration
  → il2Cpp.Init(codeRegistration, metadataRegistration)
       → 讀 Il2CppCodeRegistration / Il2CppMetadataRegistration
       → 展開 methodPointers / genericMethodPointers / invokerPointers / customAttributeGenerators 等
       → 讀 types[]、fieldOffsets[]、metadataUsages、codeGenModules（v24.2+）
       → 建立 methodDefinitionMethodSpecs / methodSpecGenericMethodPointers 兩張 dict
```

特殊修正：v27 + IsDumped 時，[`Init` 在最後修正 metadata.ImageBase](../Il2CppDumper/Program.cs#L238-L243)，方法是反推 `typeDefs[0].byvalTypeIndex` 對應的 `typeHandle - typeDefinitionsOffset`。

### 6.3 `Dump` 階段（寫檔）

```
new Il2CppExecutor(metadata, il2Cpp)        ← 中介層
  ↓
Il2CppDecompiler.Decompile(config, outputDir)
  → 遍歷 metadata.imageDefs → typeDefs → fields/properties/methods
  → 對每個 method：il2Cpp.GetMethodPointer(imageName, methodDef) 取出 VA
  → 計算 RVA = il2Cpp.GetRVA(methodPointer)
  → 寫到 dump.cs

  if config.GenerateStruct:
      StructGenerator.WriteScript(outputDir)
        → 寫 stringliteral.json (所有字串字面值)
        → 寫 script.json (給 IDA/Ghidra/Binja 用：方法名 + 地址 + 簽名)
        → 寫 il2cpp.h (struct 定義 + vtable + RGCTX)

  if config.GenerateDummyDll:
      DummyAssemblyExporter.Export(executor, outputDir, addToken)
        → 切到 outputDir/DummyDll/
        → 從 Resource1.Il2CppDummyDll bytes 載入 dummy module
        → new DummyAssemblyGenerator → 用 Mono.Cecil 為每個 image 建 AssemblyDefinition
        → assembly.Write(stream) → File.WriteAllBytes("{imageName}.dll")
```

---

## 7. 重要常數與 magic

| Constant | 出處 | 用途 |
|---------|------|------|
| `0xFAB11BAF` | [Metadata.cs:46](../Il2CppDumper/Il2Cpp/Metadata.cs#L46), [Program.cs:41](../Il2CppDumper/Program.cs#L41) | global-metadata.dat magic |
| `0x6D736100` | [Program.cs:134](../Il2CppDumper/Program.cs#L134) | WebAssembly `\0asm` |
| `0x304F534E` | [Program.cs:138](../Il2CppDumper/Program.cs#L138) | NSO `NSO0` |
| `0x905A4D` | [Program.cs:142](../Il2CppDumper/Program.cs#L142) | PE `MZ\0\x90` |
| `0x464C457F` | [Program.cs:145](../Il2CppDumper/Program.cs#L145) | ELF `\x7FELF` |
| `0xCAFEBABE` / `0xBEBAFECA` | [Program.cs:155-156](../Il2CppDumper/Program.cs#L155-L156) | Mach-O FAT |
| `0xFEEDFACF` / `0xFEEDFACE` | [Program.cs:174,177](../Il2CppDumper/Program.cs#L174) | Mach-O 64 / 32 |
| `mscorlib.dll\0`（13 bytes） | [SectionHelper.cs:349](../Il2CppDumper/Utils/SectionHelper.cs#L349) | PlusSearch 在 data section 找這串字串當錨點 |
| `0x10000000` / `0x180000000` | [PE.cs:131-135](../Il2CppDumper/ExecutableFormats/PE.cs#L131-L135) | PE 32/64bit 預設 ImageBase；不等於就視為 dump |

---

## 8. 入口檔對照表

| 你想了解… | 看這裡 |
|----------|--------|
| 命令列怎麼接、整個流程 | [Program.cs](../Il2CppDumper/Program.cs) |
| 預設輸出開關 | [Config.cs](../Il2CppDumper/Config.cs) + [config.json](../Il2CppDumper/config.json) |
| 結構在哪、欄位是什麼 | [DataModel.md](DataModel.md) |
| 找 Code/MetadataRegistration 的搜尋邏輯 | [Loaders_And_Search.md](Loaders_And_Search.md) |
| 輸出的四種檔案怎麼產生 | [Outputs.md](Outputs.md) |
| `[Version(Min=X, Max=Y)]` 怎麼運作、各版本差異 | [Version_Compatibility.md](Version_Compatibility.md) |
| 縮寫術語不知道是什麼 | [Glossary.md](Glossary.md) |
| 整體資料夾結構 | [Project_File_Tree.md](Project_File_Tree.md) |
