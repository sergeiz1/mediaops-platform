from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_file_logging(log_path: Path, max_bytes: int = 2 * 1024 * 1024 * 1024, backup_count: int = 5) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    resolved = str(log_path.resolve())

    formatter = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")

    def _attach(logger_name: str) -> None:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)
        for handler in logger.handlers:
            if isinstance(handler, RotatingFileHandler) and getattr(handler, "baseFilename", "") == resolved:
                return
        file_handler = RotatingFileHandler(
            resolved,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    _attach("")
    _attach("uvicorn")
    _attach("uvicorn.error")
    _attach("uvicorn.access")
