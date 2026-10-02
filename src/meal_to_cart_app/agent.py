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
import asyncio
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from meal_to_cart import gateway, household, profile
from meal_to_cart.aggregate import aisle_for, parse_amount
from meal_to_cart.cart import build_plan as search_and_score
from meal_to_cart.importer import import_recipe
from meal_to_cart.mealplan.grocery import aggregate
from meal_to_cart.mealplan.planner import plan_week
from meal_to_cart.mealplan.rules import Ruleset
from meal_to_cart.mealplan.shopping import Buy, is_non_ingredient, optimize
from meal_to_cart.resolve import (NoProduct, Product, Resolution, Resolved,
                                  Unknown, resolve)
from meal_to_cart.walmart import WalmartHTTP
from .live_rank import RankingError, rank_recipes


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


def _current_values(profile_name: str) -> dict:
    """The profile's own saved answers, for a request that brought no form.

    Read through profile.values_path(), the ONE definition of where a profile's
    values live and the same call save_profile writes through, so the reader and
    the writer cannot come to mean two different files. Without this the saved
    budget and dinner count were unreachable on any request that posted no form,
    which made the second visit read as the first one.
    """
    path = profile.values_path(profile_name)
    if not path.is_file():
        return {}
    return json.loads(path.read_text())


def store_id_for(profile_name: str, retailer=gateway.WALMART) -> str | None:
    """The store this profile shops at, or None when it states none.

    Read from the profile's OWN stores slot -- profile.paths(name)["stores"] --
    which is the engine's one answer for where a profile's store facts live. None
    is not "use a default": a Walmart link carries storeId because the store
    decides what is on the shelf, guessing one fills a cart at a shop the visitor
    does not use, and the engine's own link builder refuses to render without it.
    No store here means no link, and the reason is named in "unresolved".
    """
    try:
        path = profile.paths(profile_name)["stores"]
    except profile.UnknownProfile:
        return None
    if not path.is_file():
        return None
    for entry in json.loads(path.read_text()).get("stores") or []:
        if isinstance(entry, dict) and str(entry.get("key", "")).strip() == retailer.key:
            return str(entry.get("storeId") or "").strip() or None
    return None


def _qty(amount: str) -> float | None:
    """The number the importer read, or None when it read no amount.

    None is the planner's own word for "as needed": the line reaches the list
    without a quantity and the seam refuses to size it later, which is right. Zero
    would be a small amount, and an amount nobody stated is not one.
    """
    parsed = parse_amount(amount)
    return parsed.quantity if parsed.known else None


def _recipes_from(imported: list, servings: int) -> list[dict]:
    """The visitor's readable links, in the planner's own recipe shape.

    One conversion, here, because the importer's words and the planner's are not
    the same words: the importer reports amount/unit as written ("1", "teaspoon")
    and the planner reads qty/unit/aisle. A link that yielded no ingredient list
    is not a recipe and is skipped -- its reason is already in "unresolved", so
    its absence is visible rather than silent.
    """
    out: list[dict] = []
    for raw in imported:
        if not raw.ingredients:
            continue
        scale = servings / raw.servings if getattr(raw, "servings", None) else 1.0
        out.append({
            "id": raw.source or raw.title,
            "title": raw.title or "(a recipe with no title)",
            "source": raw.source,
            "creator": raw.creator,
            "tags": [],
            "servings": servings,
            "time_min": 30,
            "ingredients": [
                {"item": ing.item, "qty": (_qty(ing.amount) * scale if _qty(ing.amount) is not None else None), "unit": ing.unit,
                 "aisle": aisle_for(ing.item)}
                for ing in raw.ingredients
            ],
        })
    return out


def _plan_week(profile_name: str, recipes: list[dict], dinners: int,
               form: dict | None = None) -> dict:
    """The engine's own planner, on the visitor's links and the profile's rules.

    One engine, two callers: this is the same plan_week the household's own run
    uses, reading the profile's ruleset through the engine's own loader and its
    likes and dislikes through household.preferences -- the single conversion
    point between a profile's store and the planner. A rules slot that is absent
    is a profile that stated no rules, and an empty gate is that fact read
    honestly rather than a rule silently dropped.
    """
    rules_path = profile.paths(profile_name)["rules"]
    ruleset = Ruleset.load(rules_path) if rules_path.is_file() else Ruleset([])
    form = form or {}
    for key in ("allergies", "dislikes"):
        for word in form.get(key) or []:
            word = str(word).strip().lower()
            if word:
                ruleset.rules.append({"name": "Your food exclusions", "severity": "reject",
                    "tokens": [word, word + "s"], "why": f"matches {word}"})
    prefs = household.preferences(profile_name)
    if "dislikes" in form:
        prefs.dislikes = form["dislikes"]
    if not form.get("ai_enabled"):
        return plan_week(recipes, ruleset, prefs, days=dinners)
    gated = plan_week(recipes, ruleset, prefs, days=max(dinners, len(recipes)))
    eligible = [r for day in gated["days"] for r in day["recipes"]]
    ranked, evidence = rank_recipes(eligible, str(form.get("week_brief") or ""))
    plan = plan_week(ranked, ruleset, household.Prefs(), days=dinners)
    plan["rejected"], plan["review"] = gated["rejected"], gated["review"]
    plan["ai"] = evidence
    return plan


def _why_dropped(item: str) -> str:
    """Why optimize() refused a line, in the visitor's words.

    The engine hands back the refused line's name and nothing else, so the case
    is re-read from the same predicate rather than guessed at: optimize() has
    exactly two, and neither is a purchase.
    """
    if is_non_ingredient(item):
        return ("not food - a shopping list that says this wastes a trip down an "
                "aisle")
    return ("a cooking instruction rather than a purchase: it came out of the "
            "recipe with no amount")


def _lookup(match):
    """One line's answer from the engine's scorer, in the seam's own two words."""
    def lookup(line, retailer, wanted):
        if retailer is not gateway.WALMART:
            return NoProduct(
                f"this app searches and fills {gateway.WALMART.label} only, and "
                f"the line is placed at {retailer.label}")
        if match is None:
            return NoProduct("the line was never searched: it carries no query")
        if match.action != "add" or not match.item_id:
            return NoProduct(match.reason or "no product at the store matched this line")
        return Product(
            item_id=match.item_id,
            # ONE of the product the search matched, and the count is STATED, not
            # defaulted: Product.quantity has no default, exactly as Resolved's
            # has none. One is the engine's own cart path -- an approved line adds
            # one of the item (cart.apply), and the cart line carries one of it
            # (cli.buy_lines). Deciding "two trays, because the line says 3 lb and
            # the tray says 1.5 lb" is pack-size arithmetic, a separate decision
            # this build does not take.
            quantity=1,
            title=match.title,
            price=match.price,
            why=match.reason or f"matched on {match.query!r} at {match.confidence:.2f}",
        )
    return lookup


class ResolutionResults(list):
    """The normal seam results, with real candidates for explicit human review."""
    review: list


def resolve_all(lines: list[Buy], matcher=None, choices=None) -> list[tuple[Buy, Resolution]]:
    """Every planned line: the product behind it, or the reason there is none.

    THE ONE PLACE this app supplies the engine's seam with a product lookup.
    resolve() cannot search -- the engine's own tests pin that so the network can
    never sit inside the seam -- so the caller hands the search in, exactly as
    importer.import_recipe takes its fetch. The search and the scorer are the
    engine's own (cart.build_plan searches each line, match.score decides whether
    the row it found is the product), so a line becomes a usItemId here the same
    way it does in the household's own run.

    One pair per line, IN ORDER, and never one fewer: a line that cannot be
    placed comes back as an Unknown carrying a non-empty reason, because a list
    shorter than the truth and looking complete is the one failure this app
    exists to prevent.

    matcher is injectable for the same reason fetch is: a test can hold the
    network still and exercise everything on both sides of it.
    """
    if not lines:
        return []
    searcher = matcher or WalmartHTTP()
    seen = {}

    class CapturingSearch:
        async def search(self, query, limit=10):
            rows = await searcher.search(query, limit=limit)
            seen[query] = rows
            return rows

    matches = asyncio.run(search_and_score(lines, CapturingSearch()))
    review = []
    for match in matches:
        rows = seen.get(match.query, [])
        selected = (choices or {}).get(match.buy.item)
        if selected:
            row = next((r for r in rows if str(r.get("item_id")) == str(selected)
                        and not r.get("out_of_stock") and r.get("can_add_to_cart")), None)
            if row is not None:
                match.item_id = str(row["item_id"])
                match.title, match.price = str(row.get("title") or ""), row.get("price")
                match.action, match.reason = "add", "Product explicitly reviewed by you; rechecked in fresh search."
            else:
                match.action, match.reason = "flag", "Your reviewed product was not available in this fresh search. Review again."
        if match.action != "add" and rows:
            # Candidates are choices, never accepted substitutions. Keep title,
            # form and pack visible; the user must open and check the product.
            candidates = [{"item_id": str(r["item_id"]), "title": str(r.get("title") or ""),
                           "url": "https://www.walmart.com/ip/" + str(r["item_id"]),
                           "price": r.get("price")}
                          for r in rows if r.get("item_id") and r.get("title")
                          and not r.get("out_of_stock") and r.get("can_add_to_cart")]
            review.append({"line": match.buy.item, "reason": match.reason,
                           "candidates": candidates[:10]})
    by_line = {id(result.buy): result for result in matches}
    results = ResolutionResults((line, resolve(line, lookup=_lookup(by_line.get(id(line)))))
                                for line in lines)
    results.review = review
    return results


def build_week(profile_name: str, links: list[str], form: dict) -> dict:
    """One week from the visitor's links and form.

    Budget is a TARGET: shown and compared, never obeyed. Being over it can
    never stop a week being produced, and a cart that cannot be completed is
    never rendered at all -- the reasons are named in "unresolved" instead.

    The plan, the list and the cart link are the engine's own: the same planner,
    the same aggregator, the same seam and the same link builder its household
    run uses, with this profile's rules and this visitor's links.
    """
    # A public run is request-scoped: another visitor cannot overwrite this
    # visitor's preferences while their cart is being built. /profile still saves.
    values = _current_values(profile_name)
    values.setdefault("plan", {})
    values.setdefault("budget", {})
    for key in ("servings", "dinners"):
        if key in form:
            values["plan"][key] = int(form[key])
    if "budget_weekly" in form:
        values["budget"]["weekly_target"] = float(form["budget_weekly"])
    plan_rules = values.get("plan") or {}
    budget_rules = values.get("budget") or {}
    target = float(budget_rules.get("weekly_target") or 0.0)
    dinners = int(plan_rules.get("dinners") or 5)
    servings = int(plan_rules.get("servings") or 2)

    links = list(dict.fromkeys(links))
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

    recipes = _recipes_from(imported, servings)
    plan = _plan_week(profile_name, recipes, dinners, form) if recipes else None
    days = plan["days"] if plan else []

    lines = aggregate(days)
    buys, dropped = optimize(days, lines)
    # optimize() refuses lines that are not purchases -- equipment, or a sentence
    # from the recipe with no amount. Refused is not gone: each one is named here
    # with the reason the engine refused it, for the same reason a failed import
    # is named above.
    unresolved += [{"line": item, "reason": _why_dropped(item)} for item in dropped]

    choices = form.get("product_choices") if form.get("review_confirmed") is True else None
    results = resolve_all(buys, choices=choices) if choices else resolve_all(buys)
    resolved = [r for _, r in results if isinstance(r, Resolved)]
    unresolved += [{"line": r.item, "reason": r.reason}
                   for _, r in results if isinstance(r, Unknown)]

    # What the week costs, over the lines that came back with a price. "over" is
    # COMPUTED from the two numbers it compares, never a flag set by hand: a
    # hardcoded False is indistinguishable from an honest under-target result and
    # would go on saying "under" after real prices arrive. A target is shown and
    # compared and never obeyed -- being over it cannot stop a week being made.
    priced = [r for r in resolved if r.price is not None]
    subtotal = sum(float(r.price) * int(r.quantity) for r in priced) if priced else None
    total = subtotal if buys and len(priced) == len(buys) and not unresolved else None
    over = total > target if total is not None else None

    # A partial cart is never rendered. With nothing resolved, or with anything
    # left unnamed -- a line the seam could not place, a link that could not be
    # read, a line the engine refused to buy -- there is no link at all, and
    # every line that stopped it is in "unresolved" above.
    cart_link, cart_summary = None, ""
    if resolved and not unresolved:
        store_id = str(form.get("store_id") or "").strip() or store_id_for(profile_name)
        if store_id is None:
            unresolved.append({
                "line": "(the whole cart)",
                "reason": (
                    "this profile states no store, and a cart link carries "
                    "storeId because the store decides what is on the shelf: a "
                    "guessed id would fill a cart at a shop the visitor does not "
                    "use, so no link is rendered. The store belongs in the "
                    f"profile's {profile.FILES['stores']} slot."),
            })
        else:
            rendered = gateway.render_cart_link(
                [r.cart_line() for r in resolved], store_id)
            # render_cart_link returns the URL and then a human block below it.
            # The link the visitor clicks is the URL ALONE: this page puts it in
            # an href, and a newline inside an href is stripped by the URL parser,
            # which would glue the summary onto the query string and forge a
            # different cart. Both halves are kept, each where it belongs.
            cart_link, _, cart_summary = rendered.partition("\n\n")

    return {
        "plan": [
            {"day": day.get("day", ""), "title": recipe.get("title", ""),
             "source": recipe.get("source", ""), "creator": recipe.get("creator", "")}
            for day in days
            for recipe in day.get("recipes", [])
        ],
        # The engine's own shopping lines, one row per purchase, exactly as
        # shopping.optimize built them: aisle, the nights that use the item, the
        # recipe's own amount, and what comes back spare.
        "shopping": [vars(buy) for buy in buys],
        "cart_link": cart_link,
        "cart_summary": cart_summary,
        "unresolved": unresolved,
        "product_review": getattr(results, "review", []),
        "ai": plan.get("ai") if plan else {"status": "not_called", "reason": "No readable recipes."},
        "coverage": {"requested": dinners, "planned": sum(bool(d.get("recipes")) for d in days),
                     "unfilled": [d["day"] for d in days if not d.get("recipes")]},
        "budget": {
            "target": target,
            "total": total,
            "known_subtotal": subtotal,
            "over": over,
            # A target is shown, never a blocker: it cannot stop the week.
            "blocked": False,
            "currency": str(budget_rules.get("currency") or "USD"),
            # How many of the week's lines that total covers. A total summed over
            # the priced lines alone is not the week's cost, and saying how many
            # lines it covers is cheaper than letting a partial sum read as the
            # whole one.
            "priced": len(priced),
            "lines": len(buys),
        },
        "imported": [
            {"source": r.source, "title": r.title, "creator": r.creator,
             "confidence": r.confidence, "note": r.note,
             "ingredients": len(r.ingredients)}
            for r in imported
        ],
        # The planner's own notes and the recipes the profile's rules barred.
        # Barred is not unresolved: a rule the visitor stated excluded that
        # dinner on purpose, so it is REPORTED here and does not stop the cart.
        # A line that could not be RESOLVED is a different fact, and that one
        # stops the link.
        "notes": (list(plan["notes"]) if plan else []) + [
            f"{r.title}: the source does not state servings; ingredient amounts stay as published."
            for r in imported if r.ingredients and not getattr(r, "servings", None)],
        "barred": [{"title": v.title, "reason": v.explain()}
                   for v in (plan["rejected"] if plan else [])],
        "review": [{"title": v.title, "reason": v.explain()}
                   for v in (plan["review"] if plan else [])],
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
            try:
                length = int(self.headers.get("Content-Length") or 0)
                if not 0 <= length <= 32768:
                    raise ValueError("Request is too large.")
                body = json.loads(self.rfile.read(length) or b"{}")
                if not isinstance(body, dict):
                    raise ValueError("Send a JSON object.")
            except (ValueError, TypeError):
                self._json({"error": "Invalid request: send a JSON object up to 32 KB."}, 400)
                return
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
                try:
                    links, form = body.get("links", []), body.get("form", {})
                    if not isinstance(links, list) or not isinstance(form, dict) or len(links) > 12:
                        raise ValueError("Use at most 12 links and one preferences card.")
                    if not 1 <= int(form.get("dinners", 5)) <= 7 or not 1 <= int(form.get("servings", 2)) <= 10:
                        raise ValueError("Choose 1–7 dinners and 1–10 servings.")
                    if len(str(form.get("week_brief") or "")) > 800:
                        raise ValueError("Keep your week preferences under 800 characters.")
                    for key in ("allergies", "dislikes"):
                        if key in form and (not isinstance(form[key], list) or len(form[key]) > 20
                            or any(not isinstance(w, str) or len(w) > 80 for w in form[key])):
                            raise ValueError("Use a short list of food exclusions.")
                    if form.get("product_choices") and not isinstance(form["product_choices"], dict):
                        raise ValueError("Invalid product choices.")
                    store = str(form.get("store_id") or "").strip()
                    if store and (not store.isdigit() or len(store) > 8):
                        raise ValueError("Walmart store ID must be digits.")
                    self._json(build_week(body.get("profile", "demo"), links, form))
                except RankingError as exc:
                    self._json({"error": str(exc)}, 503)
                except (ValueError, TypeError, profile.UnknownProfile) as exc:
                    self._json({"error": str(exc)}, 400)
                except Exception:
                    self._json({"error": "The build did not finish. No completed cart was returned; try again."}, 500)
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
