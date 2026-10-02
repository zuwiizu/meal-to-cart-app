# How I designed and refined the prompts

These are explanations of the prompts used during the build, summarized from the reviewed conversations. They are not verbatim messages or a newly executed prompt sequence. The video uses diagrams to explain the reasoning.

| Stage | What I asked the agent to do | Why | How I judged the result |
|---|---|---|---|
| Ground the workflow | Begin with saved favourites and similar creator recipes | Give the agent evidence of actual taste | Meals should reflect the starting collection without simply repeating it |
| Define the recurring job | Build a reusable weekly system, initially five dinners and two lunches, with explicit exclusions | Make the task and constraints concrete | A repeatable plan and grocery list, not only a one-off document |
| Expand the library | Add variety from more creators and support selection by taste, preferences and deals | The first output was too close to the original collection | Source-linked recipes and a reusable selection pipeline |
| Debug the wrong week | Compare the recipe pack with the groceries actually ordered | A stale plan had been selected | The current plan must be tied to the actual order |
| Use household state | Schedule from Saturday, prioritise fragile food and record already-bought cooked beef | A useful plan must reflect timing and purchases | Cooking order and recipes match what is already owned |
| Simplify the cart build | Reuse the repository, existing Hermes/VPS setup and link-based Walmart path | Reduce the work required to demonstrate the useful flow | A simple page with inspectable parsing and product matching |
| Define completion | Show the full app-to-cart journey | A generated URL alone does not prove a populated cart | Visible imported ingredients, shopping lines and filled Walmart cart |

Hermes was the AI interface and implementation agent. The initial public app used deterministic meal selection. The current app calls Jev live to score eligible recipe titles and ingredients against the weekly preference brief. Python controls exclusions, aggregation, product matching and cart completeness. Existing infrastructure and earlier meal-planning work were reused.

The full household brief is broader than the public dinner-and-cart demo. The diagrams explain the intended workflow; they do not assert that every household requirement is implemented in the public form.

[Working demo](https://meal-to-cart-demo.pages.dev/) · [App repository](https://github.com/zuwiizu/meal-to-cart-app) · [Engine repository](https://github.com/zuwiizu/meal-to-cart)

The engine also contains [curated discovery prompts](https://github.com/zuwiizu/meal-to-cart/blob/main/prompts/01-discovery.md) and [curated build prompts](https://github.com/zuwiizu/meal-to-cart/blob/main/prompts/02-build.md). Those are separate repository build records; this document explains the user's prompt intent and corrections.

The new [executed application prompt](https://github.com/zuwiizu/meal-to-cart-app/blob/main/prompts/live-meal-ranking.md) documents the actual live Jev scoring request, validation and failure path. The user-tested repair also distinguishes partial weeks, unknown prices and explicit product review. These changes were added after the earlier build.
