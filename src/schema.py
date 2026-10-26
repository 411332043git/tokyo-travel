"""claude -p 回傳的固定格式 JSON：解析與檢查。任何不合格都丟 AnalysisError，由呼叫端轉成友善回覆。"""
from __future__ import annotations

import json
from dataclasses import dataclass

CATEGORIES = ("日語翻譯", "精品比價", "地鐵導航", "藥妝辨識", "非旅遊項目")
NON_TRAVEL = "非旅遊項目"
NON_TRAVEL_NOTICE = "本工具僅限東京旅遊相關諮詢（日語翻譯、精品比價、地鐵導航、藥妝辨識）。"

_LIMITS = {"title": 100, "analysis": 8000, "reminders": 3000}


class AnalysisError(ValueError):
    """claude -p 的回覆不是我們要的格式。"""


@dataclass(frozen=True)
class Analysis:
    category: str
    title: str  # 主識別名稱
    analysis: str  # 主要分析結果
    reminders: str  # 補充法規與提醒


def _extract_object(raw: str) -> dict:
    text = raw.strip()
    candidates = [text]
    # claude 偶爾會在 JSON 前後多寫一句話或包 ``` 區塊：取最外層的 { ... }
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        candidates.append(text[start : end + 1])
    for candidate in candidates:
        try:
            value = json.loads(candidate)
        except (json.JSONDecodeError, ValueError):
            continue
        if isinstance(value, dict):
            return value
    raise AnalysisError("不是合法的 JSON 物件")


def parse_analysis(raw: str) -> Analysis:
    data = _extract_object(raw)

    category = data.get("category")
    if category not in CATEGORIES:
        raise AnalysisError(f"category 不是合法值：{category!r}")

    fields: dict[str, str] = {}
    for key, limit in _LIMITS.items():
        value = data.get(key)
        if value is None and key == "reminders":
            value = ""
        if not isinstance(value, str):
            raise AnalysisError(f"{key} 必須是文字")
        fields[key] = value.strip()[:limit]

    if not fields["analysis"]:
        raise AnalysisError("analysis 是空的")
    if not fields["title"]:
        fields["title"] = "（未辨識）"

    if category == NON_TRAVEL and NON_TRAVEL_NOTICE not in fields["reminders"]:
        fields["reminders"] = f"{fields['reminders']}\n{NON_TRAVEL_NOTICE}".strip()

    return Analysis(category=category, **fields)
