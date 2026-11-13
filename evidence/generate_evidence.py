
import json
import sys
from pathlib import Path

# Add the project root to Python's import path.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from refresh_strategy import RefreshManager


def generate_evidence():

    manager = RefreshManager(
        threshold=3,
        keep_recent=2,
        max_chars=500
    )

    messages = [
        ("user", "The project goal is to create a memory system."),
        ("assistant", "The project needs reliable retrieval."),
        ("user", "The deadline is December."),
        ("assistant", "We will preserve recent conversation context.")
    ]

    for role, text in messages:
        manager.add_message(role, text)

    context = manager.build_context("project goal")

    evidence = {
        "assessment": "Topic 17 - Refresh Strategies",
        "refresh_count": manager.refresh_count,
        "summary": manager.state.summary,
        "long_term_memory": manager.state.long_term,
        "vector_store": manager.vector_store.items,
        "recent_messages": [
            {
                "role": message.role,
                "text": message.text
            }
            for message in manager.state.short_term
        ],
        "retrieved_memory": context["retrieved_memory"],
        "refresh_events": manager.refresh_events,
        "context_size": manager.context_size(),
        "configuration": {
            "threshold": manager.threshold,
            "keep_recent": manager.keep_recent,
            "max_chars": manager.max_chars
        }
    }

    output_path = (
        Path(__file__).resolve().parent / "evidence_summary.json"
    )

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(evidence, file, indent=4)

    print("\nEvidence generated successfully!")
    print("Output:", output_path)
    print("Refresh count:", manager.refresh_count)
    print("Long-term memories:", len(manager.state.long_term))
    print("Vector store items:", len(manager.vector_store.items))


if __name__ == "__main__":
    generate_evidence()
