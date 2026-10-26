"""啟動入口：uv run python -m src.main

四段安全防護位置（行數會隨修改略有出入，用搜尋 "==== 防護" 最準）：
  防護 1  claude -p 的檔案範圍隔離        src/claude_runner.py 第 61～68 行
  防護 2  上傳者的字只當資料              src/claude_runner.py 第 70～78 行
  防護 3  檔名清洗，避免路徑亂跑          src/photo_store.py   第 22～36 行
  防護 4  Excel 開頭 = + - @ 轉純文字     src/excel_store.py   第 27～31 行
"""
from __future__ import annotations

import logging
import sys

from .bot import TravelBot
from .config import ConfigError, load_config
from .excel_store import ExcelStore
from .logging_setup import setup_logging


def main() -> int:
    # Windows 終端機常用 cp950，印 ⏳ ⚠️ 之類的符號會出錯；改成印不出來就用 ? 代替
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(errors="replace")

    try:
        config = load_config()
    except ConfigError as exc:
        print(f"設定有問題：{exc}", file=sys.stderr)
        return 1

    log_path = setup_logging(config.data_dir)  # 終端機顯示，同時累加存進 DATA_DIR/agent.log
    log = logging.getLogger("main")
    log.info("啟動：頻道=%s 模型=%s 資料夾=%s 日誌=%s",
             config.channel_id, config.claude_model, config.data_dir, log_path)
    bot = TravelBot(config, ExcelStore(config.excel_path))
    bot.run(config.discord_token, log_handler=None)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
