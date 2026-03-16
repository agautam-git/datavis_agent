import asyncio
from openai import OpenAI
from config import OPENAI_API_KEY
from memory.memory import MemoryManager
from agent.agent import run_agent
from observability.logger import logger


def main():
    logger.info("starting data agent")

    client = OpenAI(api_key=OPENAI_API_KEY)
    memory = MemoryManager(client=client)

    print("\nData Agent ready. Type your question (or 'quit' to exit, 'reset' to clear memory)\n")

    while True:
        question = input("You: ").strip()

        if not question:
            continue

        if question.lower() == "quit":
            logger.info("shutting down")
            break

        if question.lower() == "reset":
            memory.reset()
            print("Memory cleared.\n")
            continue

        result = run_agent(question, memory)

        if result is None:
            print("Agent failed to answer. Please try again.\n")


if __name__ == "__main__":
    main()