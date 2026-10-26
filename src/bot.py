"""Discord Gateway 入口：只聽 CHANNEL_ID 指定的頻道；收到先加 ⏳，再一件一件排隊處理。"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path

import discord

from .claude_runner import Image
from .config import Config
from .excel_store import ExcelStore
from .logging_setup import preview
from .pipeline import process
from .replies import FAILURE_TEXT, split_message

log = logging.getLogger(__name__)

QUEUED, DONE, FAILED = "⏳", "✅", "❌"
MAX_IMAGES_PER_MESSAGE = 10
MAX_IMAGE_BYTES = 10 * 1024 * 1024
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
NO_MENTIONS = discord.AllowedMentions.none()


def image_ext(attachment: discord.Attachment) -> str | None:
    ext = Path(attachment.filename).suffix.lower()
    if ext in IMAGE_EXTS:
        return ".jpg" if ext == ".jpeg" else ext
    if (attachment.content_type or "").startswith("image/"):
        return ".jpg"
    return None


@dataclass
class Batch:
    """同一則訊息拆出來的所有工作；全部做完才把 ⏳ 換成 ✅ 或 ❌。"""

    message: discord.Message
    remaining: int
    failed: bool = False


@dataclass
class Job:
    batch: Batch
    text: str
    attachment: discord.Attachment | None = None


class TravelBot(discord.Client):
    def __init__(self, config: Config, store: ExcelStore) -> None:
        intents = discord.Intents.default()
        intents.message_content = True  # 要在 Developer Portal 打開 Message Content Intent
        super().__init__(intents=intents)
        self.config = config
        self.store = store
        self.queue: asyncio.Queue[Job] = asyncio.Queue()

    async def setup_hook(self) -> None:
        # 只開一個工作者：同一時間最多一個 claude -p
        self.worker_task = asyncio.create_task(self._worker())

    async def on_ready(self) -> None:
        log.info("已登入為 %s，只聽頻道 %s", self.user, self.config.channel_id)

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or message.channel.id != self.config.channel_id:
            return
        text = message.content.strip()
        images = [a for a in message.attachments if image_ext(a)]
        if not images and not text:
            return
        log.info("收到訊息 作者=%s (%s) 文字=%r 照片=%d 張",
                 message.author.display_name, message.author.id, preview(text), len(images))

        notes: list[str] = []
        if len(images) > MAX_IMAGES_PER_MESSAGE:
            notes.append(f"一則訊息最多處理 {MAX_IMAGES_PER_MESSAGE} 張照片，其餘的請分批傳。")
            images = images[:MAX_IMAGES_PER_MESSAGE]
        big = [a for a in images if a.size > MAX_IMAGE_BYTES]
        if big:
            notes.append("有照片超過 10 MB，已略過。")
            images = [a for a in images if a.size <= MAX_IMAGE_BYTES]
        if notes:
            log.warning("訊息超出限制：%s", " ".join(notes))
            await self._reply(message, "\n".join(notes))
        if not images and not text:
            return

        await self._react(message, QUEUED)
        if images:
            batch = Batch(message, remaining=len(images))
            for attachment in images:
                await self.queue.put(Job(batch, text, attachment))
        else:
            await self.queue.put(Job(Batch(message, remaining=1), text))
        log.info("已排隊（本則 %d 件，佇列裡共 %d 件等待）", len(images) or 1, self.queue.qsize())

    async def _worker(self) -> None:
        while True:
            job = await self.queue.get()
            log.info("輪到處理（訊息 %s，還剩 %d 件在等）", job.batch.message.id, self.queue.qsize())
            try:
                await self._run(job)
            except Exception:  # noqa: BLE001  單一工作出任何錯都不能讓 bot 停擺
                log.exception("處理工作時發生未預期的錯誤")
                job.batch.failed = True
                await self._reply(job.batch.message, FAILURE_TEXT)
            finally:
                job.batch.remaining -= 1
                if job.batch.remaining == 0:
                    await self._finish(job.batch)
                self.queue.task_done()

    async def _run(self, job: Job) -> None:
        message = job.batch.message
        image = None
        if job.attachment is not None:
            image = Image(await job.attachment.read(), image_ext(job.attachment) or ".jpg")
        uploader = f"{message.author.display_name} ({message.author.id})"
        result = await process(self.config, self.store, uploader, job.text, image)
        if not result.ok:
            job.batch.failed = True
        await self._reply(message, result.reply)
        log.info("已回覆（訊息 %s）結果=%s", message.id, "成功" if result.ok else "失敗")

    async def _finish(self, batch: Batch) -> None:
        log.info("訊息 %s 全部處理完畢 → %s", batch.message.id, FAILED if batch.failed else DONE)
        try:
            await batch.message.remove_reaction(QUEUED, self.user)
        except discord.HTTPException:
            pass
        await self._react(batch.message, FAILED if batch.failed else DONE)

    async def _react(self, message: discord.Message, emoji: str) -> None:
        try:
            await message.add_reaction(emoji)
        except discord.HTTPException as exc:
            log.warning("加 %s 反應失敗（bot 可能缺少 Add Reactions 權限）：%s", emoji, exc)

    async def _reply(self, message: discord.Message, text: str) -> None:
        for chunk in split_message(text):
            try:
                await message.reply(chunk, mention_author=False, allowed_mentions=NO_MENTIONS)
            except discord.HTTPException as exc:
                log.warning("回覆失敗：%s", exc)
                return
