
from refresh_strategy import RefreshManager


def print_context(title, context):

    print(f"\n{'=' * 65}")
    print(title)
    print("=" * 65)

    print("\nSUMMARY:")
    print(context["summary"] or "(No summary)")

    print("\nRETRIEVED MEMORIES:")

    if context["retrieved_memory"]:
        for memory in context["retrieved_memory"]:
            print("-", memory)
    else:
        print("(No relevant memories found)")

    print("\nRECENT MESSAGES:")

    for message in context["recent_messages"]:
        print(f"[{message['role']}] {message['text']}")


def main():

    print("\nTOPIC 17 - REFRESH STRATEGIES ASSESSMENT")
    print("=" * 65)

    manager = RefreshManager(
        threshold=4,
        keep_recent=2,
        max_chars=500
    )

    # --------------------------------------------------------
    # CONVERSATION 1
    # --------------------------------------------------------

    print("\n\nCONVERSATION 1 - PROJECT INFORMATION")

    conversation_1 = [
        ("user", "The project goal is to develop an AI assistant."),
        ("assistant", "We will use Python for implementation."),
        ("user", "The project needs a reliable memory system."),
        ("assistant", "We should preserve important project decisions."),
        ("user", "The deadline for the project is December.")
    ]

    for role, text in conversation_1:
        context = manager.add_message(role, text)

    print_context(
        "CONVERSATION 1 - CONTEXT AFTER REFRESH",
        context
    )

    # --------------------------------------------------------
    # CONVERSATION 2
    # --------------------------------------------------------

    print("\n\nCONVERSATION 2 - NEW REQUIREMENTS")

    conversation_2 = [
        ("user", "The project prefers a modular architecture."),
        ("assistant", "We can separate memory and retrieval components."),
        ("user", "The project needs duplicate prevention.")
    ]

    for role, text in conversation_2:
        context = manager.add_message(role, text)

    print_context(
        "CONVERSATION 2 - CURRENT CONTEXT",
        context
    )

    # --------------------------------------------------------
    # RETRIEVAL DEMONSTRATION
    # --------------------------------------------------------

    print("\n\nRETRIEVAL DEMONSTRATION")

    query = "project goal AI assistant"

    retrieved = manager.retrieve(query, top_k=3)

    print("Query:", query)

    for memory in retrieved:
        print("-", memory)

    reconstructed_context = manager.build_context(
        query,
        retrieved
    )

    print_context(
        "RECONSTRUCTED CONTEXT",
        reconstructed_context
    )

    # --------------------------------------------------------
    # MANUAL REFRESH
    # --------------------------------------------------------

    print("\n\nMANUAL REFRESH DEMONSTRATION")

    context = manager.manual_refresh(
        query="project architecture"
    )

    print_context(
        "CONTEXT AFTER MANUAL REFRESH",
        context
    )

    # --------------------------------------------------------
    # FINAL INSPECTION
    # --------------------------------------------------------

    print("\n\nFINAL MEMORY INSPECTION")

    manager.inspect()

    manager.inspect_context_size()

    # --------------------------------------------------------
    # FINAL STATISTICS
    # --------------------------------------------------------

    print("\n========== FINAL STATISTICS ==========")

    print("Total refreshes:", manager.refresh_count)

    print("Long-term memories:", len(manager.state.long_term))

    print("Vector store items:", len(manager.vector_store.items))

    print("Recent messages:", len(manager.state.short_term))

    print("Refresh events:", len(manager.refresh_events))

    print("\nTopic 17 demonstration completed.")


if __name__ == "__main__":
    main()
