# The video

A 5-10 minute screen recording of this app, spoken by you, in your own voice.
This file is the shot list and the words. Everything under **SAY** is written to
be read aloud by a human: no synthetic narration is used in this project and none
is used here.

Read the whole file once before you record. The middle of it is the part that
matters, and it is the part a first-time presenter is tempted to talk past.

## What the video has to land

1. **It starts from your links, not from a catalogue.** A link goes in and comes
   back with a title, an ingredient count, and a confidence.
2. **A cart is emitted only when every line resolved.** When one line cannot be
   placed, the app emits nothing, names the line, and says why. That is the
   product, so the video shows it happening on purpose.
3. **No credential ever touches the browser.** The pipeline ends at a URL the
   human opens and checks out themselves.

## The one rule about the refusal

Do not skip it, do not re-record around it, and do not apologise for it.

Say it once, plainly: **this app would rather give you nothing than a cart with
holes in it.** Then read out the lines it refused and why. A reviewer who watches
a tidy cart go by has watched a shopping list; a reviewer who watches the refusal
and the reasons beside it has seen the whole thesis.

---

## Before you record

### What has to be running

Two terminals, both in `meal-to-cart-app`.

**Terminal A - the agent.** The only part that is not a static file.

    uv run python -m meal_to_cart_app.agent
    # prints: meal-to-cart agent on http://127.0.0.1:8787

**Terminal B - the page.**

    python3 -m http.server 8000 --directory site
    # then open http://127.0.0.1:8000

The page is three files and opens from disk, but a browser will not let a
`file://` page call the agent, so serve it for the recording.

Then, in the page, open the **Agent** panel at the bottom, paste
`http://127.0.0.1:8787`, and press **Save and check**. It must say *Connected*
and name the demo profile before you start. (Recording against the published
page instead? Start the tunnel first and paste its URL there - see `SETUP.md`.)

### The pre-flight check you must not skip

The reader this app uses is a third-party service. Run this before you record,
or you will find out on camera:

    cd meal-to-cart-app
    uv run python - <<'PY'
    from meal_to_cart.importer import import_recipe
    r = import_recipe("https://www.skinnytaste.com/air-fryer-chicken-thighs/")
    print(repr(r.title), r.confidence, repr(r.note), len(r.ingredients))
    PY

Expect exactly this:

    'Air Fryer Chicken Thighs' 0.88 '' 8

If it prints `could not read this link: HTTP Error 403`, stop and read **If
something breaks** at the end of this file. Do not record Beat 1 with that on
screen.

### Prepare the second link

Beat 3 ends in a refusal. The second build at the end of the video shows the
success path, and it needs a recipe whose **every** ingredient line states a
unit the reader knows (teaspoon, tablespoon, cup, ounce, pound, clove, can, jar,
bunch, slice, head, pint, quart, liter, ml, sprig, gram). Pick one during
rehearsal and paste it once to be sure it resolves before you record. A recipe
you wrote and published yourself is the only one you can guarantee, so that is
the safe choice.

If even one line of that second recipe comes back unresolved, **do not fake
it** - show the refusal again and say the rule held. That is a better video than
an edited one.

### Numbers you may say, and numbers you may not

Two things come from the recipe text and are the same on every run:

* the recipe reads as **8 ingredient lines** at confidence **0.88**;
* **two of those lines state a number and no unit** - `1 lemon` and
  `6 chicken thighs, with bone and skin` - so no amount can be read for them,
  and the app will not buy them whatever the search finds.

Everything else - which products the store search returns, their prices, and how
many of the other lines resolve - is live and moves between runs. So say the
shape, never a total you have not just seen on screen.

For reference, the two runs measured while this file was written:

| run | lines | priced | named as unresolved | cart link | total |
|---|---|---|---|---|---|
| the same link, live, on 2026-09-25 | 8 | 4 | 4: two with no amount, two the store search would not stand behind | none | 25.28 |
| the committed fixture with the search held still | 8 | 6 | 2: both with no amount | none | 23.88 |

Both end in the refusal. The constant is the two lines with no amount:
they are named on every run, whatever the search returns.

### Showing the cart link as text

If you ever want the link visible as text - on a slide, or in a terminal - use
the run's `cart_summary`, which is the human block: the lines, their prices, and
the store binding. Never paste `cart_link` as prose: it is the URL alone, built
for an `href`, and a newline inside an `href` is silently mangled by the URL
parser.

---

## The shot list

Eight minutes at a calm pace. Timings are a guide, not a cue sheet; if a beat
runs long, take it out of the close, not out of the refusal.

### 0:00 - 0:40  Cold open

**ON SCREEN** The page, from the top, nothing typed. Scroll slowly to the bottom
and back so the shape registers: three numbered beats, one card, one button.

**SAY**

> Hi. What I've built takes the recipe links you already have - the ones sitting
> in a tab, or in a message to yourself - and turns them into a week of dinners,
> one shopping list in the order you walk a shop, and one cart waiting for you to
> check out yourself. There is one rule underneath all of it, and the middle of
> this video is where it shows up.

### 0:40 - 2:20  Beat one: bring your recipes

**ON SCREEN** The **Recipe links** box. Paste the link. Press **Read these
links**. The row lands: the title as a link, a green `confidence 0.88` chip, the
meter bar, and `Skinnytaste - 8 ingredient lines` underneath.

**SAY**

> Beat one: bring your recipes. I paste one link - a recipe I actually cook from -
> and press Read these links. This page does not read it. It sends the link to the
> agent, a small program running on my own machine, and the agent hands it to a
> reader that turns a web page into plain text. Back comes the title, who wrote
> it, how many ingredient lines it found, and a confidence: 0.88.
>
> That number is the honest part of this app. It is not a guess about whether the
> recipe is any good - it counts how many ingredient lines came back with an
> amount it can trust. Eight lines, six of them with an amount. That is the 0.88.
>
> A page it cannot read at all comes back at 0.00 with the reason attached, and it
> is never dropped quietly. That matters more than it sounds: a recipe that
> vanishes becomes a shopping list with a hole in it, and a hole in a shopping
> list is how you get home without dinner.

### 2:20 - 3:20  Beat two: tell it about your week

**ON SCREEN** The card. Set five dinners, two servings, a weekly target. Hover the
hints under the budget field and under the two "leave out" fields. Type one
dislike if you like.

**SAY**

> Beat two: tell it about my week. One card, not a wizard. Five dinners, two
> servings, and a weekly budget target.
>
> Target is the word that matters. The week is measured against that number and
> can never be blocked by it. Over or under, you get the week - and the app tells
> you which it was.
>
> The last two fields are what to leave out - things I do not eat. Nothing gets
> removed quietly here either: anything a rule takes out is named in the reasons
> panel beside everything else that did not make it.

### 3:20 - 5:40  Beat three: build my week, and the refusal

**ON SCREEN** Press **Build my week**. The status line. The plan (with one link,
expect a single dinner and a note about the cooldown). The list grouped by aisle.
The budget comparison. Then the **No cart link** chip, the refusal sentence, and
the **What did not resolve** list with the two lines and their reasons. Give the
reasons three or four seconds of stillness so they can be read.

**SAY**

> Beat three: build my week. One request goes to my agent with the links and this
> card. It plans the dinners, merges the ingredients into shopping lines, sorts
> them by aisle - and then it stops and refuses.
>
> There is no cart link here. What is here is this sentence: *No link was emitted:
> a cart with holes in it is worse than none.* And underneath it, the lines that
> stopped it. *1 lemon.* *6 chicken thighs, with bone and skin.* Both of those
> state a number. Neither states a unit. The reader found a number with no unit
> word after it that it can trust, so there is no amount to buy - and an unsized
> line is never addable, because a line that constrains nothing is how a
> twelve-pack gets bought.
>
> So it gives me nothing rather than something short. And notice what it did not
> do: it did not quietly invent one lemon. That is the tempting fix, and it is the
> one thing this app exists to refuse.
>
> Look at the budget line for a second, because it sharpens the point. This
> refusal has nothing to do with money. A target here is a comparison, never a
> limit - it cannot stop a week being made. What stopped this cart is two lines
> with no amount.
>
> What would clear it? A unit on the line - the recipe giving a weight or a
> measure instead of a bare count. Some countable things genuinely have no unit in
> the recipe text, and reading those correctly is a rule the engine does not have
> yet. I did not add one to make my own demo look better. That is a product
> decision, and until it is made the app does the useful thing instead: it tells
> me exactly which line it could not place, so I know what to fix.
>
> One more thing the page does, which is easy to miss. Even if the agent had
> handed back a cart link anyway, this page would not show it - not while a single
> line is unresolved. Both halves have to agree, or the rule is not a rule.

### 5:40 - 7:10  The second build: the link

**ON SCREEN** Clear the links box, paste the all-sized recipe, press **Build my
week**. The plan, the list, the budget, and then the green **Cart ready** chip
with the **Open my Walmart cart** button. Hover the button. Do not open it.

**SAY**

> Same app, one different link. This recipe states a unit on every line - a
> teaspoon, a cup, a pound. Watch what changes.
>
> Every line resolved, so now there is a button: *Open my Walmart cart*. Under it,
> the store the link is bound to. That binding is not decoration: the link carries
> the store, because the store decides what is actually on the shelf that day.
> Guess one, and you fill a cart at a shop the visitor does not use - so with no
> store stated, this app renders no link at all and says so.
>
> I am not going to open my own signed-in cart on camera, and that is the point of
> the whole design. The link is where this app stops. I open it in my browser,
> where I am already signed in, I look the cart over, I change anything I want,
> and I check out - or I close the tab and nothing happened at all.

### 7:10 - 8:10  The close

**ON SCREEN** The page, back at the top, or the cart block left on screen.

**SAY**

> So that is the whole thing. A static page - three files, no framework, no build
> step, no account - and one small agent running on the machine that owns the
> login. The page holds no account of its own. There is no password field
> anywhere in it, and there never will be, because the last step is a link, and
> the link opens in my browser, where I am already signed in.
>
> No credential ever touches the browser.
>
> Nothing is ordered without you. The link opens, you look at the cart, change it
> if you like, and you check out. That is the deal: it does the tedious part and
> leaves the decision - and the money - with you.

---

## Do not

* **Do not apologise for the refusal.** Do not call it a bug, an edge case, or
  "something I would fix with more time". It is the feature.
* **Do not promise a cart.** The output is either a link or the reasons there is
  none, and both are the product working.
* **Do not read a number off the screen that is not there.** Prices and totals
  move between runs.
* **Do not show anything of your own** on screen: no bookmarks bar, no other
  tabs, no receipts, no mail, no signed-in shopping account, no real store or
  location anywhere in frame. The demo store is the invented one the repo
  ships with; leave it as it is.
* **Do not describe the app as ordering groceries.** It fills a cart. A human
  buys.
* **Do not add a voice-over from a synthesiser.** Read it yourself.

## If something breaks

| what you see | what it is | what to do |
|---|---|---|
| The pre-flight prints `could not read this link: HTTP Error 403` | The third-party reader refused the request. The engine currently asks it while claiming to be a browser, and the reader blocks that. | Fix the engine's reader request before recording - the fix is to stop sending the spoofed browser user-agent. Then re-run the pre-flight. |
| The page says *No agent answered at ...* | The agent is not running, or the address in the Agent panel is not the one it printed. | Start the agent (Terminal A), paste `http://127.0.0.1:8787`, **Save and check**. The page is fine meanwhile: it falls back to a saved example run, clearly marked as one. |
| A link comes back at confidence 0.00 with a reason | The reader could not read that page. That is the app being honest, not broken. | Say so, and paste a different link. This is a good moment for the "never dropped quietly" line. |
| The plan is one dinner, with a note about a cooldown | One link plans one dinner, and the cooldown keeps the same recipe from repeating inside a few days. | Say it. It is the planner's own note, and it is the reason to bring more than one link. |
| Beat 3 shows more unresolved lines than the two with no amount | The live store search would not stand behind some of the other lines that day. | Read the reasons out - they are the app's own words. Do not edit the demo to hide it. |
| No link and no unresolved lines at all | The run did not finish. | Build again. If it repeats, restart the agent and watch its terminal. |

## After you record

Stop the agent (Ctrl-C). If you started a tunnel, Ctrl-C that too. Nothing the
video showed is still running, and no credential was ever involved.
