import os
import sys
from loguru import logger
from config import LOGS_DIR


def setup_logger() -> logger:
    """
    Configure loguru logger.
    Console → INFO and above
    File    → DEBUG and above, daily rotation
    """
    logger.remove()

    # ── Console ───────────────────────────────────────────────────
    logger.add(
        sink=sys.stdout,
        level="INFO",
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
    )

    # ── File ──────────────────────────────────────────────────────
    os.makedirs(LOGS_DIR, exist_ok=True)
    logger.add(
        sink=os.path.join(LOGS_DIR, "agent_{time:YYYY-MM-DD}.log"),
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        rotation="1 day",
        retention="7 days",
        compression="zip",
    )

    return logger


# ── initialise once at import time ───────────────────────────────
logger = setup_logger()
