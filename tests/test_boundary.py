"""Nothing this repository publishes may carry a real household value.

The rule the split exists for: the demo values are invented, and no ZIP, city,
store id, store name or any other household fact may ever reach this repo. That
is a claim about every published byte, so it is checked rather than trusted.

Two things this test deliberately does NOT do, both learned the hard way:

  * It does not write the forbidden values down. A test that hardcodes the
    strings it searches for matches ITSELF and fails forever -- the guard would
    be the leak. The terms are read from a gitignored file, and the engine's own
    data/private-terms.txt is where they already live.
  * It does not fail when that file is absent. A fresh clone and the published
    tree have no private terms by design, and a guard that always fails is worse
    than one that skips and says so. The shape scan below runs either way, so
    this module never reports "nothing to see" merely because it skipped a scan.

It scans the paths that are actually published, not the whole working copy: a
scan of the whole tree would have to read the term list itself, which is the
self-match bug one line up.
"""
from __future__ import annotations

import pytest

from meal_to_cart import guard
from meal_to_cart_app import ROOT

# A developer may keep this repo's own list; the engine's gitignored list is the
# fallback, so the terms normally live in exactly one place. Precedence, never a
# merge: two half-lists combined would hide which file is actually authoritative,
# which is the one-store-per-fact rule household.preferences() already follows.
TERMS_HERE = ROOT / ".private-terms.txt"

# Everything that ships when this repository is published or zipped. The VCS
# directory, the installed environment and the caches are left out (guard.scan
# skips them too), and the term list itself is left out because it is the one
# file that must contain the terms.
PUBLISHED = (
    "src",
    "tests",
    "profiles",
    "site",
    "pyproject.toml",
    "uv.lock",
    "README.md",
    "SETUP.md",
    "VIDEO.md",
    ".github",
)


def _published_paths() -> list:
    return [ROOT / name for name in PUBLISHED if (ROOT / name).exists()]


def _terms() -> list[str]:
    """The real terms, or [] when this checkout holds none.

    A gitignored file still rides along in a zip of the folder, so the default
    source is the ENGINE's list, which lives outside this repository entirely.
    """
    if TERMS_HERE.is_file():
        return [
            line.strip().lower()
            for line in TERMS_HERE.read_text().splitlines()
            if line.strip() and not line.startswith("#")
        ]
    return guard.load_terms()


def test_no_private_term_reaches_a_published_path():
    terms = _terms()
    if not terms:
        pytest.skip(
            "no private terms in this checkout: the list is gitignored in both "
            "repos, so a fresh clone has nothing to search for. The shape scan "
            "below still runs."
        )
    hits = guard.scan(_published_paths(), terms=terms)
    assert not hits, (
        "a real household value reached a published path: "
        + repr(hits)
        + ". The demo profile's values must be invented."
    )


def test_the_guard_skips_rather_than_fails_without_the_terms(monkeypatch, tmp_path):
    """A guard that always fails is worse than one that skips and says so.

    A fresh clone, the published tree and CI all have no private terms -- by
    design, since the list is gitignored in both repos. Failing there would mean
    every clone is broken; passing silently would mean nobody is watching. So it
    skips, and this pins that: the skip is the contract, not an accident.
    """
    import sys

    absent = tmp_path / "no-such-terms.txt"
    boundary = sys.modules[__name__]          # this module, whatever pytest named it
    monkeypatch.setattr(boundary, "TERMS_HERE", absent)
    monkeypatch.setattr(guard, "TERMS_FILE", absent)

    with pytest.raises(pytest.skip.Exception):
        boundary.test_no_private_term_reaches_a_published_path()


def test_no_published_path_carries_a_secret_shape():
    """Runs without any private terms: these are patterns, not words.

    An address, an email or a postal code is a household value whatever it says,
    so the engine's own shape patterns are applied to the published paths here,
    on every run, in every clone.
    """
    hits = guard.scan(_published_paths(), terms=[])
    assert not hits, (
        "a published path carries a value shaped like private data: "
        + repr(hits)
        + ". Use invented placeholders."
    )
