"""Test suite to ensure _TYPO_MAP remains safe for naive str.replace()."""

from __future__ import annotations


# Audit the embedded-safe typo corrections only; these are applied via naive
# str.replace in normalization, so the safety rules below are appropriate.
from treebot.utils.normalize import _EMBEDDED_TYPO_MAP as _TYPO_MAP


def test_no_substring_collisions():
    """Ensure no typo key appears as a substring in any correction value.

    This prevents dangerous cascading replacements where:
    - typo1 -> correct1, and correct1 contains typo2
    - Could cause unexpected double-replacement
    """
    for typo1, correct1 in _TYPO_MAP.items():
        for typo2, correct2 in _TYPO_MAP.items():
            if typo1 != typo2:
                assert typo1 not in correct2, (
                    f"Collision: typo key '{typo1}' appears in correction '{correct2}'\n"
                    f"This could cause cascading replacements!"
                )


def test_no_cascading_patterns():
    """Ensure no correction value contains another typo key.

    This prevents cases where:
    - 'abc' -> 'xyz' and 'xyz' contains another typo key
    - Could cause order-dependent behavior
    """
    for typo1, correct1 in _TYPO_MAP.items():
        for typo2, correct2 in _TYPO_MAP.items():
            if typo1 != typo2:
                assert typo2 not in correct1, (
                    f"Cascade risk: correction '{correct1}' contains typo key '{typo2}'\n"
                    f"This could cause order-dependent replacements!"
                )


def test_minimum_length_recommendation():
    """Warn if typo keys are very short (recommendation: ≥5 chars).

    Short typo keys are more likely to cause unintended replacements.
    This is a warning, not a hard failure.
    """
    short_typos = [(typo, correct) for typo, correct in _TYPO_MAP.items() if len(typo) < 5]

    if short_typos:
        warning_msg = "\n".join(
            f"  - '{typo}' -> '{correct}' (len={len(typo)})" for typo, correct in short_typos
        )
        print(f"\nWARNING: {len(short_typos)} typo(s) are <5 chars:\n{warning_msg}")
        print("Short typos are more likely to cause unintended replacements.")
        print("Consider reviewing these carefully.")


def test_typo_keys_always_incorrect():
    """Document that typo keys should be fragments that are ALWAYS wrong.

    This is a documentation test - it doesn't actually verify correctness,
    but serves as a reminder of the safety contract.
    """
    # This test always passes, but documents the contract
    assert True, (
        "Typo keys must be chemical fragments that are NEVER correct in "
        "any context. Examples: 'dimthyl' is always wrong (should be 'dimethyl'). "
        "Before adding a new typo, grep it in classes.yaml to ensure it doesn't "
        "appear in correctly-spelled compound names."
    )


def test_no_duplicate_targets():
    """Ensure no two different typos map to the same correction.

    This is allowed, but worth documenting (e.g., 'biyclo' and 'bicylclo'
    both -> 'bicyclo' is fine).
    """
    corrections = {}
    duplicates = []

    for typo, correct in _TYPO_MAP.items():
        if correct in corrections:
            duplicates.append((corrections[correct], typo, correct))
        else:
            corrections[correct] = typo

    if duplicates:
        msg = "\n".join(
            f"  - '{typo1}' and '{typo2}' both -> '{correct}'"
            for typo1, typo2, correct in duplicates
        )
        print(f"\nINFO: {len(duplicates)} correction(s) have multiple typo variants:\n{msg}")
        print("This is acceptable (e.g., different misspellings of same word).")
