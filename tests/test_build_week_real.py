"""The week is REAL: the plan, the list and the cart link come from the engine.

Before this file existed, build_week returned empty lists staged for exactly this
task. What it pins is the product's whole promise: every line the engine planned
is either a product at the shop or a named reason it is not one, and a cart link
exists only when there is nothing left unnamed.

The resolution seam is fed the REAL importer (its fetch injected, so the committed
fixture's bytes stand in for the network) and the seam's own Resolved objects.
The store id is the demo profile's own invented one, read from its stores slot.
"""
from pathlib import Path

from meal_to_cart import gateway, resolve as resolve_seam
from meal_to_cart_app.agent import build_week

# CORRECTED 2026-09-25 before dispatch. The original test called
# build_week("demo", links=[], form={}) and expected a link. That cannot work:
# links=[] imports no recipes, so there are zero lines, and render_cart_link
# refuses an empty cart BY DESIGN -- an empty link is exactly the "cart with
# holes in it" the project exists to refuse. A test that demands a link from no
# lines is demanding a lie. It now supplies one link and one real line.
FIXTURE = Path(__file__).resolve().parents[2] / "meal-to-cart" / "tests" / "fixtures" / "recipe-skinnytaste.md"


def _one_link_worth_of_recipes(monkeypatch, agent_module):
    """Feed the committed fixture instead of the network: same bytes, no fetch.

    Uses the REAL import_recipe with its injectable fetch seam, not a stub, so
    this still exercises source/creator stamping and the parse.
    """
    from meal_to_cart import importer
    text = FIXTURE.read_text()
    real = importer.import_recipe
    monkeypatch.setattr(agent_module, "import_recipe",
                        lambda url: real(url, fetch=lambda _u: text))


def _resolved(line, item_id="123456789"):
    from meal_to_cart import gateway
    return resolve_seam.Resolved(line, gateway.WALMART, wanted=frozenset({line.item}),
                                 item_id=item_id, quantity=1, title=line.item,
                                 price=3.5)


def test_a_resolved_week_yields_a_walmart_link(monkeypatch):
    from meal_to_cart_app import agent
    _one_link_worth_of_recipes(monkeypatch, agent)
    monkeypatch.setattr(agent, "resolve_all", lambda lines: [(l, _resolved(l)) for l in lines])
    # A Walmart link REQUIRES a store id: render_cart_link raises without one, because
    # guessing could fill a cart at the wrong store. The demo profile's store is INVENTED
    # and clearly illustrative; a real visitor brings their own. Never the household's.
    out = build_week("demo", links=["https://example.test/air-fryer-chicken-thighs"], form={})
    assert out["shopping"], "the fixture must yield shopping lines, or this proves nothing"
    assert out["unresolved"] == []
    assert out["cart_link"].startswith("https://www.walmart.com/sc/cart/addToCart?items=")
    assert "storeId=" in out["cart_link"], "a Walmart link without a store picks the wrong shop"


def test_one_unknown_line_means_no_link_at_all(monkeypatch):
    from meal_to_cart_app import agent
    from meal_to_cart import resolve as rs
    _one_link_worth_of_recipes(monkeypatch, agent)

    def half_unknown(lines):
        out = []
        for i, l in enumerate(lines):
            out.append((l, _resolved(l)) if i else (l, rs.Unknown(l, gateway.WALMART, l.item, "no match")))
        return out

    monkeypatch.setattr(agent, "resolve_all", half_unknown)
    out = build_week("demo", links=["https://example.test/air-fryer-chicken-thighs"], form={})
    assert out["cart_link"] is None, "a partial cart must never be rendered"
    assert out["unresolved"], "the unknown line must be named"


def test_the_link_carries_no_credential():
    for key in ("password", "session", "cookie", "token", "auth"):
        assert key not in gateway.BASE_URL.lower()


# --------------------------------------------------------------------------
# The same two answers, on the real path, with only the search held still.
# --------------------------------------------------------------------------

# Every line carries an amount, so no line is refused for stating none. Written
# here rather than committed as a fixture: this file's other fixture is the real
# one, and a second file would only be this test's own input.
SIZED_ONLY = """Title: Demo Pantry Bowls

## Ingredients
* 2 teaspoon olive oil
* 1 teaspoon kosher salt
* 1 teaspoon garlic powder
* 0.5 teaspoon black pepper
"""

# Not one line says HOW MANY. This is the case the refusal exists for, and it is
# now the only input in this file that exercises it: the importer must not invent
# an amount, and the seam must refuse the line rather than let it into a cart.
NO_AMOUNTS = """Title: Seasoning Only

## Ingredients
* kosher salt, to taste
* freshly ground black pepper
* olive oil
* a handful of parsley
"""


class _HeldStill:
    """The search, held still: one canned product row per query, no network.

    The engine's own scorer still decides what that row is worth, exactly as it
    does in a live run -- only the bytes are ours, which is what lets a test
    assert on a link without opening one.
    """

    def __init__(self) -> None:
        self.queries: list[str] = []
        self.issued: list[str] = []

    async def search(self, query: str, limit: int = 5) -> list[dict]:
        self.queries.append(query)
        item_id = f"10{len(self.queries):07d}"
        self.issued.append(item_id)
        return [_a_product_row(query, item_id)]


def _a_product_row(query: str, item_id: str) -> dict:
    """One Walmart row in the shape walmart.products_from_next_data builds.

    promises_known is False because this row is ours: the tile says nothing about
    delivery, and a page that says nothing must never be read as a page that
    promises nothing -- that misreading is a real discount the scorer applies.
    """
    return {
        "title": f"{query} Demo Brand, 1 Count", "price": 3.98, "price_text": "$3.98",
        "item_id": item_id, "rating": "4.5", "url": f"/ip/{item_id}",
        "sponsored": False, "seller": "Walmart.com", "fulfillment": "STORE",
        "store_ids": ["0000"], "pickup": True, "delivery_stores": [],
        "pickup_stores": ["0000"], "delivery_dates": [], "promises": {},
        "promises_known": False, "unit_price": "", "stock": "IN_STOCK",
        "out_of_stock": False, "can_add_to_cart": True,
    }


def _search_without_a_network(monkeypatch, agent_module) -> _HeldStill:
    """Hand resolve_all a search and change nothing else about it.

    resolve_all itself still runs: the engine's cart.build_plan searches,
    match.score decides, the seam answers, gateway renders. One function is ours.
    """
    held = _HeldStill()
    real = agent_module.resolve_all
    monkeypatch.setattr(agent_module, "resolve_all",
                        lambda lines: real(lines, matcher=held))
    return held


def test_the_real_seam_refuses_a_week_whose_recipe_states_no_amounts(monkeypatch):
    """The refusal, through the real seam rather than a hand-made Unknown.

    REPAIRED 2026-09-25 after the importer was deliberately changed. It used to
    lean on the committed fixture's two countable lines ("1 lemon", "6 chicken
    thighs") being read as unsized. They are now read as SIZED, because a bare
    count before a countable noun is itself a size -- so the fixture no longer
    contains anything unsized and this test could no longer prove the refusal on
    it. Rather than delete the only real-seam proof of the refusal, it now uses a
    recipe that genuinely states no amounts at all.

    Note what is still true and still load-bearing: a line with NO number is an
    amount the importer will not invent, the seam refuses it with NO_SIZE before
    any lookup runs, and so the week cannot become a cart however perfect the
    search is. The search below hands back a perfect row for every query.
    """
    from meal_to_cart import importer
    from meal_to_cart_app import agent
    monkeypatch.setattr(agent, "import_recipe",
                        lambda url: importer.import_recipe(url, fetch=lambda _u: NO_AMOUNTS))
    held = _search_without_a_network(monkeypatch, agent)

    out = build_week("demo", links=["https://example.test/seasoning-only"], form={})

    assert out["shopping"], "this recipe must yield list lines, or it proves nothing"
    assert out["cart_link"] is None, "a partial cart must never be rendered"
    named = {entry["line"]: entry["reason"] for entry in out["unresolved"]}
    assert named, "the unsized lines must be named, not filtered away"
    # NOT every line here is refused, and that is the engine working correctly
    # rather than a gap: the aggregator resolves some lines to a concrete buy on
    # its own ("a handful of parsley" came back as '1 bunch'). So this asserts the
    # mechanism -- the refused lines are refused FOR STATING NO AMOUNT, and at
    # least one line was refused -- instead of asserting a count I had guessed at.
    # An equality here was my own error, and it failed on the first run.
    for line, reason in named.items():
        assert "does not state one usable amount" in reason, (line, reason)
    assert len(named) < len(out["shopping"]), (
        "if every line were refused this would prove the search broken, not the refusal")
    assert held.queries, "the sized lines are searched; only the unsized ones are refused first"


def test_a_week_that_all_resolves_renders_the_real_link_end_to_end(monkeypatch):
    """The link, end to end, with only the search ours.

    importer -> planner -> aggregator -> seam -> gateway, so the link below is
    the one a live run renders: the scorer's own item ids, its prices in the
    budget, and the profile's own store on the link.
    """
    from meal_to_cart import importer
    from meal_to_cart_app import agent
    monkeypatch.setattr(agent, "import_recipe",
                        lambda url: importer.import_recipe(url, fetch=lambda _u: SIZED_ONLY))
    held = _search_without_a_network(monkeypatch, agent)

    out = build_week("demo", links=["https://example.test/demo-pantry-bowls"], form={})

    assert out["plan"], "the plan is the engine's, and it is not empty"
    assert out["unresolved"] == [], out["unresolved"]
    assert out["cart_link"].startswith("https://www.walmart.com/sc/cart/addToCart?items=")
    items = out["cart_link"].split("items=")[1].split("&storeId=")[0].split(",")
    assert len(items) == len(out["shopping"]) == len(held.issued)
    assert {entry.split("_")[0] for entry in items} == set(held.issued),         "every line in the link carries the id the search handed back"
    assert all(entry.endswith("_1") for entry in items)
    assert out["cart_link"].endswith("&storeId=0000"),         "the demo profile's invented store is the one read from its stores slot"
    assert out["cart_summary"], "the human half of render_cart_link is kept, off the href"
    assert gateway.BASE_URL in out["cart_link"]
    assert out["budget"]["total"] > 0 and out["budget"]["priced"] == len(out["shopping"])


def test_the_committed_fixture_now_resolves_fully_and_renders_a_link(monkeypatch):
    """The demo's happy path, on the real committed recipe.

    Recorded because it is a BEHAVIOUR CHANGE the household asked for: "1 lemon"
    and "6 chicken thighs, with bone and skin" used to be read as unsized and the
    week ended in a refusal. A bare count before a countable noun is itself a size
    -- it says how many to buy -- so those lines are now sized, the fixture
    resolves completely, and the demo produces a link instead of a refusal.

    The guard is untouched and still proves itself: a line with no number at all
    is still refused (see the NO_AMOUNTS test above).
    """
    from meal_to_cart import importer
    from meal_to_cart_app import agent
    monkeypatch.setattr(agent, "import_recipe",
                        lambda url: importer.import_recipe(
                            url, fetch=lambda _u: FIXTURE.read_text()))
    held = _search_without_a_network(monkeypatch, agent)

    out = build_week("demo", links=["https://example.test/air-fryer-chicken-thighs"], form={})

    assert out["unresolved"] == [], out["unresolved"]
    assert len(out["shopping"]) == 8, "the fixture states 8 ingredients"
    assert out["cart_link"], "a fully resolved week must render a link"
    assert "storeId=0000" in out["cart_link"]
