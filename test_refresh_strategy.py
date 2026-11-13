
import unittest

from refresh_strategy import (
    RefreshManager,
    SimpleVectorStore,
    Message
)


class TestRefreshStrategy(unittest.TestCase):

    def test_messages_below_threshold(self):
        manager = RefreshManager(threshold=6, keep_recent=3)

        manager.add_message("user", "Hello")
        manager.add_message("assistant", "Hi")
        manager.add_message("user", "How are you?")

        self.assertEqual(manager.refresh_count, 0)
        self.assertEqual(len(manager.state.short_term), 3)

    def test_threshold_refresh(self):
        manager = RefreshManager(threshold=3, keep_recent=2)

        for index in range(4):
            manager.add_message("user", f"Message {index}")

        self.assertEqual(manager.refresh_count, 1)
        self.assertEqual(len(manager.state.short_term), 2)

    def test_summary_updated(self):
        manager = RefreshManager(threshold=2, keep_recent=1)

        manager.add_message("user", "The project goal is testing.")
        manager.add_message("user", "This is another message.")
        manager.add_message("user", "Trigger refresh.")

        self.assertIn("project goal", manager.state.summary.lower())

    def test_durable_fact_storage(self):
        manager = RefreshManager(threshold=2, keep_recent=1)

        manager.add_message("user", "The project goal is testing.")
        manager.add_message("user", "Another message.")
        manager.add_message("user", "Trigger refresh.")

        self.assertIn(
            "The project goal is testing.",
            manager.state.long_term
        )

    def test_retrieve_by_query(self):
        store = SimpleVectorStore()

        store.add("The project goal is to build an AI agent.")
        store.add("The deadline is Friday.")

        results = store.search("project goal")

        self.assertTrue(results)
        self.assertIn("project goal", results[0][1].lower())

    def test_context_reconstruction(self):
        manager = RefreshManager(threshold=2, keep_recent=1)

        manager.add_message("user", "The project goal is testing.")
        manager.add_message("assistant", "We need a refresh.")
        context = manager.add_message("user", "Trigger refresh.")

        self.assertIn("summary", context)
        self.assertIn("retrieved_memory", context)
        self.assertIn("recent_messages", context)

    def test_repeated_refresh(self):
        manager = RefreshManager(threshold=2, keep_recent=1)

        manager.add_message("user", "The project goal is testing.")
        manager.add_message("user", "Another message.")
        manager.add_message("user", "Trigger one.")

        manager.manual_refresh("project")

        self.assertEqual(manager.refresh_count, 2)

        normalized = [
            fact.casefold()
            for fact in manager.state.long_term
        ]

        self.assertEqual(len(normalized), len(set(normalized)))

    def test_empty_query_retrieval(self):
        store = SimpleVectorStore()

        store.add("The project goal is testing.")

        self.assertEqual(store.search(""), [])

    def test_manual_refresh_reason(self):
        manager = RefreshManager(threshold=6, keep_recent=3)

        manager.add_message("user", "The project goal is testing.")

        manager.manual_refresh("project")

        self.assertEqual(
            manager.refresh_events[-1]["reason"],
            "manual"
        )

    def test_context_size(self):
        manager = RefreshManager(
            threshold=10,
            keep_recent=2,
            max_chars=500
        )

        manager.add_message("user", "Hello")
        manager.add_message("assistant", "Welcome")

        self.assertEqual(manager.context_size(), 12)

    def test_context_size_refresh(self):
        manager = RefreshManager(
            threshold=10,
            keep_recent=1,
            max_chars=10
        )

        manager.add_message("user", "123456")
        manager.add_message("assistant", "789012")

        self.assertEqual(manager.refresh_count, 1)

        self.assertEqual(
            manager.refresh_events[-1]["reason"],
            "context_size"
        )

    def test_invalid_threshold(self):
        with self.assertRaises(ValueError):
            RefreshManager(threshold=0)

    def test_invalid_keep_recent(self):
        with self.assertRaises(ValueError):
            RefreshManager(threshold=3, keep_recent=4)

    def test_duplicate_vector_store_items(self):
        store = SimpleVectorStore()

        store.add("Project goal")
        store.add("Project goal")

        self.assertEqual(len(store.items), 1)

    def test_duplicate_fact_storage(self):
        manager = RefreshManager()

        manager.store_facts(["Project goal"])
        manager.store_facts(["project goal"])

        self.assertEqual(len(manager.state.long_term), 1)

    def test_empty_manual_refresh(self):
        manager = RefreshManager()

        context = manager.manual_refresh("project")

        self.assertEqual(manager.refresh_count, 0)
        self.assertEqual(context["recent_messages"], [])

    def test_case_insensitive_retrieval(self):
        store = SimpleVectorStore()

        store.add("The Project Goal is testing.")

        results = store.search("PROJECT GOAL")

        self.assertEqual(len(results), 1)


if __name__ == "__main__":
    unittest.main()
