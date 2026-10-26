"""呼叫 claude -p。防護 1（檔案範圍隔離）與防護 2（使用者文字只當資料）都在這支檔案。

每一段防護的做法：先寫「沒有防護時的預設值」，防護區塊再把它們改成安全版本。
所以把某一段整段註解掉，程式仍能跑，只是少了那層保護。
"""
from __future__ import annotations

import asyncio
import logging
import os
import re
import shutil
import tempfile
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from .config import Config
from .prompts import BASE_RULES, DATA_RULES, TASK_PROMPT

log = logging.getLogger(__name__)
TIMEOUT_SECONDS = 180


class ClaudeError(RuntimeError):
    """claude -p 沒能給出結果（找不到程式、逾時、非 0 結束）。"""


@dataclass(frozen=True)
class Image:
    data: bytes
    ext: str  # 含點，例如 ".jpg"


@dataclass(frozen=True)
class Invocation:
    argv: list[str]
    cwd: Path
    stdin: bytes | None


@contextmanager
def prepare_invocation(
    config: Config, text: str, image: Image | None = None, job_id: str | None = None
) -> Iterator[Invocation]:
    job_id = job_id or uuid.uuid4().hex[:8]

    # ---- 沒有防護時的預設值（刻意寬鬆，由下面的防護區塊收緊）----
    workdir = config.data_dir  # claude 在整個 DATA_DIR 底下工作
    stage_dir = config.data_dir / "_incoming"
    tools = "Read,Glob,Grep,WebSearch,WebFetch"
    system_prompt = BASE_RULES
    prompt = TASK_PROMPT + (f"\n\n使用者說：{text}" if text else "")  # 文字直接接進指令
    stdin_text: str | None = None
    tmp: tempfile.TemporaryDirectory | None = None
    photo_path: Path | None = None

    try:
        # ==== 防護 1：claude -p 的檔案範圍隔離 開始 ====
        # 工作資料夾換成全新的暫存資料夾，裡面只會放「這一張」待分析照片；
        # 不傳 --add-dir，DATA_DIR 完全不開放；工具只留讀檔與上網查詢。
        tmp = tempfile.TemporaryDirectory(prefix="tokyo-job-")
        workdir = Path(tmp.name)
        stage_dir = workdir
        tools = "Read,WebSearch,WebFetch"
        # ==== 防護 1 結束 ====

        # ==== 防護 2：上傳者的字只當資料，不接進指令 開始 ====
        # 指令與規則是固定文字；使用者的字改走 stdin，包在 <user_message> 裡，
        # 並先破壞文字中的標籤，避免對方假裝資料區已經結束。
        prompt = TASK_PROMPT
        system_prompt = BASE_RULES + "\n\n" + DATA_RULES
        if text:
            defanged = re.sub(r"<\s*(/?)\s*user_message\s*>", r"＜\1user_message＞", text, flags=re.I)
            stdin_text = f"<user_message>\n{defanged}\n</user_message>"
        # ==== 防護 2 結束 ====

        if text and "user_message" in text.lower():
            log.warning("上傳文字裡含有 user_message 標籤，疑似想假裝資料區已結束")
        log.info("claude -p 工作資料夾=%s 工具=%s 文字走 %s", workdir, tools,
                 "stdin" if stdin_text is not None else ("指令參數（沒有防護 2）" if text else "無文字"))

        if image is not None:
            stage_dir.mkdir(parents=True, exist_ok=True)
            photo_path = stage_dir / f"photo-{job_id}{image.ext}"
            photo_path.write_bytes(image.data)
            rel = photo_path.relative_to(workdir).as_posix()
            prompt += f"\n\n待分析照片檔案（用 Read 工具讀取）：{rel}"

        exe = shutil.which("claude")
        if exe is None:
            raise ClaudeError("找不到 claude 指令，請確認 Claude Code 已安裝並在 PATH 裡。")

        argv = [
            exe,
            "-p",
            prompt,
            "--model", config.claude_model,
            f"--tools={tools}",
            f"--allowedTools={tools}",
            "--append-system-prompt", system_prompt,
            "--no-session-persistence",
            "--disable-slash-commands",
            "--setting-sources=project",  # 不載入使用者自己的 hooks 與外掛
        ]
        yield Invocation(argv=argv, cwd=workdir, stdin=stdin_text.encode("utf-8") if stdin_text else None)
    finally:
        if photo_path is not None:
            photo_path.unlink(missing_ok=True)
        if tmp is not None:
            tmp.cleanup()


async def analyze(config: Config, text: str, image: Image | None = None) -> str:
    """跑一次 claude -p，回傳它印出的原始文字（還沒檢查格式）。"""
    # 子程序不需要、也不該拿到 bot token
    env = {k: v for k, v in os.environ.items() if k != "DISCORD_TOKEN"}
    with prepare_invocation(config, text, image) as inv:
        inv.cwd.mkdir(parents=True, exist_ok=True)
        proc = await asyncio.create_subprocess_exec(
            *inv.argv,
            cwd=str(inv.cwd),
            env=env,
            stdin=asyncio.subprocess.PIPE if inv.stdin is not None else asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            out, err = await asyncio.wait_for(proc.communicate(inv.stdin), TIMEOUT_SECONDS)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            raise ClaudeError(f"claude -p 超過 {TIMEOUT_SECONDS} 秒沒回應") from None
    if proc.returncode != 0:
        detail = err.decode("utf-8", "replace").strip()[:300]
        raise ClaudeError(f"claude -p 結束碼 {proc.returncode}：{detail}")
    return out.decode("utf-8", "replace")
