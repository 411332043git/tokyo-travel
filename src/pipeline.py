"""一則工作從頭到尾：分析 → 檢查 → 存照片 → 記 Excel → 組回覆。不碰 Discord，方便測試。"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Awaitable, Callable

from .claude_runner import ClaudeError, Image, analyze as claude_analyze
from .config import Config
from .excel_store import ExcelStore
from .logging_setup import preview
from .photo_store import save_photo
from .replies import FAILURE_TEXT, format_reply
from .schema import AnalysisError, parse_analysis

log = logging.getLogger(__name__)
JST = timezone(timedelta(hours=9))  # 日本沒有夏令時間，固定 +9 即可
NO_PHOTO = "（無照片）"

AnalyzeFn = Callable[[Config, str, "Image | None"], Awaitable[str]]


@dataclass(frozen=True)
class Result:
    reply: str
    ok: bool


async def process(
    config: Config,
    store: ExcelStore,
    uploader: str,
    text: str,
    image: Image | None = None,
    analyze: AnalyzeFn = claude_analyze,
    now: Callable[[], datetime] = lambda: datetime.now(JST),
) -> Result:
    log.info("開始分析 上傳者=%s 文字=%r 照片=%s 模型=%s",
             uploader, preview(text), f"{len(image.data) // 1024} KB" if image else "無", config.claude_model)
    started = time.monotonic()
    raw = ""
    try:
        raw = await analyze(config, text, image)
        log.info("claude -p 回傳 %d 字，耗時 %.1f 秒", len(raw), time.monotonic() - started)
        result = parse_analysis(raw)
    except ClaudeError as exc:
        log.warning("分析失敗（claude -p 沒給出結果，耗時 %.1f 秒）：%s", time.monotonic() - started, exc)
        return Result(FAILURE_TEXT, ok=False)
    except AnalysisError as exc:
        log.warning("分析失敗（回傳格式不對）：%s｜原始內容開頭：%r", exc, preview(raw, 120))
        return Result(FAILURE_TEXT, ok=False)
    log.info("解析成功 類別=%s 品名=%r", result.category, preview(result.title))

    when = now()
    photo_location = NO_PHOTO
    if image is not None:
        try:
            saved = save_photo(config.photos_dir, image.data, when, result.category, result.title, image.ext)
            photo_location = saved.relative_to(config.data_dir).as_posix()
            log.info("照片已存 %s", photo_location)
        except (OSError, ValueError) as exc:
            log.warning("照片存檔失敗：%s", exc)
            photo_location = "（照片存檔失敗）"

    # 純文字查詢：「查詢內容」記使用者原話；有照片：記辨識出的品名
    query = text if (image is None and text) else result.title
    written = await asyncio.to_thread(
        store.append,
        [
            f"{when:%Y-%m-%d %H:%M:%S}",
            uploader,
            result.category,
            query,
            result.analysis,
            result.reminders,
            photo_location,
        ],
    )
    log.info("處理完成 類別=%s Excel=%s 總耗時 %.1f 秒", result.category,
             "已寫入" if written else "暫存待補", time.monotonic() - started)
    return Result(format_reply(result), ok=True)
