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
