# Translation SOP Token-Safe

> 目的：讓 Doomsday Phase2 `Annotated -> Final` 還原流程少燒 token、少返工、少互相覆蓋。
> 權威翻譯規則仍以 `memory/_staging/Doomsday_Phase2_SOP.md` 與 `Doomsday_Phase2_Progress.md` 為準；本文件只管 token-safe 工作流。
> 最近更新：2026-05-19

---

## 1. 開工入口

每批只讀這些：

1. `_AIDocs/_INDEX.md`
2. `_AIDocs/Doomsday_Phase2_Progress.md`
3. `memory/_staging/Doomsday_Phase2_SOP.md`
4. 若遇到 IFix fast-path，再讀 `_AIDocs/Doomsday_IFix_Hotpatch.md`
5. 只讀本批對應的 Annotated 檔與少量 Final sample

不要一開始讀整個 `_AIDocs/`、整個 `Input/Doomsday/`、整個 session log。

---

## 2. 批次大小

| 檔案類型 | 建議批次 | 理由 |
|---|---:|---|
| enum / interface / pure DTO | 20~50 檔 | 低風險、context 小 |
| 一般 class | 5~15 檔 | 需要對照 fields / methods |
| 大型 manager / cache | 1~3 檔 | pseudocode 長，容易爆 context |
| IFix / unsafe runtime | 1~5 檔 | 指標與 runtime convention 高風險 |
| build 失敗修復 | 只處理同一 error cluster | 避免把全專案錯誤混進單批 |

單檔超過 1500 行時，不要整檔讀進來；改用 method / property 分段。

---

## 3. 標準流程

| 階段 | 動作 | Token-safe 做法 | 產出 |
|---|---|---|---|
| 1. 選範圍 | 從進度表挑未認領範圍 | 先列檔名與行數，不讀內容 | batch 名稱與檔案清單 |
| 2. 掃概況 | 判斷檔案類型 | `rg -n "class|struct|enum|interface|IsPatched|Ghidra"` 限定檔案 | 分類：simple / normal / complex |
| 3. 精讀 | 讀 Annotated 片段 | `sed -n` 一次 200~400 行 | 只帶必要 pseudocode |
| 4. 還原 | 寫 Final | 一檔一檔處理，不用整 dll context | mirror path Final |
| 5. 驗收 | marker / stub / build 摘要 | grep 只看本批檔案，build log 只取 root cause | 驗收結果 |
| 6. 記錄 | 更新進度與成本 | 補 `_AIDocs/Token_Cost_Ledger.md` | 可追蹤 batch |

---

## 4. 禁止模式

| 禁止 | 原因 | 改用 |
|---|---|---|
| `rg <keyword> Input/Doomsday` 直接掃全樹 | 可能吐數十萬到數百萬 token | 先限定 dll / path，再 `-l` |
| `cat` 大檔 | 無法控制輸出 | `sed -n 'start,endp'` |
| 全專案 build log 直接進 context | warning / dependency error 會淹沒 root cause | build 到 log，再 `rg -n "error|warning" log | head` |
| 一次認領整個大 dll | 容易上下文爆炸與品質下降 | 依檔案類型切批 |
| 完成前只看檔案存在 | 容易把空殼當完成 | 必跑 marker/stub 檢查 |
| 從 pseudocode 猜 StringLiteral 真值 | 容易 hallucination | 查 `script.json` 對應 `ScriptString[N-1]` |

---

## 5. 必跑驗收

每批完成後，至少跑以下檢查。檢查範圍必須是本批檔案清單，不要掃整個 `Input/Doomsday`。

```bash
rg -n "Il2CppDummyDll|\\[Token|\\[Address|\\[FieldOffset|Ghidra:|FUN_180|StringLiteral_|return default;|NotImplementedException" <batch-final-files>
```

若是 C# 語法或 build 檢查：

```bash
dotnet build <target>.csproj > /tmp/doomsday-build.log 2>&1
rg -n "error CS|warning CS|Build FAILED|建置失敗" /tmp/doomsday-build.log | head -80
```

回報時只貼 root cause，不貼完整 log。

---

## 6. Batch 記錄模板

```markdown
## Batch: <name>

- 日期：
- 範圍：
- 檔案數：
- 讀取文件：
- 驗收：
  - marker grep：
  - build / syntax：
  - skip：
- Token 成本：
  - total tokens：
  - 最大工具輸出：
  - 成本原因：
- 後續限制：
```

---

## 7. Annotate / Mapping 建議

若要建立 `Annotate/`，建議只放索引型文件，不放長篇全文：

```text
Annotate/
  glossary.md
  file-map.md
  dll-batch-map.md
  translation-style.md
  token-budget.md
```

每個 mapping 都應該回答「這批任務要讀哪些最少文件」，而不是把背景知識全部塞入 context。

