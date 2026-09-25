# Setup

Paste recipe links. Answer one card. Get a week of dinners, a shopping list
grouped the way a shop is laid out, and one cart waiting at the store for you to
open and check out yourself.

Two pieces have to be running for that to happen: a **static page**, which can sit
anywhere, and an **agent**, a small program on the machine that owns the store
login. This file sets both up, then puts the agent within reach of a hosted page
with a temporary tunnel.

## What you need

* Python 3.11 or newer
* `uv` - it installs the dependencies, and `uv run` builds `.venv` on first use
* the engine, checked out as a sibling directory (step 1)
* `cloudflared`, only if you want a hosted page to reach the agent (step 5)
* a browser

## 1. The layout, and why it is two directories

    Apps/                     any parent directory
      meal-to-cart/           the engine: planning, recipe reading, matching, the cart link
      meal-to-cart-app/       this repository: the page, the agent, the demo profile

This repository does not contain the engine. It depends on it by path, declared
in `pyproject.toml`:

    [tool.uv.sources]
    meal-to-cart = { path = "../meal-to-cart", editable = true }

`uv run` installs that path into this project's environment. Nothing here imports
without the sibling checkout - that is the split working, not a missing step. One
engine, two callers, so the pipeline exists once instead of drifting in two
copies.

## 2. Run the agent

    cd meal-to-cart-app
    uv run python -m meal_to_cart_app.agent

It prints:

    meal-to-cart agent on http://127.0.0.1:8787

Leave it running. It binds loopback only, so nothing on your network or the
internet can reach it directly; the tunnel in step 5 is the only door. Pass
`--port` to use a different one.

It answers four things, all JSON:

| method | path | what it does |
|---|---|---|
| GET | `/profiles` | the profiles this app may read |
| POST | `/profile` | the setup form's answers, written into the profile it names |
| POST | `/import` | one pasted link, read and reported with its confidence |
| POST | `/plan` | one week: the plan, the list, the cart link - or what stopped it |

`POST /import` with an empty url answers `400 {"error": "no url"}` rather than
fetching something arbitrary and calling it a recipe.

## 3. Open the page

    python3 -m http.server 8000 --directory site

Then open <http://127.0.0.1:8000>.

Three files, no build step, no framework, no network calls except to the agent
you point it at. It also opens straight from disk, but a browser will not let a
`file://` page talk to the agent, so serve it while you are using one.

## 4. Point the page at the agent

At the bottom of the page, open the **Agent - where your links are sent** panel.
Paste `http://127.0.0.1:8787` into **Agent URL** - the address must start with
`http://` or `https://` - and press **Save and check**.

It should answer:

    Connected. The agent at http://127.0.0.1:8787 offers demo.

The address is kept in this browser's local storage and nowhere else. Nothing is
sent anywhere until you press one of the buttons, and everything you do send goes
to that one address.

## 5. Reach the agent from a hosted page

If the page is hosted somewhere other than your own machine, it cannot see
`127.0.0.1` on your laptop. The agent has to be reachable, so give it a
temporary public address:

    cloudflared tunnel --url http://127.0.0.1:8787

It prints something like:

    https://something-something.trycloudflare.com

Paste **that** URL into the same **Agent URL** field on the hosted page and press
**Save and check**. The hosted page is now talking to the agent on your machine.

Three things to know about the tunnel:

* **The address changes every time you start it.** Restart the tunnel, paste the
  new URL again. Nothing about the page changes; it is the same static file.
* **Treat the URL as a key while it is up.** Anyone who has it can ask your agent
  to build a week. That is by design - the page is hosted elsewhere, so the agent
  has to accept the call - and it is why the tunnel is temporary. The agent can
  order nothing and holds no credential, but it will do the work it is asked for.
* **Ctrl-C both when you are done.** The tunnel first, then the agent. The URL
  stops existing with the tunnel, and the agent stops listening.

## 6. Use it

1. **Bring your recipes.** One link per line in the links box, then **Read these
   links**. Each link comes back with its title, its ingredient count, and a
   confidence between 0.00 and 1.00. A link that could not be read comes back with
   the reason instead of an empty success.
2. **Tell it about your week.** One card: how many dinners, how many servings, a
   weekly budget target, and anything to leave out. The budget is a target -
   measured and shown, never a limit that blocks a plan.
3. **Build my week.** One request to the agent: the plan, the list grouped by
   aisle, the budget comparison, and then either a cart link or the reasons there
   is none.

**If there is no cart link, read the reasons.** The app emits a cart only when
every single line resolved. A line it could not place is named with the reason it
could not be placed, because a cart that looks complete while missing items is the
one thing this app exists to prevent.

## 7. Where your answers live

The setup form writes into the profile it is given, as
`profiles/<name>/values.json` in this repository. No account, no server-side
store, nothing sent anywhere except the one agent address you pasted.

The profile this repo ships, `profiles/demo`, is fiction - every value in it says
so in its own words. **If you name a profile of your own, keep it out of git**:
add `profiles/<your-name>/` to `.gitignore` before you use it. The demo profile is
tracked on purpose; yours should not be.

## 8. When it does not work

| what you see | what it is | what to do |
|---|---|---|
| *No agent answered at ...* | The agent is not running, or the address does not match the one it printed. | Start it (step 2), paste the exact URL, **Save and check**. The page falls back to a saved example run meanwhile, marked as one. |
| A link comes back at confidence 0.00 | The reader could not read that page, and the reason is shown. | Try another link. This is the app reporting honestly, not a crash. |
| Every link fails with a network reason | The reader service the agent uses is unreachable or refusing the request. Start with the reason in the message. | Check the agent's terminal, then try a plain page to see whether the reader answers at all. |
| The page is unstyled | The three files were not served from the same directory. | Serve `site/` as a directory (step 3) rather than opening single files. |
| No cart link, and a list of reasons | By design: not every line could be placed. | Fix the named lines - most often a recipe line that states a number with no unit - and build again. |
| *this profile states no store* in the reasons | A cart link carries a store, and the app will not guess one. | Put the store's id in the profile's stores slot. The demo's `0000` is invented, for the demo only. |

## 9. Tests

    cd meal-to-cart-app
    uv run --extra dev pytest -q

The suite covers the split from the engine, the four endpoints, the page's
promises, and the privacy boundary. `tests/test_boundary.py` scans everything
this repository publishes for a real value; the terms it searches for live in a
private list outside this repository, so on a fresh clone the term scan **skips
and says so** rather than failing - while the scan for the shapes of private data
(an address, an email, a postal code) runs either way.

## 10. Publishing

`.github/workflows/pages.yml` scans the published bytes and refuses to deploy if
it finds a private value or the shape of one, then uploads `site/` alone - never
the repository root, and never the engine. The local test above is the
authoritative gate; the workflow is the net that runs without a private checkout.

Pushing this repository anywhere is a human decision. The workflow runs when a
push to `main` reaches a remote, and not before.
