# Version Compatibility — 版本相容矩陣

> IL2CPP metadata version 與 Unity 版本的對應、`[Version(Min, Max)]` 在程式內的分佈、以及版本切換的內部邏輯。

---

## 1. 支援範圍

[Metadata.cs:55-58](../Il2CppDumper/Il2Cpp/Metadata.cs#L55-L58)：

```csharp
if (version < 16 || version > 31)
    throw new NotSupportedException($"ERROR: Metadata file supplied is not a supported version[{version}].");
```

對應 Unity 版本（[README.md:13](../README.md#L13)）：**Unity 5.3 ~ 2022.2**。

---

## 2. 版本號的小數編碼

`Metadata.Version` 與 `Il2Cpp.Version` 都是 `double`，因為同一個整數版號（如 24）可能對應多個 minor 變體：

| double | 整數版 | Unity 對應 / 引入時機 | 主要差別 |
|--------|-------|---------------------|---------|
| `16` | 16 | Unity 5.3 ~ 5.4 | 起始版本 |
| `17` | 17 | Unity 5.5 | — |
| `18` | 18 | Unity 5.6 | — |
| `19` | 19 | Unity 2017.1 | 加入 metadataUsage 機制、fieldRefs、referencedAssemblies |
| `20` | 20 | Unity 2017.2 ~ 2017.3 | — |
| `21` | 21 | Unity 2017.4 ~ 2018.1 | 加入 attributesInfo、ccwMarshalingFunctions |
| `22` | 22 | Unity 2018.2 | 加入 reversePInvokeWrappers、unresolvedVirtualCallPointers |
| `23` | 23 | Unity 2018.3 ~ 2018.4 | 加入 interopData、windowsRuntimeTypeNames |
| `24` | 24 | Unity 2019.1 | 24.1 之前 |
| `24.1` | 24 | Unity 2019.2 | `imageDef.token != 1`（細分） |
| `24.2` | 24 | Unity 2019.3 | 引入 `codeGenModules`（per-image method 表）、`metadataUsageLists`/`metadataUsagePairs` 改新編碼 |
| `24.3` | 24 | Unity 2019.4.0~? | `interopDataCount == 0` 變體 |
| `24.4` | 24 | Unity 2020.1 ~ 2020.2 | `assembliesSize/68 < imageDefs.Length` 變體 |
| `24.5` | 24 | Unity 2020.2 ~ 2020.3 | `reversePInvokeWrapperCount > limit` 變體；加入 genericAdjustorThunks |
| `27` | 27 | Unity 2021.1 ~ 2021.2 | bit-encoded indices 改 `index >> 1`；type lookup 走 `typeHandle - ImageBase` |
| `27.1` | 27 | Unity 2021.2 | `invokerPointersCount > limit` 變體 |
| `27.2` | 27 | Unity 2021.3 | `Il2CppType.bits` 重切（27.2 的 bit 24-28 改 5 bit、加 `valuetype` bit） |
| `29` | 29 | Unity 2022.1 | CustomAttribute 完全改寫成 blob；attributeDataRange |
| `29.1` | 29 | Unity 2022.2 | `genericMethodPointersCount > limit` 變體；`unresolvedVirtualCallCount` 拆成 instance + static |
| `31` | 31 | Unity 2022.2 後續 | 加入 `returnParameterToken`；偵測時可能回退為 29 |

> 註：Unity 對應是社群整理的近似，官方沒有公開對照表。`24.1` 等變體是 Il2CppDumper 自己定義的小數版號，不在 Unity 官方文件內。

---

## 3. `[Version]` 在程式內的角色

```csharp
[AttributeUsage(AttributeTargets.Field, AllowMultiple = true)]
class VersionAttribute : Attribute {
    public double Min { get; set; } = 0;
    public double Max { get; set; } = 99;
}
```

只用在 POCO 欄位上，被 [`BinaryStream.ReadClass`](../Il2CppDumper/IO/BinaryStream.cs#L115-L150) 解讀：

```csharp
if Attribute.IsDefined(field, typeof(VersionAttribute)):
    foreach attr in field.GetCustomAttributes<VersionAttribute>():
        if Version >= attr.Min && Version <= attr.Max:
            讀這個欄位 → break
        else:
            繼續下個 attr
    都沒中 → 跳過該欄位
```

### 3.1 多重 `[Version]` 範例

`Il2CppCodeRegistration.genericAdjustorThunks`（[Il2CppClass.cs:33-35](../Il2CppDumper/Il2Cpp/Il2CppClass.cs#L33-L35)）：

```csharp
[Version(Min = 24.5, Max = 24.5)]
[Version(Min = 27.1)]
public ulong genericAdjustorThunks;
```

意思：「`24.5` 有 → 中間 25/26/27 沒有 → `27.1+` 又有」。`Il2CppCodeGenModule.adjustorThunkCount/adjustorThunks` / `Il2CppGenericMethodIndices.adjustorThunk` 也用同樣模式。

### 3.2 `[Version(Max = X)]` = 「X 之前 + X」

注意 `Max` 是 inclusive：`[Version(Max = 24.1)]` 包含 24.0 與 24.1。

### 3.3 完整 `[Version]` 分佈速查

| 結構 | 欄位 | 範圍 | 說明 |
|------|------|------|------|
| `Il2CppGlobalMetadataHeader` | `rgctxEntriesOffset/Count` | `Max=24.1` | v24.2 開始 RGCTX 改 per-module |
| | `metadataUsageLists/Pairs Offset/Count` | `Min=19, Max=24.5` | v27+ 改編碼 |
| | `fieldRefsOffset/Size` | `Min=19` | 加入 fieldRefs |
| | `referencedAssembliesOffset/Size` | `Min=20` | — |
| | `attributesInfoOffset` 系列 | `Min=21, Max=27.2` | v29 完全廢除，改 attributeDataRange |
| | `attributeData*` 系列 | `Min=29` | 新版 CustomAttribute |
| | `unresolvedVirtualCall*` | `Min=22` | — |
| | `windowsRuntimeTypeNames*` | `Min=23` | — |
| | `windowsRuntimeStrings*` | `Min=27` | — |
| | `exportedTypeDefinitions*` | `Min=24` | — |
| `Il2CppAssemblyDefinition` | `token` | `Min=24.1` | — |
| | `customAttributeIndex` | `Max=24` | v24.1 之後改 imageDef.customAttribute* |
| | `referencedAssembly*` | `Min=20` | — |
| `Il2CppAssemblyNameDefinition` | `hashValueIndex` | `Max=24.3` | v24.4 移除 |
| `Il2CppImageDefinition` | `exportedType*` | `Min=24` | — |
| | `token` | `Min=19` | — |
| | `customAttribute*` | `Min=24.1` | — |
| `Il2CppTypeDefinition` | `customAttributeIndex` | `Max=24` | — |
| | `byrefTypeIndex` | `Max=24.5` | v27 移除 |
| | `rgctx*` | `Max=24.1` | — |
| | `delegateWrapper*`、`marshalingFunctionsIndex` | `Max=22` | v23 後改 interopData |
| | `ccwFunctionIndex`、`guidIndex` | `Min=21, Max=22` | 只活兩個版本 |
| | `token` | `Min=19` | — |
| `Il2CppMethodDefinition` | `returnParameterToken` | `Min=31` | v31 新增 |
| | `customAttributeIndex` | `Max=24` | — |
| | `methodIndex`、`invokerIndex`、`delegateWrapperIndex`、`rgctx*` | `Max=24.1` | v24.2 改 per-image |
| `Il2CppCodeRegistration` | `methodPointers*` | `Max=24.1` | — |
| | `delegateWrappersFromNativeToManaged*` | `Max=21` | — |
| | `reversePInvokeWrapper*` | `Min=22` | — |
| | `delegateWrappers*`、`marshalingFunctions*` | `Max=22` | — |
| | `ccwMarshalingFunctions*` | `Min=21, Max=22` | — |
| | `genericAdjustorThunks` | `Min=24.5,Max=24.5` + `Min=27.1` | 兩段式 |
| | `customAttribute*` | `Max=24.5` | v27+ per-module |
| | `guid*` | `Min=21, Max=22` | — |
| | `unresolvedVirtualCall*` | `Min=22` | — |
| | `unresolvedInstance/StaticCallPointers` | `Min=29.1` | 取代 unresolvedVirtualCall |
| | `interopData*` | `Min=23` | — |
| | `windowsRuntimeFactory*` | `Min=24.3` | — |
| | `codeGenModules*` | `Min=24.2` | per-image 切換的核心 |
| `Il2CppMetadataRegistration` | `methodReferences*` | `Max=16` | v17 移除 |
| | `metadataUsages*` | `Min=19` | — |
| `Il2CppGenericClass` | `typeDefinitionIndex` | `Max=24.5` | — |
| | `type` | `Min=27` | 改用 `Il2CppType` 指標 |
| `Il2CppGenericMethodIndices` | `adjustorThunk` | `Min=24.5,Max=24.5` + `Min=27.1` | — |
| `Il2CppCodeGenModule` | `adjustorThunkCount/adjustorThunks` | `Min=24.5,Max=24.5` + `Min=27.1` | — |
| | `customAttributeCacheGenerator` | `Min=27, Max=27.2` | v29 廢除 |
| | `moduleInitializer`、`staticConstructorTypeIndices`、`metadataRegistration`、`codeRegistaration` | `Min=27` | — |
| `Il2CppRGCTXDefinition` | `type_pre29` + `data` | `Max=27.1` | — |
| | `type_post29` + `_data` | `Min=27.2` / `Min=29` | bit 編碼擴張 |
| `Il2CppCustomAttributeTypeRange` | `token` | `Min=24.1` | — |

---

## 4. 版本偵測流程

### 4.1 `Metadata` 建構子（[Metadata.cs:60-90](../Il2CppDumper/Il2Cpp/Metadata.cs#L60-L90)）

```
讀 header (假設版本是 metadata sanity 後讀到的整數版本)
if version == 24:
    if header.stringLiteralOffset == 264:
        Version = 24.2     ← 偵測 24.2 變體
        重讀 header（24.2 header layout 不同）
    else:
        讀 imageDefs
        if imageDefs.Any(x => x.token != 1):
            Version = 24.1 ← imageDef 內 token 欄位才有的特徵
        else:
            Version 維持 24

讀 imageDefs（如果剛剛沒讀）

if Version == 24.2:
    if header.assembliesSize / 68 < imageDefs.Length:
        Version = 24.4  ← 24.4 的 assembly 結構大小不同

if Version == 24.1:
    if header.assembliesSize / 64 == imageDefs.Length:
        v241Plus = true
        Version = 24.4   ← 暫時切 24.4 讀 assemblies
        讀 assemblyDefs
        Version = 24.1   ← 讀完切回
```

⚠️ 「先切版本、讀資料、切回」是因為 `assemblyDefs` 的欄位被 `[Version]` 控制，v24.1 與 v24.4 的 struct size 不同。

### 4.2 `Il2Cpp.AutoPlusInit`（[Il2Cpp.cs:51-118](../Il2CppDumper/Il2Cpp/Il2Cpp.cs#L51-L118)）

讀完 `pCodeRegistration` 後，根據欄位值修正版本：

| 觸發 | 動作 |
|------|------|
| `Version >= 24.2` 才開始檢查 | — |
| `Version == 31 && genericMethodPointersCount > limit` | `codeRegistration -= PointerSize * 2`（v31 變體） |
| `Version == 31 && <= limit` | `Version = 29`（這份其實是 v29 的 binary） |
| `Version == 29 && genericMethodPointersCount > limit` | `Version = 29.1; codeRegistration -= PointerSize * 2` |
| `Version == 27 && reversePInvokeWrapperCount > limit` | `Version = 27.1; codeRegistration -= PointerSize` |
| `Version == 24.4` | `codeRegistration -= PointerSize * 2`（無條件） |
| `Version == 24.4 && reversePInvokeWrapperCount > limit` | `Version = 24.5; codeRegistration -= PointerSize` |
| `Version == 24.2 && interopDataCount == 0` | `Version = 24.3; codeRegistration -= PointerSize * 2` |

### 4.3 `Il2Cpp.Init` 二次修正（[Il2Cpp.cs:120-159](../Il2CppDumper/Il2Cpp/Il2Cpp.cs#L120-L159)）

讀完 `pCodeRegistration` 後再檢查 `invokerPointersCount`：

| 觸發 | 動作 |
|------|------|
| `Version == 27 && invokerPointersCount > limit` | `Version = 27.1; 重讀 pCodeRegistration` |
| `Version == 27.1` 且第一個 module 的 RGCTX 都 > limit | `Version = 27.2` |
| `Version == 24.4 && invokerPointersCount > limit` | `Version = 24.5; 重讀` |
| `Version == 24.2 && codeGenModules == 0` | `Version = 24.3; 重讀` |

> `limit` = `0x35000` (WebAssembly) / `0x50000` (其他)。是經驗值，不是規格保證。

---

## 5. 重要版本切換點

### 5.1 v19：metadataUsage 機制誕生

v16~18 的 IL2CPP 直接把 string literal / type ref 編在 IL 中（透過 globally encoded 索引）；v19 開始把所有 metadata reference 集中到 `metadataUsageLists` + `metadataUsagePairs`，每個 method 透過 `destinationIndex` 引用一個全域 slot。

對 dump 的影響：v19 前的 dump.cs 在 string default value 上可能有差異。

### 5.2 v24.2：per-image method 表

最劇烈的一次變動。`Il2CppCodeRegistration.methodPointers` 全域陣列被廢除，改成每個 image 一個 `Il2CppCodeGenModule`，內含該 image 的 `methodPointers[]`，索引方式從 `methodDef.methodIndex` 改為 `methodDef.token & 0x00FFFFFF - 1`。

對 [`Il2Cpp.GetMethodPointer`](../Il2CppDumper/Il2Cpp/Il2Cpp.cs#L323-L340) 也分兩條路徑。

### 5.3 v27：bit 編碼與 type lookup 變更

- `metadataUsagePair.encodedSourceIndex` 改 `(idx & 0x1FFFFFFE) >> 1`（[Metadata.cs:247-254](../Il2CppDumper/Il2Cpp/Metadata.cs#L247-L254)）
- IsDumped 時，type lookup 從 `klassIndex` 改成 `typeHandle - ImageBase - typeDefinitionsOffset` 算 index（[Il2CppExecutor.cs:293-305](../Il2CppDumper/Utils/Il2CppExecutor.cs#L293-L305)）
- `Il2CppGenericClass.typeDefinitionIndex` 改 `type`（指向 `Il2CppType*`）

### 5.4 v27.2：`Il2CppType.bits` 重新切

| 欄位 | v < 27.2 | v ≥ 27.2 |
|------|----------|----------|
| `num_mods` | 6 bit (24-29) | 5 bit (24-28) |
| `byref` | 30 | 29 |
| `pinned` | 31 | 30 |
| `valuetype` | （無） | 31 |

`Il2CppType.Init(version)` 在這裡分岔（[Il2CppClass.cs:151-169](../Il2CppDumper/Il2Cpp/Il2CppClass.cs#L151-L169)）。

### 5.5 v29：CustomAttribute 完全改寫

舊版（v21~27.2）：`customAttributeGenerators` 指標表 + `attributeTypeRanges`，輸出只能列 attribute 型別名。

v29+：完整 blob 編碼，每個 attribute 含 ctor args + named args + enum values。Il2CppDumper 用 [`CustomAttributeDataReader`](../Il2CppDumper/Utils/CustomAttributeDataReader.cs) 解析，dump.cs 可以印出完整 `[Foo("bar", x = 42)]`。

### 5.6 v29.1：unresolvedVirtualCall 拆分

| v29 | v29.1+ |
|-----|--------|
| `unresolvedVirtualCallCount / Pointers` | 改名為 `unresolvedIndirectCallCount`（同欄位） |
| — | 新增 `unresolvedInstanceCallPointers` |
| — | 新增 `unresolvedStaticCallPointers` |

### 5.7 v31：方法回傳參數 token

`Il2CppMethodDefinition` 增加 `returnParameterToken`（[MetadataClass.cs:240-241](../Il2CppDumper/Il2Cpp/MetadataClass.cs#L240-L241)）。

---

## 6. 新增版本支援的步驟

當 Unity 出新版且現有 Il2CppDumper 不支援時：

1. **確認 metadata version**：用 hex editor 看 `global-metadata.dat` offset 4（version 整數）
2. **放寬 `Metadata.cs:55-58` 的上限**：如果是新整數版號，先讓它能通過 sanity check
3. **判定哪些 struct 改了**：
   - 用 `Il2CppDumper` 跑，看哪一步爆掉
   - 對照 Unity 對應版本的 `il2cpp-metadata.h`（Unity Hub 安裝目錄下 `Editor/Data/il2cpp/libil2cpp/utils`）
4. **加 `[Version(Min=N)]` 給新欄位、`Max=N-1` 給移除的欄位**
5. **若有變體偵測需求**（同 metadata version 但 layout 不同），在 `Metadata.cs` 建構子加偵測，並引入小數版號（如 `31.1`）
6. **可能要改 `Il2Cpp.AutoPlusInit` / `Init`**：因 pCodeRegistration 欄位變動需重新對齊 offset
7. **跑 dump.cs 與 IL2CPP runtime 比對**：確認方法 RVA、欄位 offset 正確

---

## 7. 常見錯誤與版本相關

| 症狀 | 可能原因 |
|------|---------|
| dump.cs 全是亂碼型別名 | `Version` 判定錯（如 24.2 vs 24.3） |
| 方法 RVA 都偏移固定值 | `codeRegistration` 對的位置但 `Version` 內部減錯 PointerSize |
| 某些 type/method 抓不到（index 越界） | metadata version 跟 il2cpp.dll runtime version 不一致 |
| `Il2CppType.byref` 全是 1 或 0 | v27.2 與 v27 的 bit 拆解搞錯 |
| CustomAttribute 都空白 | v29+ 但 `CustomAttributeDataReader` 解析失敗 |
| `pCodeRegistration.codeGenModules == 0` 卻是 v24.2 | 實際是 v24.3，`AutoPlusInit` 沒抓到 |

排查時優先檢查 `Console.WriteLine($"Change il2cpp version to: {Version}")` 訊息序列。
