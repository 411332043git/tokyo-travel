# Tokyo Travel Agent

住在 Discord 裡的東京自由行助手：同行的少數人傳文字或照片，Agent 用 `claude -p` 做日語翻譯、精品台日比價、地鐵導航、藥妝辨識，並把結果累加記進每人自己的 Excel。

## 開始任何工作前

先讀 `docs/architecture.md`（架構與決策依據），需求原文在 `docs/requirements.md`。

## 四段安全防護

四段防護（見 architecture.md 第 12 節）寫在用到它的地方（`src/claude_runner.py`、`src/photo_store.py`、`src/excel_store.py`），位置見 README，搜尋 `==== 防護` 即可找到。每段都要用清楚的註解標出開始與結束：

```python
# ==== 防護 N：說明 開始 ====
...
# ==== 防護 N 結束 ====
```

- 防護 1：claude -p 讀不到 DATA_DIR 裡別人的照片和紀錄
- 防護 2：上傳者打的字只當資料，不當指令
- 防護 3：品名當檔名前，清掉 `/ \ .. :` 等會讓路徑亂跑的字
- 防護 4：寫進 Excel 的文字若以 `= + - @` 開頭，轉成純文字

**一開始四段全部開啟。** 教學用的開關預設為開，不可以在沒有明確要求時關掉。

## 不可以 commit

- `.env`（含 `DISCORD_TOKEN`，絕對不能公開）
- DATA_DIR 裡的所有內容：使用者照片、Excel、記憶檔
- 只提交 `.env.example`（只列項目名稱，不寫真值）
