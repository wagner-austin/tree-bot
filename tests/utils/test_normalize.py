from __future__ import annotations

from treebot.utils.normalize import normalize_text


def test_normalize_text_basic() -> None:
    assert normalize_text("  Foo  ") == "foo"
    assert normalize_text("a ,  b") == "a, b"
    assert normalize_text("a -  b") == "a-b"


def test_normalize_text_greek() -> None:
    assert normalize_text("alpha") == "alpha"
    assert normalize_text("β-pinene") == "beta-pinene"
