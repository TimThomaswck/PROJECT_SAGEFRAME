"""Local file storage utilities for file ingestion."""

import os
import shutil
import uuid
from pathlib import Path
from typing import Tuple

from app.database import DATABASE_PATH


def get_ingest_root() -> Path:
    # Store near the database file in user app data dir
    root = Path(DATABASE_PATH).parent / "ingest"
    root.mkdir(parents=True, exist_ok=True)
    return root


def store_imported_file(src_path: str) -> Tuple[str, str, str]:
    """Copy source file to local ingest storage.

    Returns (stored_path, file_name, ingest_uuid)
    """
    src = Path(src_path)
    if not src.exists():
        raise FileNotFoundError(f"File not found: {src_path}")

    ingest_uuid = str(uuid.uuid4())
    dest_dir = get_ingest_root() / ingest_uuid
    dest_dir.mkdir(parents=True, exist_ok=True)

    file_name = src.name
    dest_path = dest_dir / file_name
    shutil.copyfile(src, dest_path)

    return str(dest_path), file_name, ingest_uuid
