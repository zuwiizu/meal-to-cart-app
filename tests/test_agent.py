"""The agent: the four endpoints, and the rules they may not bend.

The tests below are the brief's, verbatim, plus two guards the brief's own
comments ask for but could not yet check:

  * A link that could not be read is NAMED in `unresolved`. The brief's
    unresolved test iterates a list that is empty today, so it would pass while
    a failed import vanished.
  * The module isolates MTC_ROOT into tmp_path. Three of the brief's tests call
    build_week("demo", form=...), and the form is WRITTEN into the profile it
    names -- which, without isolation, is the published profiles/demo/values.json
    this repo ships. A test run must not rewrite the file the boundary test
    promises is invented and stable.
"""
from __future__ import annotations

import json

import pytest

from meal_to_cart_app.agent import build_week


@pytest.fixture(autouse=True)
def _profile_root_in_tmp(tmp_path, monkeypatch):
    """Every test in this module reads and writes under tmp_path, never the repo."""
    monkeypatch.setenv("MTC_ROOT", str(tmp_path))


def test_build_week_returns_the_four_parts():
    out = build_week("demo", links=[], form={"servings": 2, "dinners": 5})
    assert set(out) >= {"plan", "shopping", "cart_link", "unresolved"}


def test_a_save_writes_the_form_into_the_profile(tmp_path, monkeypatch):
    # Redirect through the ENGINE's root, the same one the engine reads through.
    # Monkeypatching agent.ROOT instead would prove only that the writer agrees
    # with itself, which is exactly the check that cannot catch a split path rule.
    from meal_to_cart import profile as profile_mod
    from meal_to_cart_app import agent
    monkeypatch.setenv("MTC_ROOT", str(tmp_path))
    (tmp_path / "profiles" / "new").mkdir(parents=True)
    agent.save_profile("new", {"servings": 4, "budget_weekly": 120})
    saved = json.loads(profile_mod.values_path("new").read_text())
    assert saved["plan"]["servings"] == 4
    assert saved["budget"]["weekly_target"] == 120


def test_budget_is_a_target_and_never_blocks():
    # No priced groceries means no comparison. Missing prices must not become
    # zero and make the page claim a free or under-budget week.
    out = build_week("demo", links=[], form={"budget_weekly": 1})
    b = out["budget"]
    assert b["target"] == 1.0
    assert b["blocked"] is False
    assert b["total"] is None
    assert b["over"] is None


def test_a_budget_over_target_still_produces_the_week():
    # The whole point of "target, not ceiling": being over never blocks.
    out = build_week("demo", links=[], form={"budget_weekly": 1})
    assert out["budget"]["blocked"] is False
    assert isinstance(out["shopping"], list)


def test_unresolved_lines_are_listed_never_hidden():
    out = build_week("demo", links=[], form={})
    for u in out["unresolved"]:
        assert u["line"] and u["reason"]


def test_a_link_that_could_not_be_read_is_named_not_dropped(monkeypatch):
    """A page the importer could not read is a line the week cannot be built
    from, so it is reported with its reason -- never filtered out, because a
    list shorter than the truth is the failure this app exists to prevent."""
    from meal_to_cart.importer import ImportedRecipe
    from meal_to_cart_app import agent

    unread = ImportedRecipe(
        source="https://example.invalid/recipe",
        note="could not read this link: boom",
    )
    monkeypatch.setattr(agent, "import_recipe", lambda url: unread)

    out = build_week("demo", links=[unread.source], form={})

    named = {"line": unread.source, "reason": "could not read this link: boom"}
    # "in", not "==": the week's own unresolved shopping lines belong here too,
    # and this one must stay visible beside them whatever else lands.
    assert named in out["unresolved"]
    assert out["cart_link"] is None, "a week missing a recipe is never a cart"
