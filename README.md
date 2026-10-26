# 東京智慧旅遊全能助手 (Tokyo Travel Agent)

住在 Discord 裡的東京自由行助手。在指定頻道傳文字或照片，它用 `claude -p` 分析（日語翻譯 / 精品比價 / 地鐵導航 / 藥妝辨識），回覆在原訊息底下，並把每次結果記進一個 Excel。

設計依據見 [`docs/architecture.md`](docs/architecture.md)，需求見 [`docs/requirements.md`](docs/requirements.md)。

## 安裝與啟動

需要：Python 3.12、[uv](https://docs.astral.sh/uv/)、已登入的 Claude Code（`claude` 指令在 PATH 裡）。

```
uv sync
copy .env.example .env      # 然後用記事本填入 .env 的真值
uv run python -m src.main
```

Discord 端的設定見 [`docs/discord-server-setup.md`](docs/discord-server-setup.md) 和 [`docs/discord-bot-setup.md`](docs/discord-bot-setup.md)。

跑自動測試：

```
uv run pytest
```

## .env 設定

| 項目 | 說明 |
|---|---|
| `DISCORD_TOKEN` | bot 的密碼。**絕對不能公開、不能 commit。** |
| `CHANNEL_ID` | Agent 只聽這一個頻道 |
| `CLAUDE_MODEL` | 傳給 `claude -p --model` 的模型名稱，例如 `haiku`、`sonnet` |
| `DATA_DIR` | 資料夾。相對路徑以專案資料夾為基準，預設 `./data` |

`.env` 與 `data/`（照片、Excel）都已列在 `.gitignore`，**不要刪掉那幾行**。

## 資料放在哪

```
data/
  records.xlsx    ← 紀錄，一直往下加
  photos/         ← 照片，檔名：2026-10-26 14-05-12 藥妝辨識KEFLEX眼藥水.jpg
  agent.log       ← 日誌，累加記錄（超過 1 MB 自動換檔，保留 5 份）
  pending.jsonl   ← 只有 Excel 被你開著寫不進去時才會出現，下次寫入成功會自動補上
```

Excel 被你開著時，終端機會印出 ⚠️ 警告並重試；請關掉 Excel，資料不會遺失。

## 日誌

處理資料的每個階段都會印在終端機，同時累加存進 `data/agent.log`（日本時間）：收到訊息（誰、文字開頭、幾張照片）→ 排隊（佇列長度）→ 輪到處理 → `claude -p` 回傳（字數、耗時）→ 解析結果（類別、品名）→ 照片存檔位置 → Excel 寫入第幾列 → 已回覆 → ✅／❌。失敗、Excel 被占用重試、防護被觸發（檔名被清洗、儲存格被轉純文字、疑似注入）都會以警告記下來。

為了不讓日誌變成第二份完整紀錄，使用者打的字與模型回傳內容只記前面約 60 字；`DISCORD_TOKEN` 不會出現在日誌裡。完整內容看 Excel。`agent.log` 在 `data/` 底下，同樣不會被 commit。

## 四段安全防護在哪裡

每一段都用下面這種註解包起來，可以單獨整段註解掉來對照效果（預設全部開啟）：

```python
# ==== 防護 N：說明 開始 ====
...
# ==== 防護 N 結束 ====
```

| 防護 | 做什麼 | 位置 |
|---|---|---|
| 1 | `claude -p` 只能碰到「只放這一張照片」的暫存資料夾，碰不到 `data/` | `src/claude_runner.py` 第 61～68 行 |
| 2 | 上傳者打的字只當資料（走 stdin、包在標籤裡），不接進指令 | `src/claude_runner.py` 第 70～78 行 |
| 3 | 品名當檔名前，清掉 `/ \ .. :` 等會讓路徑亂跑的字 | `src/photo_store.py` 第 22～36 行 |
| 4 | Excel 文字以 `= + - @` 開頭時轉成純文字 | `src/excel_store.py` 第 27～31 行 |

修改程式後行數會變動，用搜尋 `==== 防護` 最準。

怎麼設計成「整段註解掉也能跑」：每個檔案先寫一份「沒有防護時的預設值」，防護區塊再把它改成安全版本。

## 目前沒有做的事

這一版比 `docs/architecture.md` 簡單：沒有白名單／邀請碼／每日額度、沒有長期記憶、沒有 `/匯出`、`/清除`、沒有 English 模式；所有人共用同一份 Excel 和同一個照片資料夾，彼此看得到。

## 提醒

- 每分析一次就會用掉你自己的 Claude 額度；頻道裡的人可以一直傳，請只把 bot 放在自己信任的伺服器。
- 精品價格、地鐵路線都是模型的回答，可能有誤；回覆裡有來源和日期就看來源，沒有就當參考。
