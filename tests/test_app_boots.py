"""This repo boots on its own, and every value in it is invented.

Each assertion is a way the private/public split could be quietly fake:

1. ROOT is THIS repo, not the household's. A path that resolved one level too
   far up would make every "the app ships X" claim below a claim about the
   private tree instead.
2. The engine imports with the personal repository nowhere in the import path.
   If importing meal_to_cart needed the household's tree, the engine would still
   be two things wearing one name.
3. The demo values SAY they are fiction, in the file itself. A reader has to be
   able to tell without asking anyone.
4. The engine declares a home for every slot a real user needs. A slot the
   engine never names is a feature nobody can have; recipes is the one the DEMO
   deliberately ships without, because the demo brings links instead.
5. The demo provides the slots it actually ships -- values and rules, and
   deliberately not recipes.json, which would misrepresent the product.
6. Those values are reached through the ENGINE's own profile resolver, not
   through a path this repo built for itself. A hand-built second path is the
   drift defect the engine's profile.py documents.
7. The rules slot is real: the engine's own reader loads it and it rejects
   something. A file the engine cannot read is a slot that only looks filled.
8. The app cannot reach the household's private profile at all. That is the
   split made structural: MTC_ROOT is set at import, so the engine's profile
   root for this process is this repository.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from meal_to_cart import profile
from meal_to_cart_app import ROOT

DEMO = ROOT / "profiles" / "demo"


def test_app_root_is_the_app_repo():
    assert (ROOT / "pyproject.toml").exists()
    assert (ROOT / "profiles").is_dir()


def test_the_engine_imports_without_the_personal_repo():
    # The engine must carry no household values. If this import needs the
    # personal tree, the split has failed.
    from meal_to_cart import gateway, mealplan
    assert gateway.WALMART.id_field


def test_demo_values_are_invented():
    v = json.loads((DEMO / "values.json").read_text())
    assert v["_what"], "values must say they are invented"
    assert "invented" in v["_what"].lower()


def test_the_engine_declares_every_slot_a_user_would_need():
    # The engine must declare a home for a real user's recipes even though the
    # demo profile ships without any -- an unspecified slot is a missing feature.
    assert {"values", "rules", "recipes"} <= set(profile.FILES)


def test_the_demo_profile_provides_the_slots_it_claims():
    # Exactly the slots this task creates. Deliberately NOT recipes: the demo
    # ships values and rules, and imports its recipes from links at run time.
    for slot in ("values", "rules"):
        assert (DEMO / profile.FILES[slot]).exists(), slot


def test_the_engine_finds_the_demo_values_in_this_repo():
    """The demo values are reached the way the engine reaches ANY profile.

    A path this repo built by hand would be a second copy of the rule, and the
    engine would not be reading it. So this asks the engine where the file is
    and then asks the engine to read it.
    """
    from meal_to_cart import household

    assert profile.values_path("demo") == DEMO / "values.json"
    stated = json.loads((DEMO / "values.json").read_text())["preferences"]
    prefs = household.preferences("demo")
    assert prefs.likes == stated["likes"]
    assert prefs.dislikes == stated["dislikes"]
    assert prefs.likes, "a demo profile that stated nothing would prove nothing"


def test_the_demo_rules_are_in_the_engines_own_format():
    """A rules file the engine cannot read is a slot that only looks filled.

    The engine's reader takes name/tokens per rule, not id/match; this asserts
    the reader, not the file's appearance, so the demo profile is one the engine
    can actually plan with.
    """
    from meal_to_cart.mealplan.rules import REJECT, Ruleset

    ruleset = Ruleset.load(DEMO / profile.FILES["rules"])
    assert ruleset.rules, "the demo ruleset must state at least one rule"
    verdict = ruleset.evaluate(
        {"id": "x", "title": "Garlic Shrimp Pasta", "ingredients": [{"item": "shrimp"}]}
    )
    assert verdict.status == REJECT, verdict.explain()
    # ... and that it carries the engine's exception scrub, so a rule about wine
    # does not reject the vinegar a recipe legitimately deglazes with.
    vinegar = ruleset.evaluate({"id": "y", "title": "Wine Vinegar Chicken"})
    assert vinegar.status != REJECT, vinegar.explain()


def test_the_app_can_only_reach_its_own_profiles():
    """The split is structural, not a promise.

    Importing this package relocated the engine's profile root to this repo, so
    the engine's no-argument readers resolve inside the app too. The household's
    file is not merely unread -- it is not on any path this process builds.
    """
    from meal_to_cart import household

    assert Path(os.environ.get("MTC_ROOT", "")).resolve() == ROOT
    assert not (ROOT / "data" / "household.defaults.json").exists(), (
        "the app must ship no household.defaults.json: the engine reads it when "
        "no profile is named, and the app has no household of its own to describe"
    )
    assert household.load() == {}, "the engine read a household file from somewhere"
