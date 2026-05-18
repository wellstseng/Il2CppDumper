# Doomsday Phase 2 — restore_phase2.py + phase2_ghidra_translator.py 機械翻譯工具鏈

- Scope: project
- Confidence: [固]
- Trigger: Doomsday Phase 2, Annotated→Final, restore_phase2.py, 機械翻譯, dls.im, dls.config, dls.message, USDK.Windows, Epic, dls.framework, protomsg, IFix fast-path
- Last-used: 2026-05-18
- Confirmations: 1
- Type: reference

- Related: workflow-rules

## 知識

- [固] 位置：`tools/restore_phase2.py`（已 commit 進 git，commit `a697ab6`）
- [固] 用途：批量機械翻譯 `Input/Doomsday/RestoredSolution/Annotated/<dll>/*.cs` → `Final/<dll>/*.cs`，避免手翻或派 LLM agent 一檔檔做（後者已多次撞 context limit 留空殼）

## 三種執行模式

```bash
# dry-run（無旗標）：只印分類統計與樣本
python3 tools/restore_phase2.py <dll>

# 寫 preview 到 memory/_staging/phase2_mechanical_preview/<dll>/
python3 tools/restore_phase2.py <dll> --write-preview

# 直寫 Final/<dll>/（主要用法）
python3 tools/restore_phase2.py <dll> --apply
```

## 自動分類（classify）

| status | 處理 | 寫 Final？ |
|---|---|---|
| skip | IFix build artifact / AssemblyInfo / UnitySourceGenerated | 不寫 |
| mechanical-ok | 純 enum / interface / 空容器類 | 寫（transform 後） |
| mechanical-protobuf-stub | `IMessage<>` + Google.Protobuf 訊息類，從 fields 重生 v3 標準模板 | 寫（generate_protobuf） |
| mechanical-review | 含 Ghidra 但 method body 已被 enhance 補實 | 寫（transform 後） |
| needs-llm | ILSpy 整檔無法反編譯，body 全空 | 寫 transform 後（restore Ghidra）+ `phase2_ghidra_translator.translate_file()` 保守白名單翻譯 method body：可決定性對應翻成 C#，剩餘行 wrap 為 `// Ghidra:` 註解。前提：**不加油添醋**（SOP §6） |

## protobuf 模板生成範圍

`generate_protobuf()` 從 Annotated 的 fields 與 enum 表，重生：Parser/FullName/Clone/Equals/GetHashCode/WriteTo/CalculateSize/MergeFrom/`pb_003A_003AGoogle_002EProtobuf_002EIMessage_002EFullName`。wire type 自動推斷：string/ByteString/uint32/uint64/int32/int64/bool/float/double/enum/message + RepeatedField。

## 已知邊界 case 與修補

- `[Il2CppDummyDll.Token/Address/FieldOffset(...)]` fully-qualified attribute 形式也會被砍（ATTR_RE 涵蓋）
- 純容器類（只有 class declaration 無 method）不被誤判為 empty-body-remains
- `restore_unhandled_blocks()` 在 needs-llm 路徑下會**啟用**（依 SOP §6 腳本翻譯例外，把 Ghidra pseudocode 保留在 method body 內當參考；非 needs-llm 路徑同樣啟用，補實 ctor / property 等少數空 body 場合）

## phase2_ghidra_translator.py 翻譯 pipeline（needs-llm 路徑）

1. 抽 field offset → name/type 表（從 Annotated.cs `[FieldOffset(Offset="0xN")]`）
2. 拆 Ghidra 區塊（`/* === Ghidra ... === end pseudocode === */`）
3. unwrap → strip function header → merge 跨行 statement
4. strip static init guard / IFix fast-path / runtime helpers（FUN_18055b140/a480/b3e0/class_init）
5. 合併 alloc + ctor + offset 三步為 `_field = new Type();`
6. line-level translate：field 讀取 `*(T*)(this+0xN)` → `_fieldName`、stdlib 白名單（Dictionary/List 的 ContainsKey/get_Item/Add/Remove/set_Item/Count/Clear/Contains）、變數歸一 uVar/lVar → v1/v2、param_1 → this/param_N → 參數名、hex 字面量
7. 未識別行 wrap 為 `// Ghidra: <原文>`（保持忠實，不發明）

## 戰績

- dls.im 380 → Final 374（commit `a697ab6` → `a7812ac` → `e1eaafa`，2026-05-18）
  - 271 protobuf-stub + 43 mechanical-ok + 3 mechanical-review + 57 needs-llm + 6 skip
  - needs-llm 路徑：94/96 method 成功翻譯為可讀 C#，例如 `ChatData.cs` 8218 → 4094 行
  - marker grep 在 mechanical-* 314 檔=0；needs-llm 含 `// Ghidra:` 註解為設計

## 後續使用建議

- 下個 dll 接續：dls.config (2,946) / USDK.Windows (1,776) / Epic (1,698) / dls.message (7,867) 都是純未開始
- 流程：dry-run → --apply → grep marker / comm 檔數 / 抽 10 檔 → 更新 `_AIDocs/Doomsday_Phase2_Progress.md` §1 + §9 → commit（中文 log）
- 遇到新邊界 case（誤分類 / 漏砍 marker）按 fix-on-discovery 順手補強腳本一併 commit
