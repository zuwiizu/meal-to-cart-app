"""What the stranger's browser talks to.

The page is static and cannot hold a session or run a plan. This process
does, on the machine that owns the login. It returns a URL to click and
never a credential, and it refuses to hand back a cart with holes in it.

    GET  /profiles   the profiles this app may read, discovered by the engine
    POST /profile    the setup form, written into the profile it names
    POST /import     one pasted link, read and reported with its confidence
    POST /plan       one week: plan, list, cart link -- or what stopped it

Run it with:

    uv run python -m meal_to_cart_app.agent [--port 8787]
"""
from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from meal_to_cart import profile
from meal_to_cart.importer import import_recipe


def save_profile(name: str, form: dict) -> dict:
    """Write the form's answers into that profile's own values file.

    ONE definition of where a profile's values live: profile.values_path(), the
    same call the engine reads through. Building ROOT / "profiles" / name here
    would be a second copy of that rule -- the drift defect profile.py documents
    -- and it would let this writer and the engine's reader mean two different
    files while both look correct.
    """
    path = profile.values_path(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    current = json.loads(path.read_text()) if path.exists() else {}
    current.setdefault("_what", "Values entered in the app's setup form.")
    current.setdefault("preferences", {})
    current.setdefault("plan", {})
    current.setdefault("budget", {})
    if "servings" in form:
        current["plan"]["servings"] = int(form["servings"])
    if "dinners" in form:
        current["plan"]["dinners"] = int(form["dinners"])
    if "likes" in form:
        current["preferences"]["likes"] = list(form["likes"])
    if "dislikes" in form:
        current["preferences"]["dislikes"] = list(form["dislikes"])
    if "budget_weekly" in form:
        current["budget"]["weekly_target"] = float(form["budget_weekly"])
        current["budget"]["currency"] = "USD"
    path.write_text(json.dumps(current, indent=2) + "\n")
    return current


def build_week(profile_name: str, links: list[str], form: dict) -> dict:
    """One week from the visitor's links and form.

    Budget is a TARGET: shown and compared, never obeyed. Being over it can
    never stop a week being produced, and a cart that cannot be completed is
    never rendered at all -- the reasons are named in "unresolved" instead.
    """
    values = save_profile(profile_name, form) if form else {}
    target = float((values.get("budget") or {}).get("weekly_target") or 0.0)

    imported = [import_recipe(url) for url in links]

    # A link that yielded no ingredient list is a line this week cannot be built
    # from, so it is NAMED here with its reason. Never filtered out: a list
    # shorter than the truth, looking complete, is the one failure this app
    # exists to prevent.
    unresolved = [
        {"line": r.source or "(a pasted link)",
         "reason": r.note or "no ingredient list"}
        for r in imported
        if not r.ingredients
    ]

    # Nothing is priced yet, so the week spends 0.00. "over" is COMPUTED from
    # the two numbers it compares, never a flag set by hand: a hardcoded False
    # is indistinguishable from today's honest under-target result, and it would
    # go on saying "under" after real prices arrive.
    total = 0.0
    over = total > target

    return {
        # The plan and the list are the engine's to build from the imported
        # recipes, and that join is not wired yet: until it is, the week is
        # EMPTY rather than guessed at. An empty list is visible to the visitor;
        # a short one that looks complete is not. Everything imported is
        # reported in full below either way.
        "plan": [],
        "shopping": [],
        # A partial cart is never rendered. With nothing resolved, there is no
        # link at all, and every line that stopped it is in "unresolved".
        "cart_link": None,
        "unresolved": unresolved,
        "budget": {
            "target": target,
            "total": total,
            "over": over,
            # A target is shown, never a blocker: it cannot stop the week.
            "blocked": False,
        },
        "imported": [
            {"source": r.source, "title": r.title, "creator": r.creator,
             "confidence": r.confidence, "note": r.note}
            for r in imported
        ],
    }


def create_app(port: int = 8787) -> ThreadingHTTPServer:
    """The four endpoints, bound to loopback: the tunnel is the only door."""

    class Handler(BaseHTTPRequestHandler):
        def _json(self, payload, status=200):
            body = json.dumps(payload).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_OPTIONS(self):                        # noqa: N802
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()

        def do_GET(self):                            # noqa: N802
            if self.path.startswith("/profiles"):
                # The engine's own discovery, not a path built here: the list
                # and save_profile's write must never mean different places.
                self._json({"profiles": profile.available()})
                return
            self._json({"error": "not found"}, 404)

        def do_POST(self):                           # noqa: N802
            length = int(self.headers.get("Content-Length") or 0)
            body = json.loads(self.rfile.read(length) or b"{}")
            if self.path.startswith("/import"):
                url = str(body.get("url") or "").strip()
                if not url:
                    # Reading "" would fetch the reader's own homepage and call
                    # whatever came back a recipe. Refuse it instead.
                    self._json({"error": "no url"}, 400)
                    return
                r = import_recipe(url)
                self._json({"title": r.title, "creator": r.creator,
                            "confidence": r.confidence, "note": r.note,
                            "ingredients": [i.raw for i in r.ingredients]})
                return
            if self.path.startswith("/profile"):
                self._json(save_profile(body.get("profile", "demo"), body.get("form", {})))
                return
            if self.path.startswith("/plan"):
                self._json(build_week(body.get("profile", "demo"),
                                      body.get("links", []), body.get("form", {})))
                return
            self._json({"error": "not found"}, 404)

        def log_message(self, *args):                # noqa: N802 - stdlib naming
            pass

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="meal-to-cart-app")
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args(argv)
    print(f"meal-to-cart agent on http://127.0.0.1:{args.port}")
    create_app(args.port).serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
