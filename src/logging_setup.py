"""日誌：同時印在終端機，並累加存進 DATA_DIR/agent.log（超過 1 MB 自動換檔，保留 5 份）。

只記「發生了什麼」：誰、什麼時候、哪一類、成功或失敗、花多久。
不記 DISCORD_TOKEN；使用者打的字與模型回傳內容只記前幾十個字，避免日誌檔變成第二份完整紀錄。
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path

JST = timezone(timedelta(hours=9))
FORMAT = "%(asctime)s %(levelname)-7s %(name)s | %(message)s"
LOG_NAME = "agent.log"


def preview(text: str, limit: int = 60) -> str:
    """把一段文字縮成單行、最多 limit 字，給日誌用。"""
    flat = " ".join(str(text).split())
    return flat if len(flat) <= limit else flat[:limit] + "…"


def setup_logging(data_dir: Path, level: int = logging.INFO) -> Path:
    data_dir.mkdir(parents=True, exist_ok=True)
    log_path = data_dir / LOG_NAME

    formatter = logging.Formatter(FORMAT, datefmt="%Y-%m-%d %H:%M:%S")
    formatter.converter = lambda ts: datetime.fromtimestamp(ts, JST).timetuple()  # 時間用日本時間

    console = logging.StreamHandler()
    file = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=5, encoding="utf-8")
    for handler in (console, file):
        handler.setFormatter(formatter)

    root = logging.getLogger()
    for old in list(root.handlers):  # 重複呼叫時不要重複輸出
        root.removeHandler(old)
    root.setLevel(level)
    root.addHandler(console)
    root.addHandler(file)

    # discord.py 本身很吵，只留警告以上；連線成功與否由我們自己的 on_ready 記錄
    logging.getLogger("discord").setLevel(logging.WARNING)
    return log_path
