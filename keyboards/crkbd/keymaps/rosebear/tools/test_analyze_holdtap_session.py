#!/usr/bin/env python3

from __future__ import annotations

import unittest

from analyze_holdtap_session import (
    Domain,
    HoldTapObservation,
    TypedKind,
    classify_resolution,
)


class ResolutionTruthTableTest(unittest.TestCase):
    def test_resolution_truth_table(self) -> None:
        cases = [
            (True, True, "true_positive"),
            (True, False, "false_negative"),
            (False, False, "true_negative"),
            (False, True, "false_positive"),
        ]

        for domain in [Domain.MODIFIER, Domain.LAYER]:
            for typed_kind in [TypedKind.PRINTABLE, TypedKind.NONE]:
                for expected_hold, resolved_hold, expected in cases:
                    with self.subTest(
                        domain=domain,
                        typed_kind=typed_kind,
                        expected_hold=expected_hold,
                        resolved_hold=resolved_hold,
                    ):
                        obs = HoldTapObservation(
                            domain=domain,
                            expected_hold=expected_hold,
                            resolved_hold=resolved_hold,
                            target="A" if expected_hold else "a",
                            actual="A" if typed_kind == TypedKind.PRINTABLE else "",
                            mechanism="test",
                            typed_kind=typed_kind,
                            correct=True,
                        )

                        self.assertEqual(classify_resolution(obs), expected)

    def test_true_positive_with_wrong_output_keeps_resolution_but_marks_other_wrong(self) -> None:
        for domain in [Domain.MODIFIER, Domain.LAYER]:
            for typed_kind in [TypedKind.PRINTABLE, TypedKind.NONE]:
                with self.subTest(domain=domain, typed_kind=typed_kind):
                    obs = HoldTapObservation(
                        domain=domain,
                        expected_hold=True,
                        resolved_hold=True,
                        target="A",
                        actual="B" if typed_kind == TypedKind.PRINTABLE else "",
                        mechanism="test",
                        typed_kind=typed_kind,
                        correct=False,
                    )

                    self.assertEqual(classify_resolution(obs), "true_positive_other_wrong")

    def test_true_negative_with_wrong_output_keeps_resolution_but_marks_other_wrong(self) -> None:
        for domain in [Domain.MODIFIER, Domain.LAYER]:
            for typed_kind in [TypedKind.PRINTABLE, TypedKind.NONE]:
                with self.subTest(domain=domain, typed_kind=typed_kind):
                    obs = HoldTapObservation(
                        domain=domain,
                        expected_hold=False,
                        resolved_hold=False,
                        target="a",
                        actual="b" if typed_kind == TypedKind.PRINTABLE else "",
                        mechanism="test",
                        typed_kind=typed_kind,
                        correct=False,
                    )

                    self.assertEqual(classify_resolution(obs), "true_negative_other_wrong")


if __name__ == "__main__":
    unittest.main()
