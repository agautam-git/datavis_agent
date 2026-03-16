from langfuse import Langfuse
from config import LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST
from observability.logger import logger


def setup_langfuse() -> Langfuse:
    client = Langfuse(
        public_key=LANGFUSE_PUBLIC_KEY,
        secret_key=LANGFUSE_SECRET_KEY,
        host=LANGFUSE_HOST
    )

    try:
        if client.auth_check():
            logger.info("langfuse connected")
        else:
            logger.warning("langfuse auth failed — traces disabled")
    except Exception as e:
        logger.warning(f"langfuse unavailable: {e}")

    return client


# ── initialise once at import time ───────────────────────────────
langfuse = setup_langfuse()
