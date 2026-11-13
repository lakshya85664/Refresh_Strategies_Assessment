
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Optional
import re


# ============================================================
# 1. DATA STRUCTURES
# ============================================================

@dataclass
class Message:
    role: str
    text: str


@dataclass
class MemoryState:
    short_term: List[Message] = field(default_factory=list)
    long_term: List[str] = field(default_factory=list)
    summary: str = ""


# ============================================================
# 2. SIMPLE VECTOR STORE
# ============================================================

class SimpleVectorStore:

    def __init__(self):
        self.items: List[str] = []

    def add(self, text: str) -> None:

        normalized = text.casefold().strip()

        existing = {
            item.casefold().strip()
            for item in self.items
        }

        if normalized and normalized not in existing:
            self.items.append(text)

    @staticmethod
    def _tokens(text: str) -> set:

        return set(
            re.findall(r"\b[a-zA-Z0-9_]+\b", text.lower())
        )

    def search(
        self,
        query: str,
        top_k: int = 3
    ) -> List[Tuple[int, str]]:

        if top_k <= 0:
            return []

        query_tokens = self._tokens(query)

        if not query_tokens:
            return []

        scored = []

        for item in self.items:

            score = len(
                query_tokens & self._tokens(item)
            )

            if score > 0:
                scored.append((score, item))

        # Higher similarity first; alphabetical order breaks ties.
        scored.sort(
            key=lambda item: (-item[0], item[1].casefold())
        )

        return scored[:top_k]


# ============================================================
# 3. REFRESH MANAGER
# ============================================================

class RefreshManager:

    def __init__(
        self,
        threshold: int = 6,
        keep_recent: int = 3,
        max_chars: int = 500
    ):

        if threshold < 1:
            raise ValueError("Threshold must be at least 1.")

        if keep_recent < 1:
            raise ValueError("keep_recent must be at least 1.")

        if keep_recent > threshold:
            raise ValueError(
                "keep_recent cannot be greater than threshold."
            )

        if max_chars < 1:
            raise ValueError("max_chars must be at least 1.")

        self.threshold = threshold
        self.keep_recent = keep_recent
        self.max_chars = max_chars

        self.state = MemoryState()

        self.vector_store = SimpleVectorStore()

        self.refresh_count = 0

        self.last_refresh_older: List[Message] = []

        self.refresh_events: List[Dict[str, Any]] = []

    # --------------------------------------------------------
    # EXERCISE 1: ADD CONVERSATION MESSAGE
    # --------------------------------------------------------

    def add_message(
        self,
        role: str,
        text: str,
        query: Optional[str] = None
    ):

        if not role.strip():
            raise ValueError("Message role cannot be empty.")

        if not text.strip():
            raise ValueError("Message text cannot be empty.")

        message = Message(
            role=role,
            text=text
        )

        self.state.short_term.append(message)

        print(f"Message added: [{role}] {text}")

        # Priority 1: Message-count threshold.
        if len(self.state.short_term) > self.threshold:

            return self.refresh(
                query=query or text,
                reason="threshold"
            )

        # Priority 2: Character-based context threshold.
        if self.context_size() > self.max_chars:

            return self.refresh(
                query=query or text,
                reason="context_size"
            )

        return self.build_context(query or text)

    # --------------------------------------------------------
    # EXERCISE 2: SUMMARIZATION
    # --------------------------------------------------------

    def summarize(self, messages: List[Message]) -> str:

        if not messages:
            return self.state.summary

        parts = [
            f"{message.role}: {message.text}"
            for message in messages
        ]

        new_summary = " | ".join(parts)

        if self.state.summary:
            new_summary = (
                self.state.summary + " | " + new_summary
            )

        # Keep the summary bounded to 700 characters.
        self.state.summary = new_summary[-700:]

        return self.state.summary

    # --------------------------------------------------------
    # EXERCISE 2: DURABLE FACT EXTRACTION
    # --------------------------------------------------------

    def extract_facts(
        self,
        messages: List[Message]
    ) -> List[str]:

        markers = (
            "project",
            "goal",
            "deadline",
            "prefers",
            "preference",
            "needs"
        )

        facts = []

        for message in messages:

            text = message.text.strip()
            lower = text.lower()

            if any(
                marker in lower
                for marker in markers
            ):

                if text not in facts:
                    facts.append(text)

        return facts

    # --------------------------------------------------------
    # EXERCISE 2: LONG-TERM MEMORY STORAGE
    # --------------------------------------------------------

    def store_facts(self, facts: List[str]) -> int:

        stored_count = 0

        existing = {
            fact.casefold().strip()
            for fact in self.state.long_term
        }

        for fact in facts:

            normalized = fact.casefold().strip()

            if normalized and normalized not in existing:

                self.state.long_term.append(fact)

                self.vector_store.add(fact)

                existing.add(normalized)

                stored_count += 1

        return stored_count

    # --------------------------------------------------------
    # EXERCISE 3: RETRIEVAL
    # --------------------------------------------------------

    def retrieve(
        self,
        query: str,
        top_k: int = 3
    ) -> List[str]:

        results = self.vector_store.search(
            query,
            top_k
        )

        return [
            text
            for score, text in results
        ]

    # --------------------------------------------------------
    # EXERCISE 4: CONTEXT SIZE MEASUREMENT
    # --------------------------------------------------------

    def context_size(self) -> int:

        return sum(
            len(message.text)
            for message in self.state.short_term
        )

    # --------------------------------------------------------
    # EXERCISE 4: MANUAL REFRESH
    # --------------------------------------------------------

    def manual_refresh(self, query: str = ""):

        if not self.state.short_term:
            print("No messages available for manual refresh.")
            return self.build_context(query)

        return self.refresh(
            query=query,
            reason="manual"
        )

    # --------------------------------------------------------
    # REFRESH PIPELINE
    # --------------------------------------------------------

    def refresh(
        self,
        query: str = "",
        reason: str = "threshold"
    ):

        self.refresh_count += 1

        # Capture state before refresh.
        before_count = len(self.state.short_term)
        before_chars = self.context_size()

        # Separate older and recent messages.
        older = self.state.short_term[:-self.keep_recent]

        recent = self.state.short_term[-self.keep_recent:]

        self.last_refresh_older = older

        # Step 1: Summarize older conversation.
        self.summarize(older)

        # Step 2: Extract durable facts.
        facts = self.extract_facts(older)

        # Step 3: Store facts in long-term memory.
        stored_count = self.store_facts(facts)

        # Step 4: Retain recent messages.
        self.state.short_term = recent

        # Step 5: Retrieve relevant long-term memories.
        retrieved = self.retrieve(query)

        # Record refresh event.
        event = {
            "refresh_number": self.refresh_count,
            "reason": reason,
            "messages_before": before_count,
            "messages_summarized": len(older),
            "recent_messages_retained": len(recent),
            "characters_before": before_chars,
            "characters_after": self.context_size(),
            "facts_extracted": len(facts),
            "facts_stored": stored_count,
            "retrieved_count": len(retrieved)
        }

        self.refresh_events.append(event)

        print("\n========== REFRESH OCCURRED ==========")

        print("Refresh number:", self.refresh_count)
        print("Refresh reason:", reason)
        print("Messages before refresh:", before_count)
        print("Older messages summarized:", len(older))
        print("Facts extracted:", len(facts))
        print("New facts stored:", stored_count)
        print("Retrieved memories:", len(retrieved))
        print("Recent messages retained:", len(recent))
        print("Characters before refresh:", before_chars)
        print("Characters after refresh:", self.context_size())

        print("======================================\n")

        return self.build_context(query, retrieved)

    # --------------------------------------------------------
    # EXERCISE 3: CONTEXT RECONSTRUCTION
    # --------------------------------------------------------

    def build_context(
        self,
        query: str = "",
        retrieved: Optional[List[str]] = None
    ):

        if retrieved is None:
            retrieved = self.retrieve(query)

        return {
            "summary": self.state.summary,

            "retrieved_memory": retrieved,

            "recent_messages": [
                {
                    "role": message.role,
                    "text": message.text
                }
                for message in self.state.short_term
            ]
        }

    # --------------------------------------------------------
    # EXERCISE 4: CONTEXT SIZE INSPECTION
    # --------------------------------------------------------

    def inspect_context_size(self):

        current_size = self.context_size()

        print("\n========== CONTEXT SIZE INSPECTION ==========")

        print("Current characters:", current_size)
        print("Maximum characters:", self.max_chars)

        print("=============================================\n")

        return current_size

    # --------------------------------------------------------
    # EXERCISE 4: REFRESH INSPECTION
    # --------------------------------------------------------

    def inspect(self):

        print("\n========== REFRESH INSPECTION ==========")

        print("Refresh count:", self.refresh_count)

        print("Configured threshold:", self.threshold)

        print("Recent-message limit:", self.keep_recent)

        print("Maximum characters:", self.max_chars)

        print("\nSummary:")

        print(self.state.summary or "(empty)")

        print("\nLong-term memory:")

        for fact in self.state.long_term:
            print("-", fact)

        print("\nVector store items:")

        for item in self.vector_store.items:
            print("-", item)

        print("\nRecent short-term messages:")

        for message in self.state.short_term:

            print(
                f"- [{message.role}] {message.text}"
            )

        print("\nRefresh events:")

        for event in self.refresh_events:
            print(event)

        print("========================================\n")


# ============================================================
# 5. DEMONSTRATION
# ============================================================

if __name__ == "__main__":

    manager = RefreshManager(
        threshold=6,
        keep_recent=3,
        max_chars=500
    )

    messages = [
        (
            "user",
            "The project goal is to build a refresh strategy demo."
        ),
        (
            "assistant",
            "We will keep recent messages in short-term memory."
        ),
        (
            "user",
            "The project needs a compact implementation."
        ),
        (
            "assistant",
            "Older details can be summarized during refresh."
        ),
        (
            "user",
            "The user prefers clear console inspection output."
        ),
        (
            "assistant",
            "Long-term facts can be retrieved when relevant."
        ),
        (
            "user",
            "The deadline for the project is Friday."
        )
    ]

    print("\n========== MESSAGE INGESTION ==========\n")

    for index, (role, text) in enumerate(messages):

        query = "project goal" if index == 6 else None

        context = manager.add_message(
            role,
            text,
            query=query
        )

    print("\n========== FINAL RECONSTRUCTED CONTEXT ==========")

    print("\nSummary:")
    print(context["summary"])

    print("\nRetrieved long-term memory:")

    for item in context["retrieved_memory"]:
        print("-", item)

    print("\nRecent messages:")

    for message in context["recent_messages"]:

        print(
            f"- [{message['role']}] {message['text']}"
        )

    manager.inspect()

    manager.inspect_context_size()
