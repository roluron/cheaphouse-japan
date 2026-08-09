import unittest

from ingestion.pipeline.freshness import PENDING_REGEX, SOLD_REGEX, state_updates


class FreshnessStateTests(unittest.TestCase):
    def test_sold_source_is_retained_as_unavailable(self):
        updates = state_updates("sold", checked_at="2026-08-09T00:00:00+00:00")
        self.assertEqual(updates["listing_status"], "sold")
        self.assertEqual(updates["freshness_label"], "unavailable")
        self.assertIsNotNone(updates["gone_since"])

    def test_network_error_is_uncertain_not_removed(self):
        updates = state_updates("error", previous_errors=8)
        self.assertEqual(updates["listing_status"], "uncertain")
        self.assertEqual(updates["check_error_count"], 9)
        self.assertNotIn("gone_since", updates)

    def test_active_check_resets_failures(self):
        updates = state_updates("active", previous_errors=2)
        self.assertEqual(updates["listing_status"], "active")
        self.assertEqual(updates["check_error_count"], 0)
        self.assertIsNone(updates["gone_since"])

    def test_pending_is_not_sold_or_active(self):
        self.assertIsNotNone(PENDING_REGEX.search("This home is under contract"))
        updates = state_updates("pending")
        self.assertEqual(updates["listing_status"], "uncertain")

    def test_status_patterns_cover_japanese_sources(self):
        self.assertIsNotNone(SOLD_REGEX.search("この物件は成約済です"))
        self.assertIsNotNone(PENDING_REGEX.search("現在商談中です"))


if __name__ == "__main__":
    unittest.main()

