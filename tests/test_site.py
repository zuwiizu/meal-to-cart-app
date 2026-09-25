"""The page: three beats, no framework, and every claim it makes must be true.

These assertions are about things that would fail silently in a browser. A page
that drops "import " into app.js, that loads a stylesheet from a CDN, that
prints the promise line with a word changed, or that ships an unlabelled input,
still LOOKS fine -- which is exactly why each one is pinned here.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from meal_to_cart_app import ROOT

SITE = ROOT / "site"


# --- the brief's four ------------------------------------------------------


def test_three_beats_are_present():
    html = (SITE / "index.html").read_text()
    for beat in ("Bring your recipes", "Tell us about your week", "Build my week"):
        assert beat in html


def test_the_page_needs_no_framework():
    js = (SITE / "app.js").read_text()
    assert "import " not in js
    assert "require(" not in js


def test_no_credential_field_anywhere():
    html = (SITE / "index.html").read_text().lower()
    for bad in ("password", 'type="password"', "login"):
        assert bad not in html


def test_the_refusal_copy_is_present_verbatim():
    js = (SITE / "app.js").read_text()
    assert "a cart with holes in it is worse than none" in js


# --- the promises that are easy to break quietly ---------------------------


def test_the_promise_line_is_verbatim_in_the_html():
    html = (SITE / "index.html").read_text()
    assert (
        "Nothing is ordered without you. The link opens in your own browser "
        "and you check out."
    ) in " ".join(html.split())


def test_the_refusal_sentence_is_whole_not_half():
    # The invariant names the entire sentence. A page that prints only the
    # colourful half -- "a cart with holes in it is worse than none" -- would
    # pass the check above while dropping the actual decision it reports.
    js = (SITE / "app.js").read_text()
    assert "No link was emitted: a cart with holes in it is worse than none." in js


def test_the_locked_palette_is_used_exactly():
    css = (SITE / "app.css").read_text()
    locked = {
        "--paper": "#FBF8F3",
        "--ink": "#1F1B16",
        "--muted": "#6B6154",
        "--line": "#E7DFD3",
        "--accent": "#C2410C",
        "--ok": "#15803D",
        "--warn": "#B45309",
    }
    for name, value in locked.items():
        assert re.search(rf"{re.escape(name)}\s*:\s*{value}\s*;", css), name


def test_the_page_never_reaches_the_network_on_its_own():
    # Manifest: no CDN, no font host, no analytics, no protocol-relative URL.
    html = (SITE / "index.html").read_text()
    assert not re.search(r'(?:src|href)\s*=\s*["\']https?://', html)
    assert not re.search(r'(?:src|href)\s*=\s*["\']//', html)
    assert "<style" not in html, "styles belong in app.css where they can be reviewed"
    css = (SITE / "app.css").read_text()
    assert "@import" not in css, "one stylesheet, and nothing fetched by it"
    assert "url(" not in css, "no remote or embedded assets"


def test_every_control_has_a_label():
    html = (SITE / "index.html").read_text()
    controls = set(
        re.findall(r'<(?:input|select|textarea)\b[^>]*\sid="([^"]+)"', html)
    )
    labelled = set(re.findall(r'<label\b[^>]*\sfor="([^"]+)"', html))
    assert controls, "no controls found at all"
    assert controls <= labelled, sorted(controls - labelled)


# The page is published, so the engine's own guard runs over it. Two things this
# deliberately does NOT do, both learned from the defect this repository already
# paid for once (recorded as ruling R4 in the plan's ledger):
#
#   * It does not write the forbidden words down. A test that hardcodes the
#     strings it searches for matches ITSELF -- the first version of this file
#     contained the banned stems as literals and made tests/test_boundary.py
#     report a privacy violation that did not exist. The terms are read from the
#     engine's gitignored list, which is the one place they already live.
#   * It skips rather than fails when that list is absent, and the shape scan
#     below runs either way, so this module never reports "nothing to see"
#     merely because it skipped a scan.


def test_no_banned_term_reaches_the_published_page():
    from meal_to_cart import guard

    terms = guard.load_terms()
    if not terms:
        pytest.skip(
            "no term list in this checkout: it is gitignored in both repos, so a "
            "fresh clone has nothing to search for. The shape scan below still runs."
        )
    hits = guard.scan([SITE], terms=terms)
    assert not hits, "the page carries a term that must never be published: " + repr(hits)


def test_the_page_carries_nothing_shaped_like_private_data():
    from meal_to_cart import guard

    # Patterns, not words: an address, an email, a session cookie or a postal
    # code is private whatever it says, so this one never skips.
    hits = guard.scan([SITE], terms=[])
    assert not hits, "the page carries a value shaped like private data: " + repr(hits)


def test_the_confidence_is_always_shown_never_dressed_up():
    # R1 plus the page's governing rule: an unreadable page is reported with its
    # reason, never rendered as a successful import with zero ingredients.
    js = (SITE / "app.js").read_text()
    assert "confidence" in js
    assert "note" in js, "the importer's reason must have somewhere to go"
