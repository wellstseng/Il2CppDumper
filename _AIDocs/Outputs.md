# Outputs — 四種輸出產物

> 本檔說明 Il2CppDumper 產出的所有檔案：`dump.cs`、`DummyDll/*.dll`、`script.json`、`stringliteral.json`、`il2cpp.h`。

---

## 1. 輸出總覽

| 檔案 | 產生條件 | 產生者 |
|------|---------|--------|
| `dump.cs` | 永遠（除非 Init 失敗） | [`Il2CppDecompiler.Decompile`](../Il2CppDumper/Outputs/Il2CppDecompiler.cs#L25) |
| `il2cpp.h` | `config.GenerateStruct` | [`StructGenerator.WriteScript`](../Il2CppDumper/Outputs/StructGenerator.cs#L42) |
| `script.json` | `config.GenerateStruct` | 同上 |
| `stringliteral.json` | `config.GenerateStruct` | 同上 |
| `DummyDll/*.dll` | `config.GenerateDummyDll` | [`DummyAssemblyExporter.Export`](../Il2CppDumper/Outputs/DummyAssemblyExporter.cs#L7) → [`DummyAssemblyGenerator`](../Il2CppDumper/Utils/DummyAssemblyGenerator.cs) |

`StructGenerator` 一個函式同時產三個檔（[StructGenerator.cs:376-431](../Il2CppDumper/Outputs/StructGenerator.cs#L376-L431)），不能單獨關掉。

[`Program.Dump`](../Il2CppDumper/Program.cs#L254-L274) 的順序固定：先 dump.cs → struct/script/header → DummyDll。

---

## 2. `dump.cs`

### 2.1 格式

```csharp
// Image 0: mscorlib.dll - 0
// Image 1: System.dll - 30
// Image 2: Assembly-CSharp.dll - 100
...

// Namespace: UnityEngine
[Serializable]                       // ← config.DumpAttribute=true 且 type 有 [Serializable] flag
public sealed class GameObject : Object, ISerializable // TypeDefIndex: 245
{
    // Fields
    private int m_InstanceID; // 0x10                  // ← config.DumpFieldOffset
    private static GameObject s_Sentinel;              // ← static
    public const int kMaxLayer = 31;                   // ← const + default value

    // Properties
    public string name { get; set; }                   // get/set 的 modifier 來自對應 method

    // Methods

    // RVA: 0x12345 Offset: 0x6789 VA: 0x18001ABC Slot: 5
    public extern void SetActive(bool value);
    /* GenericInstMethod :
    |
    |-RVA: 0x... Offset: 0x... VA: 0x...
    |-GameObject.SetActive<Foo>
    |-GameObject.SetActive<Bar>
    */
}
```

### 2.2 開關（皆來自 [Config.cs](../Il2CppDumper/Config.cs)）

| 選項 | 預設 | 影響 |
|------|------|------|
| `DumpMethod` | `true` | 印 `// Methods` 區段 |
| `DumpField` | `true` | 印 `// Fields` 區段 |
| `DumpProperty` | `false`（[Config.cs:7](../Il2CppDumper/Config.cs#L7)，但 [config.json:5](../Il2CppDumper/config.json#L5) 是 `true`） | 印 `// Properties` 區段 |
| `DumpAttribute` | `false`（同上不一致） | 在 type/field/method/param/property 前印 attribute |
| `DumpFieldOffset` | `true` | 在 field 後加 `// 0x..` |
| `DumpMethodOffset` | `true` | 在 method 前加 `// RVA: 0x.. Offset: 0x.. VA: 0x..` |
| `DumpTypeDefIndex` | `true` | 在 class 行尾加 `// TypeDefIndex: N` |

⚠️ `Config` POCO 的預設值和 `config.json` 的內容**不一致**（property/attribute 的部分）。實際取的是 `config.json`。

### 2.3 處理流程

```
foreach image in metadata.imageDefs:
    foreach typeDef in image.typeStart..typeStart+typeCount:
        ① 計算繼承/介面（parent + interfaces[]）
        ② 印 namespace + attribute + access modifier
        ③ 判定 class/struct/interface/enum
        ④ 印名稱 + 泛型參數 + extends
        ⑤ if DumpField:    foreach field → access/static/const/readonly + 型別 + 名 + default + offset
        ⑥ if DumpProperty: foreach property → 取 get/set 對應 method 算 modifier，印 `Type Name { get; set; }`
        ⑦ if DumpMethod:   foreach method → attribute → RVA/Offset/VA → modifier → 回傳型別 → 名 + 泛型 → 參數列
            泛型方法實例：在後面加 `/* GenericInstMethod : ... */`
        ⑧ 印 `}`
    try/catch：dump 中拋例外 → 寫 `/*exception*/}\n` 然後繼續下個 image
```

### 2.4 細節：method modifier 怎麼算

[`GetModifiers`](../Il2CppDumper/Outputs/Il2CppDecompiler.cs#L451-L499)：

```
access mask:
  PRIVATE / PUBLIC / FAMILY / ASSEM / FAM_AND_ASSEM / FAM_OR_ASSEM
flags:
  STATIC → "static "
  ABSTRACT → "abstract " (+ "override " if REUSE_SLOT)
  FINAL + REUSE_SLOT → "sealed override "
  VIRTUAL + NEW_SLOT → "virtual "
  VIRTUAL + REUSE_SLOT → "override "
  PINVOKE_IMPL → "extern "
```

結果用 `methodModifiers` dict 快取，相同 method 不重算。

### 2.5 default value 編碼

[Il2CppDecompiler.cs:167-194](../Il2CppDumper/Outputs/Il2CppDecompiler.cs#L167-L194)：

```
if TryGetDefaultValue(typeIndex, dataIndex, out value):
    if value is string str: 寫 "$str" (用 ToEscapedString 轉義)
    if value is char c:     寫 '\xNN'
    if value != null:       寫 ToString()
    else:                   寫 null
else:
    寫 /*Metadata offset 0xXX*/
```

`ToEscapedString` 來自 [StringExtensions.cs](../Il2CppDumper/Extensions/StringExtensions.cs)（把控制字元轉 `\xNN`）。

### 2.6 RVA / Offset / VA 三者差異

| 名稱 | 意義 | 取得 |
|------|------|------|
| **VA** (Virtual Address) | 載入記憶體後該 method 的位址 | `il2Cpp.GetMethodPointer(imageName, methodDef)` |
| **Offset** | 在檔案中的 byte offset | `il2Cpp.MapVATR(methodPointer)` |
| **RVA** (Relative Virtual Address) | VA - ImageBase（給 IDA 用） | `il2Cpp.GetRVA(methodPointer)` |

特殊：abstract 或 `methodPointer == 0` 時印 `RVA: -1 Offset: -1`。Slot 是 vtable slot，`ushort.MaxValue (0xFFFF)` 表示無 slot 不印。

---

## 3. `DummyDll/*.dll`

### 3.1 用途

把 IL2CPP 還原成「結構正確、無方法 body」的 .NET assembly。可用 dnSpy / ILSpy 開啟，可被 UtinyRipper / UABE 載入提取 MonoBehaviour / MonoScript。

### 3.2 產生流程

[`DummyAssemblyExporter.Export`](../Il2CppDumper/Outputs/DummyAssemblyExporter.cs#L7-L21)：

```csharp
Directory.SetCurrentDirectory(outputDir);   ← 注意：改了 process cwd！
if Directory.Exists("DummyDll") → Delete    ← 會炸掉舊資料夾
Directory.CreateDirectory("DummyDll");
Directory.SetCurrentDirectory("DummyDll");

var dummy = new DummyAssemblyGenerator(il2CppExecutor, addToken);
foreach (assembly in dummy.Assemblies):
    using ms = new MemoryStream();
    assembly.Write(ms);
    File.WriteAllBytes(assembly.MainModule.Name, ms.ToArray());
```

⚠️ `Directory.SetCurrentDirectory` 在多執行緒場景會踩。本工具是單執行緒命令列，OK。

### 3.3 內嵌樣板 DLL

[DummyAssemblyGenerator.cs:34-43](../Il2CppDumper/Utils/DummyAssemblyGenerator.cs#L34-L43)：

```csharp
var il2CppDummyDll = AssemblyDefinition.ReadAssembly(new MemoryStream(Resource1.Il2CppDummyDll));
// 取出 5 個 Mono.Cecil MethodDefinition 當「ctor 模板」：
//   AddressAttribute       — 給方法標 RVA/Offset/VA
//   FieldOffsetAttribute   — 給欄位標 offset
//   AttributeAttribute     — 給 attribute 標來源
//   MetadataOffsetAttribute — metadata offset
//   TokenAttribute         — IL2CPP token（addToken=true 才用）
```

`Il2CppDummyDll.dll` 真實檔案在 [Libraries/Il2CppDummyDll.dll](../Il2CppDumper/Libraries/Il2CppDummyDll.dll)，透過 `Resource1.resx`（[Resource1.Designer.cs](../Il2CppDumper/Resource1.Designer.cs)）以 `byte[]` 形式內嵌進可執行檔。

### 3.4 產生策略

按 image 一一建立 `AssemblyDefinition`，每個 type 都是 `TypeDefinition`，欄位 / 方法 / 屬性 / 事件 / 泛型參數逐個 add。方法本體用 Mono.Cecil 寫一個 `Ldnull + Throw` 的最小 IL（空 body 在 reflection-only 載入時有時會壞），但簽名完整。

幾個獨立 dict：

| dict | key → value |
|------|-------------|
| `typeDefinitionDic` | `Il2CppTypeDefinition → TypeDefinition` |
| `genericParameterDic` | `Il2CppGenericParameter → GenericParameter` |
| `fieldDefinitionDic` | `int (fieldIndex) → FieldDefinition` |
| `propertyDefinitionDic` | `int → PropertyDefinition` |
| `methodDefinitionDic` | `int → MethodDefinition` |

`AssemblyVersion` 來自 `assemblyDefs[].aname` 的 `major/minor/build/revision`；若 `build < 0`（generated assembly）則 fallback `3.7.1.6`（[DummyAssemblyGenerator.cs:62-71](../Il2CppDumper/Utils/DummyAssemblyGenerator.cs#L62-L71)）。

### 3.5 `addToken` 開關

`config.DummyDllAddToken = true` 時，每個 type 額外加 `[Token(Token="0xXXX")]` attribute（[DummyAssemblyGenerator.cs:124-129](../Il2CppDumper/Utils/DummyAssemblyGenerator.cs#L124-L129)）。方便對照 IL2CPP token。

### 3.6 Method body 內容

[DummyAssemblyGenerator.cs:252-273](../Il2CppDumper/Utils/DummyAssemblyGenerator.cs#L252-L273)：每個方法的 IL body 不是空的，而是依回傳型別產生最小 stub：

| 回傳型別 | IL stub |
|---------|---------|
| `System.Void` | `ret` |
| value type | `ldloca.s v; initobj T; ldloc.0; ret`（建一個 default 值再 ret） |
| reference type | `ldnull; ret` |
| `System.MulticastDelegate` 子類 | **不寫 body**（delegate 不能有 IL） |

⚠️ 這是給 Cecil 寫入時不報錯而設的最小 IL，不代表真實邏輯。dnSpy 開啟時方法 body 看起來像「return default」。

### 3.7 AddressAttribute 內容

每個非 abstract 方法都加 `[Address(RVA="0xX", Offset="0xY", VA="0xZ", Slot="N")]`（[DummyAssemblyGenerator.cs:302-322](../Il2CppDumper/Utils/DummyAssemblyGenerator.cs#L302-L322)）。Slot 只在 `methodDef.slot != 0xFFFF` 時加。

### 3.8 FieldOffsetAttribute 與 default value

[DummyAssemblyGenerator.cs:191-216](../Il2CppDumper/Utils/DummyAssemblyGenerator.cs#L191-L216)：

- 若 default value 在 blob 中能解出 → `fieldDefinition.Constant = value`（CIL `Constant` table）
- 若 default 解不出 → 加 `[MetadataOffset(Offset="0xXX")]` 標示原始偏移
- 非 literal field 一律加 `[FieldOffset(Offset="0xX")]`，offset 由 `il2Cpp.GetFieldOffsetFromIndex` 算出

### 3.9 三段式遍歷

`DummyAssemblyGenerator` 對所有 image 跑三輪（[DummyAssemblyGenerator.cs:57-448](../Il2CppDumper/Utils/DummyAssemblyGenerator.cs#L57-L448)）：

| Pass | 內容 |
|------|------|
| **1. 建類** | 所有 image → 所有 typeDef → `new TypeDefinition(ns, name, flags)`，加進 `moduleDefinition.Types`。`typeDefinitionDic` 建好查表 |
| **2. 結構填充** | 處理 nestedType、genericParameter、parent、interfaces。注意 genericParameter 在這階段需 `GetTypeReference` 解析 parent 之前先建好（[DummyAssemblyGenerator.cs:131-141](../Il2CppDumper/Utils/DummyAssemblyGenerator.cs#L131-L141)） |
| **3. 成員填充** | field / method / property / event。method 內含參數、回傳型別、body IL、AddressAttribute、FieldOffset、default value |
| **4. CustomAttribute** | v20+ 才有。透過 `CreateCustomAttribute` 對 type / field / method / param / property / event 加 Attribute（[DummyAssemblyGenerator.cs:386-448](../Il2CppDumper/Utils/DummyAssemblyGenerator.cs#L386-L448)） |

### 3.10 GenericParameter 處理

`CreateGenericParameter`（在後半部，未列引用行）對泛型參數的 `flags`、`constraints[]` 都處理。constraint 透過 `metadata.constraintIndices` 索引 `il2Cpp.types[]` 取得，再轉成 `TypeReference`。

### 3.11 `MyAssemblyResolver`

[Utils/MyAssemblyResolver.cs](../Il2CppDumper/Utils/MyAssemblyResolver.cs)（12 行）：繼承 `DefaultAssemblyResolver`，加 `Register(assembly)` 把建好的 assembly 註冊回 resolver，讓跨 assembly 引用能解析。

---

---

## 4. `script.json`

### 4.1 用途

給 IDA / Ghidra / BinaryNinja 的反組譯腳本讀取。對每個方法在反組譯結果上：rename function、套用型別 signature、貼上 string literal 註解。

### 4.2 結構（[Outputs/ScriptJson.cs](../Il2CppDumper/Outputs/ScriptJson.cs)）

```csharp
class ScriptJson {
    List<ScriptMethod>          ScriptMethod;          // 所有方法：Address, Name, Signature, TypeSignature
    List<ScriptString>          ScriptString;          // 所有 string literal 引用：Address, Value
    List<ScriptMetadata>        ScriptMetadata;        // metadataUsages 中的型別/欄位資訊：Address, Name, Signature
    List<ScriptMetadataMethod>  ScriptMetadataMethod;  // metadataUsage 中的 method：Address, Name, MethodAddress
    ulong[]                     Addresses;             // 所有需要 rename 為 method 的 address，供腳本一次性 make-function
}
```

### 4.3 對應的反組譯腳本

`Il2CppDumper.csproj` 把以下 Python 標記 `CopyToOutputDirectory`（[Il2CppDumper.csproj:37-59](../Il2CppDumper/Il2CppDumper.csproj#L37-L59)）：

| 腳本 | 工具 | 行數 | 行為 |
|------|------|------|------|
| `ida.py` | IDA Pro (Py2) | 78 | `make_function` 切函式邊界 → rename methods → label strings → set metadata names |
| `ida_py3.py` | IDA Pro (Py3) | 78 | 同上但 Python 3 相容 |
| `ida_with_struct.py` / `ida_with_struct_py3.py` | IDA Pro | 87 | 同上 + 從 `il2cpp.h` `idc.parse_decls` 套 struct 型別 + 對每個 method 套 function signature |
| `ghidra.py` | Ghidra (Jython) | 87 | rename + label strings；無 `Addresses[]` 處理（Ghidra 自己分析） |
| `ghidra_with_struct.py` | Ghidra | 156 | 同上 + `DataTypeManager` 載入 `il2cpp.h` |
| `ghidra_wasm.py` | Ghidra + [ghidra-wasm-plugin](https://github.com/nneonneo/ghidra-wasm-plugin) | 100 | 用 `WasmLoader.loadElementsToTable` 處理 wasm function table，再做 rename |
| `hopper-py3.py` | Hopper | 32 | 最簡：只跑 `ScriptMethod` → `setNameAtAddress` |
| `il2cpp_header_to_ghidra.py` | Ghidra | 37 | 單純匯入 `il2cpp.h` 為 Ghidra DataType |
| `il2cpp_header_to_binja.py` | BinaryNinja | 41 | 單純匯入 `il2cpp.h` 為 BinaryNinja Type |
| [`Il2CppBinaryNinja/`](../Il2CppDumper/Il2CppBinaryNinja/) | BinaryNinja plugin | — | 透過 BinaryNinja Plugin Manager 安裝，整合三段式（types → methods → strings）+ 進度條 |

注意這些 Python 不會被 Il2CppDumper 動態執行，只是檔案產出時一起複製到 build output 目錄，使用者再手動拿到對應工具裡執行。

### 4.4 各腳本通用流程

```
1. 開啟 script.json → 解析 JSON
2. (IDA only) 對 Addresses[] 依相鄰位址 make_function(start, end) 切邊界
3. for scriptMethod in ScriptMethod:
       addr = imageBase + Address
       set_name(addr, Name)
       (with_struct only) apply_function_signature(addr, Signature)
4. for scriptString in ScriptString:
       label addr → StringLiteral_N
       comment addr → Value
5. for scriptMetadata in ScriptMetadata:
       set_name(addr, Name)
       (with_struct only) apply_type(addr, Signature)
6. for scriptMetadataMethod in ScriptMetadataMethod:
       set_name(addr, Name)
       (IDA) plain_data + offset to MethodAddress
```

`get_addr(addr)` 永遠是 `imageBase + addr`，這就是 `script.json` 為什麼存 RVA 不存 VA：跨平台共用。

### 4.5 BinaryNinja Plugin（`Il2CppBinaryNinja/__init__.py`）

[`__init__.py`](../Il2CppDumper/Il2CppBinaryNinja/__init__.py) 是與其他腳本不同的整合方式 — 它是個 BinaryNinja **plugin**（透過 `PluginCommand.register` 註冊），會出現在 Plugins 選單。

執行流程（在 `BackgroundTaskThread` 內，含進度條 + cancel 支援）：

```
1. process_header()  ── 「Il2Cpp types (1/3)」
       parse_types_from_string(il2cpp.h)
       for each type: bv.define_user_type(name, type)
2. has_types = bv.get_type_by_name("Il2CppClass") is not None
3. process_methods(data)  ── 「Il2Cpp methods (2/3)」
       for scriptMethod:
           addr = bv.start + Address
           name = Name.replace("$", "_").replace(".", "_")
           if has_types:
               func.function_type = signature
           else:
               func.name = Name
4. process_strings(data)  ── 「Il2Cpp strings (3/3)」
       for scriptString:
           bv.get_data_var_at(addr).name = f"StringLiteral_{i}"
           bv.set_comment_at(addr, value)
```

注意：
- BinaryNinja plugin 用兩種 header：常規 `il2cpp.h` + 額外 `il2cpp_binja.h`（後者是 BinaryNinja 友善版本，由 [`il2cpp_header_to_binja.py`](../Il2CppDumper/il2cpp_header_to_binja.py) 預處理產生）
- 只有偵測到 `Il2CppClass` 型別存在才套 signature，否則只 rename。這個檢查避免在 header 沒載入時 BinaryNinja 套錯型別簽名
- `process_metadata` 並沒實作（plugin 跳過 ScriptMetadata），可能 BinaryNinja 對 data label 處理有差異

---

## 5. `stringliteral.json`

[StructGenerator.cs:376](../Il2CppDumper/Outputs/StructGenerator.cs#L376)

包含 metadata 內所有 string literal（CIL 程式碼裡的 `"..."`）的純文字 JSON 陣列。順序對應 `metadata.stringLiterals[]` 的索引。

格式（推測，未實際 grep struct）：

```json
[
  {"value": "PlayerData"},
  {"value": "Hello World"},
  ...
]
```

被 IDA / Ghidra 腳本用：把 `IL2CPP_METADATA_USAGE_STRING_LITERAL` 類型的 metadataUsage 變成 string comment。

---

## 6. `il2cpp.h`

### 6.1 用途

C/C++ struct header，描述 IL2CPP runtime + 解析出的 type 結構，給 IDA / Ghidra 套用 struct type。包含：

- IL2CPP runtime 通用 struct：`Il2CppObject`、`Il2CppClass`、`MethodInfo`、`Il2CppArray*` 等（從 [`HeaderConstants.cs`](../Il2CppDumper/Outputs/HeaderConstants.cs) 取固定樣板，683 行常數字串）
- 每個 type 的 fields 結構：`struct {ClassName}__Fields { ... }`
- 每個 type 的 static fields 結構：`struct {ClassName}_StaticFields { ... }`
- 每個 type 的 VTable：`struct {ClassName}__VTable { ... }`
- 泛型實例：`struct {ClassName}_{TypeArg1}_{TypeArg2}__Fields { ... }`
- RGCTX 函式宣告

### 6.2 名稱衝突處理

[StructGenerator.cs:29-33](../Il2CppDumper/Outputs/StructGenerator.cs#L29-L33) 內建 C++ 保留字集合：

```csharp
keyword = { klass, monitor, register, _cs, auto, friend, template, flat, default,
            _ds, interrupt, unsigned, signed, asm, if, case, break, continue, do,
            new, _, short, union, class, namespace };

specialKeywords = { inline, near, far };
```

撞到就用 `FixName` 加底線改名。`structNameHashSet` 確保 struct 名稱唯一。

### 6.3 ParseType 對應

[`StructGenerator.ParseType`](../Il2CppDumper/Outputs/StructGenerator.cs#L542-L677)：把 `Il2CppType` 轉成 C 型別字串。每個 typeDef 內部命名規則：`{structName}_o`（物件）、`{structName}_c`（class metadata，類似 `Il2CppClass`）、`{structName}_Fields`、`{structName}_StaticFields`、`{structName}_VTable`、`{structName}_RGCTXs`。

| IL2CPP_TYPE | C struct | 備註 |
|-------------|----------|------|
| `VOID` | `void` | — |
| `BOOLEAN` | `bool` | — |
| `CHAR` | `uint16_t` | `Il2CppChar` 是 UTF-16 |
| `I1` / `U1` | `int8_t` / `uint8_t` | — |
| `I2` / `U2` | `int16_t` / `uint16_t` | — |
| `I4` / `U4` | `int32_t` / `uint32_t` | — |
| `I8` / `U8` | `int64_t` / `uint64_t` | — |
| `R4` / `R8` | `float` / `double` | — |
| `STRING` | `System_String_o*` | — |
| `PTR` | `{ParseType(原型)}*` | 遞迴 |
| `VALUETYPE` | `{structName}_o`（inline） | enum → 解到 underlying primitive |
| `CLASS` | `{structName}_o*`（pointer） | — |
| `VAR` (class generic param) | `{ParseType(context.class_inst[num])}` | 無 context 時 → `Il2CppObject*` |
| `MVAR` (method generic param) | 同上但用 `method_inst` | issue #687 fix：method_inst==0 時 fallback class_inst |
| `ARRAY` (多維) | `{elementStructName}_array*` + 生成 `struct {name}_array` | 含 `IL2cppObject obj; Il2CppArrayBounds *bounds; il2cpp_array_size_t max_length; T m_Items[65535]` |
| `SZARRAY` (一維) | 同上 | — |
| `GENERICINST` (value type) | `{typeStructName}_o` | — |
| `GENERICINST` (ref type) | `{typeStructName}_o*` | typeStructName 來自 `genericClassStructNameDic` |
| `TYPEDBYREF` | `Il2CppObject*` | — |
| `I` / `U` | `intptr_t` / `uintptr_t` | — |
| `OBJECT` | `Il2CppObject*` | — |

### 6.4 StructInfo 巢狀關係

[`StructInfo`](../Il2CppDumper/Outputs/StructInfo.cs)：

```
StructInfo
├── TypeName              : 唯一名稱（已 FixName + GetUniqueName）
├── IsValueType           : 來自 typeDef.IsValueType
├── Parent                : structName（不含 _o 後綴）；非 valuetype + 非 enum + parent != Object
├── Fields[]              : instance 非 const 欄位
│   ├── FieldTypeName     : ParseType 結果（可能含 _o*）
│   ├── FieldName         : FixName(name)，重複時加 _i_ 前綴
│   ├── IsValueType       : 給遞迴展開判斷
│   └── IsCustomType      : 給「是否要加 struct 關鍵字」判斷
├── StaticFields[]        : instance static 非 const 欄位
├── VTableMethod[]        : 按 slot 排序的 vtable，沒填的填 `unknown`
└── RGCTXs[]              : runtime generic context
    ├── Type (data type)
    ├── TypeName / ClassName / MethodName
```

### 6.5 il2cpp.h 整體結構

由 [`StructGenerator.WriteScript`](../Il2CppDumper/Outputs/StructGenerator.cs#L394-L431) 組裝順序：

```
1. HeaderConstants.GenericHeader     ← 永遠加：Il2CppMethodPointer / Il2CppType / Il2CppObject / Il2CppRGCTXData / Il2CppRuntimeInterfaceOffsetPair
2. HeaderConstants.HeaderVxx          ← 依版本選一：
       v22       → HeaderV22
       v23/24    → HeaderV240
       v24.1     → HeaderV241
       v24.2/3/4/5 → HeaderV242
       v27/27.1/27.2 → HeaderV27
       v29/29.1/31   → HeaderV29
       其他      → 印 WARNING 並 return
3. headerStruct                       ← 由 RecursionStructInfo 為每個 type 產出 `_Fields`, `_RGCTXs`, `_VTable`, `_c`, `_o`, `_StaticFields`
4. arrayClassHeader                   ← 每個被引用的 SZARRAY/ARRAY 元素產出 `{name}_array` struct
5. methodInfoHeader                   ← 每個泛型實例方法產出 `MethodInfo_0xXXX` struct（含 RGCTX）
```

### 6.6 RecursionStructInfo 產生的 type-specific struct 模板

對每個 `StructInfo` 產出（[StructGenerator.cs:968-1126](../Il2CppDumper/Outputs/StructGenerator.cs#L968-L1126)）：

```c
struct Foo_Fields : Parent_Fields {   // C++ 繼承
    int x;
    Bar_o* y;
};

struct Foo_RGCTXs {                   // 只當 RGCTX > 0 時
    Il2CppType* _0_TypeName;
    Il2CppClass* _1_ClassName;
    MethodInfo* _2_MethodName;
};

struct Foo_VTable {                   // 只當 vtable_count > 0 時
    VirtualInvokeData _0_MethodName;
    VirtualInvokeData _1_unknown;
    ...
};

struct Foo_c {                        // class metadata（對應 IL2CPP runtime Il2CppClass）
    Il2CppClass_1 _1;
    struct Foo_StaticFields* static_fields;       // 沒有 static 就是 void*
    Foo_RGCTXs* rgctx_data;                        // 沒有 RGCTX 就是 Il2CppRGCTXData*
    Il2CppClass_2 _2;
    Foo_VTable vtable;                             // 沒有則 VirtualInvokeData vtable[32]
};

struct Foo_o {                        // 物件（instance）
    Foo_c *klass;       // 非 valuetype 才有
    void *monitor;      // 非 valuetype 才有
    Foo_Fields fields;
};

struct Foo_StaticFields {             // 只當 StaticFields > 0 時
    int x;
    ...
};
```

PE 平台 + 非 valuetype 會加 `__declspec(align(4))` / `__declspec(align(8))`（[StructGenerator.cs:989-998](../Il2CppDumper/Outputs/StructGenerator.cs#L989-L998)），給 MSVC 對齊。

### 6.7 MethodInfo struct 對應版本變化

[`GenerateMethodInfo`](../Il2CppDumper/Outputs/StructGenerator.cs#L1336-L1420)：每個泛型方法實例生成一個專屬 `MethodInfo_0xXXX`：

| 欄位 | v ≤ 24 | v 25-28 | v ≥ 29 |
|------|--------|---------|--------|
| `methodPointer` | ✅ | ✅ | ✅ |
| `virtualMethodPointer` | — | — | ✅ |
| `invoker_method` | `void*` | `void*` | `InvokerMethod` |
| `name` | ✅ | ✅ | ✅ |
| `declaring_type` / `klass` | `declaring_type` | `klass` | `klass` |
| `return_type` | ✅ | ✅ | ✅ |
| `parameters` | `void*` (ParameterInfo*) | `void*` | `Il2CppType**` |
| `rgctx_data` | type-specific | 同 | 同 |
| union {genericMethod, genericContainer/Handle} | `genericContainer` | `genericContainerHandle` (v27+) | 同 |
| `customAttributeIndex` | ✅ | — | — |
| `token`, `flags`, `iflags`, `slot`, `parameters_count`, `bitflags` | ✅ | ✅ | ✅ |

### 6.8 MetadataUsage 兩條路徑

v19~26：用 `metadata.metadataUsageDic` 直接拿到 `slot → typeIndex` 對照表，遍歷產生 ScriptMetadata（[StructGenerator.cs:342-368](../Il2CppDumper/Outputs/StructGenerator.cs#L342-L368)）。

v27+：metadataUsage 不在 metadata.dat 內，改散落在 binary 的 data section。`StructGenerator` 自己掃描所有 data section，逐個 pointer 解碼：

```csharp
if (metadataValue < uint.MaxValue):
    encodedToken = (uint)metadataValue;
    usage = GetEncodedIndexType(encodedToken);       // 高 3 bit
    decodedIndex = GetDecodedMethodIndex(encodedToken);
    
    // 驗證重編碼後能還原 → 確認真的是 metadataUsage 而非雜湊
    if (metadataValue == ((usage << 29) | (decodedIndex << 1)) + 1):
        va = MapRTVA(addr);
        switch (usage): kIl2CppMetadataUsageTypeInfo / IL2CppType / MethodDef / FieldInfo / StringLiteral / MethodRef
```

關鍵：`+1` 是 v27+ encoded index 的 LSB 設位（給 metadataUsage 識別）。掃描完整 data 區段成本不小，所以 v27+ 處理時間明顯比 v24 長。

### 6.9 script.json 五大區段內容

[`StructGenerator.WriteScript`](../Il2CppDumper/Outputs/StructGenerator.cs#L42)（接續 §4.2 的 schema）：

| 欄位 | 來源 | IDA/Ghidra 用法 |
|------|------|----------------|
| `ScriptMethod[].Address/Name/Signature/TypeSignature` | 所有 method（含泛型實例）的 RVA + 完整 C++ signature | rename function + apply function type signature |
| `ScriptString[].Address/Value` | metadataUsageStringLiteral | 在 string 引用位址加 comment |
| `ScriptMetadata[].Address/Name/Signature` | TypeInfo / IL2cppType / FieldInfo | rename + set type（如 `MyClass_TypeInfo` 設成 `MyClass_c*`） |
| `ScriptMetadataMethod[].Address/Name/MethodAddress` | MethodDef / MethodRef | rename `Method$Foo.Bar()` + 在 IDE 跳轉到 MethodAddress |
| `Addresses[]` | 全部 method/genericMethod/invoker/customAttribute/reversePInvoke 指標排序去重 | 給 IDA 用 `make_function(addresses[i], addresses[i+1])` 強制建立函式邊界 |

`TypeSignature` 是 emscripten function pointer 編碼（`v`=void, `i`=int/ref, `j`=long, `f`=float, `d`=double）。給 wasm 反組譯特別有用。

### 6.10 FixName 保留字處理

[`FixName`](../Il2CppDumper/Outputs/StructGenerator.cs#L521-L540)：

```
1. C++ 保留字（如 class, namespace, default, union, ...）→ 前綴 `_`
2. specialKeywords（inline, near, far）→ 前後都加 `_`
3. 以數字開頭 → 前綴 `_`
4. 非 [a-zA-Z0-9_] 字元 → 替換成 `_`
```

`structNameHashSet` + `GetUniqueName` 確保去重後唯一，撞名加 `_1` / `_2` 後綴。

---

## 7. 輸出檔的關聯

```
dump.cs                 ← Decompiler 產出，人讀 / git diff 用
DummyDll/*.dll          ← Cecil 產出，給 dnSpy 用 + UtinyRipper 抽 MonoBehaviour
il2cpp.h                ← StructGenerator 產出，給 IDA 套 struct 型別
script.json             ← StructGenerator 產出，給 ida.py/ghidra.py 等腳本讀
stringliteral.json      ← StructGenerator 產出，給腳本貼 string comment
ida.py / ghidra.py / …  ← 隨可執行檔複製到 output dir，讓使用者拿到逆向工具用
```

---

## 8. 修改時的注意事項

| 改的地方 | 風險 |
|---------|------|
| `Il2CppDecompiler` 內輸出格式 | 直接影響「git diff dump.cs 比對版本變化」工作流。**改 dump.cs 格式請走 major version** |
| `ScriptJson` 欄位 | 對應 Python 腳本的 schema，砍欄位會讓現有腳本爆 |
| `il2cpp.h` 內 struct 命名 | IDA / Ghidra 已 apply 的 struct 會變孤兒，使用者需重新 apply |
| `DummyAssemblyExporter` 改 cwd 行為 | 在 GUI / 多執行緒環境會踩 |
| 內嵌 `Il2CppDummyDll.dll` | 換 dummy DLL 需重 build resx，不能單純換檔 |
