# DataModel — 資料模型與反射讀取機制

> 本檔聚焦在「資料怎麼從磁碟上的 bytes 變成 C# 物件」。包含 `BinaryStream` 的反射讀取、版本相容欄位機制、以及 `Il2Cpp*` / `*Definition` 結構體對應的 IL2CPP runtime 概念。

---

## 1. `BinaryStream` — 反射式結構讀取

[IO/BinaryStream.cs](../Il2CppDumper/IO/BinaryStream.cs)

這是整個專案最關鍵的「黑魔法」：不需要為每個 C++ struct 寫對應的 binary reader。改成定義一個 POCO，欄位用 `[Version]` / `[ArrayLength]` 標記，呼叫 `ReadClass<T>()` 就會把 stream 內容反射填入。

### 1.1 讀取規則（[`ReadClass<T>`](../Il2CppDumper/IO/BinaryStream.cs#L115)）

```
foreach (FieldInfo field in typeof(T).GetFields()):

    1. 檢查欄位是否有 [Version(Min=X, Max=Y)]
       - 若有且 (Version < Min || Version > Max) → 跳過，不讀
       - 多個 [Version] 屬性（AllowMultiple=true）→ OR 邏輯，任一範圍命中就讀

    2. 依 FieldType 分派：
       - IsPrimitive  → ReadPrimitive(type)
       - IsEnum       → ReadPrimitive(enum 底層型別)
       - IsArray      → 需要 [ArrayLength(Length=N)] → ReadClassArray<T>(N)
       - 其他 (struct) → 遞迴 ReadClass<T>()
```

### 1.2 Primitive 型別表

[`ReadPrimitive`](../Il2CppDumper/IO/BinaryStream.cs#L94) 處理 6 種 primitive：

| C# 型別 | 讀取方式 | 注意 |
|---------|---------|------|
| `Int32` / `UInt32` | 4 bytes | — |
| `Int16` / `UInt16` | 2 bytes | — |
| `Byte` | 1 byte | — |
| `Int64` / `UInt64` | **依 `Is32Bit` 變動**（呼叫 `ReadIntPtr`/`ReadUIntPtr`） | 這就是為什麼 IL2CPP 的 `ulong` 欄位在 32bit 檔案會讀 4 bytes |

⚠️ `IL2CPP_TYPE_*` 在欄位用 `ulong` 表示 native pointer，所以同一個 POCO 在 32-bit 和 64-bit binary 上跑出來的 bytes 數**不一樣**。這是 IL2CPP 結構在不同位元的 padding 差異被吸收的地方。

### 1.3 反射快取

- `genericMethodCache`：`Type → MethodInfo`（避免每次都 `MakeGenericMethod`）
- `attributeCache`：`FieldInfo → VersionAttribute[]`（避免每次都 `GetCustomAttributes`）

兩個 cache 都是 instance 級，每個 `BinaryStream` 實例獨立。

### 1.4 寫入

`BinaryStream` 也提供 `Write(...)`，給 [`Elf64.FixedProgramSegment`](../Il2CppDumper/ExecutableFormats/Elf64.cs#L262) / `RelocationProcessing` 等場景就地修改 stream。

---

## 2. `[Version]` / `[ArrayLength]` 屬性

| Attribute | 出處 | 用法 |
|-----------|------|------|
| `VersionAttribute` | [Attributes/VersionAttribute.cs](../Il2CppDumper/Attributes/VersionAttribute.cs) | `AllowMultiple = true`。`Min` 預設 0，`Max` 預設 99。判定式：`Version >= Min && Version <= Max` |
| `ArrayLengthAttribute` | [Attributes/ArrayLengthAttribute.cs](../Il2CppDumper/Attributes/ArrayLengthAttribute.cs) | 給 byte[] / 固定長度陣列欄位（如 `public_key_token[8]`）標長度 |

`Version` 屬性的 `double` 設計重要：版本號實際是 `16`、`24.1`、`24.2`、`24.3`、`24.4`、`24.5`、`27`、`27.1`、`27.2`、`29`、`29.1`、`31` 這種小數編號。詳見 [Version_Compatibility.md](Version_Compatibility.md)。

---

## 3. Metadata 資料模型

### 3.1 `Il2CppGlobalMetadataHeader`

[MetadataClass.cs:5-109](../Il2CppDumper/Il2Cpp/MetadataClass.cs#L5-L109)

`global-metadata.dat` 的檔頭。所有 `offset`/`size` 對都是「在檔案中的位置 + 長度（bytes）」。重要 offset：

| 欄位 | 對應陣列 | 元素型別 |
|------|---------|---------|
| `stringLiteralOffset / Size` | — | 給 metadata 取 `stringLiteral` 字串 |
| `stringOffset / Size` | — | 給 metadata 取一般字串（type name、namespace、method name）|
| `eventsOffset / Size` | `eventDefs[]` | `Il2CppEventDefinition` |
| `propertiesOffset / Size` | `propertyDefs[]` | `Il2CppPropertyDefinition` |
| `methodsOffset / Size` | `methodDefs[]` | `Il2CppMethodDefinition` |
| `fieldsOffset / Size` | `fieldDefs[]` | `Il2CppFieldDefinition` |
| `parametersOffset / Size` | `parameterDefs[]` | `Il2CppParameterDefinition` |
| `typeDefinitionsOffset / Size` | `typeDefs[]` | `Il2CppTypeDefinition` |
| `imagesOffset / Size` | `imageDefs[]` | `Il2CppImageDefinition` |
| `assembliesOffset / Size` | `assemblyDefs[]` | `Il2CppAssemblyDefinition` |
| `genericContainersOffset` | `genericContainers[]` | `Il2CppGenericContainer` |
| `genericParametersOffset` | `genericParameters[]` | `Il2CppGenericParameter` |
| `attributesInfoOffset` (v21~27.2) | `attributeTypeRanges[]` | `Il2CppCustomAttributeTypeRange` |
| `attributeDataRangeOffset` (v29+) | `attributeDataRanges[]` | `Il2CppCustomAttributeDataRange` |
| `metadataUsageListsOffset` (v19~24.5) | 用來建 `metadataUsageDic` | — |

⚠️ 「Size」其實是 byte 長度，需要除以 `sizeof(struct)` 才能變成元素數。`Metadata.ReadMetadataClassArray` 自動做這個除法（[Metadata.cs:160](../Il2CppDumper/Il2Cpp/Metadata.cs#L160)），而 `SizeOf` 又是版本相關（[Metadata.cs:256](../Il2CppDumper/Il2Cpp/Metadata.cs#L256)）—— 同一個 POCO 在不同 version 下會跳過不同欄位，size 也不同。

### 3.2 `Il2CppTypeDefinition`

[MetadataClass.cs:166-233](../Il2CppDumper/Il2Cpp/MetadataClass.cs#L166-L233)

最關鍵的結構：每個 type 都是一個 `typeDef`。連續欄位有兩種角色：

**索引/長度配對**（指向其他陣列）

| Start 欄位 | Count 欄位 | 目標陣列 |
|-----------|-----------|---------|
| `fieldStart` | `field_count` | `metadata.fieldDefs[]` |
| `methodStart` | `method_count` | `metadata.methodDefs[]` |
| `eventStart` | `event_count` | `metadata.eventDefs[]` |
| `propertyStart` | `property_count` | `metadata.propertyDefs[]` |
| `nestedTypesStart` | `nested_type_count` | `metadata.nestedTypeIndices[]` |
| `interfacesStart` | `interfaces_count` | `metadata.interfaceIndices[]` |
| `vtableStart` | `vtable_count` | `metadata.vtableMethods[]` |
| `interfaceOffsetsStart` | `interface_offsets_count` | — |

**bitfield**（[MetadataClass.cs:216-227](../Il2CppDumper/Il2Cpp/MetadataClass.cs#L216-L227)）

```
bit 1     : valuetype
bit 2     : enumtype
bit 3     : has_finalize
bit 4     : has_cctor
bit 5     : is_blittable
bit 6     : is_import_or_windows_runtime
bit 7-10  : PackingSize (9 種值之一)
bit 11    : PackingSize is default
bit 12    : ClassSize is default
bit 13-16 : Specified PackingSize
```

只有 `IsValueType` / `IsEnum` 被以屬性 expose（[MetadataClass.cs:231-232](../Il2CppDumper/Il2Cpp/MetadataClass.cs#L231-L232)）。

### 3.3 `Il2CppMethodDefinition` 的版本演化

[MetadataClass.cs:235-261](../Il2CppDumper/Il2Cpp/MetadataClass.cs#L235-L261)

```csharp
public uint nameIndex;
public int declaringType;
public int returnType;
[Version(Min = 31)] public int returnParameterToken;   // v31 才有
public int parameterStart;
[Version(Max = 24)] public int customAttributeIndex;    // v24 之後拿掉，改走 imageDef.customAttribute*
public int genericContainerIndex;
[Version(Max = 24.1)] public int methodIndex;           // v24.2 之後改用 codeGenModule.methodPointers[token & 0xFFFFFF]
[Version(Max = 24.1)] public int invokerIndex;
[Version(Max = 24.1)] public int delegateWrapperIndex;
[Version(Max = 24.1)] public int rgctxStartIndex;       // v24.2 之後改用 rgctxsDictionary
[Version(Max = 24.1)] public int rgctxCount;
public uint token;
public ushort flags, iflags, slot, parameterCount;
```

`methodIndex` 是 v24.1 以前的「方法指標表索引」；v24.2 起改用 per-image 的 `codeGenModule.methodPointers`，索引變成 `token & 0x00FFFFFF - 1`（[Il2Cpp.cs:323-340](../Il2CppDumper/Il2Cpp/Il2Cpp.cs#L323-L340)）。

### 3.4 Metadata 內部 dictionary

`Metadata` 建構時就建好以下 dict，供之後查表：

| Dictionary | Key | Value | 用途 |
|-----------|-----|-------|------|
| `fieldDefaultValuesDic` | `fieldIndex` | `Il2CppFieldDefaultValue` | dump 欄位 default |
| `parameterDefaultValuesDic` | `parameterIndex` | `Il2CppParameterDefaultValue` | dump 參數 default |
| `attributeTypeRangesDic` | `imageDef → { token → index }` | — | 給 `GetCustomAttributeIndex` 查 |
| `metadataUsageDic` | `Il2CppMetadataUsage → SortedDict<destinationIndex, decodedIndex>` | — | v19~24.5 的 metadata usage 機制 |
| `stringCache` | string offset | 字串 | 避免重複讀 |

### 3.5 v27+ 的編碼變更

`GetDecodedMethodIndex`（[Metadata.cs:247-254](../Il2CppDumper/Il2Cpp/Metadata.cs#L247-L254)）：

```csharp
if (Version >= 27)
    return (index & 0x1FFFFFFEU) >> 1;     // bit 0 給其他用途
else
    return index & 0x1FFFFFFFU;
```

`GetEncodedIndexType`（取高 3 bit）兩者一致。

---

## 4. IL2CPP runtime 資料模型

### 4.1 `Il2CppCodeRegistration`

[Il2CppClass.cs:5-66](../Il2CppDumper/Il2Cpp/Il2CppClass.cs#L5-L66)

執行檔內描述「程式碼相關指標表」位置的中央結構。版本變動劇烈：

| 範圍 | 欄位 | 角色 |
|------|------|------|
| Max=24.1 | `methodPointersCount`, `methodPointers` | 舊版的全域方法指標表（v24.2 起改成 per-image） |
| Max=21 | `delegateWrappersFromNativeToManaged*` | 已廢除 |
| Min=22 | `reversePInvokeWrapperCount`, `reversePInvokeWrappers` | 反向 PInvoke |
| 一直都有 | `genericMethodPointersCount`, `genericMethodPointers` | 泛型方法實例的指標 |
| Min=24.5..24.5 / Min=27.1 | `genericAdjustorThunks` | adjustor thunk（這個欄位的 `[Version]` 雙標籤值得注意：24.5 only + 27.1+，跳過 25/26/27.0） |
| 一直都有 | `invokerPointersCount`, `invokerPointers` | invoker stub |
| Max=24.5 | `customAttributeGenerators` | v27+ 改成 per-module |
| Min=22 | `unresolvedVirtualCallCount/Pointers` | unresolved virtual call |
| Min=29.1 | `unresolvedInstanceCallPointers`, `unresolvedStaticCallPointers` | v29.1 又拆細 |
| Min=23 | `interopDataCount`, `interopData` | COM interop |
| Min=24.3 | `windowsRuntimeFactoryCount/Table` | WinRT |
| Min=24.2 | `codeGenModulesCount`, `codeGenModules` | per-image module 表（v24.2 大改的核心） |

> 對應註：[`Il2Cpp.Init`](../Il2CppDumper/Il2Cpp/Il2Cpp.cs#L120) 內的 `if (Version >= 24.2) { ... pCodeGenModules ... }` 就是處理這個切換。

### 4.2 `Il2CppCodeGenModule`（v24.2+）

[Il2CppClass.cs:261-290](../Il2CppDumper/Il2Cpp/Il2CppClass.cs#L261-L290)

每個 image / module 對應一個 `Il2CppCodeGenModule`，內含該 image 的：
- `methodPointers[]`：以 `token & 0x00FFFFFF - 1` 為索引
- `adjustorThunks[]`（v24.5 / v27.1+）
- `invokerIndices[]`
- `reversePInvokeWrapperIndices[]`
- `rgctxRanges[]` / `rgctxs[]`：per-image RGCTX
- v27+：`moduleInitializer`、`staticConstructorTypeIndices`、`metadataRegistration`、`codeRegistaration`（per-assembly mode）

`Il2Cpp.codeGenModules`（[Il2Cpp.cs:30](../Il2CppDumper/Il2Cpp/Il2Cpp.cs#L30)）以 module name 為 key。

### 4.3 `Il2CppType`

[Il2CppClass.cs:139-203](../Il2CppDumper/Il2Cpp/Il2CppClass.cs#L139-L203)

物理結構在 binary 中是 `ulong datapoint + uint bits`（[Il2CppClass.cs:141-142](../Il2CppDumper/Il2Cpp/Il2CppClass.cs#L141-L142)），讀完後 [`Init(version)`](../Il2CppDumper/Il2Cpp/Il2CppClass.cs#L151) 把 `bits` 解碼成 `type / attrs / num_mods / byref / pinned / valuetype`。

v27.2 之前 v27.2 之後的 bit 切分不同：

```
v < 27.2:  bits 0-15: attrs, 16-23: type, 24-29: num_mods (6 bit), 30: byref, 31: pinned
v >= 27.2: bits 0-15: attrs, 16-23: type, 24-28: num_mods (5 bit), 29: byref, 30: pinned, 31: valuetype
```

`Union` 是 C++ side 的 union 在 C# 用 inline property 模擬：依語意給不同名稱看同一個 `dummy` 欄位（[Il2CppClass.cs:171-202](../Il2CppDumper/Il2Cpp/Il2CppClass.cs#L171-L202)）。

### 4.4 Generics / RGCTX

- `Il2CppMethodSpec`：泛型方法實例（哪個 `methodDef` × 哪個 `classInst` × 哪個 `methodInst`）
- `Il2CppGenericInst`：實例化的型別參數陣列
- `Il2CppGenericClass`：泛型實例化的 class（v24.5 之前用 `typeDefinitionIndex`，v27+ 改用 `type` 指向 `Il2CppType`）
- `Il2CppGenericContainer`：泛型容器（一個 class 或 method 的「我有幾個型別參數」）
- `Il2CppRGCTXDefinition`：Runtime Generic Context（v24.2 之前是全域陣列，之後變 per-image 的 token range 映射）

`Il2Cpp.Init` 末段（[Il2Cpp.cs:243-256](../Il2CppDumper/Il2Cpp/Il2Cpp.cs#L243-L256)）建兩張 dict：

```csharp
methodDefinitionMethodSpecs : methodDefinitionIndex → List<methodSpec>
methodSpecGenericMethodPointers : methodSpec → 對應的 genericMethodPointer (VA)
```

讓 `Decompiler` 能輸出 `GenericInstMethod` 表（[Il2CppDecompiler.cs:358-382](../Il2CppDumper/Outputs/Il2CppDecompiler.cs#L358-L382)）。

---

## 5. Field Offsets 的雙模式

[`Il2Cpp.GetFieldOffsetFromIndex`](../Il2CppDumper/Il2Cpp/Il2Cpp.cs#L274-L312) 處理兩種儲存方式：

| 模式 | 偵測 | 取值 |
|------|------|------|
| **fieldOffsetsArePointers = true**（v22+，v21 透過試讀判定） | `pMetadataRegistration.fieldOffsets[typeIndex]` 是一個指標，指向「該 type 的所有欄位 offset」 | `ReadInt32` at `MapVATR(ptr) + 4 × fieldIndexInType` |
| **fieldOffsetsArePointers = false**（v≤20） | `fieldOffsets` 是 flat 陣列 | `(int)fieldOffsets[fieldIndex]` |

額外校正：valuetype 且非 static 時，32-bit 扣 8、64-bit 扣 16（[Il2Cpp.cs:294-304](../Il2CppDumper/Il2Cpp/Il2Cpp.cs#L294-L304)）。

---

## 6. 字串系統

Metadata 內有兩種字串系統，不要搞混：

| 系統 | 用途 | 取得方式 |
|------|------|---------|
| `stringOffset / stringSize` | 一般 metadata 字串：type name、namespace、method name、parameter name… | `metadata.GetStringFromIndex(uint)` → 從 `stringOffset + index` 讀 null-terminated UTF-8 |
| `stringLiteralOffset / stringLiteralDataOffset` | C# 程式碼裡的 `"abc"` 字串字面值 | `metadata.GetStringLiteralFromIndex(uint)` → 由 `stringLiterals[index]` 取出 `dataIndex/length`，再從 `stringLiteralDataOffset + dataIndex` 讀 UTF-8 |

`stringCache` 只快取第一種。

---

## 7. CustomAttribute Blob 讀取

v21 ~ 28：使用 `customAttributeGenerators` 指標表 + `attributeTypeRanges`，輸出時只列 attribute 類型名（不 decode 引數）。

v29+：完全改寫成 blob 格式，由 [`CustomAttributeDataReader`](../Il2CppDumper/Utils/CustomAttributeDataReader.cs) 解析，可以還原 named arguments、ctor args、enum values 等。Compressed int / compressed uint 編碼見 [`BinaryReaderExtensions.ReadCompressedUInt32`](../Il2CppDumper/Extensions/BinaryReaderExtensions.cs#L39-L84) / [`ReadCompressedInt32`](../Il2CppDumper/Extensions/BinaryReaderExtensions.cs#L86-L99)。

Blob 通用 reader 入口是 [`Il2CppExecutor.GetConstantValueFromBlob`](../Il2CppDumper/Utils/Il2CppExecutor.cs#L343)，支援所有 primitive、string、SZARRAY、ENUM。v29+ 的 `U4/I4` 改用 compressed 編碼（[Il2CppExecutor.cs:369-388](../Il2CppDumper/Utils/Il2CppExecutor.cs#L369-L388)）。

### 7.1 v29+ CustomAttribute blob 完整 schema

[`CustomAttributeDataReader`](../Il2CppDumper/Utils/CustomAttributeDataReader.cs)：繼承 `BinaryReader`，從 `attributeData[startOffset..endOffset]` 切出的 buffer 解析。

**Blob 整體結構**（[CustomAttributeDataReader.cs:15-22](../Il2CppDumper/Utils/CustomAttributeDataReader.cs#L15-L22)）：

```
┌─────────────────────────────────────────────────────────┐
│ compressed UInt32: Count（這個 token 上的 attribute 數）│
├─────────────────────────────────────────────────────────┤
│ Int32 × Count: ctorIndex 陣列（每個 4 bytes）           │ ← ctorBuffer
├─────────────────────────────────────────────────────────┤
│ 對每個 attribute：                                       │ ← dataBuffer
│   compressed UInt32: argumentCount  (positional args)   │
│   compressed UInt32: fieldCount     (= named arg fields)│
│   compressed UInt32: propertyCount  (= named arg props) │
│   argumentCount × {EncodedTypeEnum, BlobValue}           │
│   fieldCount × {EncodedTypeEnum, BlobValue, namedArg}   │
│   propertyCount × {EncodedTypeEnum, BlobValue, namedArg}│
└─────────────────────────────────────────────────────────┘
```

Reader 內部維護兩個游標：`ctorBuffer`（指向下一個 ctor index）、`dataBuffer`（指向下一筆 attribute data）。每呼叫 `GetStringCustomAttributeData()` / `VisitCustomAttributeData()` 一次都會推進兩者。

### 7.2 EncodedTypeEnum 讀取

[`Il2CppExecutor.ReadEncodedTypeEnum`](../Il2CppDumper/Utils/Il2CppExecutor.cs#L464-L476)：

```csharp
type = (Il2CppTypeEnum)ReadByte();
if (type == IL2CPP_TYPE_ENUM):
    enumTypeIndex = ReadCompressedInt32();
    enumType = il2Cpp.types[enumTypeIndex];
    typeDef = GetTypeDefinitionFromIl2CppType(enumType);
    type = il2Cpp.types[typeDef.elementTypeIndex].type;   // enum 的底層型別
return type;
```

也就是說：blob 內 enum 引數會先寫 `ENUM` byte + 該 enum 的 type index，再寫底層整數值。Decoder 自動把 type 轉成 underlying primitive 型別。

### 7.3 Named Argument 編碼

[`ReadCustomAttributeNamedArgumentClassAndIndex`](../Il2CppDumper/Utils/CustomAttributeDataReader.cs#L153-L166)：

```csharp
memberIndex = ReadCompressedInt32();
if (memberIndex >= 0):
    return (typeDef, memberIndex);                     // 自家 type
else:
    memberIndex = -(memberIndex + 1);                  // 反向編碼
    typeIndex = ReadCompressedUInt32();
    declaringClass = metadata.typeDefs[typeIndex];
    return (declaringClass, memberIndex);              // 引用父類 / 別 type 的 field/property
```

> 編碼技巧：負 index 表「跨 type 的 field/property」，需要再讀一個 typeIndex 才能定位。正 index 直接指向當前 typeDef 的 `fieldStart` / `propertyStart` 偏移。

### 7.4 BlobValue 容器

[`BlobValue`](../Il2CppDumper/Utils/BlobValue.cs)：

```csharp
public class BlobValue {
    public object Value;            // 實際值（string / int / bool / BlobValue[] / Il2CppType / ...）
    public Il2CppTypeEnum il2CppTypeEnum;
    public Il2CppType EnumType;     // 如果原本是 enum，這裡指向 enum type；Value 是底層 int
}
```

### 7.5 Attribute 字串格式化

[`GetStringCustomAttributeData`](../Il2CppDumper/Utils/CustomAttributeDataReader.cs#L24-L69) 把整個 attribute 印成 `[Foo("bar", X = 1, Y = typeof(int))]`：

```
typeName = "Foo" (去掉結尾 "Attribute")
for arg in ctorArgs:    印成「值」     "bar"
for field in fields:    印成「name = 值」 X = 1
for prop in props:      印成「name = 值」 Y = typeof(int)
```

[`AttributeDataToString`](../Il2CppDumper/Utils/CustomAttributeDataReader.cs#L71-L96) 對每個 BlobValue 的格式化規則：

| TypeEnum | 輸出格式 |
|----------|---------|
| `IL2CPP_TYPE_STRING` | `"..."`（雙引號） |
| `IL2CPP_TYPE_SZARRAY` | `new[] { v1, v2, ... }` |
| `IL2CPP_TYPE_IL2CPP_TYPE_INDEX` | `typeof(Foo)` |
| 其他 | `Value.ToString()` |
| `null` | `"null"` |

⚠️ 註：原始碼 `AttributeDataToString` 有 `//TODO enum` 註解 — 即使讀到 enum，目前還沒做「印成 `EnumName.Member`」的反查，只印底層數值。

### 7.6 程式化 visitor 模式

`VisitCustomAttributeData()`（[CustomAttributeDataReader.cs:98-140](../Il2CppDumper/Utils/CustomAttributeDataReader.cs#L98-L140)）回傳 [`CustomAttributeReaderVisitor`](../Il2CppDumper/Utils/CustomAttributeReaderVisitor.cs)：

```csharp
public class CustomAttributeReaderVisitor {
    public int CtorIndex;
    public AttributeArgument[] Arguments;    // positional
    public AttributeArgument[] Fields;       // named (field)
    public AttributeArgument[] Properties;   // named (property)
}

public class AttributeArgument {
    public BlobValue Value;
    public int Index;                        // 對 Arguments: 0-based; 對 Fields/Properties: declaring.fieldStart + offset
}
```

用途：若不要文字輸出而要結構化處理 attribute（如 IDE 工具），用 visitor 比 string parser 安全。當前專案內 `dump.cs` 走 string；DummyDll 暫不還原 v29+ attribute 引數（只透過 `CreateCustomAttribute` 走舊版 path）。

---

## 8. 執行檔格式結構體（*Class.cs）

各 ExecutableFormat loader 的 POCO 結構，全部用 `[Version]` + `[ArrayLength]` 標記，由 `BinaryStream.ReadClass` 反射讀取。

### 8.1 PE / PEClass.cs

[`PEClass.cs`](../Il2CppDumper/ExecutableFormats/PEClass.cs)：

| Struct | 用途 | 重點欄位 |
|--------|------|----------|
| `DosHeader` | DOS 標頭（`MZ` 開頭，60 bytes） | `Magic=0x5A4D`、`Lfanew` 指向 PE header |
| `FileHeader` | PE 主標頭 | `Machine`（0x14c=x86, 0x8664=x64, 0xAA64=ARM64）、`NumberOfSections`、`SizeOfOptionalHeader` |
| `OptionalHeader` | 32-bit OptionalHeader | `Magic=0x10b`、`ImageBase` (uint)、`BaseOfData` |
| `OptionalHeader64` | 64-bit OptionalHeader | `Magic=0x20b`、`ImageBase` (ulong)、**沒有 `BaseOfData`** |
| `SectionHeader` | section table 元素 | `Name[8]`、`VirtualSize/Address`、`SizeOfRawData/PointerToRawData`、`Characteristics`（位元欄位） |
| `SectionCharacteristics` (Flags enum) | section flag 常數 | `MEM_EXECUTE=0x20000000`、`MEM_READ=0x40000000`、`MEM_WRITE=0x80000000` |

⚠️ `DataDirectory[]` 在原始碼註解掉（[PEClass.cs:73,110-114](../Il2CppDumper/ExecutableFormats/PEClass.cs#L73)），目前不解析 import/export 表。

### 8.2 ELF / ElfClass.cs

[`ElfClass.cs`](../Il2CppDumper/ExecutableFormats/ElfClass.cs)：32-bit 與 64-bit 並存，欄位大小差異：

| Struct 對 | 32-bit 與 64-bit 主要差異 |
|----------|--------------------------|
| `Elf32_Ehdr` vs `Elf64_Ehdr` | `e_entry/phoff/shoff` 從 `uint` → `ulong` |
| `Elf32_Phdr` vs `Elf64_Phdr` | 32-bit `p_flags` 在末尾、64-bit `p_flags` 在 `p_type` 後第二格（layout 順序不同） |
| `Elf32_Shdr` vs `Elf64_Shdr` | 所有 size/offset 欄位升級為 ulong |
| `Elf32_Sym` vs `Elf64_Sym` | 32-bit: `st_name, st_value, st_size, st_info, st_other, st_shndx`；64-bit 把 `st_info/st_other/st_shndx` 移到中間 |
| `Elf32_Dyn` vs `Elf64_Dyn` | 32-bit `d_tag=int, d_un=uint`；64-bit `d_tag=long, d_un=ulong` |
| `Elf32_Rel` vs `Elf64_Rela` | 32-bit 沒有 `r_addend`、用 `DT_REL`；64-bit 有 `r_addend`、用 `DT_RELA` |

`ElfConstants` 常數：
- e_machine：`EM_386=3`、`EM_ARM=40`、`EM_X86_64=62`、`EM_AARCH64=183`
- p_type：`PT_LOAD=1`、`PT_DYNAMIC=2`
- p_flags：`PF_X=1`
- d_tag：`DT_PLTGOT=3, DT_HASH=4, DT_STRTAB=5, DT_SYMTAB=6, DT_RELA=7, DT_RELASZ=8, DT_INIT=12, DT_FINI=13, DT_REL=17, DT_RELSZ=18, DT_JMPREL=23, DT_INIT_ARRAY=25, DT_FINI_ARRAY=26, DT_GNU_HASH=0x6ffffef5`
- sh_type：`SHT_LOUSER=0x80000000`
- relocs：`R_ARM_ABS32=2, R_386_32=1, R_AARCH64_ABS64=257, R_AARCH64_RELATIVE=1027, R_X86_64_64=1, R_X86_64_RELATIVE=8`

### 8.3 Mach-O / MachoClass.cs

[`MachoClass.cs`](../Il2CppDumper/ExecutableFormats/MachoClass.cs)（只 27 行）：

```csharp
class MachoSection      { string sectname; uint addr;  uint size;  uint offset;  uint flags; }
class MachoSection64Bit { string sectname; ulong addr; ulong size; ulong offset; uint flags; }
class Fat               { uint offset; uint size; uint magic; }   // FAT slice descriptor
```

`sectname` 經由 `Encoding.UTF8.GetString(ReadBytes(16)).TrimEnd('\0')` 從 16-byte fixed buffer 抽取。

### 8.4 NSO / NSOClass.cs

[`NSOClass.cs`](../Il2CppDumper/ExecutableFormats/NSOClass.cs)：Switch NSO 格式三層結構：

```csharp
class NSOHeader {
    uint Magic, Version, Reserved, Flags;       // Flags bit 0/1/2 = text/rodata/data 是否壓縮
    NSOSegmentHeader TextSegment;
    uint ModuleOffset;
    NSOSegmentHeader RoDataSegment;
    uint ModuleFileSize;
    NSOSegmentHeader DataSegment;
    uint BssSize;
    byte[] DigestBuildID, TextHash, RoDataHash, DataHash;
    uint TextCompressedSize, RoDataCompressedSize, DataCompressedSize;
    byte[] Padding;
    NSORelativeExtent APIInfo, DynStr, DynSym;
    NSOSegmentHeader BssSegment;                 // 不在檔案 header 內，由 .text 末尾的 module 結構解出
}

class NSOSegmentHeader   { uint FileOffset, MemoryOffset, DecompressedSize; }
class NSORelativeExtent  { uint RegionRoDataOffset, RegionSize; }
```

### 8.5 WebAssembly / WebAssemblyClass.cs

[`WebAssemblyClass.cs`](../Il2CppDumper/ExecutableFormats/WebAssemblyClass.cs)（9 行）：

```csharp
class DataSection {
    uint Index;
    uint Offset;
    byte[] Data;
}
```

WASM data section 內每個 entry 描述「Memory[Offset..Offset+Data.Length] = Data」，`WebAssembly.CreateMemory` 把它們攤平到一個 `byte[Length]` flat buffer。

## 9. 設計小教訓

1. **POCO + Attribute = 自動讀檔**：所有 IL2CPP runtime struct 都直接用 C# class 描述，靠 `[Version]` 控制欄位有無、靠 reflection 直接讀。新增 struct 變更只要編輯 [Il2Cpp/MetadataClass.cs](../Il2CppDumper/Il2Cpp/MetadataClass.cs) / [Il2Cpp/Il2CppClass.cs](../Il2CppDumper/Il2Cpp/Il2CppClass.cs) 對應欄位即可。
2. **`Is32Bit` 由 loader 設定**：[`PE` 看 magic](../Il2CppDumper/ExecutableFormats/PE.cs#L28-L33)、`WebAssembly` 強制 `true`、Macho 看 magic、ELF 看 byte[4]。一旦設好，`ReadIntPtr` / `ReadUIntPtr` 會自動切換尺寸。
3. **`Version` 是 `double`**：因為要表示 24.1、24.2、27.1、29.1 等小數版號。比較時用 `>= 24.2`，不要寫成 `== 24`（會漏掉變體）。
