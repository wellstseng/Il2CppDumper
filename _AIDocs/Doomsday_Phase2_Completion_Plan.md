# Doomsday Phase2 Completion Plan

> 目的：把剩餘 `Annotated -> Final` 翻譯工作拆成可分派給多個 model / agent 的 section。
> 入口：執行前先讀 `Doomsday_Phase2_Progress.md` §4 與 `Translation_SOP_TokenSafe.md`。
> 最近更新：2026-05-21 15:04

---

## 0. Current Numbers

兩種口徑要分開看：

| 口徑 | 數量 | 說明 |
|---|---:|---|
| Annotated total | 35,802 | `Input/Doomsday/RestoredSolution/Annotated/**/*.cs` |
| Final exists | 27,938 | 有鏡像 Final 檔；其中部分為 placeholder，不代表品質合格 |
| Disk missing | 7,864 | Annotated 有、Final 沒有（主要為 `dls.message` protobuf skipped） |
| Confirmed effective completed | 18,012 | 進度表品質口徑；舊 16,431 + `Epic` audit promotion 1,581，不含 scan-only candidate |
| Confirmed effective remaining | 17,790 | 需要翻譯或重檢後才能算完成；`dls.message` protobuf 仍依使用者指示跳過 |
| Audit-candidate ceiling | 24,797 | broad suspicious scan 後的候選上限；只能用來排批，不等於完成 |
| Explicit suspicious remaining | 3,115 | 非 skipped roots 中仍有明顯 placeholder/default/hard-stub pattern；不含 `Epic.Helper.GetDefault<T>()` 語意性 default |

`dls.im` 特例已收斂：目前磁碟 380/380、全 dll marker grep 0，且 2026-05-19 13:55 build 摘要沒有 `dls.im` 語法錯。後續若要更高標準，可再做語意抽查，但不再列為 S1 阻塞。

---

## 1. Claim Protocol

每個 agent 認領時只拿一個 section 或 subsection：

```text
Claim: <section-id>
Scope: <dll>/<namespace-or-file-list>
Write: Input/Doomsday/RestoredSolution/Final/<same mirror path>
Must read:
- _AIDocs/Doomsday_Phase2_Progress.md §4
- _AIDocs/Translation_SOP_TokenSafe.md
- memory/_staging/Doomsday_Phase2_SOP.md
```

完成後回報：

```text
Done: <section-id>
Files: X
Skipped: Y
Marker grep: clean / issues
Build/syntax: clean / blocked by existing errors
Notes: <only concrete blockers>
```

不要整個 dll 一次交給單一 agent，除非該 dll 小於 100 檔。

---

## 2. Priority Sections

| Section | Scope | Effective remaining | Why now | Suggested agents |
|---|---|---:|---|---:|
| S0 | True missing tail | 0 | ✅ done：`USDK.Module.BlacklistedWord.Editor/n.cs` dedicated pass completed | 0 |
| S1 | `dls.im` recheck | 0 | ✅ done：marker/syntax criteria passed | 0 |
| S2 | Medium partial dlls | 378 explicit suspicious | `Assembly-CSharp` 61 + `dls.framework` 216 + `dls.framework.common` 101；candidate 仍需 audit | 3-5 |
| S3 | Generated/config-like | 187 explicit suspicious + 7,867 skipped protobuf | `dls.config` 已收斂到 2,759 audit-candidate；`dls.message` protobuf 繼續 skip | 4-8 |
| S4 | External SDK wrappers | 305 explicit suspicious | `Epic` 1,698/1,698 audit complete；`USDK.Windows` 仍需按 `GPC.Modules.*` refine | 2-4 |
| S5 | `dls.game` gameplay refine | 2,245 explicit suspicious | ✅ disk-covered 7,828/7,828；hard `Phase2 stub` 仍在 March/MapOperation 舊 baseline，優先清 hard marker | 4-8 |
| S6 | `dls.ui.base` UI | 0 | ✅ done：11,128/11,128 FairyGUI generated UI restored from pseudocode | 0 |

---

## 3. Section S0 — True Missing Tail

這些是磁碟實際缺檔，先補完可讓「missing by path」更乾淨。

| Section | Files | Notes |
|---|---:|---|
| S0-A | `dls.im/IFix/IDMAP0.cs` | ✅ done |
| S0-B | `dls.im/IFix/ILFixDynamicMethodWrapper.cs` | ✅ done；大型 IFix dispatch wrapper |
| S0-C | `IFix.Core` remaining 1 | ✅ done：`Properties/AssemblyInfo.cs` |
| S0-D | `USDK.Module.BlacklistedWord.Editor` remaining 1 | ✅ done：`n.cs` 依 DFA sensitive-word pseudocode 還原；同模組 `m.cs/i.cs` 修正 `GPCPublicity` getter 命名 |

Suggested handling:
- `ILFixDynamicMethodWrapper.cs` 以 method family 分批，例如 `__Gen_Wrap_0~49`、`50~99`。
- 若 method body 是純 IFix dispatch wrapper，保留 IFix runtime idiom，不把 wrapper 當業務邏輯翻譯。

---

## 4. Section S1 — dls.im Recheck

`dls.im` 已存在 374 個舊 Final，但多數來自撤回前的程式翻譯路線。重檢目標不是只看檔案存在，而是移除舊工具痕跡並確認 body 合格。

| Section | Scope | Files | Suggested batch |
|---|---|---:|---:|
| S1-A | `IGG.IM.Actuator`, `IGG.IM.Controller` small interfaces/controllers | ✅ done | base + residual controllers marker-clean |
| S1-B | `IGG.IM.Data`, `IGG.IM.Notify`, `IGG.IM.Operation` | ✅ done | `FriendData.cs` completed in dedicated pass |
| S1-C | `IGG.IM.Network`, `IGG.IM.Sender`, `IGG.IM.Mono` | ✅ done | marker-clean |
| S1-D | `chatprotos`, `msgtype`, `protomsg` generated messages | ✅ done: 301 | generated-message marker/sampled recheck passed |
| S1-E | `IFix/*` | ✅ done | S0 tail + marker-clean |

Required grep before marking complete:

```bash
rg -n "auto-translated|Ghidra:|IFix_WrappersManagerImpl|FUN_180|StringLiteral_|return default;|Il2CppDummyDll|\\[Token|\\[Address|\\[FieldOffset" <batch-final-files>
```

---

## 5. Section S2 — Medium Partial DLLs

These sections are large enough to parallelize but small enough to finish before the huge UI/message work.

| Section | DLL | Missing | Suggested split |
|---|---|---:|---|
| S2-A | `USDK.Module.Operations.Editor` | 0 | ✅ disk-covered 207/207；含 stub 大檔，effective 207（S2A 主體 LLM 翻譯，少量 stub 大檔） |
| S2-B | `dls.framework.common` | 101 explicit suspicious | disk-covered 234/234；stricter audit reopened body refine bucket |
| S2-C | `dls.framework` | 216 explicit suspicious | disk-covered 547/547；本輪修 `IGG.Framework.Config` / Excel / StringDao / MultiKey / ConfigMgr；剩餘 explicit suspicious 216 |
| S2-D | `Assembly-CSharp` | 61 explicit suspicious | disk-covered 536/536；candidate 475，仍需 dedicated audit 才能升格 |

Top split hints:
- `dls.framework`: `FairyGUI` 209, `IGG.Framework.Config` 34, `IGG.Framework` 34, `IGG.Framework.Utils` 28.
- `dls.framework.common`: `Google.Protobuf.Reflection` 52, `Google.Protobuf.WellKnownTypes` 39, `IGG.Framework.Utils` 31.
- `Assembly-CSharp`: many small `IGG.Game.Module.*.Comps`; assign by namespace.

---

## 6. Section S3 — Generated / Config-like Large DLLs

These are big but structurally repetitive. Keep batches small enough for review.

| Section | DLL | Missing | Suggested split |
|---|---|---:|---|
| S3-A | `dls.config` | 187 explicit suspicious | disk-covered 2946/2946；本輪多批 config/Dao/helper refine 後 audit-candidate 2,759；剩餘優先 `WorkshopEquipDao`、`ExploreObject*Dao`、`TeamConfig`、`TempleConfig`、`ConfigHelper` |
| S3-B | `dls.message` | 7,867 | ⏭️ skip for now: protobuf per user instruction |

Rules:
- Protobuf is skipped for now by user instruction; focus S3 on config/enum/Dao/CfgData files.
- Generated config classes still need Final quality, but do not hand-roll business logic.
- Prefer preserving declarative fields/properties and generated-message idioms.
- Avoid whole-namespace reads; use file lists and 20-50 file batches for simple DTOs.

---

## 7. Section S4 — External SDK Wrappers

| Section | DLL | Missing | Top namespaces |
|---|---|---:|---|
| S4-A | `Epic` | 0 | ✅ 1,698/1,698 audit complete；本輪修 `QueryLeaderboardUserScoresOptionsInternal.StatInfo` 與 `RegisterPlayersCallbackInfoInternal.SanctionedPlayers` marshal count mismatch |
| S4-B | `USDK.Windows` | 305 explicit suspicious | disk-covered 1,776/1,776；audit-candidate 1,471；本輪修 `PassportInformation` / `IAPPayload` payload semantics，剩餘按 `GPC.Modules.*` namespace family |

Suggested batching:
- `Epic.OnlineServices.<module>` is a natural unit.
- `USDK.Windows` should be assigned by `GPC.Modules.*` namespace family.

---

## 8. Section S5 — dls.game Gameplay

`dls.game` is fully disk-covered (7,828/7,828). Stricter scan currently finds 2,245 explicit suspicious files; hard `Phase2 stub` hits are concentrated in March/MapOperation old baseline files and should be cleaned before broad S5 refine. Assign by namespace family and gameplay value, not by raw file count alone.

High-priority candidate splits:

| Section | Namespace | Files |
|---|---|---:|
| S5-A | `IGG.Game.Module.Activity.View` | ✅ 406/406 disk-cover, 52 effective + 354 placeholder（S5 系列最大批 769K 行，UI Activity View 業務邏輯密度最高，全 IFix-only strip-stub） |
| S5-B | `IGG.Game.Data.Cache.Mail.Type` | ✅ 341/341 disk-cover, 300 effective + 41 placeholder（Mail envelope 資料結構 small 比例 87%，全 IFix-only strip-stub） |
| S5-C | `IGG.Game.Notifys` | ✅ 155/155 disk-cover, 154 effective + 1 placeholder（event name `const string` 表，非 protobuf；S5 系列 effective 比例 99.4% 最高） |
| S5-D | `IGG.Game.Helper` | ✅ 118/118 disk-cover, 91 effective (含 6 sample) + 27 placeholder |
| S5-E | `IGG.Game.Module.MultiplierGate` | ✅ 116/116 disk-cover, 49 effective + 67 placeholder（全 IFix-only，主執行緒 strip-stub 一次過） |
| S5-F | `IGG.Game.Module.March.Actor` | ✅ 107/107 disk-cover, 32 effective + 75 placeholder（全 IFix-only strip-stub，含 baseline NIE 修補） |
| S5-G | `IGG.Game.Module.Common.View` | ✅ 104/104 disk-cover, 35 effective + 69 placeholder（全 IFix-only strip-stub，0 baseline） |
| S5-H | `IGG.Game.Data.Cache.IM` | ✅ 100/100 disk-cover, 89 effective + 11 placeholder（全 IFix-only strip-stub，0 baseline；effective 比例 89% 為 S5 系列最高） |
| S5-I | remaining `dls.game` paths | ✅ 6,311/6,311 disk-cover, 2,832 effective + 3,479 placeholder（841 目錄分組 strip-stub；全 S5 disk-cover 完成） |

Avoid:
- Do not touch existing completed Launch/Login/MainScene/Cache sample areas unless the section explicitly says rework.
- Do not fix unrelated existing build errors while translating another namespace.

---

## 9. Section S6 — dls.ui.base UI

Largest block: 11,128 files. Must be parallelized by UI namespace.

Completed:
- `s6-binder-seed`: 159 個 `*Binder.cs` effective，9,024 筆 FairyGUI `UIObjectFactory.SetPackageItemExtension` registration 已由 Annotated pseudocode + `script.json` 還原；component classes 尚未落地，後續需按 namespace 補齊 `Base*` UI class。
- `s6-small-ui-components`: `IGG.Game.UI.FogOfWar`、`IGG.Game.UI.MonsterSiege`、`IGG.Game.UI.PanelDebug`、`IGG.Game.UI.Reward`、`IGG.Game.UI.ScoreSeminder`、`IGG.Game.UI.BuildQueue`、`IGG.Game.UI.CommonLoading`、`IGG.Game.UI.GameDebug`、`IGG.Game.UI.Trade` 小 namespace 完成；component class 已依 `ConstructFromXML` pseudocode 還原 child/controller/transition binding。
- `s6-fairygui-full`: 剩餘 10,955 檔全量完成；parser guard 要求每個 field 必須由 pseudocode `GetController/GetChild/GetTransition` 綁定，未綁完即 fail；最終 marker/stub grep 0、binder type refs missing 0。

Initial section map:

| Section | Namespace | Files |
|---|---|---:|
| S6-A | `IGG.Game.UI.Activity` | 814 |
| S6-B | `IGG.Game.UI.Common` | 443 |
| S6-C | `IGG.Game.UI.Pet` | 352 |
| S6-D | `IGG.Game.UI.Guild` | 340 |
| S6-E | `IGG.Game.UI.MallShop` | 288 |
| S6-F | `IGG.Game.UI.Hero` | 240 |
| S6-G | `IGG.Game.UI.BloodCrisis` | 218 |
| S6-H | `IGG.Game.UI.Chat` | 204 |
| S6-I | `IGG.Game.UI.Mail` | 202 |
| S6-J | `IGG.Game.UI.League` | 189 |
| S6-K | `IGG.Game.UI.KOF` | 181 |
| S6-L | remaining UI namespaces | split 50-150 files each |

UI rules:
- Preserve Unity / FairyGUI lifecycle idioms.
- Remove IFix / IL2CPP noise.
- Do not invent UI helper APIs; if a widget lookup is unclear, keep conservative field/method mapping.

---

## 10. Recommended Parallel Launch Order

1. Clear hard `Phase2 stub` hits in `dls.game` March/MapOperation old baseline files.
2. Run `USDK.Windows` refine by `GPC.Modules.*` family, targeting the 305 explicit suspicious files first.
3. Run `dls.config` Dao/helper refine, targeting the 187 explicit suspicious files first.
4. Run `S2` body refine for `dls.framework.common` / `dls.framework` / `Assembly-CSharp` suspicious buckets.
5. Treat `Epic`, `dls.im`, and `dls.ui.base` as closed unless a later semantic audit explicitly reopens individual files.

---

## 11. Done Criteria

A section is complete only when:

1. Every Annotated file in scope has a mirrored Final file.
2. First line is `// Annotated: ...`.
3. Marker grep is clean for the scope.
4. No obvious empty shell bodies: `return default;`, `return null;` without semantic reason, empty setter/ctor for non-empty pseudocode.
5. Any skipped file is listed with reason and exact path.
6. `Doomsday_Phase2_Progress.md` §1 and §9 are updated.
7. `Token_Cost_Ledger.md` gets one batch row if the batch was non-trivial.
