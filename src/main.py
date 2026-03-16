from openai import OpenAI
from config import OPENAI_API_KEY
from db.database import Database
from memory.memory import MemoryManager
from agent.agent import run_agent
from observability.logger import logger


def main():
    logger.info("starting data agent")

    # ── Wire dependencies ─────────────────────────────────────────
    client = OpenAI(api_key=OPENAI_API_KEY)
    db = Database()
    memory = MemoryManager(client=client)

    logger.info(f"connected to db: {db.get_tables()}")

    # ── Conversation loop ─────────────────────────────────────────
    print(
        "\nData Agent ready. Type your question (or 'quit' to exit, 'reset' to clear memory)\n"
    )

    while True:
        question = input("You: ").strip()

        if not question:
            continue

        if question.lower() == "quit":
            logger.info("shutting down")
            db.close()
            break

        if question.lower() == "reset":
            memory.reset()
            print("Memory cleared.\n")
            continue

        result = run_agent(question, db, memory)

        if result is None:
            print("Agent failed to answer. Please try again.\n")


if __name__ == "__main__":
    main()
