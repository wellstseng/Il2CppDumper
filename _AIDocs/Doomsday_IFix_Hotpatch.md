# Doomsday — IFix 熱更機制摘要

> 對象：IGG Doomsday: Last Survivors（Tencent IFix 熱更框架）
> 來源：勘查 `Input/Doomsday/RestoredSolution/Annotated/IFix.Core/` + `Assembly-CSharp/IFix/` + 各 dll 內 `IFix/` namespace
> 對應 SOP：[`memory/_staging/Doomsday_Phase2_SOP.md`](../memory/_staging/Doomsday_Phase2_SOP.md) §3「IFix 熱更 fast-path 整段移除」
> 用途：S2 翻譯時，戰鬥/UI/業務代碼到處有 IFix fast-path；本文件解釋這些 boilerplate 背後的 runtime 機制，知其所以然才能放心砍。

---

## 1. 一句話總結

IFix = **Tencent 自製的「IL interpreter + dispatch table」熱更方案**，繞過 IL2CPP 不支援 Reflection.Emit / Assembly.Load 的限制：把 patch 後的 method 重新編成 CIL → 包成 patch 檔下發 → runtime 用自寫的 VM 解 CIL → 每個 method 入口塞 fast-path 檢查是否被 patch，是就跳 VM 跑 patched 版本，否則走原 native 編譯結果。

---

## 2. 三大角色

| 角色 | 位置 | 職責 |
|---|---|---|
| **PatchManager** | `IFix.Core/PatchManager.cs` (2135 行) | patch 檔載入入口；解析 method/field/type 索引表、external ref 表、IL bytecode；建立 `VirtualMachine` 實例 |
| **VirtualMachine** | `IFix.Core/VirtualMachine.cs` (8477 行) | IL interpreter；單一 `Execute(Instruction* pc, ...)` 巨無霸 method 從 L1284 跑到 L8205（~6900 行 switch case 對應所有 CIL opcodes） |
| **Call** | `IFix.Core/Call.cs` (997 行) | native↔patch 邊界的 stack frame；`PushXxx`/`GetXxx` 各 primitive type 一對；native code 推參數進來、VM 跑完再取回傳值 |

---

## 3. 業務層 fast-path（每個 method 入口）

從 Annotated pseudocode 看到的標準型態（範例：`GameContext.get_IsInGuide` RVA 0xfe7cc0）：

```
char cVar1 = IFix_WrappersManagerImpl__IsPatched(0xa65c, 0);
if (cVar1 == '\0') {
    // 原生實作（C# 源碼編出來的 IL2CPP native code）
    ...
} else {
    longlong lVar4 = IFix_WrappersManagerImpl__GetPatch(0xa65c, 0);
    if (lVar4 != 0) {
        return IFix_ILFixDynamicMethodWrapper____Gen_Wrap_18(lVar4, param_1, 0);
    }
}
FUN_18055b3e0();  // never-return null trap
```

對應 C# 源碼（IFix 工具在 build time CIL inject 的，原作者**沒寫**）：

```csharp
if (WrappersManagerImpl.IsPatched(0xa65c)) {
    var patch = WrappersManagerImpl.GetPatch(0xa65c);
    if (patch != null) return patch.__Gen_Wrap_18(this);
}
// 原始 C# 邏輯
...
```

**Phase2 Final 內這段一律整段砍掉**（[`SOP §3`](../memory/_staging/Doomsday_Phase2_SOP.md)），只保留 else branch 的原生邏輯。

---

## 4. WrappersManagerImpl — fast-path 查表

`Assembly-CSharp/IFix/WrappersManagerImpl.cs`：

```csharp
public class WrappersManagerImpl : WrappersManager {
    private VirtualMachine virtualMachine;

    public static ILFixDynamicMethodWrapper GetPatch(int id) {
        return ILFixDynamicMethodWrapper.wrapperArray[id];
    }

    public static bool IsPatched(int id) {
        return id < ILFixDynamicMethodWrapper.wrapperArray.Length
            && ILFixDynamicMethodWrapper.wrapperArray[id] != null;
    }
}
```

**關鍵**：
- `wrapperArray[]` 是 **static array**，PatchManager.Load 時填充
- patch ID（範例：0xa65c）= 此 method 在全域 patch table 的索引
- **未 patch 的 method**：`wrapperArray[id] == null` → `IsPatched` false → 走原 native
- **已 patch**：`wrapperArray[id]` 是某個 `ILFixDynamicMethodWrapper` 實例
- 同一 dll 內每個 dll 都有自己的 `WrappersManagerImpl`（`Assembly-CSharp/IFix/`、`dls.game/IFix/`、`dls.framework/IFix/`、`dls.framework.common/IFix/`、`dls.im/IFix/`）

> **Ghidra demangle 痕跡**：`IFix_WrappersManagerImpl__IsPatched(0xa65c, 0)` 的 trailing `0` 是 IL2CPP method-info pointer（calling convention），C# 源碼只有 `IsPatched(0xa65c)`。

---

## 5. ILFixDynamicMethodWrapper — patch dispatch

每個 patch-able method 一個 wrapper 實例：

```csharp
public class ILFixDynamicMethodWrapper {
    private VirtualMachine virtualMachine;  // 0x10
    private int methodId;                   // 0x18
    private object anonObj;                 // 0x20
    public static ILFixDynamicMethodWrapper[] wrapperArray;  // static 0x0

    public ILFixDynamicMethodWrapper(VirtualMachine vm, int methodId, object anonObj) { ... }

    public void __Gen_Wrap_0(object P0) { ... }
    public bool __Gen_Wrap_18(object P0) { ... }
    public CampInfo __Gen_Wrap_5000(object P0) { ... }
    public ICameraDist __Gen_Wrap_5001(object P0, float P1) { ... }
    // ... 上萬個 wrapper，每個對應一種 method signature
}
```

**`__Gen_Wrap_N` 的 N**：不是 method ID，而是 **signature ID**（不同的「參數型別組合 + 回傳型別」對應不同 N）。所以同一 N 會被多個 patch method 共用——只要 signature 一樣，dispatch 路徑相同。

**典型 wrapper body**（pseudocode `__Gen_Wrap_0`）：
```
puVar1 = Call.Begin();           // 取 thread-local stack frame
// PushObject(this/args) via Call.PushXxx
// 把 *puVar1（Call 結構：argumentBase / evaluationStackBase / managedStack / currentTop / topWriteBack）拷貝
VirtualMachine.Execute(methodId, ref call, argsCount);  // 跑 patch CIL
// Call.GetXxx 取回傳值
```

**檔案爆量原因**：
- `Assembly-CSharp/IFix/ILFixDynamicMethodWrapper.cs` 只有 1705 行（小 dll，patch wrapper 少）
- **`dls.game/IFix/ILFixDynamicMethodWrapper.cs` 463561 行**（dls.game patch 點極多，signature 變化也多，每個 wrapper ~30-60 行 × 上萬個）
- `dls.framework/IFix/ILFixDynamicMethodWrapper.cs` 39429 行
- `dls.im/IFix/` 6733 行
- `dls.framework.common/IFix/` 5546 行

---

## 6. IDMAP0/1/2 — patch ID 對應表

`dls.game/IFix/IDMAP0.cs` (65526 行)、`IDMAP1.cs` (65526)、`IDMAP2.cs` (49106) 是 **enum**：

```csharp
public enum IDMAP0 {
    IGG_002DFileUtils_002DCheckFileExist0 = 0,
    IGG_002DFileUtils_002DCreateFileDirectory0 = 1,
    IGG_002DFileUtils_002DDeleteFileDirectory0 = 3,  // ID 不連續，按 patch 配置決定
    ...
}
```

- **命名規則**：`Namespace_002DType_002DMethod{OverloadIndex}` —— `_002D` 是 Unicode escape `-`（IFix 把 namespace.type.method 用 `-` 串接後 escape）
- **值** = patch ID（與 `WrappersManagerImpl.IsPatched(id)` 的 id 對應）
- 切 3 個檔是因為單 enum 太大會撞 metadata limit
- **這 enum 是 IFix 工具產生的 build artifact**，原作者不寫；S2 翻譯時跳過 IDMAP* 整族（沒有業務語意）

---

## 7. PatchManager — 載入入口

`IFix.Core/PatchManager.cs` public API：

```csharp
public static VirtualMachine Load(string filepath);
public static VirtualMachine Load(Stream stream, bool checkNew = true);
public static void Unload(Assembly assembly);
```

`Load(Stream)` 流程概要（從 method 簽名與 private helpers 推斷）：
1. `BinaryReader` 讀 patch 檔 header
2. `readMethod(reader, externTypes)` — 解析所有 patch method 的 metadata（target class、signature、CIL bytecode）
3. `getRedirectField` / `getMapId` / `readSlotInfo` — 處理 field redirect、interface method 對應、virtual slot 表
4. 建立 `VirtualMachine` 實例 + 設成 `VirtualMachine.global`
5. 把每個 patch wrapper instance 寫進 `ILFixDynamicMethodWrapper.wrapperArray[id]`

**全域 singleton**：
```csharp
VirtualMachine.SetGlobal(vm);
VirtualMachine.GetGlobal();
VirtualMachine.InitializeGlobal(Stream);  // = Load + SetGlobal
VirtualMachine.ReplaceGlobal(Stream);     // 熱更替換
VirtualMachine.RemoveGlobal();
```

---

## 8. VirtualMachine — IL interpreter 內部

```csharp
public class VirtualMachine {
    private Instruction** unmanagedCodes;          // patch method 的 CIL 指令陣列（unsafe）
    private ExceptionHandler[][] exceptionHandlers;
    private ExternInvoker[] externInvokers;        // 呼叫 .NET runtime API 的 reflection thunk
    private MethodBase[] externMethods;
    private Type[] externTypes;
    private string[] internStrings;
    internal FieldInfo[] fieldInfos;
    internal Dictionary<int, NewFieldInfo> newFieldInfos;
    private AnonymousStoreyInfo[] anonymousStoreyInfos;
    private Type[] staticFieldTypes;
    private object[] staticFields;
    private int[] cctors;
    private WrappersManager wrappersManager;

    public unsafe Value* Execute(
        Instruction* pc, Value* argumentBase, object[] managedStack,
        Value* evaluationStackBase, int argsCount, int methodIndex,
        int refCount = 0, Value** topWriteBack = null);  // L1284 ~ L8205
}
```

**Execute 為什麼 ~6900 行**：IFix 自己實作了 CIL evaluation stack interpreter，每個 opcode（ldarg/stloc/call/callvirt/newobj/ldfld/stfld/box/unbox/throw/conv.*/branch/...）都有一個 case 分支處理 `Value*` stack 操作。`Value*` 是 fixed-size primitive stack slot（與 managedStack 對稱：value type 用 `Value*`，reference type 用 `managedStack`）。

**跨呼叫 .NET runtime**：`externInvokers[]` 是 build time 預先生成的反射 thunk 陣列；patch CIL 內遇到 `call System.Math.Round` 之類就走 `externInvokers[index].Invoke(...)`。

---

## 9. 完整熱更流程

```
[Build time]
.cs 源碼 + IFix 標記 → IFix tool 抽 CIL → 產生 patch file（含 ID 對應 + bytecode）
                                       → CIL inject 業務 method 入口 fast-path
                                       → 產生 IDMAP enum + ILFixDynamicMethodWrapper.__Gen_Wrap_N
                                       → IL2CPP 編譯整包到 native

[Runtime load]
App 啟動 → PatchManager.InitializeGlobal(patchStream)
        → readMethod / readSlotInfo / 建 externInvokers
        → 填 ILFixDynamicMethodWrapper.wrapperArray[id]
        → VirtualMachine.SetGlobal(vm)

[每次呼叫業務 method]
1. native fast-path: IsPatched(id)?
2. 否 → 跑原 native 編譯結果（IL2CPP 那一份）
3. 是 → GetPatch(id) → wrapper.__Gen_Wrap_N(args)
4. wrapper: Call.Begin() → Call.PushXxx(args) → VM.Execute(methodId, ...) → Call.GetXxx()
5. VM.Execute: 解 patch CIL，遇 extern call 透過 externInvokers 跳回 .NET runtime
6. 回傳給 native caller
```

---

## 10. Phase2 翻譯時的處置（與 SOP 對應）

| 看到什麼 | Final 怎麼處理 | 理由 |
|---|---|---|
| `IFix_WrappersManagerImpl__IsPatched(0xa65c, 0)` / `__GetPatch` / `__Gen_Wrap_N` fast-path 三段組合 | **整段砍**，只保留 else branch 原生邏輯 | 原作者沒寫，build-time CIL injection |
| `IFix.IDMAP0/1/2` enum 全族 | **跳過整族檔案**（不翻譯） | build artifact，無業務語意 |
| `IFix.ILFixDynamicMethodWrapper`（5 個 dll 內各一個） | **跳過整族檔案**（不翻譯） | build artifact，~46 萬行純機械生成 |
| `IFix.WrappersManagerImpl`（5 個 dll 內各一個） | **跳過**（除非要驗證 IsPatched/GetPatch 機制） | runtime helper，不在業務邏輯 |
| `IFix.Core/*` 全 namespace | **跳過整族**（除非要 debug 熱更本身） | 第三方 runtime（Tencent IFix），不是這個遊戲的程式碼 |

---

## 11. 引用節點 / 跨 session 對照

- SOP：[`memory/_staging/Doomsday_Phase2_SOP.md`](../memory/_staging/Doomsday_Phase2_SOP.md) §3 「IFix 熱更 fast-path」
- 通用 SOP：`~/.claude/memory/_staging/_il2cpp_source_restore.md`
- S1 sample：`Input/Doomsday/RestoredSolution/Final/dls.game/IGG.Game.Module.Launch/GameContext.cs`（含已砍 fast-path 的範例）
- 進度：[`memory/_staging/next-phase.md`](../memory/_staging/next-phase.md)
