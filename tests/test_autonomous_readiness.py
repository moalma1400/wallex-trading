import unittest

from wallex_research.autonomous_readiness import REQUIRED_EVIDENCE, evaluate_live_readiness


class AutonomousReadinessTests(unittest.TestCase):
    def complete_evidence(self):
        return {key: True for key in REQUIRED_EVIDENCE}

    def test_default_empty_evidence_blocks(self):
        result = evaluate_live_readiness(
            {}, kill_switch_enabled=True, challenge_window_active=False,
            configuration_hash=None, tool_contract_version=None,
        )
        self.assertFalse(result.ready)
        self.assertIn("KILL_SWITCH_ACTIVE_OR_UNKNOWN", result.reason_codes)
        self.assertIn("CONFIGURATION_HASH_MISSING", result.reason_codes)

    def test_all_explicit_gates_are_required(self):
        evidence = self.complete_evidence()
        evidence["order_tool_schemas_verified"] = False
        result = evaluate_live_readiness(
            evidence, kill_switch_enabled=False, challenge_window_active=True,
            configuration_hash="sha256:config", tool_contract_version="smart98-contract-v1",
        )
        self.assertFalse(result.ready)
        self.assertIn("MISSING_OR_UNVERIFIED_ORDER_TOOL_SCHEMAS_VERIFIED", result.reason_codes)

    def test_ready_is_only_a_readiness_snapshot(self):
        result = evaluate_live_readiness(
            self.complete_evidence(), kill_switch_enabled=False,
            challenge_window_active=True, configuration_hash="sha256:config",
            tool_contract_version="smart98-contract-v1",
        )
        self.assertTrue(result.ready)
        self.assertEqual(result.reason_codes, ())


if __name__ == "__main__":
    unittest.main()
