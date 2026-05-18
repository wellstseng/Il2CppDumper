# Glossary — 術語與縮寫表

> 按字母排序。專案內常見但對非 IL2CPP 背景讀者不直觀的詞。

---

## A

**Adjustor thunk**
泛型 value type 的方法在被 boxing/unboxing 後呼叫的小型 trampoline。IL2CPP 24.5 / 27.1+ 才有獨立欄位（`genericAdjustorThunks`）。

**ARM mod_init_func**
Mach-O 的 section，存所有 static initializer 的位址。Il2CppDumper 的 `Macho64.Search` 走這條找 IL2CPP 初始化函式的指令樣式。

**Assembly (IL2CPP)**
對應 .NET assembly 概念，IL2CPP 內以 `Il2CppAssemblyDefinition` 表示，但對應的 module / image 才是有 type 的容器（`Il2CppImageDefinition`）。一個 assembly 對一個 image，1:1。

---

## B

**Blob**
CIL ECMA-335 用詞，指 metadata 中變長編碼的二進位資料。在 IL2CPP 中：default value、custom attribute 引數都是 blob。讀取入口 [`Il2CppExecutor.GetConstantValueFromBlob`](../Il2CppDumper/Utils/Il2CppExecutor.cs#L343)。

**Boyer-Moore-Horspool**
字串/byte 搜尋演算法。用在 [`SectionHelper.FindCodeRegistration2019`](../Il2CppDumper/Utils/SectionHelper.cs#L361) 對 data section 搜 `mscorlib.dll\0`。

---

## C

**Cecil (Mono.Cecil)**
讀寫 .NET assembly 的低階函式庫。`DummyAssemblyGenerator` 用它生 `DummyDll/*.dll`。

**CIL token**
ECMA-335 用詞，一個 32-bit 整數，高 8 bit 表 table type，低 24 bit 表 row index。IL2CPP 的 `Il2CppMethodDefinition.token` 是 CIL token，v24.2+ 用 `token & 0x00FFFFFF - 1` 當 `codeGenModule.methodPointers` 索引。

**CodeRegistration（`Il2CppCodeRegistration`）**
原生 binary 內描述「方法指標、invoker、PInvoke wrapper、codeGenModule 等程式碼相關表格位置」的中央結構。Il2CppDumper 必須找到它的 VA 才能展開。

**Compressed UInt/Int**
ECMA-335 ECMA-355 的可變長度整數編碼。1-byte (< 0x80)、2-byte、4-byte、5-byte（first byte == 0xF0）。讀取見 [`BinaryReaderExtensions.ReadCompressedUInt32`](../Il2CppDumper/Extensions/BinaryReaderExtensions.cs#L39)。v29+ 的 CustomAttribute blob 用此編碼。

**Custom Attribute Generator**
v21~28 的機制：每個 `attributeTypeRange` 對應一個 native function pointer，runtime call 它就能拿到實例化好的 attribute object。v29+ 改成 blob 完整描述，廢除 generator。

---

## D

**DummyDll**
Il2CppDumper 用 Mono.Cecil 產生的 .NET assembly。type 結構完整、方法 body 是 stub。`dnSpy` / `ILSpy` 開得起來，但執行不了。對 UtinyRipper / UABE 抽 MonoBehaviour 必要。

**dumped file**
從 game 進程記憶體 dump 出來的 binary（如 `libil2cpp.so` 被 GameGuardian dump）。特徵：section header 已被破壞、ImageBase 不是預設值。Il2CppDumper 用 `CheckDump()` 偵測（ELF：找不到 `.text` section；PE：ImageBase ≠ default）。

**Dynamic section (ELF)**
`PT_DYNAMIC` segment 內的 `Elf*_Dyn` 表。包含 `DT_STRTAB`/`DT_SYMTAB`/`DT_HASH`/`DT_RELA` 等指標。`SymbolSearch` 依賴它取得 `g_CodeRegistration` 符號。

---

## E

**ELF**
Unix 家族的可執行格式。Linux / Android（`libil2cpp.so`）使用。Magic：`0x7F 45 4C 46`（`\x7FELF`）。

**Encoded Source Index (metadataUsage)**
v19~24.5 機制：32-bit 整數，高 3 bit 是 `Il2CppMetadataUsage` enum，低位是目標 index。v27+ 改 `(idx & 0x1FFFFFFE) >> 1`。

---

## F

**Field Offset**
欄位在 instance 內的 byte offset。IL2CPP 兩種儲存：v22+ 為 pointer table（每 type 一張），v ≤ 21 為 flat array。詳見 [DataModel.md §5](DataModel.md)。

**FieldRef (`Il2CppFieldRef`)**
跨組件的欄位引用。v19+ 才有 `fieldRefsOffset`。Generic 實例化時用到。

---

## G

**Generic container**
描述一個 class 或 method 「有幾個型別參數」的結構（`Il2CppGenericContainer`）。

**Generic inst**
一個泛型實例化的型別引數清單（`Il2CppGenericInst`），如 `<int, string>`。

**Generic class**
`Il2CppGenericClass` = 一個泛型 type definition + 一組 generic inst（class_inst + method_inst）。

---

## I

**IL2CPP**
Unity 的 C# → C++ 轉譯器 + runtime。把 IL 轉成 C++，再用平台 C++ compiler 編成 native binary。檔案產物：`libil2cpp.so` (Android) / `GameAssembly.dll` (Windows) / `UnityFramework` (iOS) + `global-metadata.dat`。

**Image (IL2CPP)**
對應 .NET module 概念，一個 image 對應一份 .NET assembly 的 PE/.dll 等價。`Il2CppImageDefinition` 描述。`imageDef.token`（v19+）是 ECMA token 的 module index。

**Invoker**
泛型方法 / 動態呼叫時的 trampoline，把 `void*` 參數 cast 回正確型別後 call 真實方法。`Il2CppCodeRegistration.invokerPointers[]` 內。

---

## L

**LC_SEGMENT_64**
Mach-O load command type `0x19`，描述 64-bit segment + sections。

**LC_ENCRYPTION_INFO_64**
Mach-O load command type `0x2C`，標記 iOS 加密區段（FairPlay DRM）。Il2CppDumper 偵測但不自動解密。

**LZ4**
快速壓縮演算法。Switch NSO 三個 segment 各自可選 LZ4 壓縮。Il2CppDumper 用 [`Lz4DecoderStream`](../Il2CppDumper/IO/Lz4DecoderStream.cs) 純 C# 解。

---

## M

**Magic**
檔案開頭幾個 byte，用來辨識格式。完整表見 [Architecture.md §7](Architecture.md)。

**Metadata (`global-metadata.dat`)**
IL2CPP 中所有「型別/方法/欄位 metadata」獨立於 binary 之外的 blob 檔。Magic：`0xFAB11BAF`。

**MetadataRegistration（`Il2CppMetadataRegistration`）**
原生 binary 內描述「型別表、field offset、metadata usage 等資料相關表格位置」的中央結構。與 CodeRegistration 並列為「Il2Cpp.Init 必須的兩個錨點」。

**metadataUsage**
v19~24.5 機制：將 IL 內所有 type ref / string literal / method ref 集中到一個全域 slot 陣列，IL 內只引用 slot index。`metadataUsageDic` 是 `usage type → (slot → decoded index)` 的對照表。

**Mach-O**
Apple 平台可執行格式（macOS / iOS）。32-bit magic `0xFEEDFACE`，64-bit `0xFEEDFACF`，多架構 fat 是 `0xCAFEBABE`/`0xBEBAFECA`。

---

## N

**NSO**
Switch Nintendo Operating System Object。Switch 平台原生格式。三個 segment（text/rodata/data）+ 可選 LZ4。Magic：`NSO0`（`0x304F534E`）。

---

## P

**PE**
Portable Executable，Windows / Xbox 的 binary 格式。Magic：`0x905A4D`（DOS `MZ` + offset 至 PE header）。

**PlusSearch**
Il2CppDumper 的 section-based heuristic search：先按格式分 exec/data/bss section，在 data 內掃 `mscorlib.dll` 字串特徵，反向找 imageDefs → codeRegistration。三段式偵測的第一段。

**Pointer-in-exec**
有些 ELF 編譯器把指標表放在 exec section（如 `.rodata.rel.ro`）。SectionHelper 處理此情況時設 `pointerInExec` 旗標，影響 metadataRegistration 驗證邏輯。

**P/Invoke**
Platform Invoke，.NET 與 native function 交互機制。IL2CPP 內 `reversePInvokeWrappers` 是「native 呼叫 managed」方向。

---

## R

**Relocation**
ELF 動態載入時把 absolute address 調整到實際載入位址的過程。Il2CppDumper 對非 dumped ELF 主動套用（`R_AARCH64_RELATIVE` / `R_X86_64_RELATIVE` 等），直接寫回 stream。

**RVA (Relative Virtual Address)**
相對於 ImageBase 的虛擬位址。IDA 顯示用 RVA。`il2Cpp.GetRVA(VA)` = `VA - ImageBase`（PE / Macho64）；dumped ELF 用 `pointer - ImageBase`，非 dumped 直接回傳 pointer。

**RGCTX (Runtime Generic Context)**
泛型實例化時 IL2CPP runtime 需要的 metadata 表，給 reflection 與 generic dispatch 用。v24.2 之前是全域陣列（`metadata.rgctxEntries`），之後變 per-image 的 token range 對應（`il2Cpp.rgctxsDictionary`）。

---

## S

**Sanity check**
`global-metadata.dat` 開頭的 4-byte magic `0xFAB11BAF`，名稱直接取自 IL2CPP 原始碼變數名。

**Section (PE/ELF/Macho)**
binary 內的命名區段。PE 的 `.text`/`.rdata`/`.data`、ELF 的 `.text`/`.rodata`/`.bss`、Macho 的 `__text`/`__const`/`__data` 等。

**Sentinel value (`ushort.MaxValue`)**
`Il2CppMethodDefinition.slot` 在無 vtable slot 時是 `0xFFFF`，dump.cs 用此判定不印 `Slot: N`。

**Static initializer**
全域變數初始化 / `[ModuleInitializer]` 對應的程式碼。Mach-O 的 `__mod_init_func` section 列出所有 static init function pointer，IL2CPP runtime 的 `LoadMetadataFile` 是其中一個。

**Symbol table**
ELF 的 `.dynsym`（PT_DYNAMIC 的 DT_SYMTAB 指向）。`SymbolSearch` 從這裡取 `g_CodeRegistration` / `g_MetadataRegistration` 符號。

---

## T

**Token (CIL)**
見 *CIL token*。

**TypeDef (`Il2CppTypeDefinition`)**
一個 type 的完整 metadata。包含繼承、欄位/方法/屬性/事件的 start+count 索引、interface/vtable 引用、bitfield flags。

**TypeDefIndex**
`metadata.typeDefs[]` 的整數 index。`Il2CppType` 在非 dumped / v27 之前用 `data.klassIndex` 直接索引；v27 + IsDumped 用 `(typeHandle - ImageBase - typeDefinitionsOffset) / sizeof(Il2CppTypeDefinition)` 反推。

---

## U

**ULEB128**
Unsigned Little-Endian Base-128，wasm 用的可變長度編碼。每 byte 取低 7 bit 拼接，最高 bit 是 continuation flag。讀取見 [`BinaryReaderExtensions.ReadULeb128`](../Il2CppDumper/Extensions/BinaryReaderExtensions.cs#L20)。

---

## V

**VA (Virtual Address)**
binary 載入記憶體後的虛擬位址。`il2Cpp.MapVATR(VA)` 把 VA 轉成檔案 offset 來讀，反向是 `MapRTVA`。

**Version (in Il2CppDumper)**
`double` 型別，IL2CPP metadata 主版號 + 變體小數（如 24.2、27.1、29.1）。詳見 [Version_Compatibility.md](Version_Compatibility.md)。

**VTable**
虛擬方法表。`Il2CppTypeDefinition.vtableStart / vtable_count` 索引 `metadata.vtableMethods[]`，每個 entry 是 encoded method ref。

---

## W

**WASM (WebAssembly)**
瀏覽器/Unity WebGL 的虛擬機字節碼格式。Magic：`\0asm`（`0x6D736100`）。資料存在 wasm data section，需要先攤平到一個 flat memory image 才能像普通 binary 操作（Il2CppDumper 透過 `WebAssembly → WebAssemblyMemory` 兩階段處理）。

**WinRT (Windows Runtime)**
Windows 8+ 的 native API。IL2CPP 對 WinRT 有 `windowsRuntimeFactory` / `windowsRuntimeTypeNames` / `windowsRuntimeStrings` 等專屬欄位（不同版本範圍）。

---

## 符號

**`0xFAB11BAF`**
`global-metadata.dat` magic。注意這串字面像 "fab one one baf"，是 IL2CPP runtime 的 sanity 常數，不是隨機數。

**`0xFFFFFFFF` (= -1 in `int`)**
常見 sentinel：`customAttributeIndex = -1` 表示無 attribute；`declaringTypeIndex = -1` 表示非 nested type；`genericContainerIndex = -1` 表示非泛型。
