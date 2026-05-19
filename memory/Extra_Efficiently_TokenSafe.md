# 決策記憶 — 效率與 Token 節省

> 三層分類系統定義見全域 `~/.claude/CLAUDE.md`。
> [固] = 跨 session 永久；[觀] = 反覆模式觀察中；[臨] = 當前任務暫存。

---

## 工程決策

### [臨] 知識庫優先原則 — 能查就不要 LLM 處理（2026-05-19）

- **規則**：凡能用知識庫（`_AIDocs/`、`memory/`、`script.json`、已完成 Final 樣本）查到的事實，一律直接讀檔引用，**不**丟給 LLM agent 用 token 重新推理／翻譯／統計。
- **Why**：使用者 2026-05-19 在 S5 派工討論前明確指示「可以用知識庫查的就不要用LLM處理 節省token」。Phase2 翻譯工作 token 成本敏感（見 `_AIDocs/Token_Cost_Ledger.md`），重複用 LLM 推導已存在的事實是純浪費。
- **How to apply**：
  - StringLiteral 索引解析 → 直接讀 `script.json` 的 `ScriptString[N-1]`，不要請 agent 「推測語意」
  - IFix wrapper / Protobuf descriptor / Reflection stub 樣式 → 直接抄已驗證的 Final 範本（如 `dls.im/IFix/*`、`dls.framework.common/IFix/*`），不要逐檔 LLM 翻譯
  - 翻譯硬規則 / SOP / 風格範本 → 直接引用 `_AIDocs/Doomsday_Phase2_Progress.md §5/§6`、`Translation_SOP_TokenSafe.md`，不要重述
  - 派 subagent 時，prompt 內優先給檔案路徑＋查表規則，再給 Annotated 內容；agent 應「查表→翻譯」而非「LLM 推導→翻譯」

---

## 演化日誌

| 日期 | 記憶 | 變更 |
|------|------|------|
| 2026-05-17 | 知識庫建立 | 透過 `/init-project` 初始化 _AIDocs 與記憶工作流 |
