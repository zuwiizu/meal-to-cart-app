import json
import threading
import urllib.error
import urllib.request

import pytest

from meal_to_cart import gateway
from meal_to_cart.importer import ImportedRecipe, Ingredient, parse_page
from meal_to_cart.mealplan.shopping import Buy
from meal_to_cart.resolve import Resolved, Unknown
from meal_to_cart_app import agent, live_rank


def recipe(title, ingredients):
    return {"title": title, "ingredients": [{"item": i} for i in ingredients]}


def response(scores):
    return {"model": "jev-test", "answers": {f"recipe_{i}": {
        "type": "score", "score": score, "confidence": .9} for i, score in enumerate(scores)}}


def test_live_ranking_applies_scores_and_emits_fresh_receipts():
    recipes = [recipe("Salmon", ["salmon"]), recipe("Chicken", ["chicken"])]
    bodies = []
    def send(body):
        bodies.append(body)
        return response([1, 4])
    ranked, evidence = live_rank.rank_recipes(recipes, "Prefer chicken", send=send)
    _, second = live_rank.rank_recipes(recipes, "Prefer chicken", send=send)
    assert ranked[0]["title"] == "Chicken"
    assert evidence["status"] == "live" and evidence["model"] == "jev-test"
    assert evidence["run_id"] != second["run_id"]
    assert set(bodies[0]["state"]) == {"week_brief", "recipes"}
    assert "allergies" not in json.dumps(bodies)


@pytest.mark.parametrize("bad", [None, {}, response([float("nan")]), response([5]), response([True])])
def test_invalid_provider_answers_do_not_fall_back_to_fake_ai(bad):
    with pytest.raises(live_rank.RankingError):
        live_rank.rank_recipes([recipe("Chicken", ["chicken"])], "Prefer chicken", send=lambda b: bad)


def test_dietary_exclusions_precede_model_and_model_controls_plan(tmp_path, monkeypatch):
    monkeypatch.setenv("MTC_ROOT", str(tmp_path))
    (tmp_path / "profiles" / "demo").mkdir(parents=True)
    calls = []
    def rank(recipes, brief):
        calls.append(recipes)
        return list(reversed(recipes)), {"status": "live"}
    monkeypatch.setattr(agent, "rank_recipes", rank)
    recipes = [recipe("Sesame Chicken", ["sesame", "chicken"]),
               recipe("Chicken", ["chicken"]), recipe("Salmon", ["salmon"])]
    plan = agent._plan_week("demo", recipes, 1,
        {"allergies": ["sesame"], "ai_enabled": True, "week_brief": "Prefer fish"})
    assert [r["title"] for r in calls[0]] == ["Chicken", "Salmon"]
    assert plan["days"][0]["recipes"][0]["title"] == "Salmon"
    assert plan["rejected"][0].title == "Sesame Chicken"


def test_missing_or_partial_prices_never_mean_under_budget(tmp_path, monkeypatch):
    monkeypatch.setenv("MTC_ROOT", str(tmp_path))
    (tmp_path / "profiles" / "demo").mkdir(parents=True)
    imported = ImportedRecipe(source="https://recipe.test/chicken", title="Chicken",
        ingredients=[Ingredient("chicken thighs", "2"), Ingredient("olive oil", "1", "tablespoon")], servings=2)
    monkeypatch.setattr(agent, "import_recipe", lambda url: imported)
    def resolved(lines):
        return [(line, Resolved(line, gateway.WALMART, frozenset({line.item}),
                               "123", 1, line.item, 3.5 if i else None))
                for i, line in enumerate(lines)]
    monkeypatch.setattr(agent, "resolve_all", resolved)
    out = agent.build_week("demo", [imported.source], {"dinners": 3, "servings": 2, "budget_weekly": 120})
    assert out["budget"]["total"] is None and out["budget"]["over"] is None
    assert out["budget"]["known_subtotal"] == 3.5
    assert out["coverage"] == {"requested": 3, "planned": 1, "unfilled": ["Tuesday", "Wednesday"]}
    assert out["notes"]


def test_stated_source_servings_scale_recipe_amounts():
    text = '<script type="application/ld+json">' + json.dumps({
        "@type": "Recipe", "name": "Baked Chicken Thighs", "recipeYield": "6 servings",
        "recipeIngredient": ["6 bone-in skin-on chicken thighs", "2 tablespoon olive oil"]}) + '</script>'
    imported = parse_page(text, "https://recipe.test/chicken")
    converted = agent._recipes_from([imported], 2)[0]
    assert converted["ingredients"][0]["qty"] == 2
    assert converted["ingredients"][1]["qty"] == pytest.approx(2 / 3)


def test_manual_candidate_requires_fresh_search_and_does_not_change_automatic_threshold():
    line = Buy(item="bone-in skin-on chicken thighs", buy="2", aisle="meat")
    class Search:
        async def search(self, query, limit=10):
            return [{"item_id": "456", "title": "Fresh Chicken Thighs, 2 lb",
                     "can_add_to_cart": True, "stock": "IN_STOCK", "price": None}]
    unapproved = agent.resolve_all([line], Search())
    assert isinstance(unapproved[0][1], Unknown)
    assert unapproved.review[0]["candidates"][0]["item_id"] == "456"
    approved = agent.resolve_all([line], Search(), choices={line.item: "456"})
    assert isinstance(approved[0][1], Resolved)
    missing = agent.resolve_all([line], Search(), choices={line.item: "999"})
    assert isinstance(missing[0][1], Unknown)
    assert "fresh search" in missing[0][1].reason


def test_provider_failure_is_a_visible_http_error(monkeypatch):
    def fail(*args):
        raise live_rank.RankingError("Live AI ranking did not answer.")
    monkeypatch.setattr(agent, "build_week", fail)
    server = agent.create_app(0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    request = urllib.request.Request(f"http://127.0.0.1:{server.server_port}/plan",
        data=json.dumps({"links": [], "form": {}}).encode(), headers={"Content-Type": "application/json"})
    try:
        with pytest.raises(urllib.error.HTTPError) as exc:
            urllib.request.urlopen(request)
        assert exc.value.code == 503
        assert json.loads(exc.value.read())["error"] == "Live AI ranking did not answer."
    finally:
        server.shutdown()
        server.server_close()
