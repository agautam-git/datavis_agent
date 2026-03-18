from langfuse import Langfuse
from langfuse.callback import CallbackHandler  # Add this
from config import LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST
from observability.logger import logger


def setup_langfuse():
    client = Langfuse(
        public_key=LANGFUSE_PUBLIC_KEY,
        secret_key=LANGFUSE_SECRET_KEY,
        host=LANGFUSE_HOST
    )

    # Create the handler that LangGraph/LangChain uses
    handler = CallbackHandler(
        public_key=LANGFUSE_PUBLIC_KEY,
        secret_key=LANGFUSE_SECRET_KEY,
        host=LANGFUSE_HOST
    )

    try:
        if client.auth_check():
            logger.info("langfuse connected")
        else:
            logger.warning("langfuse auth failed")
    except Exception as e:
        logger.warning(f"langfuse unavailable: {e}")

    return client, handler

# Export both
langfuse, langfuse_handler = setup_langfuse()