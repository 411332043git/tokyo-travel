"""組出回覆文字、處理 Discord 單則訊息長度限制。"""
from __future__ import annotations

from .schema import Analysis

FAILURE_TEXT = "分析失敗，請再試一次"
DISCORD_LIMIT = 2000


def format_reply(a: Analysis) -> str:
    parts = [f"**【{a.category}】{a.title}**", "", a.analysis]
    if a.reminders:
        parts += ["", "📌 **補充提醒**", a.reminders]
    return "\n".join(parts)


def split_message(text: str, limit: int = DISCORD_LIMIT - 100) -> list[str]:
    """盡量在換行處切開，每段不超過 limit 字。"""
    chunks: list[str] = []
    current = ""
    for line in text.split("\n"):
        while len(line) > limit:  # 單行就超長：硬切
            if current:
                chunks.append(current)
                current = ""
            chunks.append(line[:limit])
            line = line[limit:]
        candidate = f"{current}\n{line}" if current else line
        if len(candidate) > limit:
            chunks.append(current)
            current = line
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks or [""]
