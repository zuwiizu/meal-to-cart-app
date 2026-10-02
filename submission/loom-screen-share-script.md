# Loom screen-share script — about 8–9 minutes

Open the walkthrough page and the working demo in separate tabs. Use your own voice and adjust the wording naturally. The diagrams summarize prompt intent; they are not original chat messages. Click the existing cards to highlight them while you speak.

## Tabs to open

- [Walkthrough page](http://127.0.0.1:8123/loom-walkthrough.html)
- [Working app](https://meal-to-cart-demo.pages.dev/)
- [Demo recipe: Air Fryer Chicken Thighs](https://www.skinnytaste.com/air-fryer-chicken-thighs/)
- [App repository](https://github.com/zuwiizu/meal-to-cart-app)
- [Shared engine repository](https://github.com/zuwiizu/meal-to-cart)

## 0:00–0:40 — The recurring workflow

SHOW: the recipe website, then the walkthrough page.

“This is a recurring workflow for my household: deciding what to eat during the week, collecting the recipes, combining the ingredients, checking what we already have, and finding the products to buy.

The repetitive part is keeping those steps consistent. A meal plan can look good while still being wrong for the groceries we ordered or the ingredients we already own.

I already had Hermes and supporting tools running on my VPS, and the household meal-planning work started earlier. I reused that foundation to refine the workflow and extend it into this cart demo.”

## 0:40–1:40 — Define the brief

SHOW: [The brief](http://127.0.0.1:8123/loom-walkthrough.html#3). Click each card as you explain it.

“My initial brief had three parts. First, start with recipes we already liked, including saved Home Chef meals and creator recipes. That gave the agent evidence of our taste.

Second, make the constraints explicit: initially five dinners and two lunches, more variety, and ingredients we don’t eat.

Third, build a reusable system, rather than just produce one weekly document.

Hermes was the conversational AI interface and helped build the workflow. The public demo is a narrower dinner-to-cart path, so it doesn’t cover every household lunch or snack requirement.”

## 1:40–2:30 — Refine the prompts

SHOW: [Recipe library](http://127.0.0.1:8123/loom-walkthrough.html#4).

“The first output repeated too much of the original collection. I clarified that I wanted a broader recipe library, with source links, that we could select from using taste, preferences and available deals.

That changed the task from making a document to building a reusable collection and selection pipeline.

The earlier household planner used tags across saved recipes as taste signals. The public app now has a live Jev preference-ranking stage, which I’ll explain in the ranking view.

The important part of the prompting process was checking usefulness and making the missing requirement explicit.”

## 2:30–3:30 — A failure and the adjustment

SHOW: [Failure and correction](http://127.0.0.1:8123/loom-walkthrough.html#5).

“A real failure was a recipe pack that didn’t match the groceries we had ordered. Several versions of the week existed, and Hermes had selected an older plan.

I asked it to check the recipes against the actual order. The correction was to use the order-linked plan as the source of truth for the current week.

I also asked to start from Saturday and cook the food that would spoil first earlier. When a beef recipe didn’t fit my purchase, I clarified that the pulled beef was already cooked and needed to remain recorded as an existing purchase.

The adjustment was making the workflow account for the selected week, the order and what we already owned.”

## 3:30–4:15 — The corrected output

SHOW: [Meal plan](http://127.0.0.1:8123/loom-walkthrough.html#6). Scroll slowly; click a relevant row.

“This is historical output from the corrected household workflow.

The fresh chicken is scheduled earlier, frozen ingredients later, and the already-bought beef stays in the plan.

That makes the output practical: it helps decide what to make and in what order, rather than just naming appealing meals.

The household build includes recipe import, preferences and exclusion rules, meal selection, ingredient aggregation, grocery planning and document output.”

## 4:15–5:05 — The backend

FIRST: open the working app, paste the three recipe links below, choose **3 dinners / 2 servings**, leave **Live AI** on, and enter **Prefer salmon and fish first, chicken later**. Click **Build my week**, then return to the diagram while the store searches run. You can prepare the import preview before recording to keep this section short.

SHOW: [Backend](http://127.0.0.1:8123/loom-walkthrough.html#1). Highlight the top row, then the engine stages.

“The web app is a browser interface backed by a Python service running on my VPS. The browser sends the recipe URLs and form answers to that service as JSON.

The backend calls the shared meal-to-cart engine. It imports recipes, applies dietary rules, selects meals, combines repeated ingredients into shopping lines, searches Walmart products and returns the results to the page.

It calls the existing Jev gateway to score the eligible meals against this week’s preferences. Python validates those typed scores and puts the best-fitting meals first.

It returns a cart link when every shopping line has a product. Otherwise, it names the gaps and offers real candidates for me to review. Hermes helped build the system; the app makes its own live Jev call.”

## 5:05–5:55 — How ranking works

SHOW: [Ranking](http://127.0.0.1:8123/loom-walkthrough.html#2). Highlight recipe selection, product matching, then the garlic example.

“There are two rankings. For recipes, exclusion rules run first. Only eligible recipes reach Jev, with their titles, ingredients and my plain-language preferences for the week. Jev returns preference-fit scores from zero to four. Each supplied recipe appears at most once per week.

For products, the engine scores how closely a Walmart result matches the ingredient, including the product form and known stock information. It accepts the best candidate at a score of at least 0.70.

In this illustrative example, fresh garlic scores 0.88 and garlic powder scores 0.68 when the request is for garlic.

The grocery match scores are coded; the meal scores come from Jev live. I kept the jobs separate: the model ranks preferences, while Python controls exclusions and cart completeness. Laya isn’t in this request path.”

## 5:55–6:35 — The cart build

SHOW: [Cart build](http://127.0.0.1:8123/loom-walkthrough.html#7).

“The remaining gap was turning the grocery list into something actionable at the store.

I directed the agent to reuse the existing project and simplify the cart path. Earlier browser automation hit bot challenges. The later implementation reads store search data, scores product candidates and creates a Walmart cart link.

The person reviews the products and handles checkout. The tool prepares the cart.”

## 6:35–7:05 — Define completion

SHOW: [Demo checks](http://127.0.0.1:8123/loom-walkthrough.html#8).

“I wanted evidence of the whole journey. A generated URL alone wasn’t enough.

The checks are: did the recipe import correctly, did the shopping list reflect it, and did opening the link actually populate the cart?

Missing prices must remain unknown, and unresolved ingredients must stay visible.”

## 7:05–8:20 — Run the app

SHOW: [Working app](https://meal-to-cart-demo.pages.dev/).

RETURN: to the live build started earlier. Show the imported titles and ingredient lines, then the result.

“I supplied three real recipe links and asked for three dinners. My preference was fish first, chicken later. The Python backend turns the recipes into shopping lines and searches for matching products.”

SHOW: Live AI ranking, including its model, timestamp, scores and run ID. Then show the shopping list and any unresolved lines.

“This is a fresh model call, not a saved AI answer. I can change the weekly preferences and build again to see the meals reordered.”

“I’m checking the output rather than assuming the request succeeded. Any unresolved lines need to be explained before a cart is produced.”

IF FEWER DINNERS ARE PLANNED: point to the coverage warning and explain the rejected or unreadable recipes. One unique recipe can fill only one night in this demo.

IF A PRODUCT NEEDS REVIEW: select a candidate, open its product page, check the form and pack size, confirm the review, then click Use reviewed choices and rebuild.

“Here the recipe says bone-in, skin-on thighs, but the search title doesn’t state every detail. I want that uncertainty visible. I choose after checking the actual product, and the backend rechecks my selected ID in a fresh search.”

IF A CART LINK APPEARS: open it.

“This is the handoff to Walmart. I would review the products, quantities, store and availability here. The link uses one pack per shopping line, so I check that the packs cover the recipe quantities. If I haven’t entered my store ID, the demo uses a fictional store profile. Checkout stays with the person.”

Use a separate demo browser profile for the Walmart shot so your address and unrelated cart items are not part of the recording. If using your existing cart, show only the relevant products and explain that the link adds to the current cart.

IF THE LIVE RUN FAILS: explain the visible failure. You can show the previous recording at 6:25 in `stripe-meal-workflow-visual.mp4` and say: “This is a prior successful run, rather than the result of today’s attempt.”

## 8:20–8:40 — Close

SHOW: the repositories or overall diagram.

“My contribution was defining the recurring job, grounding it in real preferences, correcting outputs that missed the task, simplifying the implementation and requiring evidence of the complete journey.

I reused existing infrastructure and earlier work. The working demo, prompt-design notes and repositories are linked with the submission.”

## Additional source links

- [Prompt-design notes](prompt-design-notes.md) — explanations of your prompt intent, not verbatim messages.
- [Curated discovery prompts](https://github.com/zuwiizu/meal-to-cart/blob/main/prompts/01-discovery.md)
- [Curated build prompts](https://github.com/zuwiizu/meal-to-cart/blob/main/prompts/02-build.md)
- [Live Jev prompt and rubric](https://github.com/zuwiizu/meal-to-cart-app/blob/main/prompts/live-meal-ranking.md)
- [Python backend](https://github.com/zuwiizu/meal-to-cart-app/blob/main/src/meal_to_cart_app/agent.py)
- [Recipe selection logic](https://github.com/zuwiizu/meal-to-cart/blob/main/src/meal_to_cart/mealplan/planner.py)
- [Product scoring logic](https://github.com/zuwiizu/meal-to-cart/blob/main/src/meal_to_cart/match.py)

The repository prompt files are curated build records; don’t describe all of them as your original messages. If discussing build time, the record estimates about five hours for the first cart build plus later fixes; don’t claim the entire system was built from scratch in a few hours. The live Jev stage and this user-tested repair were added afterward.

For a three-dinner demonstration, paste three unique links: the Skinnytaste recipe above, [Baked Chicken Thighs](https://www.spendwithpennies.com/baked-chicken-thighs/) and [Garlic Butter Baked Salmon](https://www.spendwithpennies.com/garlic-butter-baked-salmon/). Try “Prefer fish first, chicken later,” then reverse that preference. Treat any import or store failure as a visible failure; never describe a partial week as complete.

Copy these three links into the app:

```text
https://www.skinnytaste.com/air-fryer-chicken-thighs/
https://www.spendwithpennies.com/baked-chicken-thighs/
https://www.spendwithpennies.com/garlic-butter-baked-salmon/
```
