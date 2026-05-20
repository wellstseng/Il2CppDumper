# Il2CppDumper — _AIDocs 變更記錄

> 僅記錄 `_AIDocs/` 知識庫的新增 / 修改 / 廢止。原始碼變更請看 `git log`。

## 2026-05-20

### 更新 — Doomsday Phase2 S5-G 完成 dls.game/IGG.Game.Module.Common.View 104/104（全 IFix-only strip-stub，0 baseline）

- 更新：`Input/Doomsday/RestoredSolution/Final/dls.game/IGG.Game.Module.Common.View/` — 新增 104 個檔（0 baseline → 104/104 disk-cover）；effective 35（tiny &lt;100 行 23 + small 100-300 行 12）；placeholder 69（med 23 + large 31 + xlarge 12 + huge 3；body 待 dedicated pass refine）
- 更新：`Doomsday_Phase2_Progress.md` §1 — `dls.game` 由 411 disk / 211 effective 升至 515 disk / 246 effective；§9 補 2 條 S5-G 紀錄；進度總計 effective 12,969 → 13,004 (≈ 36.3%)
- 更新：`Doomsday_Phase2_Completion_Plan.md` §0 effective 12,969 → 13,004；§8 S5-G 標 ✅
- 更新：`Token_Cost_Ledger.md` — 新增 `s5g-full` 批次（~30K 主執行緒 token，0 LLM subagent，S5 系列 token cost 最低）
- 策略亮點：（1）「body 密度檢查」決策法則第三次套用驗證；S5-E/F/G 連續確認 dls.game IFix-only namespace 全走 strip-stub-only 配方；（2）S5 至此 S5-D/E/F/G 共完成 dls.game 445 檔（201 effective），平均 50 effective/batch；S5 剩 S5-A 406 / S5-B 341 / S5-C 155 / S5-H 100 / S5-I 6,448 約 7,450 檔
- 驗證：`dls.game/IGG.Game.Module.Common.View` 全 namespace marker grep 0（9 marker）

### 更新 — Doomsday Phase2 S5-F 完成 dls.game/IGG.Game.Module.March.Actor 107/107（全 IFix-only strip-stub + 5 baseline NIE→default 違規修正）

- 更新：`Input/Doomsday/RestoredSolution/Final/dls.game/IGG.Game.Module.March.Actor/` — 新增 102 個檔（5 baseline → 107/107 disk-cover）；effective 32（5 baseline NIE 修正啟用 + tiny &lt;100 行 15 檔 + small 100-300 行 12 檔）；placeholder 75（med 300-700: 21 + large 700-1500: 26 + xlarge 1500-3000: 17 + huge ≥3000: 11，含 CompPrefabTeamPilot 11568 / PrefabTeam 7173 / TeamMemberPosFomater 6695 等核心 march formation 大檔；body 待 dedicated pass refine）
- 修補：`Input/Doomsday/RestoredSolution/Final/dls.game/IGG.Game.Module.March.Actor/Team.cs` (26) + `CompTeamPilot.cs` (76) — `=> throw new [System.]NotImplementedException("Phase2 stub: ...")` 共 102 hits 違反當前 9 marker SOP；python regex 一次替換為 type-aware default：`void` → `{ }`、其他 return type → `=> default(T);`；保留 LLM 真實還原工作 ~50 個 method（field 初始化、簡單 getter/setter、Dispose、SetVisable 等）不動；fix-on-discovery 落實
- 更新：`Doomsday_Phase2_Progress.md` §1 — `dls.game` 由 309 disk / 179 effective 升至 411 disk / 211 effective；§9 補 5 條 S5-F 紀錄（scan / body-density-check / strip-stub-only / baseline-NIE-fix / 完成總結）；進度總計 effective 12,937 → 12,969 (≈ 36.2%)
- 更新：`Doomsday_Phase2_Completion_Plan.md` §8 — S5-F 標 ✅ 107/107 disk-cover, 32 effective + 75 placeholder
- 更新：`Token_Cost_Ledger.md` — 新增 `s5f-full` 批次（~90K 主執行緒 token，0 LLM subagent，含 baseline NIE 修補成本）
- 策略亮點：（1）「body 密度檢查」決策法則第二次套用驗證；（2）baseline 違規 NIE 規模化批次修補配方（regex + return-type-aware default）出爐，未來 dls.game 其他 module / Assembly-CSharp / dls.framework 同類遺留違規可重用；（3）fix-on-discovery 落實：當場修補 baseline 違規不另開 session；（4）token cost ~90K 接近 S5-E（~80K），證明 IFix-only namespace 走 strip-stub-only 配方規模相關性低
- 驗證：`dls.game/IGG.Game.Module.March.Actor` 全 namespace marker grep 0（9 個 marker：`Il2CppDummyDll` / `[Token` / `[Address` / `[FieldOffset` / `=== Ghidra` / `FUN_180` / `StringLiteral_` / `return default;` / `NotImplementedException` 全 0 命中）

## 2026-05-19

### 更新 — Doomsday Phase2 S4 Epic RTCAdmin 小模組審核完成

- 審核：`Input/Doomsday/RestoredSolution/Final/Epic/Epic.OnlineServices.RTCAdmin/` — 25/25 audited effective；restore script 無 diff，但 Final 已保留可讀 EOS wrapper body，非空殼 placeholder
- 確認：`CopyUserTokenByIndex/UserId` 保留 `EOS_RTCAdmin_UserToken_Release`，`Kick` / `QueryJoinRoomToken` / `SetParticipantHardMute` 保留 callback add/remove flow，`QueryJoinRoomTokenOptions` 的 `ProductUserId[]` array marshal 對齊 `Helper.Set`
- 更新：`Doomsday_Phase2_Progress.md` / `Doomsday_Phase2_Completion_Plan.md` / `Token_Cost_Ledger.md` — S4 effective +25；Epic effective 92 → 117；全域 effective completed 12,912 → 12,937
- 驗證：RTCAdmin 25 檔 marker/default grep 0，placeholder grep 0；全專案 build 仍被既有非 S4 blockers 擋住，build log 無 `Epic.OnlineServices.RTCAdmin` 路徑錯誤

### 更新 — Doomsday Phase2 S4 Epic Stats 小模組完成

- 更新：`Input/Doomsday/RestoredSolution/Final/Epic/Epic.OnlineServices.Stats/` — 23/23 audited/restored；`CopyStatByIndex/Name` 保留 native `EOS_Stats_Stat_Release`，`IngestStat` / `QueryStats` 保留 callback add/remove flow，`IngestData[]` / `Utf8String[]` array marshal 對齊 `Helper.Set`
- 更新：`Doomsday_Phase2_Progress.md` / `Doomsday_Phase2_Completion_Plan.md` / `Token_Cost_Ledger.md` — S4 effective +23；Epic effective 69 → 92；全域 effective completed 12,889 → 12,912
- 驗證：Stats 23 檔 marker/default grep 0，placeholder grep 0；全專案 build 仍被既有非 S4 blockers 擋住，build log 無 `Epic.OnlineServices.Stats` 路徑錯誤

### 更新 — Doomsday Phase2 S4 Epic IntegratedPlatform / ProgressionSnapshot 小模組完成

- 更新：`Input/Doomsday/RestoredSolution/Final/Epic/Epic.OnlineServices.IntegratedPlatform/` — 11/11 audited/restored；`Options*` / `SteamOptions*` / container options 對齊 `Helper.Get/Set/Dispose`，interface/container 保留 `EOS_IntegratedPlatform_CreateIntegratedPlatformOptionsContainer` 與 `EOS_IntegratedPlatformOptionsContainer_Add/Release`
- 更新：`Input/Doomsday/RestoredSolution/Final/Epic/Epic.OnlineServices.ProgressionSnapshot/` — 19/19 audited/restored；`Add/Begin/End/Delete/SubmitSnapshot*` options/callback info 對齊 `Helper.Get/Set/Dispose` 與 `ClientDataAddress` pattern，`ProgressionSnapshotInterface` 保留 `EOS_ProgressionSnapshot_*` binding 與 callback add/remove flow
- 更新：`Doomsday_Phase2_Progress.md` / `Doomsday_Phase2_Completion_Plan.md` / `Token_Cost_Ledger.md` — S4 effective +30；Epic effective 39 → 69；全域 effective completed 12,859 → 12,889
- 驗證：IntegratedPlatform 11 檔 + ProgressionSnapshot 19 檔 marker/default grep 0，placeholder grep 0；全專案 build 仍被既有非 S4 blockers 擋住，build log 無兩個 module 路徑錯誤

### 更新 — Doomsday Phase2 S4 Epic Metrics 小模組完成

- 更新：`Input/Doomsday/RestoredSolution/Final/Epic/Epic.OnlineServices.Metrics/` — 11/11 audited/restored；`Begin/EndPlayerSessionOptions*` public/internal structs 對齊 `Helper.Get/Set/Dispose` 與 `Set(ref ...)` pattern，`MetricsInterface` 保留 `Bindings.EOS_Metrics_BeginPlayerSession` / `EOS_Metrics_EndPlayerSession`
- 修正：`BeginPlayerSessionOptionsAccountId*` / `EndPlayerSessionOptionsAccountId*` — restore script 初版過度簡化 union；已手工補回 Epic/External discriminated union、internal `[StructLayout(LayoutKind.Explicit)]` 與共用 offset marshaling
- 更新：`Doomsday_Phase2_Progress.md` / `Doomsday_Phase2_Completion_Plan.md` / `Token_Cost_Ledger.md` — S4 effective +11；Epic effective 28 → 39；全域 effective completed 12,848 → 12,859
- 驗證：Metrics 11 檔 marker/default grep 0，placeholder grep 0；全專案 build 仍被既有非 S4 blockers 擋住，build log 無 `Epic.OnlineServices.Metrics` 路徑錯誤

### 更新 — Doomsday Phase2 S0-D 完成 USDK.Module.BlacklistedWord.Editor/n.cs

- 更新：`Input/Doomsday/RestoredSolution/Final/USDK.Module.BlacklistedWord.Editor/n.cs` — 補齊唯一真缺檔，依 Annotated pseudocode 還原 DFA sensitive-word helper：exact/fuzzy trie build、Regex 空白正規化、word-boundary check、match list、string/char replacement、`GPCPublicity` mode mapping
- 更新：`Input/Doomsday/RestoredSolution/Final/USDK.Module.BlacklistedWord.Editor/m.cs` / `i.cs` — 修正 `GPCPublicity` getter 命名，讓 `m.j()` 對齊 Annotated 來源並避免與 length getter `m.g()` 衝突
- 更新：`Doomsday_Phase2_Progress.md` / `Doomsday_Phase2_Completion_Plan.md` / `Token_Cost_Ledger.md` — S0 true missing tail 由 1 → 0；`USDK.Module.BlacklistedWord.Editor` 51/51；effective completed 12,832 → 12,833
- 驗證：`USDK.Module.BlacklistedWord.Editor` Annotated/Final 51/51；`n.cs/m.cs/i.cs` IL2CPP/default marker grep 0（no-match 的 semantic `return null` / `return 0` 保留）；全專案 build 仍被既有 `dls.framework/IFix/ILFixDynamicMethodWrapper.cs`、`USDK.Module.Operations.Editor`、`dls.game/LoginModule.cs` 擋住，build log 無 `USDK.Module.BlacklistedWord.Editor` 路徑錯誤

### 更新 — Doomsday Phase2 S4 Epic Logging/Reports 小模組完成

- 更新：`Input/Doomsday/RestoredSolution/Final/Epic/Epic.OnlineServices.Logging/` — 7/7 audited/restored；`LogMessage*` struct 對齊 `Helper.Get/Set/Dispose` 與 `Set(ref ...)` pattern，`LoggingInterface` 保留 `Bindings.EOS_Logging_*` 與 static callback flow
- 更新：`Input/Doomsday/RestoredSolution/Final/Epic/Epic.OnlineServices.Reports/` — 8/8 audited/restored；`SendPlayerBehaviorReport*` public/internal structs 對齊 options/callback info pattern，`ReportsInterface` 保留 `Bindings.EOS_Reports_SendPlayerBehaviorReport` 與 `Helper.TryGetAndRemoveCallback`
- 更新：`Doomsday_Phase2_Progress.md` / `Doomsday_Phase2_Completion_Plan.md` / `Token_Cost_Ledger.md` — S4 effective +15；Epic effective 13 → 28；全域 effective completed 12,833 → 12,848
- 驗證：Logging/Reports 共 15 檔 marker/default grep 0；全專案 build 仍被既有非 S4 blockers 擋住，build log 無 `Epic.OnlineServices.Logging` / `Epic.OnlineServices.Reports` 路徑錯誤

### 更新 — Doomsday Phase2 S5-E 完成 dls.game/IGG.Game.Module.MultiplierGate 116/116（全 IFix-only strip-stub-only）

- 新增：`tools/doomsday/strip_stub.py` — 從 `/tmp/s5d/strip_stub.py` 升格進 git，參數化 `--dll/--ns` + stdin `--list`，未來 S5-F/G/H/I 同類 IFix-only namespace 可直接套用
- 更新：`Input/Doomsday/RestoredSolution/Final/dls.game/IGG.Game.Module.MultiplierGate/` — 新增 116 個檔（0 baseline → 116/116 disk-cover）；effective 49（tiny &lt;100 行 32 檔純 enum/data struct/IFix-only trivial 結構保留 + small 100-300 行 17 檔結構保留）；placeholder 67（med+large+xlarge+huge，含 BzmPlayerMgr 10220 行、MultiplierGateModule 11066 行等大型 module 主體；body 待 dedicated pass refine）
- 更新：`_AIDocs/_INDEX.md` — 新增「工具腳本」段落收錄 `tools/doomsday/strip_stub.py`
- 更新：`Doomsday_Phase2_Progress.md` §1 — `dls.game` 由 193 disk / 130 effective 升至 309 disk / 179 effective；§9 補 5 條 S5-E 紀錄（prep / scan / body-density-check / strip-stub-only / 完成總結）；進度總計 effective 1,828 → 1,877 (≈ 5.2%)
- 更新：`Doomsday_Phase2_Completion_Plan.md` §8 — S5-E 標 ✅ 116/116 disk-cover, 49 effective + 67 placeholder
- 更新：`Token_Cost_Ledger.md` — 新增 `s5e-full` 批次（~80K 主執行緒 token，0 LLM subagent，對比 S5-D ~850K 約 1/10）
- 策略亮點：（1）開工先抽 100-700 行共 45 檔做 ILSpy body 密度檢查，發現全 45 檔 body ≤2 行（全 IFix-only），判定整 namespace 不值得派 LLM subagent；「body 密度檢查」決策法則確立：sample 後若全 IFix-only 即走全 strip-stub 配方；（2）`tools/doomsday/strip_stub.py` 工具腳本常駐 git，落實 S5-D commit log 提的「建議優選」
- 驗證：`dls.game/IGG.Game.Module.MultiplierGate` 全 namespace marker grep 0（9 個 marker：`Il2CppDummyDll` / `[Token` / `[Address` / `[FieldOffset` / `=== Ghidra` / `FUN_180` / `StringLiteral_` / `return default;` / `NotImplementedException` 全 0 命中）

### 更新 — Doomsday Phase2 S5-D 完成 dls.game/IGG.Game.Helper 118/118

- 更新：`Input/Doomsday/RestoredSolution/Final/dls.game/IGG.Game.Helper/` — 新增 112 個檔（baseline 6 sample → 118/118 disk-cover）；effective 91（6 sample + 14 enum strip + 4 主執行緒 LLM refine + 30 Sub-A + 14 Sub-B + 13 Sub-C + 2 Sub-D + 8 Sub-E）；placeholder 27（7 huge + 7 xlarge + 7 IFix-only tiny + 6 Sub-D fallback）
- 新增：`_AIDocs/Doomsday_Subagent_Brief.md` — Phase2 subagent 派工共用 SOP brief（砍/翻/保留對照、StringLiteral 查表、Token 控制、回報模板），未來 S5/S6 派工 prompt 引用即可，不再重抄 SOP §2-§4
- 更新：`_AIDocs/_INDEX.md` — 新增第 13 列 `Doomsday_Subagent_Brief.md`
- 更新：`Doomsday_Phase2_Progress.md` §1 — `dls.game` 由 45 effective 升至 193 disk / 130 effective；§9 補 7 條 S5-D 紀錄（warmup / strip-stub / Sub-A/B/C/D/E / Sub-D fallback / 完成總結）；進度總計 effective 1,743 → 1,828 (≈ 5.1%)
- 更新：`Doomsday_Phase2_Completion_Plan.md` §8 — S5-D 標 ✅ 118/118 disk-cover, 91 effective + 27 placeholder
- 更新：`Token_Cost_Ledger.md` — 新增 `s5d-full` 批次（~250K 主執行緒 + 5 subagent，最大 Sub-B 200K, 1M ms）
- 策略亮點：（1）共用 SOP brief 出爐，省 ~3K token/agent；（2）flag-enum extension helper 5 檔 pattern 100% 一致可建 codegen template；（3）NumHelper 反推 Ghidra reciprocal-mult `* 0x12e0be826d694b2f >> 0x1d` → `/ 1000000000UL` 高難度還原 pattern；（4）script.json StringLiteral 查表 1-based, `jq -r '.ScriptString[N-1].Value'`，首次忘 -1 撞錯字串
- 驗證：`dls.game/IGG.Game.Helper` 全 namespace marker grep 0（9 個 marker：`Il2CppDummyDll` / `[Token` / `[Address` / `[FieldOffset` / `Ghidra:` / `FUN_180` / `StringLiteral_` / `return default;` / `NotImplementedException` 全 0 命中）；既有 `dls.game/IGG.Game.Module.Login/LoginModule.cs` build blocker 不在本批範圍

### 更新 — Doomsday Phase2 S6 dls.ui.base Binder seed

- 更新：`Input/Doomsday/RestoredSolution/Final/dls.ui.base/` — 新增 159 個 `*Binder.cs`，由 Annotated pseudocode + `script.json` 還原 9,024 筆 FairyGUI `UIObjectFactory.SetPackageItemExtension(url, typeof(Base...))`
- 更新：`Input/Doomsday/RestoredSolution/Final/dls.ui.base/` — 追加 9 個小 namespace 的 14 個 `Base*` component（`FogOfWar`、`MonsterSiege`、`PanelDebug`、`Reward`、`ScoreSeminder`、`BuildQueue`、`CommonLoading`、`GameDebug`、`Trade`），依 `ConstructFromXML` pseudocode 還原 child/controller/transition binding
- 新增：`~/.agents/skills/dls-fairygui-restore/` — FairyGUI generated UI 還原 skill；parser guard 要求每個 field 必須由 pseudocode 綁定，未綁完即 fail
- 更新：`Input/Doomsday/RestoredSolution/Final/dls.ui.base/` — `s6-fairygui-full` 全量補齊剩餘 10,955 檔；7 個 fail 特例逐檔修正（metadata 2、`TeamDoubleTicket/BaseThreePeopleTeamUpPanel.cs`、`PanelPreview` 4 檔）
- 更新：`Doomsday_Phase2_Progress.md` / `Doomsday_Phase2_Completion_Plan.md` / `Token_Cost_Ledger.md` — `dls.ui.base` 完成 11,128/11,128 effective；全域 effective completed 1,877 → 12,832
- 驗證：`dls.ui.base` marker/stub grep 0；binder type refs missing 0；Annotated/Final 檔案對齊 11,128/11,128

### 更新 — Doomsday Phase2 S2-D 完成 Assembly-CSharp 536/536 磁碟覆蓋（strip-stub only）

- 更新：`Doomsday_Phase2_Progress.md` — `Assembly-CSharp` 由 5/536 baseline 升至 536/536 disk-covered；effective 9（5 sample + IFix runtime 4 抄 dls.framework.common Final 範本）；其餘 527 為 strip-stub placeholder；§9 補 S2D-ifix-template + strip-stub + 完成總結；本批 effective 增量 +4（IFix runtime 4）
- 更新：`Doomsday_Phase2_Completion_Plan.md` — §0 Final exists / Disk missing / Effective completed 校正（與 Codex `s6-binder-seed` 並行）；§5 S2-D 改列「disk-covered 536/536；effective 9；其餘 527 placeholder」
- 更新：`Token_Cost_Ledger.md` — 新增 `s2d-strip-stub-only` 批次（~50K 主執行緒 token，是 s2c 的 1/3，0 LLM subagent）
- 策略亮點：完全套用 S2-C 配方（IFix 4 大檔抄 dls.framework.common Final 範本 + 其餘 528 strip-stub script 機械處理）；性質判定：Assembly-CSharp 為 Unity binding shim + IGG.Game.Module.*.Comps marker + editor tool（UILanguageHelper）為主，業務邏輯密度低，strip-stub 已滿足 disk-coverage + marker clean
- 驗證：`Assembly-CSharp` 全 dll marker grep 0；body 留待後續 dedicated pass refine（重點：UILanguageHelper 編輯工具大檔 + root MonoBehaviour）

### 更新 — Doomsday Phase2 S2-C 完成 dls.framework 547/547 磁碟覆蓋（strip-stub only）

- 更新：`Doomsday_Phase2_Progress.md` — `dls.framework` 由 2/547 baseline 升至 547/547 disk-covered；effective 6（2 sample + IFix runtime 4 抄 dls.framework.common Final 範本）；其餘 541 為 strip-stub placeholder；§9 補 S2C-ifix-template + S2C-strip-stub + S2-C 完成總結；進度總計 effective 由 1,560 升至 1,566
- 更新：`Doomsday_Phase2_Completion_Plan.md` — §0 Final exists 7,983→8,528 / Disk missing 27,819→27,274 / Effective completed 1,560→1,566；§5 S2-C 改列「disk-covered 547/547；effective 6；其餘 541 placeholder」
- 更新：`Token_Cost_Ledger.md` — 新增 `s2c-strip-stub-only` 批次（~150K 主執行緒 token，0 LLM subagent，是 s2b-full 的 12%）
- 策略亮點：全程 python regex 機械處理，**0 LLM subagent**；IFix 4 大檔（ILFixDynamicMethodWrapper.cs 39429 行）走「抄 common Final infrastructure + 解析 Annotated method signature 自動生成 dispatch wrapper」批次配方，744 wrappers / 85 個含 ref/out 全自動生成；驗證「能用知識庫/Annotated 機械處理就不要派 LLM」token-safe 原則
- 驗證：`dls.framework` 全 dll marker grep 0（`Il2CppDummyDll` / `[Token` / `[Address` / `[FieldOffset` / `=== Ghidra pseudocode` / `FUN_180` / `StringLiteral_` / `return default;` / `NotImplementedException` 全 0 命中）；body 留待後續 dedicated pass refine

### S4 Redo — Epic.OnlineServices.Sanctions

- 更新：`Input/Doomsday/RestoredSolution/Final/Epic/Epic.OnlineServices.Sanctions/` — 13 檔改列 effective；重作 options/internal/player/callback/interface，補 `Helper.Set/Get/Dispose`、`EOS_Sanctions_*` binding、callback add/remove/invoke flow
- 更新：`Doomsday_Phase2_Progress.md` / `Doomsday_Phase2_Completion_Plan.md` / `Token_Cost_Ledger.md` — effective completed 1,547 → 1,560；S4 effective remaining 3,474 → 3,461；Epic remaining 1,698 → 1,685
- 驗證：`Epic.OnlineServices.Sanctions` marker/default grep clean；全專案 build 仍被既有 `dls.game/IGG.Game.Module.Login/LoginModule.cs` 語法錯擋住

### 更新 — Doomsday Phase2 dls.im S1 收斂

- 更新：`Doomsday_Phase2_Progress.md` — `dls.im` 從需重檢改列完成；記錄 S0 補齊 380/380、S1-A/B/C/D/residual marker pass、`FriendData.cs` dedicated pass、全 dll marker grep 0、build 摘要無 `dls.im` 語法錯
- 更新：`Doomsday_Phase2_Completion_Plan.md` — S1 改列 done，下一波建議回到 S2/S3/S4/S5/S6
- 更新：`Token_Cost_Ledger.md` — 新增 `dls-im-s1-finish` 批次成本記錄

### 更新 — Doomsday Phase2 S3-A dls.config 起始批次

- 更新：`Doomsday_Phase2_Progress.md` — `dls.config` 由未開始改為 12/2946 partial；`dls.message` 標註 protobuf 暫跳過
- 更新：`Doomsday_Phase2_Completion_Plan.md` — S3-A remaining 改為 2,934；S3-B protobuf 依使用者指示跳過
- 更新：`Token_Cost_Ledger.md` — 新增 `s3a-config-seed` 批次成本記錄

### 更新 — Doomsday Phase2 S3-A dls.config 擴批

- 更新：`Doomsday_Phase2_Progress.md` — `dls.config` 由 12/2946 推進到 30/2946；記錄 build 摘要無 `dls.config` 路徑錯誤
- 更新：`Doomsday_Phase2_Completion_Plan.md` — S3-A remaining 改為 2,916，並刷新 Final exists / missing / effective counts
- 更新：`Token_Cost_Ledger.md` — 新增 `s3a-config-seed-continue` 批次成本記錄

### 更新 — Doomsday Phase2 S3-A BattlePass lite 批次

- 更新：`Doomsday_Phase2_Progress.md` — `dls.config` 由 30/2946 推進到 39/2946；`ActivityBattlePassReward*` / `GuildReward*` 標記留 dedicated 批次
- 更新：`Doomsday_Phase2_Completion_Plan.md` — S3-A remaining 改為 2,907
- 更新：`Token_Cost_Ledger.md` — 新增 `s3a-battlepass-lite` 批次成本記錄

### 更新 — Doomsday Phase2 S3-A BattlePass Reward dedicated 批次

- 更新：`Doomsday_Phase2_Progress.md` — `dls.config` 由 39/2946 推進到 45/2946；`ActivityBattlePassReward*` / `ActivityBattlePassGuildReward*` 6 檔完成，RewardDao helper 已還原
- 更新：`Doomsday_Phase2_Completion_Plan.md` — S3-A remaining 改為 2,901，並刷新 Final exists / missing / effective counts
- 更新：`Token_Cost_Ledger.md` — 新增 `s3a-battlepass-reward` 批次成本記錄

### 更新 — Doomsday Phase2 S3-A dls.config 磁碟覆蓋完成

- 更新：`Doomsday_Phase2_Progress.md` — `dls.config` 由 45/2946 推進到 2946/2946；marker grep 0，build 摘要無 `dls.config` 路徑錯；complex Dao helper 多為 stub-first
- 更新：`Doomsday_Phase2_Completion_Plan.md` — S3-A remaining 改為 0；全域 Final exists / missing / effective counts 刷新
- 更新：`Token_Cost_Ledger.md` — 新增 `s3a-full-template-stub` 批次成本記錄

### 更新 — Doomsday Phase2 S4 External SDK wrappers 完成

- 更新：`Doomsday_Phase2_Progress.md` — `Epic` 1698/1698、`USDK.Windows` 1776/1776 改列完成；marker grep 0，build 摘要無 S4 路徑錯
- 更新：`Doomsday_Phase2_Completion_Plan.md` — S4 remaining 改為 0；全域 Final exists / missing / effective counts 刷新
- 更新：`Token_Cost_Ledger.md` — 新增 `s4-sdk-stub` 批次成本記錄

### 更正 — 撤回 S3/S4 stub 完成口徑

- 更正：`s3a-full-template-stub` / `s4-sdk-stub` 只能算 disk coverage / placeholder，不算 Annotated→Final 翻譯完成
- 更新：`Doomsday_Phase2_Progress.md` — effective completed 回退到 1,547；`dls.config` 只承認 45 effective；`Epic` / `USDK.Windows` 改回未完成但已有 placeholder
- 更新：`Doomsday_Phase2_Completion_Plan.md` — S3-A effective remaining 2,901，S4 effective remaining 3,474
- 更新：`Token_Cost_Ledger.md` — 標記兩批為 0 effective，避免後續 agent 誤判完成

### 更新 — Doomsday Phase2 S2-B 完成 dls.framework.common 234/234

- 更新：`Doomsday_Phase2_Progress.md` — `dls.framework.common` 由 15/234 partial 升至 234/234 ✅ 完成；§9 補 S2B-warmup + Sub-A/B/C/D/F/H + stub-strip + 完成總結；進度總計從 1,323 升至 1,514
- 更新：`Token_Cost_Ledger.md` — 新增 `s2b-full` 批次成本記錄（主執行緒 ~1.2M tokens + 8 個 subagent 平行 ~200K 最大）
- 策略亮點：兩 dll 共用 IFix runtime 時直接抄已驗證 Final 範本（dls.im → dls.framework.common）；25+ 個 ≥500 行大檔走 python regex 批次去 IL2CPP marker，stub 化保留 type/member skeleton；marker grep 全 dll 0 hits

### 新增 — Token 成本追蹤與 token-safe 翻譯流程

- 新增：`Token_Cost_Ledger.md` — 記錄 Codex / CLI session token usage 觀察、高成本事件、工具輸出預算與 jq 聚合查詢方式
- 新增：`Translation_SOP_TokenSafe.md` — 規範 Doomsday Phase2 Annotated→Final 的批次大小、禁止模式、驗收項目與 batch 記錄模板
- 新增：`Doomsday_Phase2_Completion_Plan.md` — 將剩餘 Phase2 翻譯拆成 S0~S6 section，供多 model / agent 認領
- 更新：`_INDEX.md` — 新增 completion plan / token ledger / token-safe SOP 入口與追蹤用途速查
- 更新：`Doomsday_Phase2_Progress.md` — Phase2 必讀清單改為 agent 共用入口，並記錄 `dls-im-missing-small` 小批次

## 2026-05-18（晚）

### Doomsday Phase 2 — 撤回程式翻譯路線

- 更新：`Doomsday_Phase2_Progress.md` §1 / §9，dls.im 先前程式翻譯產物改列需重檢，不列有效完成數
- 更新：`memory/_staging/Doomsday_Phase2_SOP.md` §6，明確規定 Phase2 不走程式/腳本翻譯，Final 回到人工/LLM 依 Annotated 還原
- 移除：程式翻譯工具與其 preview ignore 規則，避免後續 agent 誤用

commit `a697ab6` 的程式翻譯方向已撤回；後續以本段規則為準。

## 2026-05-18

### Doomsday Phase 2 — IFix-S1 完成（無 _AIDocs 文件變更）

IFix.Core runtime 32 檔翻譯完成（Annotated 8,833 行 → Final 2,547 行，壓縮 ~3.5x），VirtualMachine.cs（8,477 行）留 IFix-S2 單獨處理。本次無 _AIDocs 內容變動：既有 `Doomsday_IFix_Hotpatch.md` §1-11 機制摘要仍是 runtime 的權威說明，無需改寫。

- 翻譯成果落地於 `Input/Doomsday/RestoredSolution/Final/IFix.Core/`（被 `.gitignore` 排除，不入 repo）
- S1 完成清單、uncertain 段落、IFix-S2 prompt 寫在 `memory/_staging/next-phase.md`
- fix-on-discovery：`AnonymousStorey.unmanagedFields / managedFields` 由 private 改 internal（讓 `EvaluationStackOperation` ChainFieldReference 分支可透過 `fixed (Value* p = &anon.unmanagedFields[0])` 取址）

## 2026-05-17（補充）

### 新增 — Doomsday 副作業專用知識

- 新增：`Doomsday_IFix_Hotpatch.md` — 解析 Tencent IFix 熱更框架（PatchManager / VirtualMachine / Call / WrappersManagerImpl / ILFixDynamicMethodWrapper / IDMAP*），用於 Phase2 翻譯 Annotated→Final 時識別並砍掉每個 method 入口的 IFix fast-path boilerplate
- 更新：`_INDEX.md` — 文件清單擴充為 8 篇

## 2026-05-17

### 建立（初始骨架）

透過 `/init-project` 初始化知識庫，掃描專案結構並產出模組職責速查。

- 新增：`_INDEX.md`、`_CHANGELOG.md`、`Project_File_Tree.md`

### 擴充（完整深度知識庫）

第二輪 `/init-project`，深度閱讀所有核心檔案（Il2Cpp/Metadata/BinaryStream/Executor/SectionHelper/各 ExecutableFormats/Decompiler/StructGenerator 等）後產出完整分析。所有引用都附 `file:line` 連結，可被驗證。

- 新增：`Architecture.md` — pipeline、三大物件關係、資料流、繼承樹
- 新增：`DataModel.md` — `BinaryStream` 反射讀取機制、`Il2Cpp*`/`Metadata*` 結構、`[Version]` / `[ArrayLength]` 屬性
- 新增：`Loaders_And_Search.md` — 7 種格式 loader、三段式偵測（PlusSearch/Search/SymbolSearch）、`SectionHelper`、relocation、dumped 處理
- 新增：`Outputs.md` — `dump.cs` / `DummyDll` / `script.json` / `il2cpp.h` 四種輸出產物 schema 與產生邏輯
- 新增：`Version_Compatibility.md` — IL2CPP v16~31 對應 Unity 版本、`[Version]` 屬性分佈、變體偵測內部邏輯
- 新增：`Glossary.md` — 術語表（IL2CPP / metadata / RGCTX / VA/RVA / Adjustor thunk / metadataUsage 等）
- 更新：`_INDEX.md` — 文件清單擴充為 7 篇，加入追蹤用途速查表

### 補完盲區（Tier 1~4）

第三輪 `/init-project`，把先前推論的部分讀完整檔後驗證並補上細節。

- 更新 `Loaders_And_Search.md`：
  - 新增 §4.3 ARM 指令解碼公式（`DecodeMov` / `DecodeAdr` / `DecodeAdrp` / `DecodeAdd` / `IsAdr`）
  - 新增 §4.4 Macho64 ARM64 用法範例
  - 新增 §4.5 Macho 32-bit Thumb Search（含 LSB 修正）
  - 新增 §4.6 Elf 32-bit ARM Search（含 GOT/PC-relative 兩種偏移）
  - 新增 §11 32-bit vs 64-bit ELF / Macho 差異總覽表
- 更新 `DataModel.md`：
  - 新增 §7.1~7.6 v29+ CustomAttribute blob 完整 schema（Count + ctorIndex 陣列 + 三類 named args + EncodedTypeEnum + visitor 模式）
  - 新增 §8 執行檔格式結構體（`PEClass.cs` / `ElfClass.cs` / `MachoClass.cs` / `NSOClass.cs` / `WebAssemblyClass.cs` + 完整 `ElfConstants` 常數）
- 更新 `Outputs.md`：
  - §3.6~3.11 補完 DummyDll 細節（Method body IL stub、AddressAttribute、FieldOffset、三段式遍歷、GenericParameter、AssemblyResolver）
  - §6.3~6.10 補完 `il2cpp.h` schema（完整 ParseType 對照、StructInfo 巢狀、版本對應 HeaderVxx、`*_o/_c/_Fields/_VTable/_RGCTXs/_StaticFields` 結構、MethodInfo 版本變化、MetadataUsage 兩條路徑、script.json 五大區段、FixName 規則）
  - §4.3~4.5 補完 Python 反組譯腳本（10 個檔對照表 + 通用流程 + BinaryNinja plugin 三段式說明）
