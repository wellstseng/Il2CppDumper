# Doomsday Annotated 產出計畫（S0）

> 建立日期：2026-05-17
> **方法論**：ILSpy skeleton + Ghidra pseudocode → 產生 `Annotated/` 對照資料
> **界線**：本文件只描述 S0 的 `Annotated/` 生成；Phase2 `Final/` 還原不走程式/腳本翻譯，依 `Doomsday_Phase2_SOP.md` 由人工/LLM 處理
> 參考：Launcher_Archiver 留下的 `annotate_with_pseudocode.py` 已驗證此 pipeline

---

## 1. 目標

把 `Input/Doomsday.zip` 內的 IGG Doomsday: Last Survivors（Unity IL2CPP 二進位）完整還原成人類可讀的 C# source tree，產出物落在 `Input/Doomsday/RestoredSolution/Annotated/`。

「完整還原」定義：
- ✅ **所有業務 type** 的結構 / signature / property / field — 來自 ILSpy 反編譯
- ✅ **所有業務 method body** — 以 `/* === Ghidra pseudocode RVA 0xXXX === ... */` 區塊註解嵌入 method body 內
- ❌ **不還原** Unity stock / mscorlib / BCL / 純第三方 SDK（Wwise / Firebase / AWSSDK / DOTween / Castle / Newtonsoft / Cinemachine / spine 等）

---

## 2. 規模實況（已掃描確認）

| 指標 | 實際值 |
|------|--------|
| `dump.cs` | **290 萬行（110 MB）** |
| 總 ScriptMethod | **636,778** |
| 業務 method（要還原） | **304,436**（48%） |
| 排除（Unity / BCL / SDK） | 277,868 |
| 排除（compiler-generated） | 47,460 |
| 排除（global 無特徵） | 7,014 |
| 業務 DLL 數 | 25（從 128 個 DummyDll 篩出） |

業務 namespace 分布（前 10 大）：
| Namespace | Method 數 |
|-----------|----------|
| Protomsg | 91,223 |
| IFix | 9,934 |
| IGG.Game.Module.Activity.View | 8,218 |
| IGG.Game.Data.Config | 7,982 |
| (global) | 6,651 |
| behaviac | 4,821 |
| protomsg | 2,556 |
| IGG.Game.Module.March.Actor | 2,540 |
| IGG.Game.UI.Activity | 2,452 |
| Epic.OnlineServices | 2,005 |

> 確認專案為 **IGG Doomsday: Last Survivors**（IGG Games 香港）。

---

## 3. 方法論：產出 Annotated 對照資料

```
ILSpy 反編譯 25 個業務 DLL
   ↓
RestoredSolution/_raw/<dll>/<Type>.cs   每 type 一個 .cs，含 [Address(RVA="0x...")] attribute
                                         method body 是 throw null;

Ghidra 載入 GameAssembly.dll + Il2CppDumper 自動化腳本標符號
   ↓
跑 ExportPseudocode.java（吃 _target_rvas.tsv 30 萬筆 RVA）
   ↓
pseudocode/<RVA_hex>__<method_name>.c   每個 method 一個 .c 檔，Ghidra 反編譯結果

   ↓ annotate_with_pseudocode.py 合併對照資料
        - regex 抓 [Address(RVA="0x...")] 的 RVA
        - 查 pseudocode/{RVA_hex}__*.c
        - 用 /* === Ghidra pseudocode === */ 區塊註解貼到 method body 內最前面

RestoredSolution/Annotated/<dll>/<Type>.cs   每 method 有完整 Ghidra pseudocode 註解
```

成本：**$0 LLM token**。此處只產生 Annotated，不代表 Final 可用程式批次翻譯。

---

## 4. Sprint 拆分

### S0：Annotated 生成（必做、~1-2 天）

| 步驟 | 動作 | 狀態 | 執行者 |
|------|------|------|--------|
| 0-1 | 解壓 Doomsday.zip → `Input/Doomsday/` | ✅ 完成 | AI |
| 0-2 | Il2CppDumper → dump.cs / DummyDll / script.json | ✅ 完成 | AI |
| 0-3 | `Input/Doomsday/_scripts/select_targets.py` → `_target_rvas.tsv` (304,436 行) | ✅ 完成 | AI |
| 0-4 | `Input/Doomsday/_scripts/ExportPseudocode.java`（路徑改 Doomsday） | ✅ 完成 | AI |
| 0-5 | `Input/Doomsday/_scripts/decompile_dummydll.sh` 跑 ilspycmd 反編譯 25 dll → `RestoredSolution/_raw/` | 🟡 進行中 | AI |
| 0-6 | Ghidra GUI 載入 GameAssembly.dll + global-metadata.dat，跑 Il2CppDumper 自動腳本標符號（首次分析 8-12h，要分配 24GB JVM heap） | ⏳ 待使用者 | **使用者** |
| 0-7 | Ghidra Script Manager 跑 `ExportPseudocode.java` 批次匯出 pseudocode（30 萬 method 估 4-12h） | ⏳ 待使用者 | **使用者** |
| 0-8 | 改 `annotate_with_pseudocode.py` 路徑生成 `RestoredSolution/Annotated/` | 待 | AI |
| 0-9 | 寫 `RestoredSolution/_NOTES.md` 統計：annotated/skipped 數、命中率 | 待 | AI |

**S0 通過條件**：
- [ ] `_target_rvas.tsv` 304,436 行（已達成 ✅）
- [ ] `_raw/` 內每個業務 DLL 都有對應目錄與 .cs 檔
- [ ] `pseudocode/` 內 .c 檔數 ≥ target_rvas × 0.85（Ghidra 解析失敗率 < 15%）
- [ ] `Annotated/` 內 method annotation 命中率 ≥ 80%

---

### S1+：LLM 高品質翻譯（按需、可選、不在預設範圍）

S0 完成後使用者就有「完整可讀」的成品（雖然 method body 是 Ghidra pseudocode 風格）。

如果某個特定 class / 模組需要更高可讀性（變數重命名、modern C# 改寫），再開 S1+ 針對性處理：
- 使用者指定範圍（例：「`IGG.Game.Module.March.Actor` 整個 namespace」）
- AI 用 LLM 把該範圍 pseudocode → 漂亮 C#
- 成本與範圍成正比（按需付費）

S1+ 沿用 Launcher 之前確立的還原規則（見附錄 B）。

---

## 5. 時程與成本（修正版）

| 項目 | 估值 |
|------|------|
| AI 工作量 | < 2 小時 wall clock |
| 使用者投入 | Ghidra 載入分析 8-12h + Export 4-12h ≈ **12-24h 機器 IO** |
| **總 wall clock** | **1-2 天** |
| **LLM token 成本** | **$0** |
| Session 數 | **1**（S0 即可全部完成） |

> 註：先前計畫文件的「$6K-$50K / 3-6 個月」是把 S0 Annotated 生成誤讀成 LLM-per-method 翻譯造成的高估，已修正。

---

## 6. 風險與緩解

| 風險 | 影響 | 緩解 |
|------|------|------|
| Ghidra 32GB RAM 跑 200MB binary 會 swap | 分析時間拉長 | 配 24GB JVM heap、關閉其他程式 |
| Ghidra Export 30 萬 method 估計需 4-12h | 使用者要等 | 可分批跑（先 dls.game 範圍 RVA） |
| pseudocode 解析失敗率高（> 30%） | 部分 method 無 body | annotate 腳本自動 skip，無 body 的 method 保留 `throw null;` |
| ilspy 對某些 DLL 反編譯失敗 | 部分 DLL 缺 skeleton | 從 `_decompile.log` 找錯誤逐個處理 |

---

## 7. 目錄結構

```
Input/Doomsday/
├── GameAssembly.dll              # IL2CPP 二進位（200 MB）
├── global-metadata.dat           # 63 MB
├── NEP2.dll                      # 暫不處理
├── UnityPlayer.dll               # 暫不處理
├── _scripts/                     # 專案專屬工具鏈
│   ├── select_targets.py         # ScriptMethod → RVA 白名單
│   ├── ExportPseudocode.java     # Ghidra script，批次匯出 pseudocode
│   └── decompile_dummydll.sh     # ilspycmd 批次反編譯
├── output/                       # Il2CppDumper 產物
│   ├── dump.cs                   # 290 萬行
│   ├── DummyDll/                 # 128 個
│   ├── il2cpp.h
│   ├── script.json
│   ├── stringliteral.json
│   ├── _target_rvas.tsv          # 304,436 行（業務 method RVA）
│   └── pseudocode/               # S0-7 產出
│       └── <RVA_hex>__<method>.c
└── RestoredSolution/
    ├── _raw/                     # S0-5 產出（ILSpy 反編譯）
    │   └── <dll>/<Type>.cs
    └── Annotated/                # S0-8 產出（機械合併成品）
        └── <dll>/<Type>.cs       # 每 method 內含 Ghidra pseudocode 註解
```

---

## 附錄 A：S0-6 / S0-7 使用者操作指引

1. 安裝 Ghidra（如已安裝跳過）：
   - 從 https://ghidra-sre.org/ 下載 11.x（需要 JDK 17+）
   - macOS 上設定 JVM heap：編輯 `support/launch.properties` → `VMARGS_LINUX_MAC=-Xmx24G`

2. 建立專案：
   - File → New Project → Non-Shared Project
   - 命名 `Doomsday`，放在你任意位置

3. Import：
   - File → Import File → `Input/Doomsday/GameAssembly.dll`
   - Format: Portable Executable (PE) — 自動偵測即可

4. 第一次 Auto-Analyze：
   - 雙擊匯入的 program 開 CodeBrowser
   - 接受預設分析選項（Decompiler Parameter ID 開啟）
   - 等 1-3 小時完成基本分析

5. 套用 IL2CPP 符號：
   - Window → Script Manager
   - 加入 `Input/Doomsday/output/` 為 script directory
   - 找到 `ghidra_with_struct_auto.py`（Il2CppDumper 產的）→ Run
   - 等 4-8 小時套完 30 萬個符號 + struct

6. 匯出 pseudocode：
   - Script Manager → 加入 `Input/Doomsday/_scripts/` 為 script directory
   - 找到 `ExportPseudocode.java` → Run
   - 進度會印在 console，估 4-12 小時
   - 完成後 `Input/Doomsday/output/pseudocode/` 會有 ~30 萬 .c 檔

7. 完成後通知 AI，由 AI 接 S0-8（annotate 合併）

---

## 附錄 B：S1+ LLM 翻譯規則（沿用 Launcher）

按需才執行。每個 type 做：
1. 讀 `Annotated/<dll>/<namespace>/<Type>.cs`（已含 pseudocode 註解）
2. 對每個 method：把 pseudocode 翻譯成可讀 C#
   - 刪除 `/* === Ghidra pseudocode === */` 區塊
   - method body 寫不出來時：`throw new NotImplementedException(/* RVA: 0xXXXXX */);` + `// TODO: pseudocode 不夠清楚`
   - 變數命名拋棄 `lVar1` / `uVar9` / `local_58`，改用語義名
   - 用 modern C#（using var / pattern match / null-conditional / nameof）
   - 跳過 nested compiler-generated class（class 名含 `<>c__` 或 `<>d__`）
3. 輸出到 `Final/<dll>/<namespace>/<Type>.cs`
