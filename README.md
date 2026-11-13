# Topic 17 – Refresh Strategies Assessment

## Project Overview
This project implements a lightweight conversation-memory refresh strategy using Python's standard library. It maintains a bounded recent-message window, summarizes older messages, extracts selected durable facts, stores them without case-insensitive duplicates, and retrieves relevant information when reconstructing context.

The implementation does not call an external LLM, embedding service, database, or API. Its retrieval component is a token-overlap baseline, not a production embedding model.

## Objectives
- Refresh when active message count exceeds a configured threshold.
- Refresh when short-term message text exceeds a character threshold.
- Retain a configured number of recent messages.
- Summarize older messages into a bounded summary.
- Extract durable facts and prevent duplicate storage.
- Retrieve relevant facts using token overlap.
- Reconstruct context from summary, retrieved memories, and recent messages.
- Support manual refresh, inspection, tests, and JSON evidence.

## Project Structure
```text
Refresh_Strategies_Assessment/
├── evidence/
│   ├── generate_evidence.py
│   └── evidence_summary.json
├── refresh_strategy.py
├── test_refresh_strategy.py
├── demo_refresh.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Implementation
`Message` stores a role and text. `MemoryState` maintains short-term messages, long-term facts, and a summary.

`RefreshManager` accepts `threshold`, `keep_recent`, and `max_chars`. It supports threshold-triggered, character-triggered, and manual refresh. Older messages are summarized and candidate facts are extracted using markers such as `project`, `goal`, `deadline`, `prefers`, `preference`, and `needs`.

`SimpleVectorStore` stores unique text entries and ranks them by shared query-token count. This is lexical retrieval, not semantic embedding search. `build_context()` combines the summary, retrieved long-term memories, and recent messages.

## How to Run
Use Windows CMD from the project directory:
```cmd
python -m venv .venv
.venv\Scripts\activate
python refresh_strategy.py
python -m unittest -v test_refresh_strategy.py
python -m unittest discover -v
python demo_refresh.py
python evidence\generate_evidence.py
```
Only the Python standard library is required.

## Verification Results
- Unit tests: **17 tests passed, 0 failures**.
- Multi-conversation demo: **3 refresh events** (2 threshold-triggered and 1 manual).
- Final demo state: **5 long-term memories**, **5 vector-store entries**, and **2 recent messages**.
- Evidence-generation script completed successfully and reported **1 refresh**, **2 long-term memories**, and **2 vector-store items**.

## Limitations and Future Improvements
The character counter measures only short-term message text, not the summary or retrieved memories. Summarization concatenates messages rather than generating an abstractive summary. Fact extraction uses keyword markers and can miss useful facts or select irrelevant sentences. Token-overlap retrieval does not understand synonyms or semantic similarity. Runtime memory is held in process memory; the JSON evidence file is an assessment artifact, not a persistent runtime database.

## Reflection
Building this refresh strategy helped me understand how an agent can manage a growing conversation without keeping every message in its active context. I implemented a configurable message threshold and a character-based trigger, then separated older messages from the recent-message window. This made the refresh process observable and allowed me to inspect how much short-term content remained after each refresh.

I also learned that summarization and long-term memory solve different problems. The summary preserves a compact record of earlier conversation content, while fact extraction selects information that may be useful again later. I added duplicate prevention so the same fact is not repeatedly stored, and connected the stored facts to a simple token-overlap retrieval component. The reconstructed context combines the running summary, relevant retrieved memories, and recent messages.

Testing was important because the refresh manager has several paths: threshold refresh, context-size refresh, manual refresh, empty retrieval, and repeated refresh. The 17 passing unit tests gave me confidence that these behaviors work as expected. The multi-conversation demonstration further showed how memory can be accumulated, searched, and inspected across refresh events.

One limitation is that the retrieval method uses shared words rather than semantic embeddings, and the summary is created by concatenating text rather than generating a natural-language abstraction. The character counter also measures only recent message text. These are useful areas for future improvement. Overall, this activity strengthened my understanding of context-window management, memory lifecycle design, retrieval, and testing deterministic agent components.
