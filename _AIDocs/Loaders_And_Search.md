# Loaders & Search — 格式 Loader 與 Registration 偵測

> 本檔聚焦在「如何把原生執行檔讀進來」+「如何在裡面找到 `CodeRegistration` / `MetadataRegistration` 兩個錨點」。

---

## 1. Loader 對照表

| 格式 | 子類 | Is32Bit | 主要解析 | dump 偵測 |
|------|------|---------|----------|-----------|
| PE | [`PE`](../Il2CppDumper/ExecutableFormats/PE.cs) | 看 OptionalHeader magic（`0x10b`=32, `0x20b`=64） | DOS + PE header + SectionHeader[] | `ImageBase ≠ 預設值`（32: `0x10000000`、64: `0x180000000`） |
| ELF32 | [`Elf`](../Il2CppDumper/ExecutableFormats/Elf.cs) | true | Elf32_Ehdr/Phdr/Dyn/Sym/Shdr | `CheckSection()`：找不到 `.text` section name |
| ELF64 | [`Elf64`](../Il2CppDumper/ExecutableFormats/Elf64.cs) | false | Elf64_Ehdr/Phdr/Dyn/Sym/Shdr | 同上 |
| Mach-O 32 | [`Macho`](../Il2CppDumper/ExecutableFormats/Macho.cs) | true | LC_SEGMENT load commands | `CheckDump() => false`（不偵測 dump） |
| Mach-O 64 | [`Macho64`](../Il2CppDumper/ExecutableFormats/Macho64.cs) | false | LC_SEGMENT_64 load commands + LC_ENCRYPTION_INFO_64 | `CheckDump() => false` |
| Mach-O FAT | [`MachoFat`](../Il2CppDumper/ExecutableFormats/MachoFat.cs) | — | 不是 `Il2Cpp`，只是 dispatcher：列出所有 slice 讓使用者選 | — |
| NSO（Switch） | [`NSO`](../Il2CppDumper/ExecutableFormats/NSO.cs) | false | NSO header + 3 segment（text/rodata/data）+ LZ4 解壓 | `CheckDump() => false` |
| WebAssembly | [`WebAssembly`](../Il2CppDumper/ExecutableFormats/WebAssembly.cs) → [`WebAssemblyMemory`](../Il2CppDumper/ExecutableFormats/WebAssemblyMemory.cs) | true | 解 data sections → 建一個 flat memory image | `CheckDump() => false` |

### 1.1 dispatcher：[Program.cs:130-180](../Il2CppDumper/Program.cs#L130-L180)

```csharp
switch (il2cppMagic) {
    case 0x6D736100: var web = new WebAssembly(stream); il2Cpp = web.CreateMemory();   break;
    case 0x304F534E: var nso = new NSO(stream);         il2Cpp = nso.UnCompress();     break;
    case 0x905A4D:                                       il2Cpp = new PE(stream);       break;
    case 0x464C457F:                                     il2Cpp = bytes[4] == 2 ? new Elf64(stream) : new Elf(stream); break;
    case 0xCAFEBABE: case 0xBEBAFECA:
        var fat = new MachoFat(stream);
        // 互動：使用者按 1/2/... 選 slice
        // 取出對應 slice bytes 後 goto 0xFEEDFACF / 0xFEEDFACE 兩個 case
    case 0xFEEDFACF: il2Cpp = new Macho64(stream); break;
    case 0xFEEDFACE: il2Cpp = new Macho(stream);   break;
    default: throw new NotSupportedException();
}
```

### 1.2 NSO 解壓特殊處理（[NSO.cs:237-323](../Il2CppDumper/ExecutableFormats/NSO.cs#L237-L323)）

NSO 三個 segment 各自可能 LZ4 壓縮（看 Flags bit 0/1/2）。`UnCompress()` 會：

1. 寫一個新的 NSO header（Flags = 0），修正三個 segment 的 FileOffset 變成解壓後的位置
2. 對每個 segment：壓縮的就 `Lz4DecoderStream` 解壓再寫；否則直接寫
3. 重新 `new NSO(unCompressedStream)` 再回到正常流程

`Lz4DecoderStream`（[IO/Lz4DecoderStream.cs](../Il2CppDumper/IO/Lz4DecoderStream.cs)）是純 C# LZ4 解碼器，無外部依賴。

### 1.3 WebAssembly 兩階段

`WebAssembly` 本身**不繼承** `Il2Cpp`，只負責解 wasm 的 data section（11 號）。每個 data section 有 i32.const offset + 內容 bytes。`CreateMemory()` 把所有 data 攤平到一個 `Length` 大小的 buffer 裡，再 `new WebAssemblyMemory`，後者才是 `Il2Cpp` 子類。

`WebAssemblyMemory` 的特殊點：
- `MapVATR` / `MapRTVA` 都是 identity（位址 = offset）
- `GetSectionHelper`（[WebAssemblyMemory.cs:43-71](../Il2CppDumper/ExecutableFormats/WebAssemblyMemory.cs#L43-L71)）裡的 exec/bss 是 hack：`offsetEnd = methodCount`、`addressEnd = long.MaxValue`，因為 wasm 沒有真實的「可執行 section」概念

---

## 2. 三段式偵測：`PlusSearch` → `Search` → `SymbolSearch`

[Program.cs:208-237](../Il2CppDumper/Program.cs#L208-L237)

```csharp
var flag = il2Cpp.PlusSearch(methodCount, typeDefinitionsCount, imageDefsLen);

// Windows PE 額外備援：用 LoadLibrary 重新載入
if (RuntimeInformation.IsOSPlatform(OSPlatform.Windows))
    if (!flag && il2Cpp is PE) {
        Console.WriteLine("Use custom PE loader");
        il2Cpp = PELoader.Load(il2cppPath);
        il2Cpp.SetProperties(version, metadataUsagesCount);
        flag = il2Cpp.PlusSearch(...);
    }

if (!flag) flag = il2Cpp.Search();
if (!flag) flag = il2Cpp.SymbolSearch();

if (!flag) {
    // 手動：使用者輸入兩個位址
    var codeRegistration = Convert.ToUInt64(Console.ReadLine(), 16);
    var metadataRegistration = Convert.ToUInt64(Console.ReadLine(), 16);
    il2Cpp.Init(codeRegistration, metadataRegistration);
}
```

各 loader 的支援矩陣：

| Loader | `PlusSearch` | `Search` | `SymbolSearch` |
|--------|:------------:|:--------:|:--------------:|
| PE | ✅ | ❌ return false | ❌ return false |
| Elf | ✅ | ✅（ARM 指令樣式） | ✅（dynsym） |
| Elf64 | ✅ | ❌ return false | ✅（dynsym） |
| Macho | ✅ | ✅（ARM mod_init_func） | ❌ |
| Macho64 | ✅ | ✅（ARM64 mod_init_func） | ❌ |
| NSO | ✅ | ❌ | ❌ |
| WebAssemblyMemory | ✅ | ❌ | ❌ |

---

## 3. `PlusSearch` 深入解析

實作在 [`SectionHelper`](../Il2CppDumper/Utils/SectionHelper.cs)。每個 loader 的 `PlusSearch` 都長一樣（[Elf64.cs:92-98](../Il2CppDumper/ExecutableFormats/Elf64.cs#L92-L98) / [PE.cs:83-89](../Il2CppDumper/ExecutableFormats/PE.cs#L83-L89)）：

```csharp
var sectionHelper = GetSectionHelper(methodCount, typeDefinitionsCount, imageCount);
var codeRegistration = sectionHelper.FindCodeRegistration();
var metadataRegistration = sectionHelper.FindMetadataRegistration();
return AutoPlusInit(codeRegistration, metadataRegistration);
```

### 3.1 SectionHelper 的三組區段

`SectionHelper` 持有 `exec` / `data` / `bss` 三個 `List<SearchSection>`（[SectionHelper.cs:9-21](../Il2CppDumper/Utils/SectionHelper.cs#L9-L21)）。每個 `SearchSection`（[Utils/SearchSection.cs:10-16](../Il2CppDumper/Utils/SearchSection.cs#L10-L16)）描述：

```csharp
public ulong offset;        // file offset start
public ulong offsetEnd;
public ulong address;       // virtual address start
public ulong addressEnd;
```

各 loader 的 `GetSectionHelper` 用該格式的 flag 分類 section：

| 格式 | exec 判定 | data 判定 | bss |
|------|----------|----------|-----|
| PE | `Characteristics == 0x60000020`（CODE+EXECUTE+READ） | `0x40000040 / 0xC0000040`（READ-only / READ+WRITE+INIT） | 同 data |
| ELF | `p_flags` 含 `PF_X`（1/3/5/7） | 含 `PF_W` 但不含 `PF_X`（2/4/6） | 同 data |
| Mach-O 64 | `flags == 0x80000400`（[Macho64.cs:260](../Il2CppDumper/ExecutableFormats/Macho64.cs#L260)） | `sectname ∈ {__const, __cstring, __data}` | `flags == 1` |
| NSO | `TextSegment` | `DataSegment + RoDataSegment`（兩個） | `BssSegment` |
| WASM | hack：`[0, methodCount)` | `[1024, Length)` | `[bssStart, MAX)` |

### 3.2 `FindCodeRegistration` — 新版（v24.2+，2019+）

[SectionHelper.cs:351-407](../Il2CppDumper/Utils/SectionHelper.cs#L351-L407)

核心特徵：所有 IL2CPP binary 都包含 `mscorlib.dll\0` 這 13 byte 字串。從這個字串往回找：

```
1. 在 data section 掃 "mscorlib.dll\0" 出現位置 → dllva（虛擬位址）
2. 找誰指向 dllva → refva（這是個 Il2CppImageDefinition.name 之類的位置）
3. 找誰指向 refva → refva2（這是 imageDefs 陣列首位的指標）
4. 對 i in [0..imageCount):
       找誰指向 refva2 - i × PointerSize → refva3
       這個 refva3 是 Il2CppCodeRegistration.codeGenModules
       refva3 - PointerSize × N 就是 Il2CppCodeRegistration 起點
          v29+: N = 14
          v27+: N = 13
```

> 註：v27+ 用 `for (i = imageCount - 1; i >= 0; i--)` 反向掃，且每個 candidate 都驗證「往前 1 個 pointer 是否等於 imageCount」（[SectionHelper.cs:374-391](../Il2CppDumper/Utils/SectionHelper.cs#L374-L391)）。v<27 簡單地 `return refva3 - PointerSize × 13`。

ELF 與其他格式的順序不同（[SectionHelper.cs:167-196](../Il2CppDumper/Utils/SectionHelper.cs#L167-L196)）：

```csharp
if (il2Cpp is ElfBase) {
    先試 exec section，沒中再試 data       // ELF 編碼器常把指標表放 exec section
    pointerInExec 旗標被設
} else {
    先試 data，沒中才試 exec
}
```

`pointerInExec` 旗標會影響 `FindMetadataRegistrationV21` 的最終驗證（[SectionHelper.cs:302-309](../Il2CppDumper/Utils/SectionHelper.cs#L302-L309)）：data 內的指標必須指到 exec / 還是 data。

### 3.3 `FindCodeRegistrationOld`（v < 24.2）

[SectionHelper.cs:211-243](../Il2CppDumper/Utils/SectionHelper.cs#L211-L243)

```
在 data section 掃，找到一個 ptr 滿足：
    *ptr == methodCount
    *(ptr+1) 指向一個 data section 內的位址
    從該位址讀 methodCount 個 pointer，全部都落在 exec section 內

成功就回 ptr 的虛擬位址
```

`methodCount` 是 `metadata.methodDefs.Count(x => x.methodIndex >= 0)`，因為 v24.1 之前 `methodPointers` 只包含實作方法。

### 3.4 `FindMetadataRegistration`

兩種變體：

| 條件 | 函式 | 邏輯 |
|------|------|------|
| v < 19 | return 0（IL2CPP v16-18 沒有 metadataUsages） | — |
| v ≥ 27 | [`FindMetadataRegistrationV21`](../Il2CppDumper/Utils/SectionHelper.cs#L281-L327) | 找連續兩個 `typeDefinitionsCount`（v27 起 `Il2CppMetadataRegistration.typesCount` 出現兩次），驗證 `pointer` 指向 `typeDefinitionsCount` 個指標都落在合理 section |
| 其他 | [`FindMetadataRegistrationOld`](../Il2CppDumper/Utils/SectionHelper.cs#L245-L279) | 找 `typeDefinitionsCount` + 跳 16 bytes + pointer，驗證指到 `metadataUsagesCount` 個 bss section pointer |

兩者都用 [`CheckPointerRangeDataRa`](../Il2CppDumper/Utils/SectionHelper.cs#L329) / [`Exec`](../Il2CppDumper/Utils/SectionHelper.cs#L334) / [`Data`](../Il2CppDumper/Utils/SectionHelper.cs#L339) / [`Bss`](../Il2CppDumper/Utils/SectionHelper.cs#L344) 驗證所有 pointer 都落在預期 section 內。

### 3.5 `AutoPlusInit` 的版本自動調整

[Il2Cpp.cs:51-118](../Il2CppDumper/Il2Cpp/Il2Cpp.cs#L51-L118)

`AutoPlusInit(codeRegistration, metadataRegistration)` 不只 `Init`，還會根據 `pCodeRegistration` 內欄位值「修正版本」。例子：

| 條件 | 動作 |
|------|------|
| `Version == 24.2 && pCodeRegistration.interopDataCount == 0` | `Version = 24.3; codeRegistration -= PointerSize * 2` |
| `Version == 24.4 && pCodeRegistration.reversePInvokeWrapperCount > limit` | `Version = 24.5; codeRegistration -= PointerSize` |
| `Version == 27 && pCodeRegistration.reversePInvokeWrapperCount > limit` | `Version = 27.1` |
| `Version == 29 && pCodeRegistration.genericMethodPointersCount > limit` | `Version = 29.1; codeRegistration -= PointerSize * 2` |
| `Version == 31 && pCodeRegistration.genericMethodPointersCount > limit` | `codeRegistration -= PointerSize * 2`（v31 變體偵測） |
| `Version == 31 && pCodeRegistration.genericMethodPointersCount <= limit` | `Version = 29`（這個 binary 其實是 v29 metadata 配 v31 runtime） |

⚠️ `limit` 取 `WebAssemblyMemory ? 0x35000 : 0x50000`，是「方法/指標數合理上限」的啟發式（[Il2Cpp.cs:55](../Il2CppDumper/Il2Cpp/Il2Cpp.cs#L55) 註 TODO）。

`Init` 進階修正（[Il2Cpp.cs:120-159](../Il2CppDumper/Il2Cpp/Il2Cpp.cs#L120-L159)）：再對 27 → 27.1 → 27.2、24.4 → 24.5 做 invoker count 與 rgctx 檢查；27.2 透過 `rgctxs[0].data.rgctxDataDummy > limit` 判定。

---

## 4. `Search` — ARM 指令啟發式（Macho only）

只有 `Macho`/`Macho64` 實作非 trivial 的 `Search`（[Macho64.cs:93-237](../Il2CppDumper/ExecutableFormats/Macho64.cs#L93-L237)）。

### 4.1 原理

Mach-O `__mod_init_func` section 內存所有 static initializer 的位址。IL2CPP runtime 的 `il2cpp::vm::MetadataLoader::LoadMetadataFile` 是其中一個，它的開頭一定是：

```
MOV X2, #0     (0x2 0x0 0x80 0xD2)   ← FeatureBytes1（ARM64）
MOV W3, #0     (0x3 0x0 0x80 0x52)   ← FeatureBytes2
ADR X1, sub
...
```

`Search()` 對每個 mod_init 函式：

1. 讀前 4 bytes 比對 FeatureBytes1
2. 接下來 4 bytes 比對 FeatureBytes2
3. 用 [`ArmUtils.DecodeAdr`](../Il2CppDumper/Utils/ArmUtils.cs) 解出 sub 位址
4. 進入 sub，前兩條 ADRP+ADD 算出 `codeRegistration`
5. 後兩條 ADRP+ADD 算出 `metadataRegistration`

### 4.2 三個版本變體

| Unity 版本 | 指令序順序 |
|-----------|----------|
| `Version < 23` | 兩種變體：FeatureBytes1 在前 / 在後（[Macho64.cs:99-153](../Il2CppDumper/ExecutableFormats/Macho64.cs#L99-L153)） |
| `Version == 23` | `ADRP + ADD + ADR + NOP + MOV X2,#0 + MOV W3,#0 + B` |
| `Version >= 24` | `ADRP + ADD + ADR + NOP + MOV W3,#0 + MOV X2,#0 + B`（順序顛倒） |

### 4.3 ARM 指令解碼公式

[`Utils/ArmUtils.cs`](../Il2CppDumper/Utils/ArmUtils.cs)：5 個函式涵蓋 IL2CPP 載入函式內常見指令。所有解碼都先把 byte[] 轉成 little-endian bit 字串（[`HexExtensions.HexToBin`](../Il2CppDumper/Extensions/HexExtensions.cs#L13-L21) 對每個 byte 取 8 bit binary 再從 byte[0] 開始 `Insert(0, ...)` 反向組成 →「bit 31 在最左」表示法）。

| 函式 | 用途 | 解碼公式 |
|------|------|----------|
| `DecodeMov(byte[8])` | ARM Thumb `MOVW` + `MOVT` 配對組 32-bit immediate | `low = inst[2] + (inst[3]&0x70)<<4 + (inst[1]&0x04)<<9 + (inst[0]&0x0f)<<12`；`high` 同公式對 inst[4-7]；結果 = `(high << 16) + low` |
| `DecodeAdr(pc, byte[4])` | ARM64 `ADR Xn, label` 解出 PC-relative 21-bit signed offset | bit 切 `(bin[8..27], bin[1..3])` → 21-bit signed → sign-extend 到 64 bit → `pc + offset` |
| `DecodeAdrp(pc, byte[4])` | ARM64 `ADRP Xn, label` 解出 PC-relative 21-bit << 12 page address | 同 `DecodeAdr` 但 offset 末尾補 12 個 `0`、`pc` 先 `& 0xFFFFFFFFFFFFF000` 對齊到 page |
| `DecodeAdd(byte[4])` | ARM64 `ADD Xn, Xn, #imm` 解 12-bit unsigned immediate | `imm = bin[10..21] (12 bit)`；若 `bin[9] == 1` 表 shift-by-12，所以 `imm <<= 12` |
| `IsAdr(byte[4])` | 是否為 `ADR` 指令 | `bin[0]=='0' && bin[3..7]=="10000"`（區分 ADR vs ADRP：bit 31 = 0/1） |

### 4.4 Macho64 用法範例

ARM64 IL2CPP 載入函式典型序列（v24+ 變體）：

```
ADRP X0, page         ← DecodeAdrp(pc, inst[0:4])
ADD  X0, X0, #imm     ← DecodeAdd(inst[4:8])     → codeRegistration = page + imm
ADR  X1, sub          ← DecodeAdr(pc+0x8, ...)
NOP
MOV  W3, #0           ← FeatureBytes2
MOV  X2, #0           ← FeatureBytes1
B    sub
```

進入 sub 後再讀 4 條，前兩條 ADRP+ADD 算 codeRegistration、後兩條算 metadataRegistration（[Macho64.cs:144-150](../Il2CppDumper/ExecutableFormats/Macho64.cs#L144-L150)）。

### 4.5 Macho 32-bit Search

[`Macho.cs`](../Il2CppDumper/ExecutableFormats/Macho.cs)（Mach-O 32 bit ARM Thumb）的對應特徵：

```
FeatureBytes1 = { 0x0, 0x22 }                    ← MOVS R2, #0
FeatureBytes2 = { 0x78, 0x44, 0x79, 0x44 }       ← ADD R0, PC + ADD R1, PC
```

在 `__mod_init_func` 內每個 fn pointer `a`（注意：Thumb 模式，實際位址 `i = a - 1` 拿掉 LSB）：

```
Position = MapVATR(i) + 4
讀 2 bytes 比對 FeatureBytes1
Position += 12
讀 4 bytes 比對 FeatureBytes2
讀 DecodeMov(MapVATR(i)+10 的 8 bytes) + i + 24 - 1 → subaddr  (Thumb 偏移修正)
進 subaddr：
   DecodeMov → ptr → MapVATR(ptr) → 讀 uint32 → metadataRegistration
   讀第二組 DecodeMov 的 8 bytes（拼 rsubaddr+8 與 rsubaddr+14 的兩段）+ subaddr + (22 或 26) → codeRegistration
```

`+22` (v<21) vs `+26` (v≥21) 是這版本唯一差異。

⚠️ `Macho.Init` 末尾要把 `methodPointers` / `customAttributeGenerators` 每個都 `- 1`（Thumb 模式 LSB 修正，[Macho.cs:70-75](../Il2CppDumper/ExecutableFormats/Macho.cs#L70-L75)）。Macho64 沒這需求。

### 4.6 ELF 32-bit Search（ARM only）

[`Elf.cs`](../Il2CppDumper/ExecutableFormats/Elf.cs#L96-L150)：

```
ARMFeatureBytes = "? 0x10 ? 0xE7 ? 0x00 ? 0xE0 ? 0x20 ? 0xE0"
                   = LDR R1, [X] + ADD R0, X, X + ADD R2, X, X
```

注意 pattern 用空格分隔 + `?` 通配符（給 [`BoyerMooreHorspool.Search(string)`](../Il2CppDumper/Extensions/BoyerMooreHorspool.cs#L59) 用）。

```
for each exec segment:
   找所有 match
   檢查 match+2 的 bit[3]=='1'（LDR 才進）→ resultList

只在 resultList.Count == 1 時繼續：
   v < 24 + ARM:
       result+0x14 → codeRegistration = *(result+0x14) + GOT
       result+0x18 → ptr = *(result+0x18) + GOT; metadataRegistration = *MapVATR(ptr)
   v >= 24 + ARM:
       result+0x14 → codeRegistration = *(result+0x14) + result + 0xC + ImageBase
       result+0x10 → ptr = *(result+0x10) + result + 0x8; metadataRegistration = *MapVATR(ptr + ImageBase)
```

> ⚠️ x86 ELF：原始碼 `X86FeatureBytes` 標 `TODO`（[Elf.cs:24](../Il2CppDumper/ExecutableFormats/Elf.cs#L24)），目前複製 ARM 樣式但永遠不會 match。x86 ELF 只能走 PlusSearch / SymbolSearch。

### 4.7 Macho64 額外：`ReadUIntPtr` 修正

[Macho64.cs:271-286](../Il2CppDumper/ExecutableFormats/Macho64.cs#L271-L286)

讀 64-bit pointer 時，若值大於 `vmaddr + 0xFFFFFFFF`，且當前位置在 `__const` 或 `__data` 內，就把高 32 bit 砍掉重組：

```csharp
var rva = pointer - vmaddr;
rva &= 0xFFFFFFFF;
pointer = rva + vmaddr;
```

這是處理 iOS chained fixups 機制（pointer 的高位被 dyld 編碼成 fixup metadata）。

---

## 5. `SymbolSearch` — 從 dynsym 直接取（ELF only）

[Elf64.cs:100-128](../Il2CppDumper/ExecutableFormats/Elf64.cs#L100-L128)

如果 ELF 沒被 stripped，dynsym 內會有兩個全域符號：

```
g_CodeRegistration       → codeRegistration
g_MetadataRegistration   → metadataRegistration
```

直接從 `Elf64_Sym.st_value` 取得 VA 後 `Init`。實務上多數商業 game 都會 strip，但開發版或某些版本可能保留。

---

## 6. ELF Relocation 處理（給非 dumped 檔）

[Elf64.RelocationProcessing](../Il2CppDumper/ExecutableFormats/Elf64.cs#L183-L216)

非 dumped ELF 在載入後會走一次 relocation：

```
for rela in DT_RELA[]:
    type = rela.r_info & 0xffffffff
    sym  = rela.r_info >> 32
    
    AARCH64:
      R_AARCH64_ABS64    → write (symbolTable[sym].st_value + r_addend) at r_offset
      R_AARCH64_RELATIVE → write r_addend at r_offset
    
    x86_64:
      R_X86_64_64        → 同 ABS64
      R_X86_64_RELATIVE  → 同 RELATIVE
```

⚠️ 注意這是 **就地寫 stream**，所以後續 `MapVATR` 讀到的指標已經是 relocated 後的值。Elf32 也有對應實作（讀 DT_REL，注意是 8 byte 一筆而非 12）。

---

## 7. dumped 檔的特殊修正

當使用者輸入 dump address 後（[Program.cs:189-200](../Il2CppDumper/Program.cs#L189-L200)）：

1. `il2Cpp.ImageBase = DumpAddr` 
2. `il2Cpp.IsDumped = true`
3. 若 `il2Cpp is ElfBase` 且 `!NoRedirectedPointer` → `elf.Reload()`，會：
   - 重新讀 program segment
   - 呼叫 `FixedProgramSegment`：把 `p_offset` 改成 `p_vaddr`、`p_vaddr += ImageBase`、`p_filesz = p_memsz`
   - 呼叫 `FixedDynamicSection`：對 `DT_PLTGOT/HASH/STRTAB/SYMTAB/RELA/INIT/FINI/REL/JMPREL/INIT_ARRAY/FINI_ARRAY` 的 `d_un += ImageBase`
   - 重讀 dynsym（跳過 RelocationProcessing 與 protection 警告，因為 dumped 已經 relocated）

`NoRedirectedPointer = true`（config）會跳過 `Reload`，給「dump 出來的指標不需要 redirect」的設備用。

---

## 8. 保護偵測

[Elf64.CheckProtection](../Il2CppDumper/ExecutableFormats/Elf64.cs#L218-L251)（Elf32 也有）：

| 觸發條件 | 訊息 |
|---------|------|
| `DT_INIT` 存在 | `WARNING: find .init_proc` |
| dynsym 內有 `JNI_OnLoad` | `WARNING: find JNI_OnLoad` |
| section 中有 `SHT_LOUSER` 類型 | `WARNING: find SHT_LOUSER section` |

任一觸發都會在 Search 階段印 `ERROR: This file may be protected.`，但程式繼續跑（讓 PlusSearch 試）。

Mach-O 64 偵測加密：`LC_ENCRYPTION_INFO_64`（cmd `0x2C`）的 `cryptID != 0` 時印 ERROR（[Macho64.cs:56-63](../Il2CppDumper/ExecutableFormats/Macho64.cs#L56-L63)），但目前**不阻止繼續執行**。

---

## 9. PE 的 Windows-only 備援：`PELoader`

[Utils/PELoader.cs](../Il2CppDumper/Utils/PELoader.cs)

PE 的 PlusSearch 失敗時，且在 Windows 上，會走這條：

```csharp
var handle = LoadLibrary(fileName);    // P/Invoke kernel32
// 讀回每個 section 在記憶體中的 raw bytes
// 重新組一個 MemoryStream，內容是「裝載後」的 PE
return new PE(peMemory).LoadFromMemory(handle);
```

`LoadFromMemory` 會把每個 section 的 `PointerToRawData = VirtualAddress`，`SizeOfRawData = VirtualSize`，因為記憶體中的 PE 用 VA 直接定位。

⚠️ 32-bit / 64-bit binary 與當前 process bitness 不一致時拋例外（[PELoader.cs:29-36](../Il2CppDumper/Utils/PELoader.cs#L29-L36)），需要使用 `Il2CppDumper-x86.exe` 對應版本。

---

## 10. Boyer-Moore-Horspool 字串搜尋

[Extensions/BoyerMooreHorspool.cs](../Il2CppDumper/Extensions/BoyerMooreHorspool.cs)

- `byte[].Search(byte[] pattern)`：標準 BMH
- `byte[].Search(string pattern)`：pattern 是用空格分隔的 hex tokens，支援 `?` 通配符（"48 89 ? ? 48 8B"），給未來的 binary signature search 用

目前只有 `FindCodeRegistration2019` 用到 byte[] 版本來找 `mscorlib.dll\0`。

---

## 11. 32-bit vs 64-bit ELF / Macho 差異總覽

| 項目 | Elf | Elf64 | Macho | Macho64 |
|------|-----|-------|-------|---------|
| `Is32Bit` | true | false | true | false |
| `Search` 實作 | ✅ ARM only（Thumb） | ❌ return false（依賴 PlusSearch / SymbolSearch） | ✅ ARM Thumb（MOVS+ADD配對） | ✅ ARM64（ADRP+ADD配對） |
| `SymbolSearch` | ✅ `g_CodeRegistration` / `g_MetadataRegistration` | ✅ 同左 | ❌ | ❌ |
| Relocation type | `R_386_32` / `R_ARM_ABS32`（簡單 `DT_REL`） | `R_AARCH64_ABS64/RELATIVE`, `R_X86_64_64/RELATIVE`（`DT_RELA`） | — | — |
| dump 處理（`Reload`） | ✅ FixedProgramSegment + FixedDynamicSection（32-bit phdr 32 bytes） | ✅ 同左（64-bit phdr 56 bytes） | — | — |
| Search 特殊 | LDR R1, [X]+ADD R0+ADD R2 樣式；x86 樣式 TODO 未實作 | — | Thumb LSB 修正（`Init` 後 `methodPointers - 1`） | `ReadUIntPtr` 內處理 iOS chained fixup（高位砍掉） |
| 載入時相符 | 一律從 `e_phoff` 讀 program headers | 同左 | 從 LC_SEGMENT 累加 sections | 同左但 LC_SEGMENT_64 |
| 預設 ImageBase 偵測 | 無（dumped 由使用者輸入） | 同左 | `vmaddr` 來自 `__TEXT` segment | 同左 |
| Section 分類 | `p_flags & PF_X` → exec；`PF_W && PF_R` → data | 同左 | `sectname=="__const"` → data；`flags==0x80000400` → exec；`flags==1` → bss | 同 64 |

⚠️ Macho 與 Macho64 的 `Search()` 完全不共享，因為 Thumb 編碼（ARM 32-bit）與 ARM64 編碼差異太大。

## 12. 偵錯小抄

| 症狀 | 可能原因 | 對策 |
|------|---------|------|
| `ERROR: il2cpp file not supported` | magic 都對不到 | 檔案有 packer 或不是 IL2CPP binary |
| `ERROR: Metadata file supplied is not valid metadata file.` | `0xFAB11BAF` 對不到 | 被 obfuscate，這專案不解 |
| `ERROR: This file may be protected.` | `Elf.CheckProtection` 觸發 | 試 `Zygisk-Il2CppDumper`（README 推薦） |
| `ERROR: Can't use auto mode, try manual mode.` | 三段式都 fail | 用 IDA 等找 `g_CodeRegistration` / `g_MetadataRegistration` 後手動輸入 |
| `CodeRegistration : 0` 但繼續跑 | `FindCodeRegistration` 失敗但呼叫者沒檢查 | 不會發生：`AutoPlusInit` 在兩者皆非 0 時才 `Init` |
| dump.cs 全是泛型錯誤 | dumped 檔但沒給 ImageBase | 重跑、輸入正確的 dump VA |
| 方法 RVA 全是 `-1` | `methodIndex < 0`（abstract method）或 dumped 但 `IsDumped` 沒設 | 看 `methodPointer > 0` 的分支條件 |
