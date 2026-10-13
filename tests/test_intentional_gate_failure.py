"""INTENTIONAL NEGATIVE CI TEST — NEVER MERGE THIS BRANCH.

This test exists solely to verify that a failing safety matrix also fails
the afa-merge-gate aggregate check. Never copy to main or production.
"""
import unittest

class FailClosedGateProbe(unittest.TestCase):
    def test_negative_gate_rejects_failed_matrix(self):
        self.fail("INTENTIONAL_NEGATIVE_CI_GATE_PROBE_DO_NOT_MERGE")
