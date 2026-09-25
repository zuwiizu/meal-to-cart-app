# meal-to-cart

Paste the recipe links you planned to cook from this week. Answer one short
form. Get a reviewed Walmart cart link, and open it yourself.

Nothing is ordered without you: the link opens in your own browser, you sign in
there, and you press checkout. No credential ever touches this app. And it
refuses to hand back a cart with holes in it -- a line it could not resolve is
named, never quietly dropped.

## This repo is the public half of a two-repo split

The engine -- planning, dietary rules, ingredient parsing, cart-link rendering --
is a separate package that this repo DEPENDS ON rather than copies:

    [tool.uv.sources]
    meal-to-cart = { path = "../meal-to-cart", editable = true }

The other repo keeps a real household: their postcode, their store, their
dietary rules, their recipe library. This repo ships a demo profile whose values
are invented, and `src/meal_to_cart_app/__init__.py` points the engine's profile
root (`MTC_ROOT`) at this repository -- so a run of this app can only read this
app's profiles, and never the household's.

Copying the engine was never an option. When one fact lives in two files, the
copies drift and nothing notices; the engine's own `profile.py` records that
defect in the household's history, and depending on one engine is the fix.

## Privacy rule

No real household value is in this repo, ever: not the postcode, not the city,
not the store id, not the store name. Every value under `profiles/demo/` is
fiction, and each file says so in its own `_what` line.

`tests/test_boundary.py` checks that rather than trusting it. The forbidden
terms are read from a gitignored list and never written into the test, because a
test that hardcodes the strings it searches for matches itself and fails forever.
When no such list is present -- a fresh clone, or the published tree -- that test
SKIPS and says so, while the shape scan (an address, an email, a postal code)
runs either way.

## What is here

    profiles/demo/values.json    invented values: likes, dislikes, home, plan, budget
    profiles/demo/rules.json     invented dietary rules, in the engine's own format
    src/meal_to_cart_app/        the app package; ROOT is this repository
    tests/                       the split, the slots, and the boundary

The demo deliberately ships no `recipes.json`. Recipes arrive as links and are
imported at run time, which is the product's whole premise -- a demo recipe file
would misrepresent it.

The page, the endpoint that serves it, and `SETUP.md` come next.

## Running the tests

    uv run --extra dev pytest -q

The first run builds `.venv/` and installs the engine from the sibling checkout.
