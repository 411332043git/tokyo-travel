"""從 .env 讀設定。缺少必要項目時給出看得懂的錯誤，而不是讓程式莫名其妙當掉。"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PLACEHOLDER_TOKENS = {"", "你的bot_token"}


class ConfigError(RuntimeError):
    """設定有問題，訊息直接給使用者看。"""


@dataclass(frozen=True)
class Config:
    discord_token: str
    channel_id: int
    claude_model: str
    data_dir: Path  # 絕對路徑；相對路徑以專案資料夾為基準

    @property
    def photos_dir(self) -> Path:
        return self.data_dir / "photos"

    @property
    def excel_path(self) -> Path:
        return self.data_dir / "records.xlsx"


def load_config(env_path: Path | None = None) -> Config:
    load_dotenv(env_path or PROJECT_ROOT / ".env")

    def need(key: str) -> str:
        value = os.environ.get(key, "").strip()
        if not value:
            raise ConfigError(f".env 缺少 {key}，請補上。")
        return value

    token = need("DISCORD_TOKEN")
    if token in PLACEHOLDER_TOKENS:
        raise ConfigError(".env 的 DISCORD_TOKEN 還是占位字樣，請換成真的 bot token。")

    try:
        channel_id = int(need("CHANNEL_ID"))
    except ValueError:
        raise ConfigError(".env 的 CHANNEL_ID 必須是純數字。") from None

    data_dir = Path(need("DATA_DIR")).expanduser()
    if not data_dir.is_absolute():
        data_dir = PROJECT_ROOT / data_dir

    return Config(
        discord_token=token,
        channel_id=channel_id,
        claude_model=need("CLAUDE_MODEL"),
        data_dir=data_dir.resolve(),
    )
