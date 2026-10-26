"""把照片存進 DATA_DIR/photos。防護 3（檔名清洗）在這支檔案。"""
from __future__ import annotations

import logging
import re
from datetime import datetime
from itertools import count
from pathlib import Path

log = logging.getLogger(__name__)
LABEL_MAX = 20


def save_photo(
    photos_dir: Path, data: bytes, when: datetime, category: str, name: str, ext: str
) -> Path:
    """檔名：YYYY-MM-DD hh-mm-ss 類別品名簡稱.副檔名；同一秒撞名加 -2、-3。"""
    photos_dir.mkdir(parents=True, exist_ok=True)
    label = raw_label = f"{category}{name[:LABEL_MAX]}"
    check_inside = False  # 沒有防護 3 時：不檢查最後落在哪裡

    # ==== 防護 3：檔名清洗，避免路徑亂跑 開始 ====
    # 1) 清掉 / \ .. : * ? " < > | 與控制字元（含換行、tab）
    label = re.sub(r'[\x00-\x1f\x7f/\\:*?"<>|]', "_", label)
    label = label.replace("..", "_")
    # 2) 去掉頭尾的空白與句號（Windows 會自動吃掉它們）
    label = label.strip(" .")
    # 3) 避開 Windows 保留名稱；清完變空字串就用「未命名」
    reserved = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}
    if not label:
        label = "未命名"
    elif label.split(".")[0].upper() in reserved:
        label = f"_{label}"
    # 4) 最後防線：組出路徑後，確認真的還在 photos 資料夾裡面
    check_inside = True
    # ==== 防護 3 結束 ====

    if label != raw_label:
        log.warning("防護 3：檔名已清洗 %r → %r", raw_label, label)

    base = f"{when:%Y-%m-%d %H-%M-%S} {label}"
    root = photos_dir.resolve()
    for n in count(1):
        suffix = "" if n == 1 else f"-{n}"
        path = photos_dir / f"{base}{suffix}{ext}"
        if check_inside and root not in path.resolve().parents:
            raise ValueError(f"檔案路徑跑到照片資料夾外面了：{path}")
        try:
            with open(path, "xb") as fh:  # x：檔案已存在就失敗，絕不覆蓋
                fh.write(data)
            return path
        except FileExistsError:
            continue
    raise AssertionError("unreachable")
