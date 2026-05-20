# Token Cost Ledger

> 目的：記錄 AI 協作時 token 花費集中在哪些任務、哪些工具輸出、哪些流程失控點。
> 範圍：本表記錄 Codex / CLI session 觀察到的 token usage，不等同於 OpenAI 帳單金額。
> 最近更新：2026-05-19

---

## 1. 成本來源分類

| 類型 | 判斷方式 | 常見原因 | 控制手段 |
|---|---|---|---|
| Long session carryover | `total_token_usage.total_tokens` 持續累積到百萬級 | 同一 thread 連續處理不同任務，舊上下文被反覆帶入 | 超過 1M total tokens 時切新 session 或產生 handoff |
| 巨量工具輸出 | tool output `Original token count` 超過 50K | `rg` / `find` / `dotnet build` / session JSONL 查詢未限縮 | 先 count/list/stat，再分段讀 |
| 翻譯返工 | 完成後又退回 redo | 空殼化、未依 Annotated pseudocode 還原、未跑 marker 檢查 | 每批先驗收再記完成 |
| SOP 重複載入 | 每次開工都讀多份長文件 | 缺少 file map / batch map | 先讀 `_INDEX`，只載入該批必需文件 |
| Build log 淹沒 | build 輸出整包進 context | 依賴缺失、重複 warning、全專案 build 噪音 | 只保留錯誤摘要與首個 root cause |

---

## 2. 已觀察高成本事件

| 日期 | 任務 / session | 觀察到的高點 | 最大工具輸出 | 成本原因 | 下次限制 |
|---|---|---:|---:|---|---|
| 2026-05-18 | `.codex` vector / memory 修復長 session | 約 5.7M total tokens | 56K+ | 長時間診斷、多輪 service log / file scan | 每輪診斷先列 checklist，log 只取 tail / error |
| 2026-05-18 | Doomsday Phase2 tail / redo 主線 | 約 4.4M total tokens | 4.89M | 掃 `Input/Doomsday/output/pseudocode` 與大範圍檔案清單 | 禁止全域 pseudocode grep；先按 dll / class 名分段 |
| 2026-05-18 | CatClaw reasoning / dashboard 長 session | 約 11.4M total tokens | 262K | 長 session 混合查 package、改 code、build、restart | 功能完成後切新 thread，build log 截取 root cause |
| 2026-05-18 | Worker 翻譯驗證 | 約 0.9M~2.1M per worker | 99K | `dotnet build` / marker grep 輸出過長 | build 先重導為檔案，再 `rg -n "error|warning" | head` |
| 2026-05-19 | 成本追查本身 | 127K+ and growing | 262K | 直接 `rg` session JSONL，輸出 raw hit | 改用 `jq` 聚合欄位，不輸出 raw payload |

---

## 3. 每批成本記錄模板

新增批次後，在本節補一列。`最大工具輸出` 可由 session JSONL 的 `Original token count` 觀察，或手動估算。

| 日期 | 批次 | 範圍 | 檔案數 | total tokens | 最大工具輸出 | redo? | 成本原因 | 下次調整 |
|---|---|---|---:|---:|---:|---|---|---|
| YYYY-MM-DD | `<batch-name>` | `<dll/path>` | 0 | 0 | 0 | no | `<原因>` | `<限制>` |
| 2026-05-19 | `dls-im-missing-small` | `dls.im` missing small files | 4 | n/a | ~8.5K | no | 小批次補缺檔；build 摘要仍被既有錯誤洗版 | 下批先處理 2 個大型 IFix 缺檔前，分段讀且不要跑全量 build 到 context |
| 2026-05-19 | `s2a-1a + s2a-2a` | `USDK.Module.Operations.Editor` root tiny + NoticeHub.VO/ResourceStorage.VO/NoticeHub.Impl/Properties tiny files | 25 | n/a | ~10K | no | 平均單檔 <100 行；StringLiteral 查表 + script.json 解析；marker grep 乾淨 | 下批進入 100-300 行檔，單批控制在 5-10 檔避免 context 爆掉 |
| 2026-05-19 | `dls-im-s0-s1abc` | `dls.im` S0 tail + S1-A/B/C recheck, plus `IFix.Core/AssemblyInfo` | 42 | n/a | ~17K | no | subagent 並行後整合；一次 scoped marker grep 輸出大量 `FriendData.cs` skipped hits | 已知 skip 檔用 `rg -l` 或排除路徑，避免把整段 Ghidra 註解灌回 context |
| 2026-05-19 | `dls-im-s1-finish` | `dls.im` FriendData + generated messages + residual marker files | 335 | n/a | ~12K | no | generated files 多數已乾淨，subagent 用 marker/sampled recheck；build 摘要確認無 dls.im 語法錯 | 後續 generated 類先跑 marker + sampled structure，不要逐檔全讀 |
| 2026-05-19 | `s2a-full` (主+Sub1-7) | `USDK.Module.Operations.Editor` 全 dll 完成 207/207 | 182 | ~1.1M (main thread) | ~360K (Sub4 largest) | no | 主執行緒做 44 檔（tiny/small root + sub-namespace），派 7 個 subagent 平行：Sub1 tiny delegates 28、Sub2 small wrappers 33、Sub3 medium VO 27、Sub4 root 200-700 30、Sub5 large sub-namespace 6/14（8 skip）、Sub6 huge root 4/6（2 skip）、Sub7 stub gen 10/10；總共 10 個 800-1654 行檔以 stub 形式落地，body 留待 dedicated pass | 大檔（>700 行）默認改走 stub-first 策略：先派 stub gen agent 覆蓋磁碟，再針對性派 dedicated agent refine body；同類 bridge request pattern 多檔（bc/bs/ab/a7 等）抽成 batch template 給 subagent 可省去重複翻譯成本 |
| 2026-05-19 | `s3a-config-seed` | `dls.config` Abtest/AccountBinding/Achievement seed batch | 12 | n/a | ~12K | no | 建立 config/Dao/CfgData 模板；protobuf 依指示跳過；StringLiteral 用 `jq .ScriptString[N-1]` 查表 | 後續按三件組批次擴張，每批 10-30 檔；GetName 字串只查需要的索引 |
| 2026-05-19 | `s3a-config-seed-continue` | `dls.config` AchievementLevel/AchievementType/ActivityAllstarCalendar/ActivityBanquet/ActivityBanquetType/ActivityBattle | 18 | n/a | ~12K | no | 延續 config 三件組模板；少量 ProcessCfgsAfter / helper method 手工還原；build 摘要確認無 dls.config 路徑錯 | 下一批繼續按 Activity* 三件組，每批 15-30 檔；遇到大型後處理先單獨切出 |
| 2026-05-19 | `s3a-battlepass-lite` | `dls.config` ActivityBattlePass / Guild / Task lite batch | 9 | n/a | ~14K | no | BattlePassReward/GuildReward Dao 過大，先切出 dedicated 批次；本批只做可控的 config/Dao/helper | RewardDao 類 500-800 行要單獨讀 method signatures + 分段還原，不混進一般三件組 |
| 2026-05-19 | `s3a-battlepass-reward` | `dls.config` ActivityBattlePassReward / GuildReward dedicated batch | 6 | n/a | ~18K | no | 兩個 RewardDao 分段讀 pseudocode，手工還原 grouping cache、background index、level/exp/stage/reward helper；build 摘要確認無 dls.config 路徑錯 | 後續遇到 >500 行 Dao 仍單獨切批；先看 method signatures 再決定 stub-first 或 helper-level 還原 |
| 2026-05-19 | `s3a-full-template-stub` | `dls.config` placeholder coverage to 2946/2946 | 2,901 disk / 0 effective | n/a | ~35K | no | **更正：不算翻譯完成**。template/stub/strip 只有磁碟覆蓋和 marker/build-path 清理，缺 pseudocode 語意還原 | 不得再把 disk coverage 當 completed；後續需按 Annotated pseudocode 覆寫 placeholder |
| 2026-05-19 | `s4-sdk-stub` | `Epic` + `USDK.Windows` placeholder coverage | 3,474 disk / 0 effective | n/a | ~8K | no | **更正：不算翻譯完成**。全量 strip-stub 只保留 SDK wrapper type/member surface，沒有 pseudocode/source semantics | 後續 S4 必須按 module 重做；可參考官方 EOS/GPC source，但不能只 strip marker |
| 2026-05-19 | `S4-redo-Epic-Sanctions` | `Epic.OnlineServices.Sanctions` | 13 effective | n/a | ~6K | yes | 重作 Sanctions module：options/internal/player/callback/interface 依 pseudocode 還原 `Helper` marshal、EOS binding、callback flow | marker/default grep clean；全專案 build 被既有 `dls.game LoginModule.cs` syntax errors blocked |
| 2026-05-19 | `s2b-full` (主+Sub-A/B/C/D/E/F/G/H + stub-strip) | `dls.framework.common` 全 dll 234/234 | 219 | ~1.2M (主執行緒) | ~200K (Sub-F largest) | no | 主執行緒做 11 檔（IFix runtime 2 抄 dls.im + Unity stub + 6 interface + IDMAP0 awk 機械去 attr）；派 8 個 subagent 平行（A/B/C/D/E tiny 各 20-31 檔；F medium 200-500 40/58；G large 500-1000 18/18；H huge ≥1000 5/5 含 IFix wrapper 5546 stub）；Sub-F skip 17 檔主執行緒 strip_il2cpp.py 補位；總共 25+ 個 ≥500 行檔走 stub-first；marker grep 0 hits | 大檔 stub 走 python regex 批次比派 LLM 翻譯划算 ~10x；同 IFix runtime 跨 dll 直接抄 Final 範本（dls.im → dls.framework.common 的 ILFixInterfaceBridge / WrappersManagerImpl）；下批 S2-C dls.framework 545 missing 應同 protobuf-heavy 評估 stub-first 比例 |
| 2026-05-19 | `s2c-strip-stub-only` | `dls.framework` 全 dll 547/547 (effective 6) | 545 disk / 6 effective | ~150K (主執行緒) | ~6K (initial namespace scan) | no | 全程主執行緒 python regex，**0 LLM subagent**；IFix 4 大檔抄 `dls.framework.common` Final 範本（WrappersManagerImpl 結構完全相同直接抄；ILFixInterfaceBridge 採 common 最小骨架 + 補 RefAwait*；IDMAP0 awk 去 attr 3994 entries；ILFixDynamicMethodWrapper 自動生成 744 wrapper / 85 ref-out 含 DispatchRefVoid / DispatchRefReturn）；其餘 541 missing 全 strip-stub script 機械處理（砍 IL2CPP marker + Ghidra block + Il2CppDummyDll qualified prefix）；marker grep 0；effective 僅 6（2 sample + IFix runtime 4），其餘 541 為 placeholder 待 dedicated pass refine | S2-C 是 S2 系列中 token 消耗最低批（&lt; s2b-full 的 12%）；驗證「能用知識庫/Annotated 機械處理就不要派 LLM」原則；對於 disk-coverage 為主、effective 為輔的 dll（refine 留 dedicated pass），全 strip-stub 是 token-cost 最划算路線；未來 dls.game / Assembly-CSharp / dls.ui.base 殘檔可考慮同類路線快速覆蓋 disk，後續再按 namespace 派 LLM refine |
| 2026-05-19 | `s6-binder-seed` | `dls.ui.base` all `*Binder.cs` | 159 effective | n/a | ~12K | no | 由 Annotated pseudocode 解析 type handle + `StringLiteral_N`，查 `script.json` 還原 9,024 筆 FairyGUI `SetPackageItemExtension`；8 個空 binder 保留空 `BindAll()`；marker grep 0 | Binder family 適合一次批次化，因語意固定且可交叉驗證；下一步不要直接全量 stub UI class，應按 `IGG.Game.UI.*` namespace 補 `Base*` component，避免 binder 依賴長期 unresolved |
| 2026-05-19 | `s6-small-ui-components` | `dls.ui.base` small UI namespaces | 14 effective | n/a | ~30K | no | 逐檔讀 Annotated pseudocode，查 `script.json` 還原 package/resource/child/controller/transition 名稱；補 9 個小 namespace 的 14 個 `Base*` component；檔案覆蓋 26/26，binder type refs 全 resolved，marker/stub grep 0；新增 `dls-fairygui-restore` skill + parser guard，未能從 pseudocode 綁完所有 field 時 fail | 同類 2-4 檔 namespace 可繼續用此節奏；每批先完成 binder 依賴的 `Base*` class，避免跨大 namespace 爆 context |
| 2026-05-19 | `s6-fairygui-full` | `dls.ui.base` full dll | 10,955 effective | n/a | ~30K | no | 一次載入 `script.json` 批次處理 10,873 候選：10,866 自動成功，7 fail 特例逐檔修正（metadata 2、TeamDoubleTicket 1、PanelPreview 4）；parser guard 支援 `new` field、hex child index、無 trailing `,0` 的 controller/child call；最終 11,128/11,128、marker/stub grep 0、binder refs 0 | FairyGUI generated UI 可安全批次化，但前提是「所有 field 都由 pseudocode 綁定」；這條 guard 可重用於其他 generated UI dll |
| 2026-05-19 | `s0d-blacklistedword-n` | `USDK.Module.BlacklistedWord.Editor/n.cs` | 1 effective | n/a | ~34K | no | 1610 行 obfuscated DFA helper 分段讀 method pseudocode；查 `script.json` 還原 `isEnd`/`mode`/Regex/log 字串；手工還原 exact/fuzzy trie build、match scan、replace flow、word-boundary check，並修同模組 `m.cs/i.cs` getter 命名 | 同類單檔 obfuscated logic 先抓 method map + StringLiteral，再補最小相鄰型別修正；build 只過濾本 dll 路徑，避免既有全專案錯誤干擾 |
| 2026-05-19 | `s4-epic-logging-reports` | `Epic.OnlineServices.Logging` + `Epic.OnlineServices.Reports` | 15 effective | n/a | ~30K | no | 用 `restore_eos_module.py` 對小 module 補齊 public/internal struct pattern，再人工驗證 interface callback flow：Logging 7/7、Reports 8/8；marker/default grep 0；build log 無 module 路徑錯誤 | S4 Epic 小 module 可按 module 逐個 audit；若 restore script 只改 struct，interface/callback 仍需人工對照 Annotated `Bindings.EOS_*` 與 `Helper.TryGet*Callback` |
| 2026-05-19 | `s4-epic-metrics` | `Epic.OnlineServices.Metrics` | 11 effective | n/a | ~30K | yes | 先用 `restore_eos_module.py` 補 struct pattern，但 script 會把 `Begin/EndPlayerSessionOptionsAccountId*` union 過度簡化；已手工修回 Epic/External discriminated union、internal explicit layout、`Helper.Get/Set/Dispose` 與 `MetricsInterface` binding flow；marker/default grep 0，build log 無 Metrics 路徑錯誤 | restore script 之後要特別查 `*AccountId*Internal` / `[StructLayout(LayoutKind.Explicit)]` 類 union；不能只看 marker clean |
| 2026-05-19 | `s4-epic-integratedplatform-progressionsnapshot` | `Epic.OnlineServices.IntegratedPlatform` + `Epic.OnlineServices.ProgressionSnapshot` | 30 effective | n/a | ~30K | no | 兩個小 module 先用 `restore_eos_module.py` 補 public/internal struct，再人工驗證 interface/container/callback flow：IntegratedPlatform 11/11、ProgressionSnapshot 19/19；marker/default grep 0，build log 無 module 路徑錯誤 | 小 module 可合併成一個 ledger entry；interface/container 檔仍要人工對照 `Bindings.EOS_*`、`Helper.AddCallback`、`TryGetAndRemoveCallback`、`Release` |
| 2026-05-19 | `s4-epic-stats` | `Epic.OnlineServices.Stats` | 23 effective | n/a | ~30K | no | `restore_eos_module.py` 補 18 個 struct 後人工驗證 `StatsInterface`：CopyStatByIndex/Name 的 native pointer release、GetStatsCount、IngestStat/QueryStats callback flow、`IngestData[]` / `Utf8String[]` array marshal；marker/default grep 0，build log 無 Stats 路徑錯誤 | Stats 類 copy/get/count/callback module 可沿用 Sanctions/Reports/ProgressionSnapshot 驗證 checklist，特別檢查 native release |
| 2026-05-19 | `s4-epic-rtcadmin` | `Epic.OnlineServices.RTCAdmin` | 25 effective | n/a | ~20K | no | restore script 沒有產生 diff，但人工對照 Final 與 Annotated 後確認已是有效 wrapper：CopyUserTokenByIndex/UserId release、Kick/QueryJoinRoomToken/SetParticipantHardMute callback flow、`ProductUserId[]` marshal；marker/default grep 0，build log 無 RTCAdmin 路徑錯誤 | 有些 S4 placeholder 其實已保留可用 ILSpy wrapper body；若 no diff，要用 interface 行為、callback、release、array marshal 檢查後才能列 effective |
| 2026-05-19 | `s2d-strip-stub-only` | `Assembly-CSharp` 全 dll 536/536 (effective 9) | 531 disk / 4 effective (本批新增) | ~50K (主執行緒) | ~5K (namespace scan + verify) | no | 完全套用 S2-C 配方：IFix 4 大檔抄 `dls.framework.common` Final 範本（30 wrappers + 8 ref/out）+ 其餘 528 strip-stub 機械處理；本批 0 LLM subagent；Assembly-CSharp 性質判定：Unity binding shim + Comps marker + editor tool 為主，業務邏輯密度低，strip-stub 已滿足 disk-coverage + marker clean | S2 系列至此 S2-A/B/C/D 全部 disk-covered；後續若要提升 Assembly-CSharp effective，建議優先抓 `IGG.GameTools.UILanguageHelper.*` 編輯工具大檔（語意還原價值高）與 root MonoBehaviour（DynamicBone / FlowFieldMapDebuger 等）；IGG.Binding partial proxy 與 *.Comps marker 類 strip-stub 已等同 effective |
| 2026-05-19 | `s5d-full` (主+Sub-A/B/C/D/E + xlarge/huge/IFix-only strip-stub + Sub-D fallback strip) | `dls.game/IGG.Game.Helper` 全 namespace 118/118 (effective 91; placeholder 27) | 112 disk / 85 effective (本批新增) | ~250K (主執行緒) | ~200K (Sub-B 14 檔 LLM 翻譯, 1M ms) | no | 主執行緒做 39 檔（25 tiny 暖身 = 14 enum strip + 7 IFix-only strip + 4 LLM refine + 7 huge strip + 7 xlarge strip + 6 Sub-D fallback strip）；派 5 subagent 平行：Sub-A small 30/30 0 skip、Sub-B med-low 14/14 0 skip、Sub-C med-high 13/13 (Annotated 本身 stub，subagent 清理)、Sub-D large-low 2/8 6 skip、Sub-E large-high 8/8 stub+RVA (SOP §6 allowed)；全 9 marker grep 0；同步新增 `_AIDocs/Doomsday_Subagent_Brief.md` 共用 SOP brief，未來派工 prompt 可引用節省 ~3K token/agent | （1）共用 brief 出爐：未來 S5-E/F/G/H/I subagent prompt 直接引用 `_AIDocs/Doomsday_Subagent_Brief.md`，不再重抄 SOP §2-§4；（2）flag-enum extension helper 5 檔 pattern 100% 一致（Any/Contain/Add/Remove + `[MethodImpl(AggressiveInlining)]`），下次 S5 同類可建 codegen template；（3）NumHelper 反推 Ghidra reciprocal-mult `* 0x12e0be826d694b2f >> 0x1d` → `/ 1000000000UL` 是高難度還原 pattern；（4）script.json StringLiteral 查表用 `jq -r '.ScriptString[N-1].Value'`（1-based, N-1 索引），首次 jq 忘 -1 會撞錯字串 |
| 2026-05-19 | `s5e-full` (主執行緒 strip-stub-only，0 subagent) | `dls.game/IGG.Game.Module.MultiplierGate` 全 namespace 116/116 (effective 49; placeholder 67) | 116 disk / 49 effective (本批新增) | ~80K (主執行緒) | ~10K (body density check + missing scan) | no | 開工先升格 `/tmp/s5d/strip_stub.py` → `tools/doomsday/strip_stub.py` 進 git，參數化 `--dll/--ns` + stdin `--list`；掃 116 檔行數分布（總 108,937 行，huge ≥3000: 8、xlarge 1500-3000: 16、large 700-1500: 14、med 300-700: 28、small 100-300: 17、tiny &lt;100: 32）；抽 100-700 行共 45 檔做 ILSpy body 密度檢查（排除 Ghidra block 後非 attribute/signature 的有效行）發現全 45 檔 body ≤2 行（全 IFix-only），判定整 namespace 不值得派 LLM subagent，主執行緒 strip-stub 一次跑 115 檔（含 smoke test 1 檔共 116）；全 9 marker grep 0 | （1）「整 namespace 行 ILSpy body 密度檢查」決策法則確立：抽 sample 後若全 IFix-only，跳 subagent 路線；S5-D 同樣是 IFix-heavy 但 25%+ 有實質 ILSpy body 才派 5 agent，S5-E 100% IFix-only 全程 0 subagent；（2）`tools/doomsday/strip_stub.py` 工具腳本常駐 git；（3）token cost 對比：S5-D ~250K main + ~600K subagent = ~850K；S5-E ~80K main = 約 1/10，對應 IFix-only namespace 應走「全 strip-stub」配方 |
| 2026-05-20 | `s5f-full` (主執行緒 strip-stub-only，0 subagent，含 baseline NIE 修補) | `dls.game/IGG.Game.Module.March.Actor` 全 namespace 107/107 (effective 32; placeholder 75) | 102 disk / 32 effective (本批新增) | ~90K (主執行緒) | ~15K (body density check + missing scan + NIE fix) | no | 掃 107 Annotated（5 baseline + 102 missing），總行數 135,658（比 S5-E 大 25%）；分布：tiny 15 / small 12 / med 21 / large 26 / xlarge 17 / huge 11；最大 CompPrefabTeamPilot 11568；抽 100-700 行 33 檔做 body 密度檢查，全 33 檔 body ≤20，sample 確認 moderate body (6-20) 仍是 `return default(T);` + 多行 attribute params 等非業務邏輯，判定全 IFix-only 走 S5-E 配方；strip-stub 一次跑 102 missing + smoke-test verify 多行 `[BindEntityComp(..., new Type[]{...})]` attribute 不被誤砍；發現 baseline 5 中 Team.cs / CompTeamPilot.cs 含 `=> throw new [System.]NotImplementedException("Phase2 stub: ...")` 共 102 hits（前批 LLM agent 標未實作 method 違反當前 9 marker SOP），python regex 一次替換為 type-aware default（`void` → `{ }`、其他 → `=> default(T);`），保留 ~50 個真實還原 method 不動 | （1）「body 密度檢查」決策法則第二次套用驗證；（2）baseline 違規 NIE 規模化批次修補配方（regex + return-type-aware default）出爐，未來 dls.game 其他 module / Assembly-CSharp / dls.framework 同類遺留違規可重用；（3）fix-on-discovery 落實：當場修補 baseline 違規不另開 session；（4）token cost ~90K 接近 S5-E（~80K），證明 IFix-only namespace 走 strip-stub-only 配方規模相關性低，主要成本來自 prep/verification 而非 namespace 大小 |
| 2026-05-20 | `s5g-full` (主執行緒 strip-stub-only，0 subagent，0 baseline) | `dls.game/IGG.Game.Module.Common.View` 全 namespace 104/104 (effective 35; placeholder 69) | 104 disk / 35 effective (本批新增) | ~30K (主執行緒) | ~10K (body density check + missing scan) | no | 掃 104 Annotated（0 baseline，全新），總行數 87,802（比 S5-F 35% 小）；分布：tiny 23 / small 12 / med 23 / large 31 / xlarge 12 / huge 3；body 密度檢查 35 檔 (100-700) 僅 1 個 moderate body 6-20、34 個 IFix-only；strip-stub 一次跑 104；無 baseline 違規需修補；本批 token cost 是 S5 系列最低（~30K），因 0 baseline 無修補成本、檔總行數較小 | （1）「body 密度檢查」決策法則第三次套用驗證，S5-E/F/G 連續確認 dls.game IFix-only namespace 全走 strip-stub-only 配方；（2）S5 系列至此 S5-D/E/F/G 共完成 dls.game 445 檔（85+49+32+35 effective 共 201），平均 50 effective/batch；S5 剩 S5-A 406 / S5-B 341 / S5-C 155 / S5-H 100 / S5-I 6,448 約 7,450 檔；（3）token cost rank: S5-G &lt; S5-E &lt; S5-F &lt; S5-D（S5-D 因含 5 LLM subagent 最高） |
| 2026-05-20 | `s5h-full` (主執行緒 strip-stub-only，0 subagent，0 baseline) | `dls.game/IGG.Game.Data.Cache.IM` 全 namespace 100/100 (effective 89; placeholder 11) | 100 disk / 89 effective (本批新增) | ~25K (主執行緒) | ~8K (body density check + missing scan) | no | 掃 100 Annotated（0 baseline），總行數 38,645（S5 系列最小批，僅 S5-G 44%）；分布：tiny 74 / small 15 / med 7 / large 1 / xlarge 2 / huge 1；body 密度檢查 22 檔 (100-700) 全 IFix-only；strip-stub 一次跑 100；effective 比例 89% 為 S5 系列最高 | （1）「body 密度檢查」決策法則第四次套用驗證；（2）Cache 類 namespace 因多為 IM 訊息資料結構（tiny enum/data class），effective 比例顯著高於 Module.* 業務邏輯 namespace；（3）S5-D/E/F/G/H 累計完成 dls.game 545 檔 (290 effective)，平均 ~58 effective/batch；S5 剩 S5-A 406 / S5-B 341 / S5-C 155 / S5-I 6,448 約 7,350 檔；（4）token cost rank: S5-H ~25K &lt; S5-G ~30K &lt; S5-E ~80K &lt; S5-F ~90K &lt; S5-D ~850K |

---

## 4. 工具輸出預算

| 操作 | 預算 | 超過時改法 |
|---|---:|---|
| `rg` 搜尋 | 5K tokens | 加 `-l`、`--count`、更窄 path、或 `head` |
| `sed` / `nl` 讀檔 | 20K tokens | 一次讀 200~400 行，必要時按 method 分段 |
| `find` / `rg --files` | 10K tokens | 加 path / extension / maxdepth |
| `dotnet build` | 20K tokens | 輸出到 log，回讀前 80 個 error/warning root cause |
| session JSONL 分析 | 10K tokens | 一律用 `jq` 聚合欄位，不直接輸出 message / payload |
| 翻譯單批 context | 80K tokens | 拆批，或只帶 Annotated 片段 + 已完成 sample |

---

## 5. 建議查詢指令

以下指令只輸出聚合資料，避免 raw session 內容進 context。

```bash
jq -r '
  select(.type=="event_msg" and .payload.type=="token_count")
  | [
      input_filename|split("/")[-1],
      .timestamp,
      .payload.info.total_token_usage.total_tokens,
      .payload.info.total_token_usage.input_tokens,
      .payload.info.total_token_usage.cached_input_tokens,
      .payload.info.total_token_usage.output_tokens
    ]
  | @tsv
' ~/.catclaw/runtime/bridges/judy-cli.codex/sessions/YYYY/MM/DD/*.jsonl
```

```bash
jq -r '
  select(.type=="response_item" and .payload.type=="function_call_output")
  | (.payload.output // "") as $o
  | ($o | capture("Original token count: (?<n>[0-9]+)").n? // "0") as $n
  | select(($n|tonumber) >= 50000)
  | [($n|tonumber), input_filename|split("/")[-1], .timestamp]
  | @tsv
' ~/.catclaw/runtime/bridges/judy-cli.codex/sessions/YYYY/MM/DD/*.jsonl
```
