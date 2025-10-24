"""Audit class mappings to identify potentially incorrect entries.

This is a heuristic lint tool with expected false positives.
Treat output as advisory, not authoritative.
"""

from __future__ import annotations

import re
import yaml
from pathlib import Path
from collections import defaultdict
from typing import Mapping, MutableMapping, Sequence

# Canonicalize class synonyms
CANON: Mapping[str, str] = {
    "carboxylic_acid": "organic.acid",
    "silicone": "siloxane",
    "organosiloxane": "siloxane",
}

# Ordered rules: more specific patterns first
# Each rule: (regex, set of acceptable classes)
RULES: Sequence[tuple[re.Pattern[str], set[str]]] = [
    (re.compile(r"thiol$", re.I), {"thiol"}),
    (re.compile(r"\boic acid\b", re.I), {"organic.acid"}),
    (re.compile(r"\bacid\b", re.I), {"organic.acid"}),  # after oic acid
    (re.compile(r"al$", re.I), {"aldehyde"}),
    (re.compile(r"one$", re.I), {"ketone", "monoterpenoid"}),
    (re.compile(r"ol$", re.I), {"alcohol", "monoterpenoid"}),  # after thiol$
    (re.compile(r"yne$", re.I), {"alkyne"}),
    (
        re.compile(r"ene$", re.I),
        {"alkene", "monoterpene", "sesquiterpene", "terpene", "aromatic", "monoterpenoid"},
    ),
    (
        re.compile(r"ane$", re.I),
        {
            "alkane",
            "monoterpene",
            "sesquiterpene",
            "organosilicon",
            "siloxane",
            "epoxide",
            "halogen",
        },
    ),
    (re.compile(r"siloxane", re.I), {"siloxane"}),
    (re.compile(r"pinene", re.I), {"monoterpene"}),
    (re.compile(r"caryophyllene", re.I), {"sesquiterpene"}),
    (re.compile(r"\b(fluoro|chloro|bromo|iodo)", re.I), {"halogen"}),
    (re.compile(r"benzene", re.I), {"aromatic", "halogen", "monoterpenoid"}),
]


def load_mappings() -> Mapping[str, str]:
    """Load class mappings from classes.yaml."""
    p = Path(__file__).resolve().parent.parent / "configs" / "classes.yaml"
    with p.open("r", encoding="utf-8") as f:
        content = f.read()
        if content.startswith("\ufeff"):
            content = content[1:]
        data = yaml.safe_load(content) or {}
    m = data.get("map", {})
    if not isinstance(m, dict):
        raise ValueError("classes.yaml: top-level 'map' must be a dict")
    # Normalize key/value types to str
    out: MutableMapping[str, str] = {}
    for k, v in m.items():
        if isinstance(k, str) and isinstance(v, str):
            out[k] = v
    return out


def canon(cls: str) -> str:
    """Canonicalize class name."""
    return CANON.get(cls, cls)


def expected_classes(name: str) -> set[str]:
    """Return set of acceptable classes based on heuristics."""
    out = set()
    for rx, classes in RULES:
        if rx.search(name):
            out |= {canon(c) for c in classes}
    return out


def audit_mappings() -> None:
    """Audit mappings and report potential issues."""
    mappings = {k: canon(v) for k, v in load_mappings().items()}

    by_class = defaultdict(list)
    for compound, cls in mappings.items():
        by_class[cls].append(compound)

    print("=" * 80)
    print("CLASS MAPPING AUDIT REPORT")
    print("=" * 80)
    print(f"\nTotal compounds: {len(mappings)}")
    print(f"Total classes: {len(by_class)}")
    print("\nClass distribution:")
    for cls, compounds in sorted(by_class.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"  {cls:25s} : {len(compounds):3d} compounds")

    issues = []
    for compound, cls in sorted(mappings.items()):
        name = compound.strip().lower()
        exp = expected_classes(name)
        if not exp:
            continue  # no heuristic applies
        if cls not in exp:
            issues.append((compound, cls, f"heuristics suggest {sorted(exp)}"))

    if issues:
        print("\n" + "=" * 80)
        print("POTENTIALLY INCORRECT MAPPINGS (heuristic-based)")
        print("=" * 80)
        print("\nNOTE: These are advisory only. Many 'issues' are false positives due to")
        print("      chemical naming exceptions (aromatics, terpenes, siloxanes, etc.)")
        for compound, cls, reason in issues:
            print(f"\n[!] {compound}")
            print(f"    Current: {cls}")
            print(f"    Issue:   {reason}")
        print(f"\n[!] Found {len(issues)} potentially incorrect mappings to review")
    else:
        print("\n[OK] No obvious mapping issues found!")

    # Show short single-token entries (possible substring keys)
    fragments = []
    for compound, cls in mappings.items():
        token = compound.strip()
        if (
            " " not in token
            and "," not in token
            and "[" not in token
            and not any(c.isdigit() for c in token)
        ):
            if len(token) <= 10:  # tighter threshold
                fragments.append((compound, cls))

    if fragments:
        print("\n" + "=" * 80)
        print("SHORT SINGLE-TOKEN ENTRIES (possible substring matching keys)")
        print("=" * 80)
        print(f"\nFound {len(fragments)} short entries (used for substring matching):")
        for compound, cls in sorted(fragments)[:20]:
            print(f"  {compound:30s} -> {cls}")
        if len(fragments) > 20:
            print(f"  ... and {len(fragments) - 20} more")

    print("\n" + "=" * 80)
    print("AUDIT COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    audit_mappings()
