import tiktoken
from openai import OpenAI
from config import AGENT_MODEL, MAX_TURNS, MAX_TOKENS
from agent.prompts import SUMMARY_PROMPT
from observability.logger import logger


class MemoryManager:
    def __init__(
        self,
        client: OpenAI,
        model: str = AGENT_MODEL,
        max_turns: int = MAX_TURNS,
        max_tokens: int = MAX_TOKENS,
    ):
        self.client = client
        self.model = model
        self.max_turns = max_turns
        self.max_tokens = max_tokens
        self.encoder = tiktoken.encoding_for_model(model)
        self.history = []
        self.summary = None
        self.tables_cache = None
        self.schema_cache = {}

    # ── Token counting ────────────────────────────────────────────
    def count_tokens(self, messages: list) -> int:
        return sum(
            len(self.encoder.encode(m["content"]))
            for m in messages
            if isinstance(m.get("content"), str)
        )

    # ── Cache ─────────────────────────────────────────────────────
    def cache_tables(self, result: str):
        self.tables_cache = result
        logger.debug("tables cached")

    def cache_schema(self, table_name: str, result: str):
        self.schema_cache[table_name] = result
        logger.debug(f"schema cached: {table_name}")

    def get_cached_tables(self) -> str | None:
        return self.tables_cache

    def get_cached_schema(self, table_name: str) -> str | None:
        return self.schema_cache.get(table_name)

    # ── Q&A history ───────────────────────────────────────────────
    def add_question(self, question: str):
        self.history.append({"role": "user", "content": question})

    def add_answer(self, answer: str):
        self.history.append({"role": "assistant", "content": answer})
        self._maybe_summarise()

    def _maybe_summarise(self):
        turns = len([m for m in self.history if m["role"] == "user"])
        if turns <= self.max_turns:
            return

        keep_from = -(self.max_turns * 2)
        to_summarise = self.history[:keep_from]
        self.history = self.history[keep_from:]

        prior = (
            f"Previous summary:\n{self.summary}\n\nNew turns:\n" if self.summary else ""
        )
        text = prior + "\n".join(
            f"{m['role']}: {m['content']}"
            for m in to_summarise
            if isinstance(m.get("content"), str)
        )

        tokens_before = self.count_tokens(self.get_messages(""))
        logger.info(f"  [memory] summarising — tokens before: {tokens_before}")

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": SUMMARY_PROMPT.format(text=text)}],
        )

        self.summary = response.choices[0].message.content
        tokens_after = self.count_tokens(self.get_messages(""))
        logger.info(f"  [memory] summarised — tokens after: {tokens_after}")

    # ── Build messages ────────────────────────────────────────────
    def get_messages(self, system_prompt: str) -> list:
        messages = [{"role": "system", "content": system_prompt}]

        if self.tables_cache:
            messages.append(
                {
                    "role": "system",
                    "content": f"[Available tables]: {self.tables_cache}",
                }
            )

        if self.schema_cache:
            schema_text = "\n\n".join(
                f"[{t}]:\n{s}" for t, s in self.schema_cache.items()
            )
            messages.append(
                {"role": "system", "content": f"[Table schemas]:\n{schema_text}"}
            )

        if self.summary:
            messages.append(
                {"role": "system", "content": f"[Earlier context]: {self.summary}"}
            )

        messages.extend(self.history)
        return messages

    # ── Stats ─────────────────────────────────────────────────────
    def stats(self, system_prompt: str = ""):
        tokens = self.count_tokens(self.get_messages(system_prompt))
        turns = len([m for m in self.history if m["role"] == "user"])
        logger.info(
            f"  [memory] turns: {turns}/{self.max_turns} | cached schemas: {len(self.schema_cache)} | summary: {'yes' if self.summary else 'no'} | tokens: {tokens}/{self.max_tokens}"
        )

    def reset(self):
        self.history = []
        self.summary = None
        logger.info("  [memory] reset — cache preserved")
