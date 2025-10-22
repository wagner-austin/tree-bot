from __future__ import annotations

import re
import unicodedata
from typing import Final


# Map common Greek letters to ASCII tokens
_GREEK_MAP: Final[dict[str, str]] = {
    "α": "alpha",
    "β": "beta",
    "γ": "gamma",
    "δ": "delta",
    "ε": "epsilon",
    "μ": "mu",
    "π": "pi",
}


def _fold_greek(text: str) -> str:
    for k, v in _GREEK_MAP.items():
        text = text.replace(k, v)
    return text


def normalize_text(value: str) -> str:
    """Generic normalization (kept for non-compound use cases).

    Steps:
    - unicode normalize (NFKC)
    - fold Greek letters
    - lowercase, trim
    - collapse internal whitespace
    - normalize comma/hyphen spacing
    - strip trailing punctuation/hyphens
    """
    s = unicodedata.normalize("NFKC", value)
    s = _fold_greek(s)
    s = s.lower().strip()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\s*,\s*", ", ", s)
    s = re.sub(r"\s*-\s*", "-", s)
    s = re.sub(r"[\s\-\.,;:]+$", "", s)
    return s


_STEREOCHEM_PAREN_RE = re.compile(r"\((?:r|s|e|z|cis|trans)\)")

# Common typos found in compound names - TWO-PASS CORRECTION
#
# IMPLEMENTATION NOTE: Split typo handling for safety
# =====================================================
# We apply typos in two passes to prevent over-correction:
#
# 1. EMBEDDED-SAFE CORRECTIONS (applied first via str.replace)
#    - Typos that are safe to fix anywhere in a word
#    - Examples: 'trilfluoro' → 'trifluoro' (safe in 'trifluoromethyl')
#               'cabox' → 'carbox' (safe in 'carboxaldehyde')
#               'cylcotri' → 'cyclotri' (safe in 'cyclotrisiloxane')
#    - These are specific chemical fragments that are NEVER correct
#
# 2. TOKEN-BOUNDED CORRECTIONS (applied second via regex)
#    - Typos that should ONLY match complete tokens/words
#    - Examples: 'camphenon' → 'camphenone' (would cascade inside 'camphenone')
#               'benzen' → 'benzene' (standalone word, not in 'benzene')
#    - Use token boundaries (?<![a-z0-9])...(?![a-z0-9]) to prevent cascades
#
# SAFETY GUIDELINES when adding new typos:
# ========================================
# ✓ Embedded-safe (str.replace):
#   - Mid-word OCR errors: 'trilfluoro', 'mtehoxy', 'cabox'
#   - Bracket typos: 'bicyclo[3.1.10]' → 'bicyclo[3.1.0]'
#   - Never appear in correct compound names
#
# ✓ Token-bounded (regex):
#   - Whole-word misspellings: 'bezene', 'camphenon', 'ponene'
#   - Could cascade if applied mid-word
#   - Spacing/punctuation fixes: 'benzene1-ethyl' → 'benzene, 1-ethyl'
#
# ✗ DON'T normalize:
#   - Chemical identity changes: 'menthyl' → 'methyl', 'cendrene' → 'cedrene'
#   - Map both spellings in classes.yaml instead
#
# BEFORE ADDING: grep the pattern in classes.yaml to ensure it doesn't
# appear in correctly-spelled compound names
#

# Embedded-safe corrections: specific substrings safe to fix mid-word
_EMBEDDED_TYPO_MAP: Final[dict[str, str]] = {
    # Halogen/fluoro family (appear in trifluoromethyl, perfluorooctane, etc.)
    "trulfuoro": "trifluoro",
    "trilfluoro": "trifluoro",
    "perfuoro": "perfluoro",
    "dilfuoro": "difluoro",
    "tricloromono": "trichloromono",  # trichloromonofluoromethane, etc.
    # Cyclohexane family
    "oxyxyclohexane": "oxycyclohexane",  # trifluoroacet-oxyxyclohexane
    "cylcotri": "cyclotri",  # cylcotrisiloxane → cyclotrisiloxane
    "cyclohexne": "cyclohexene",
    "cycolohexene": "cyclohexene",
    # Bracket/index typos
    "bicyclo[3.1.10]": "bicyclo[3.1.0]",
    "bicyclo[3.10]": "bicyclo[3.1.0]",  # shorter variant of same typo
    # Common embedded fragments
    "cabox": "carbox",  # carboxaldehyde, carboxamide, etc.
    "mtehoxy": "methoxy",  # dimethoxy, trimethoxy, etc.
    "mthyl": "methyl",  # mthyl ethyl → methyl ethyl
    "tetradecultri": "tetradecyltri",  # tetradecyltrimethylammonium
    "dimthyl": "dimethyl",  # appears in many compounds
    "ethlidene": "ethylidene",  # methylethylidene
    "ethyidene": "ethylidene",  # methylethylidene
    "carboyxlic": "carboxylic",  # carboxylic acid
    "dimethyoxy": "dimethoxy",  # various compounds
    # Misc embedded
    "oct-1-ee": "oct-1-ene",
    "ethandiyl": "ethanediyl",
}

# Token-bounded corrections: only match when typo is a complete token
_TOKEN_TYPO_MAP: Final[dict[str, str]] = {
    # Benzene family (avoid matching inside correct 'benzene...')
    "benzen": "benzene",  # standalone 'benzen' → 'benzene'
    "bezene": "benzene",
    "benene": "benzene",
    "bnzene": "benzene",
    "bezeneethanamine": "benzeneethanamine",
    "benzene1-ethyl": "benzene, 1-ethyl",
    # Prevent cascades (classic case: camphenon → camphenone → camphenonee)
    "camphenon": "camphenone",
    "hentriacontan": "hentriacontane",
    # Bicyclo family
    "biyclo": "bicyclo",
    "bicylclo": "bicyclo",
    # Whole-word misspellings
    "pyyrole": "pyrrole",
    "pentaden": "pentadien",
    "thukene": "thujene",
    "methlethylidene": "methylethylidene",
    "cycloocatatetraene": "cyclooctatetraene",
    "cycloocatadiene": "cyclooctadiene",
    "oacetoxyxyclohexane": "oacetoxycyclohexane",  # specific complete token
    "xyclohexane": "cyclohexane",
    "pentadioene": "pentadiene",
    "ponene": "pinene",
    "butanl,": "butanol,",
    "cyclpbutane": "cyclobutane",
    "imidazhol": "imidazol",
    "imidaole": "imidazole",
    "carbonic aid": "carbonic acid",
    "aminomethanesulfonic aid": "aminomethanesulfonic acid",
    "butenedinitrle": "butenedinitrile",
    "cycloprpane": "cyclopropane",
    "heptanthiol": "heptanethiol",
    "teprinene": "terpinene",
    "methyethyl": "methylethyl",
    "hexen1-ol": "hexen-1-ol",
    "butan, 1-ethoxy": "butane, 1-ethoxy",
    "4-hydroxy=": "4-hydroxy",
    "trazolo": "triazolo",
    "3, 35-trimethyl": "3, 3, 5-trimethyl",
    "cyclohexene 1,": "cyclohexene, 1,",  # spacing fix
    "esther": "ester",
    "hyrazide": "hydrazide",
    "eucalpytol": "eucalyptol",
    "1, 10dimethylethoxy": "1, 1-dimethylethoxy",
}


# Back-compatibility: expose a single _TYPO_MAP for audit tests
# This map must be safe for naive str.replace, so we only include the
# embedded-safe corrections here. Token-bounded fixes remain separate.


def normalize_compound_name(value: str) -> str:
    """Normalization tailored for compound names.

    Non-destructive formatting (no synonym mapping):
    - Unicode normalize (NFKC)
    - Fold Greek letters (α→alpha, etc.)
    - Lowercase, trim
    - Strip leading punctuation (hyphens, dashes, commas, spaces)
    - Fix common typos in two passes:
      1. Embedded-safe: trilfluoro→trifluoro, cabox→carbox (anywhere in word)
      2. Token-bounded: benzen→benzene, camphenon→camphenone (complete tokens only)
    - Fix scoped typos (2h-puran→2h-pyran)
    - Remove bare stereochemistry tags in parentheses: (r),(s),(e),(z),(cis),(trans)
    - Unify missing hyphens before functional groups: -3one → -3-one
    - Collapse internal whitespace
    - Normalize comma spacing to ", " and hyphens with no surrounding spaces
    - Strip trailing instrument run tokens: ...)-96, ...] 72, ...methylene0
    - Strip trailing punctuation/hyphens
    """
    s = unicodedata.normalize("NFKC", value)
    s = _fold_greek(s)
    s = s.lower().strip()

    # Strip leading punctuation (hyphens, dashes, en-dash, em-dash, commas, spaces)
    s = re.sub(r"^[\s,–—-]+", "", s)

    # Fix common typos: TWO-PASS APPROACH
    # Pass 1: Embedded-safe corrections (simple string replacement)
    # These typos are safe to fix anywhere in a word (e.g., 'trilfluoro' in 'trifluoromethyl')
    for typo, correct in _EMBEDDED_TYPO_MAP.items():
        s = s.replace(typo, correct)

    # Pass 2: Token-bounded corrections (regex with word boundaries)
    # These typos should only match complete tokens to prevent cascading
    # (e.g., 'camphenon' → 'camphenone', but not inside 'camphenone')
    for typo, correct in _TOKEN_TYPO_MAP.items():
        pat = rf"(?<![a-z0-9]){re.escape(typo)}(?![a-z0-9])"
        s = re.sub(pat, correct, s)

    # Fix scoped puran→pyran (only in contexts like "2h-puran")
    s = re.sub(r"\b(\d+h)-puran\b", r"\1-pyran", s)

    # Remove bare stereochem markers in parentheses
    s = _STEREOCHEM_PAREN_RE.sub("", s)

    # Unify missing hyphens before functional groups (e.g., -3one → -3-one)
    # Safe: only fires on "-<digits><suffix>" at a token boundary
    # Note: methylene before ylene to match the full suffix first
    s = re.sub(
        r"-(\d+)(methylene|one|ol|al|yl|ylene|ylidene|oic|oate|amine|amide|enone|dione|diol)(?=\s|,|;|:|$|[\)\]-])",
        r"-\1-\2",
        s,
    )

    # Collapse whitespace
    s = re.sub(r"\s+", " ", s)

    # Normalize separators
    s = re.sub(r"\s*,\s*", ", ", s)
    s = re.sub(r"\s*-\s*", "-", s)

    # Fix erroneous trailing bracket after stereochem pattern at end:
    # ", ( ... )]$" (missing opening '[' earlier). Remove the final ']'.
    s = re.sub(r"(, \([^)]+\))\]$", r"\1", s)

    # Strip trailing run tokens after brackets/parens (e.g., "...)-96", "] 72")
    s = re.sub(r"([)\]])(?:-|_|\s)?\d{1,3}$", r"\1", s)

    # Strip lone trailing zero after a letter at end (e.g., "methylene0")
    s = re.sub(r"([a-z])0$", r"\1", s)

    # Strip trailing punctuation/hyphens
    s = re.sub(r"[\s\-\.,;:]+$", "", s)
    return s
