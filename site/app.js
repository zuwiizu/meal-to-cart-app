/* Meal to Cart - the page.
 *
 * Three files, no framework, no build step, no CDN, no account. It opens from
 * disk and it talks to exactly one address: the agent you point it at.
 *
 * Two rules decide everything below.
 *
 *   1. Nothing is ordered without you. This page can only ask an agent for a
 *      link; the link opens in your own browser and you check out there. No
 *      credential is ever asked for, held or sent.
 *
 *   2. An honest empty or partial state beats a full-looking lie. A link that
 *      could not be read is reported with its reason. A run with an unresolved
 *      line shows the line and the reason, and NO cart link -- the page
 *      refuses a cart with holes even if the agent hands it one.
 *
 * The saved example run below is marked as a saved example everywhere it
 * appears and is never presented as the answer to your press of Build my week.
 * It exists so the page is not blank with no agent running.
 */
(function () {
  'use strict';

  var DEFAULT_AGENT = 'http://127.0.0.1:8787';
  var AGENT_KEY = 'meal-to-cart:agent-url';
  var MAX_LINKS = 12;
  var READ_TIMEOUT = 90000;
  var BUILD_TIMEOUT = 180000;
  var PING_TIMEOUT = 4000;

  /* The invariant, whole. The first half names the decision and the second half
     names the reason; a page that prints only one of them has dropped the part
     that makes the refusal legible. */
  var REFUSAL = 'No link was emitted: a cart with holes in it is worse than none.';

  /* Real aisles, in store-walk order. If an agent returns them in another
     order the page still reads like a shop rather than a dump. */
  var AISLE_ORDER = ['produce', 'meat', 'seafood', 'dairy', 'bakery', 'frozen', 'pantry', 'spices', 'drinks', 'other'];

  var SAMPLE_RUN =   {
    "_what": "SAVED EXAMPLE RUN for the page. Not a real household, not your links. Assembled offline: the imported rows are the real output of meal_to_cart.importer.parse_recipe_markdown (first row against tests/fixtures/recipe-skinnytaste.md at confidence 0.88); the plan's ingredient lines were run through the engine's grocery.aggregate + shopping.optimize, so the aisles, merges and reuse notes are the engine's own. Prices are absent because the store lookup needs the network, and a cart link needs the store lookup, so this run ends in the refusal state.",
    "profile": "demo",
    "form": {
      "servings": 2,
      "dinners": 5,
      "budget_weekly": 120.0,
      "allergies": [],
      "dislikes": [
        "olives",
        "fennel"
      ]
    },
    "imported": [
      {
        "source": "https://www.skinnytaste.com/air-fryer-chicken-thighs/",
        "title": "Air Fryer Chicken Thighs",
        "creator": "Skinnytaste",
        "confidence": 0.88,
        "note": "",
        "ingredients": 8
      },
      {
        "source": "https://example-kitchen.test/charred-broccoli-chili-crisp",
        "title": "Charred Broccoli with Chili Crisp",
        "creator": "example-kitchen.test",
        "confidence": 0.75,
        "note": "",
        "ingredients": 4
      },
      {
        "source": "https://example-roundup.test/best-kitchen-tools",
        "title": "The Best Kitchen Tools of the Year",
        "creator": "example-roundup.test",
        "confidence": 0.0,
        "note": "no ingredient section on this page",
        "ingredients": 0
      }
    ],
    "plan": [
      {
        "day": "Monday",
        "title": "Air Fryer Chicken Thighs"
      },
      {
        "day": "Tuesday",
        "title": "Chickpea and Spinach Curry"
      },
      {
        "day": "Thursday",
        "title": "Lemon Garlic Butter Salmon"
      },
      {
        "day": "Saturday",
        "title": "Charred Broccoli with Chili Crisp"
      },
      {
        "day": "Sunday",
        "title": "Roasted Vegetable Pasta"
      }
    ],
    "shopping": [
      {
        "item": "1 lemon",
        "buy": "as needed",
        "aisle": "produce",
        "meals": [
          "Monday"
        ],
        "need": "",
        "spare": "",
        "form": ""
      },
      {
        "item": "baby spinach",
        "buy": "5 ounce",
        "aisle": "produce",
        "meals": [
          "Tuesday"
        ],
        "need": "5 ounce",
        "spare": "",
        "form": ""
      },
      {
        "item": "broccoli, cut into florets",
        "buy": "2 heads",
        "aisle": "produce",
        "meals": [
          "Saturday"
        ],
        "need": "2 heads",
        "spare": "",
        "form": ""
      },
      {
        "item": "cherry tomatoes",
        "buy": "10 ounce",
        "aisle": "produce",
        "meals": [
          "Sunday"
        ],
        "need": "10 ounce",
        "spare": "",
        "form": ""
      },
      {
        "item": "fresh parsley",
        "buy": "1 bunch",
        "aisle": "produce",
        "meals": [
          "Thursday"
        ],
        "need": "approx. 2 tbsp",
        "spare": "one bunch is ~8 tbsp, so ~6 tbsp comes back spare — freeze it for later",
        "form": "fresh"
      },
      {
        "item": "garlic",
        "buy": "1 head of garlic",
        "aisle": "produce",
        "meals": [
          "Tuesday",
          "Thursday",
          "Sunday"
        ],
        "need": "approx. 9 cloves",
        "spare": "",
        "form": ""
      },
      {
        "item": "lemon",
        "buy": "1 lemon",
        "aisle": "produce",
        "meals": [
          "Thursday"
        ],
        "need": "approx. 1 lemons",
        "spare": "",
        "form": ""
      },
      {
        "item": "red bell pepper",
        "buy": "1",
        "aisle": "produce",
        "meals": [
          "Sunday"
        ],
        "need": "1",
        "spare": "",
        "form": ""
      },
      {
        "item": "yellow onion",
        "buy": "1",
        "aisle": "produce",
        "meals": [
          "Tuesday"
        ],
        "need": "1",
        "spare": "",
        "form": ""
      },
      {
        "item": "zucchini",
        "buy": "2",
        "aisle": "produce",
        "meals": [
          "Sunday"
        ],
        "need": "2",
        "spare": "",
        "form": ""
      },
      {
        "item": "6 chicken thighs, with bone and skin",
        "buy": "as needed",
        "aisle": "meat",
        "meals": [
          "Monday"
        ],
        "need": "",
        "spare": "",
        "form": ""
      },
      {
        "item": "salmon fillets",
        "buy": "2",
        "aisle": "seafood",
        "meals": [
          "Thursday"
        ],
        "need": "2",
        "spare": "",
        "form": ""
      },
      {
        "item": "parmesan",
        "buy": "3 ounce",
        "aisle": "dairy",
        "meals": [
          "Sunday"
        ],
        "need": "3 ounce",
        "spare": "",
        "form": ""
      },
      {
        "item": "unsalted butter",
        "buy": "1.5 oz",
        "aisle": "dairy",
        "meals": [
          "Thursday"
        ],
        "need": "3 tbsp",
        "spare": "",
        "form": ""
      },
      {
        "item": "basmati rice",
        "buy": "1.5 cup",
        "aisle": "pantry",
        "meals": [
          "Tuesday"
        ],
        "need": "1.5 cup",
        "spare": "",
        "form": ""
      },
      {
        "item": "canned chickpeas",
        "buy": "15 ounce",
        "aisle": "pantry",
        "meals": [
          "Tuesday"
        ],
        "need": "15 ounce",
        "spare": "",
        "form": ""
      },
      {
        "item": "canned coconut milk",
        "buy": "13.5 ounce",
        "aisle": "pantry",
        "meals": [
          "Tuesday"
        ],
        "need": "13.5 ounce",
        "spare": "",
        "form": ""
      },
      {
        "item": "olive oil",
        "buy": "9 tablespoons",
        "aisle": "pantry",
        "meals": [
          "Tuesday",
          "Thursday",
          "Sunday",
          "Saturday"
        ],
        "need": "9 tablespoons",
        "spare": "",
        "form": ""
      },
      {
        "item": "penne",
        "buy": "12 ounce",
        "aisle": "pantry",
        "meals": [
          "Sunday"
        ],
        "need": "12 ounce",
        "spare": "",
        "form": ""
      },
      {
        "item": "black pepper",
        "buy": "0.25 teaspoon",
        "aisle": "spices",
        "meals": [
          "Monday"
        ],
        "need": "0.25 teaspoon",
        "spare": "",
        "form": ""
      },
      {
        "item": "dried herbs, such as herbs de provence or dried oregano",
        "buy": "0.5 teaspoon",
        "aisle": "spices",
        "meals": [
          "Monday"
        ],
        "need": "0.5 teaspoon",
        "spare": "",
        "form": "dried"
      },
      {
        "item": "garlic powder",
        "buy": "1 teaspoon",
        "aisle": "spices",
        "meals": [
          "Monday"
        ],
        "need": "1 teaspoon",
        "spare": "",
        "form": ""
      },
      {
        "item": "ground coriander",
        "buy": "1 teaspoon",
        "aisle": "spices",
        "meals": [
          "Tuesday"
        ],
        "need": "1 teaspoon",
        "spare": "",
        "form": ""
      },
      {
        "item": "ground cumin",
        "buy": "2 teaspoon",
        "aisle": "spices",
        "meals": [
          "Tuesday"
        ],
        "need": "2 teaspoon",
        "spare": "",
        "form": ""
      },
      {
        "item": "kosher salt",
        "buy": "1 teaspoon",
        "aisle": "spices",
        "meals": [
          "Monday"
        ],
        "need": "1 teaspoon",
        "spare": "",
        "form": ""
      },
      {
        "item": "onion powder",
        "buy": "1 teaspoon",
        "aisle": "spices",
        "meals": [
          "Monday"
        ],
        "need": "1 teaspoon",
        "spare": "",
        "form": ""
      },
      {
        "item": "red pepper flakes",
        "buy": "0.5 teaspoon",
        "aisle": "spices",
        "meals": [
          "Sunday"
        ],
        "need": "0.5 teaspoon",
        "spare": "",
        "form": ""
      },
      {
        "item": "sweet paprika",
        "buy": "0.5 teaspoon",
        "aisle": "spices",
        "meals": [
          "Monday"
        ],
        "need": "0.5 teaspoon",
        "spare": "",
        "form": ""
      }
    ],
    "unresolved": [
      {
        "line": "wooden skewers",
        "reason": "not food - a shopping list that says this wastes a trip down an aisle"
      },
      {
        "line": "chili crisp",
        "reason": "no product at the store matched this line"
      },
      {
        "line": "flaky sea salt",
        "reason": "the recipe gave no amount, so there was no size to match"
      }
    ],
    "cart_link": null,
    "budget": {
      "target": 120.0,
      "total": null,
      "currency": "USD",
      "over": null,
      "blocked": false
    }
  };

  var profileName = 'demo';

  // --------------------------------------------------------------- plumbing

  function $(id) { return document.getElementById(id); }

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) { node.className = className; }
    if (text !== undefined && text !== null && text !== '') { node.textContent = String(text); }
    return node;
  }

  function clear(node) {
    while (node.firstChild) { node.removeChild(node.firstChild); }
    return node;
  }

  function textOf(value) {
    if (value === null || value === undefined) { return ''; }
    if (Array.isArray(value)) {
      return value.map(textOf).filter(function (part) { return part !== ''; }).join(', ');
    }
    if (typeof value === 'object') { return ''; }
    return String(value).trim();
  }

  function firstOf(source, keys) {
    if (!source || typeof source !== 'object') { return undefined; }
    for (var i = 0; i < keys.length; i += 1) {
      var value = source[keys[i]];
      if (value !== undefined && value !== null && value !== '') { return value; }
    }
    return undefined;
  }

  /* A row that came back as a bare string still has to render. */
  function asList(value) {
    if (Array.isArray(value)) { return value; }
    if (value && typeof value === 'object') {
      if (Array.isArray(value.days)) { return value.days; }
      if (Array.isArray(value.items)) { return value.items; }
      if (Array.isArray(value.lines)) { return value.lines; }
      if (Array.isArray(value.entries)) { return value.entries; }
    }
    return null;
  }

  function countOf(value) {
    if (Array.isArray(value)) { return value.length; }
    if (typeof value === 'number' && isFinite(value)) { return Math.round(value); }
    return null;
  }

  function numberOrNull(value) {
    if (value === null || value === undefined || value === '') { return null; }
    var n = Number(value);
    return isFinite(n) ? n : null;
  }

  function listFrom(value) {
    if (!value) { return []; }
    return String(value).replace(/[\r\n]+/g, ',').split(',')
      .map(function (part) { return part.trim(); })
      .filter(function (part) { return part !== ''; });
  }

  /* Only two schemes are ever put in an href, and every remote string reaches
     the DOM as text. A recipe title is data from a stranger's page. */
  function safeHref(value) {
    var text = textOf(value);
    return /^https?:\/\//i.test(text) ? text : '';
  }

  function hostOf(value) {
    var text = textOf(value);
    var match = text.match(/^https?:\/\/([^\/]+)/i);
    return match ? match[1] : text;
  }

  function money(value, currency) {
    var n = numberOrNull(value);
    if (n === null) { return ''; }
    try {
      return new Intl.NumberFormat(undefined, {
        style: 'currency', currency: currency || 'USD'
      }).format(n);
    } catch (err) {
      return n.toFixed(2);
    }
  }

  function plural(count, one, many) {
    return count + ' ' + (count === 1 ? one : many);
  }

  function setStatus(message) { $('status').textContent = message || ''; }

  function setBusy(button, busy, label) {
    button.disabled = busy;
    button.setAttribute('aria-busy', busy ? 'true' : 'false');
    if (label) { button.textContent = label; }
  }

  // ------------------------------------------------------------ the agent

  function agentUrl() {
    var saved = '';
    try { saved = window.localStorage.getItem(AGENT_KEY) || ''; } catch (err) { saved = ''; }
    /* A shared link can carry its own agent: ?agent=https://... -- validated
       like any pasted address, and remembered the same way. */
    var param = '';
    try {
      param = new URLSearchParams(window.location.search).get('agent') || '';
    } catch (err) { param = ''; }
    param = param.trim().replace(/\/+$/, '');
    if (/^https?:\/\//i.test(param)) {
      storeAgentUrl(param);
      saved = param;
    }
    return (saved || DEFAULT_AGENT).replace(/\/+$/, '');
  }

  function storeAgentUrl(value) {
    try { window.localStorage.setItem(AGENT_KEY, value); } catch (err) { /* private mode still works for this visit */ }
  }

  function request(path, options, timeoutMs) {
    var opts = options || {};
    var controller = new AbortController();
    var timer = window.setTimeout(function () { controller.abort(); }, timeoutMs);
    var limits = { signal: controller.signal, method: opts.method || 'GET' };
    if (opts.body !== undefined) {
      limits.headers = { 'Content-Type': 'application/json' };
      limits.body = JSON.stringify(opts.body);
    }
    return window.fetch(agentUrl() + path, limits).then(function (response) {
      window.clearTimeout(timer);
      return response.text().then(function (text) {
        var data = null;
        try { data = text ? JSON.parse(text) : null; } catch (err) { data = null; }
        var detail = data && data.error ? ': ' + data.error : '';
        return { ok: response.ok, status: response.status, detail: detail, data: data, text: text };
      });
    }, function (error) {
      window.clearTimeout(timer);
      if (error && error.name === 'AbortError') {
        throw new Error('the agent did not answer within ' + Math.round(timeoutMs / 1000) + ' seconds');
      }
      throw new Error('the request could not be made (' + textOf(error && error.message) + ')');
    });
  }

  function checkAgent() {
    var state = $('agent-state');
    var url = agentUrl();
    state.className = 'agent-state';
    state.textContent = 'Checking for an agent at ' + url + ' ...';
    return request('/profiles', {}, PING_TIMEOUT).then(function (result) {
      if (!result.ok) { throw new Error('the agent answered ' + result.status + result.detail); }
      var profiles = asList(result.data && result.data.profiles) || [];
      if (!profiles.length) { throw new Error('the agent answered but lists no profiles'); }
      state.className = 'agent-state ok';
      state.textContent = 'Connected to the demo agent at ' + url + ' (' + profiles.join(', ') + '). Your links go there and nowhere else.';
      return profiles.map(textOf);
    }, function (error) {
      state.className = 'agent-state warn';
      state.textContent = 'No agent answered at ' + url + ' (' + error.message + '). The example week below still shows what a result looks like, and nothing is sent anywhere until an agent answers.';
      return null;
    });
  }

  // ------------------------------------------------ how each link was read

  function importRow(row) {
    var li = el('li', 'import');
    var head = el('div', 'import-head');
    var confidence = numberOrNull(row.confidence);
    var href = safeHref(row.source);
    var title = textOf(row.title);
    var slot;

    if (title) {
      slot = el('span', 'import-title');
      if (href) {
        var link = el('a', null, title);
        link.href = href;
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
        slot.appendChild(link);
      } else {
        slot.textContent = title;
      }
    } else {
      slot = el('span', 'import-title import-title-missing', href ? hostOf(href) : 'no title came back');
    }
    head.appendChild(slot);

    if (confidence === null) {
      head.appendChild(el('span', 'chip', 'confidence not reported'));
    } else {
      head.appendChild(el('span', 'chip ' + (confidence >= 0.6 ? 'chip-ok' : 'chip-warn'),
        'confidence ' + confidence.toFixed(2)));
    }
    li.appendChild(head);

    var facts = [];
    if (textOf(row.creator)) { facts.push(textOf(row.creator)); }
    var ingredients = countOf(row.ingredients);
    if (ingredients !== null) { facts.push(plural(ingredients, 'ingredient line', 'ingredient lines')); }
    if (facts.length) { li.appendChild(el('p', 'import-meta', facts.join(' \u00b7 '))); }

    if (confidence !== null) {
      var meter = el('div', 'meter' + (confidence >= 0.6 ? '' : ' meter-warn'));
      meter.setAttribute('aria-hidden', 'true');
      var fill = el('span');
      fill.style.width = Math.round(Math.max(0, Math.min(1, confidence)) * 100) + '%';
      meter.appendChild(fill);
      li.appendChild(meter);
    }

    var note = textOf(row.note) || textOf(row.error);
    if (!note && confidence === 0) {
      note = 'the page was read but nothing in it looked like a recipe, and no reason was given, which is itself worth reporting';
    }
    if (note) {
      var tag = confidence === null ? 'Not read' : (confidence === 0 ? 'Not readable' : 'Partly readable');
      var line = el('p', 'import-note');
      line.appendChild(el('span', 'note-tag', tag));
      line.appendChild(document.createTextNode(note));
      li.appendChild(line);
    }
    return li;
  }

  function importsFor(payload) {
    return asList(payload && payload.imported) || asList(payload && payload.links) || null;
  }

  function renderImports(container, rows) {
    var list = el('ul', 'import-list');
    rows.forEach(function (row) {
      list.appendChild(typeof row === 'string'
        ? importRow({ source: '', title: row, confidence: null, note: 'the agent returned this link as text with no reading attached' })
        : importRow(row));
    });
    clear(container).appendChild(list);
  }

  // ------------------------------------------------------------ the result

  function chip(text, className) { return el('span', 'chip ' + (className || ''), text); }

  function runHead(payload, meta) {
    var box = el('div', 'run-head');
    var row = el('div', 'run-head-row');
    if (meta.sample) {
      row.appendChild(chip('Example', 'chip-sample'));
      row.appendChild(el('span', 'run-where', 'a saved run, shown so the page is useful before an agent answers - none of your links are in it'));
    } else {
      row.appendChild(chip('Live run', 'chip-ok'));
      row.appendChild(el('span', 'run-where', 'built by the agent at ' + meta.agentUrl));
    }
    box.appendChild(row);

    var form = meta.form || {};
    var currency = (payload.budget && payload.budget.currency) || 'USD';
    var facts = el('dl', 'facts');
    var pairs = [
      ['Profile', meta.profile],
      ['Servings', form.servings === null || form.servings === undefined ? 'not set' : String(form.servings)],
      ['Dinners', form.dinners === null || form.dinners === undefined ? 'not set' : String(form.dinners)],
      ['Budget target', form.budget_weekly === null || form.budget_weekly === undefined ? 'none set' : money(form.budget_weekly, currency)],
      ['Allergies', (form.allergies && form.allergies.length) ? form.allergies.join(', ') : 'none given'],
      ['Dislikes', (form.dislikes && form.dislikes.length) ? form.dislikes.join(', ') : 'none given']
    ];
    pairs.forEach(function (pair) {
      var item = el('div', 'fact');
      item.appendChild(el('dt', null, pair[0]));
      item.appendChild(el('dd', null, pair[1]));
      facts.appendChild(item);
    });
    box.appendChild(facts);
    if (meta.sample) {
      box.appendChild(el('p', 'block-note', 'Those are the saved run\u2019s settings, not yours. They are shown so the numbers below can be read against the question they answer.'));
    }
    return box;
  }

  function planBlock(payload) {
    var box = el('div', 'block');
    box.appendChild(el('h3', 'block-title', 'Your week'));
    var entries = asList(payload.plan) || asList(payload.dinners) || asList(payload.meals);
    if (!entries || !entries.length) {
      box.appendChild(el('p', 'block-note', 'No dinners came back from this run. An empty week is not a light week: nothing here should be read as planned.'));
      return box;
    }
    var list = el('ol', 'plan');
    entries.forEach(function (entry) {
      var day = '';
      var dish = '';
      var source = '';
      if (typeof entry === 'string') {
        dish = entry;
      } else if (entry && typeof entry === 'object') {
        day = textOf(firstOf(entry, ['day', 'date', 'night', 'weekday']));
        var recipe = entry.recipe;
        dish = textOf(firstOf(entry, ['title', 'name', 'dish']))
          || (typeof recipe === 'string' ? recipe : textOf(firstOf(recipe, ['title', 'name'])));
        source = safeHref(firstOf(entry, ['source', 'url', 'link']))
          || safeHref(typeof recipe === 'object' ? firstOf(recipe, ['source', 'url', 'link']) : '');
      }
      var li = el('li');
      li.appendChild(el('span', 'day', day || 'one night'));
      var cell = el('span');
      cell.appendChild(el('span', 'dish', dish || 'a dinner with no title'));
      if (source) {
        var link = el('a', 'dish-src', hostOf(source));
        link.href = source;
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
        cell.appendChild(link);
      }
      li.appendChild(cell);
      list.appendChild(li);
    });
    box.appendChild(list);
    return box;
  }

  function aisleOf(entry) {
    var raw = textOf(firstOf(entry, ['aisle', 'category', 'section', 'department'])).toLowerCase();
    return raw || 'other';
  }

  function lineRow(entry) {
    var item = textOf(firstOf(entry, ['item', 'name', 'product', 'title']));
    var buy = textOf(firstOf(entry, ['buy', 'quantity', 'amount', 'size']));
    var need = textOf(firstOf(entry, ['need', 'needed', 'recipe_amount']));
    var spare = textOf(firstOf(entry, ['spare', 'leftover', 'note', 'notes']));
    var form = textOf(firstOf(entry, ['form']));
    var nights = asList(firstOf(entry, ['meals', 'uses', 'nights', 'days']));

    var li = el('li', 'line');
    var main = el('div', 'line-main');
    var left = el('span', 'line-item');
    left.appendChild(el('span', null, item || 'a line with no name'));
    if (buy) {
      left.appendChild(el('span', 'leader'));
      main.appendChild(left);
      main.appendChild(el('span', 'line-buy', buy));
    } else {
      main.appendChild(left);
    }
    li.appendChild(main);

    var tells = [];
    if (nights && nights.length > 1) { tells.push('used ' + nights.map(textOf).join(', ')); }
    if (need && need !== buy) { tells.push('the recipes ask for ' + need); }
    if (form === 'fresh' || form === 'dried') { tells.push(form); }
    if (spare) { tells.push(spare); }
    if (tells.length) { li.appendChild(el('p', 'line-tell', tells.join(' \u00b7 '))); }
    return li;
  }

  /* A list that came back as one text blob is still shown, line by line. It is
     never run through a formatter that could invent a group it did not have. */
  function groupsFromText(text) {
    var groups = [];
    var current = null;
    String(text).split(/\r?\n/).forEach(function (raw) {
      var line = raw.trim();
      if (!line) { return; }
      var heading = line.replace(/^[#*\s]+/, '').replace(/[*_]+/g, '');
      var counted = heading.match(/^(.*?)\s*[\u2014\u2013-]\s*\d+\s+items?$/i);
      if (counted) {
        current = { aisle: counted[1].toLowerCase(), lines: [] };
        groups.push(current);
        return;
      }
      if (/^#{1,6}\s/.test(line)) {
        current = { aisle: heading.toLowerCase(), lines: [] };
        groups.push(current);
        return;
      }
      if (/^[-*]\s+/.test(line)) {
        if (!current) { current = { aisle: 'other', lines: [] }; groups.push(current); }
        current.lines.push({ item: line.replace(/^[-*]\s+/, '').replace(/\*\*/g, '').replace(/\s*\(([^)]*)\)\s*$/, ' \u00b7 $1') });
      }
    });
    return groups.filter(function (group) { return group.lines.length; });
  }

  function listBlock(payload) {
    var box = el('div', 'block');
    box.appendChild(el('h3', 'block-title', 'The list'));
    var shopping = payload.shopping === undefined ? payload.list : payload.shopping;

    if (typeof shopping === 'string' && shopping.trim()) {
      box.appendChild(el('p', 'block-note', 'The agent returned this list as text rather than as rows, so it is shown exactly as it came back, grouped the way it was grouped.'));
      var groups = groupsFromText(shopping);
      if (groups.length) { box.appendChild(aisleGroups(groups, false)); return box; }
      box.appendChild(el('p', 'block-note', shopping.trim()));
      return box;
    }

    var entries = asList(shopping) || asList(payload.groceries);
    if (!entries || !entries.length) {
      box.appendChild(el('p', 'block-note', 'No lines came back from this run. An empty list is not a short list: nothing here should be read as a finished shop.'));
      return box;
    }

    var byAisle = {};
    var unlabelled = 0;
    entries.forEach(function (entry) {
      var aisle = entry && typeof entry === 'object' ? aisleOf(entry) : 'other';
      if (aisle === 'other') { unlabelled += 1; }
      if (!byAisle[aisle]) { byAisle[aisle] = []; }
      byAisle[aisle].push(entry);
    });
    var keys = Object.keys(byAisle).sort(function (a, b) {
      var rank = function (name) { var at = AISLE_ORDER.indexOf(name); return at === -1 ? AISLE_ORDER.length : at; };
      return rank(a) - rank(b) || a.localeCompare(b);
    });
    var payloadGroups = keys.map(function (key) { return { aisle: key, lines: byAisle[key] }; });
    box.appendChild(aisleGroups(payloadGroups, unlabelled === entries.length && entries.length > 1));
    return box;
  }

  function aisleGroups(groups, allUnlabelled) {
    var wrap = el('div', 'aisles');
    if (allUnlabelled) {
      wrap.appendChild(el('p', 'block-note', 'The agent did not label these lines with a store aisle, so they are listed together. Inventing groups here would tell you to walk aisles nobody checked.'));
    }
    groups.forEach(function (group) {
      var section = el('div');
      var head = el('div', 'aisle-head');
      head.appendChild(el('span', 'aisle-name', group.aisle === 'other' ? 'everything else' : group.aisle));
      head.appendChild(el('span', 'aisle-count', plural(group.lines.length, 'item', 'items')));
      section.appendChild(head);
      var list = el('ul', 'lines');
      group.lines.forEach(function (entry) {
        list.appendChild(typeof entry === 'string' ? lineRow({ item: entry }) : lineRow(entry));
      });
      section.appendChild(list);
      wrap.appendChild(section);
    });
    return wrap;
  }

  function budgetBlock(payload, meta) {
    var box = el('div', 'budget');
    var budget = (payload.budget && typeof payload.budget === 'object') ? payload.budget : {};
    var currency = textOf(budget.currency) || 'USD';
    var target = numberOrNull(firstOf(budget, ['target', 'weekly_target', 'limit']));
    if (target === null) { target = numberOrNull((meta.form || {}).budget_weekly); }
    var total = numberOrNull(firstOf(budget, ['total', 'estimated_total', 'estimate', 'spend']));

    if (target === null) {
      box.appendChild(el('span', 'budget-target', 'No weekly budget target was set, so there is nothing to measure this list against.'));
      return box;
    }
    var label = el('span', 'budget-target');
    label.appendChild(document.createTextNode('Target '));
    label.appendChild(el('b', null, money(target, currency)));

    if (total === null) {
      box.appendChild(label);
      box.appendChild(el('p', 'budget-note', 'No estimated total came back from this run, so the target cannot be compared against anything yet. Prices come from the store lookup, which this page never does itself.'));
      return box;
    }
    var difference = total - target;
    box.appendChild(label);
    if (difference > 0.005) {
      box.appendChild(el('span', 'budget-est over', money(total, currency) + ' \u00b7 ' + money(difference, currency) + ' over the target'));
      box.appendChild(el('p', 'budget-note', 'Over the target. That never blocks a plan and nothing was dropped to close the gap: the target is a comparison, not a limit.'));
    } else if (difference < -0.005) {
      box.appendChild(el('span', 'budget-est under', money(total, currency) + ' \u00b7 ' + money(-difference, currency) + ' under the target'));
      box.appendChild(el('p', 'budget-note', 'Under the target. The list is compared against the target and never trimmed to reach it, so a gap here means the week genuinely costs less.'));
    } else {
      box.appendChild(el('span', 'budget-est', money(total, currency) + ' \u00b7 exactly on the target'));
    }
    return box;
  }

  function unresolvedOf(payload) {
    var entries = asList(payload.unresolved) || asList(payload.refused) || [];
    return entries.map(function (entry) {
      var line = '';
      var reason = '';
      if (typeof entry === 'string') {
        line = entry;
      } else if (entry && typeof entry === 'object') {
        line = textOf(firstOf(entry, ['line', 'item', 'name', 'raw', 'title']));
        reason = textOf(firstOf(entry, ['reason', 'why', 'note', 'problem']));
      }
      return {
        line: line || 'a line with no name',
        reason: reason || 'no reason was given for this one, which is itself worth reporting'
      };
    });
  }

  function cartBlock(payload) {
    var box = el('div', 'cart');
    var row = el('div', 'run-head-row');
    var unresolved = unresolvedOf(payload);
    var link = safeHref(firstOf(payload, ['cart_link', 'cartLink', 'cart_url', 'cartUrl']));

    if (link && !unresolved.length) {
      row.appendChild(chip('Cart ready', 'chip-ok'));
      box.appendChild(row);
      var cta = el('p', 'cart-cta');
      var anchor = el('a', 'btn btn-primary', 'Open my Walmart cart');
      anchor.href = link;
      anchor.target = '_blank';
      anchor.rel = 'noopener noreferrer';
      cta.appendChild(anchor);
      box.appendChild(cta);
      box.appendChild(el('p', 'cart-note', 'The cart is waiting in your own browser. Review it, change it if you like, and check out there. Nothing on this page can order for you.'));
      box.appendChild(el('p', 'resolved-note', 'Every line resolved. Nothing was left out of this cart.'));
      return box;
    }

    row.appendChild(chip('No cart link', 'chip-warn'));
    box.appendChild(row);
    box.appendChild(el('p', 'verdict', REFUSAL));

    if (link && unresolved.length) {
      box.appendChild(el('p', 'cart-note', 'The agent did return a cart link. This page is not showing it: a cart built from an incomplete list is the one thing this project exists to prevent. Settle the lines below and build again.'));
    } else if (unresolved.length) {
      box.appendChild(el('p', 'cart-note', 'Each line below came back without a product to buy, or without an amount to buy it in. Nothing was quietly dropped to make the list look finished.'));
    } else {
      box.appendChild(el('p', 'cart-note', 'No link and no unresolved lines came back together. That combination means the run did not finish, so nothing is offered rather than a cart that might be short.'));
    }

    if (unresolved.length) {
      box.appendChild(el('h4', 'unresolved-title', 'What did not resolve'));
      var list = el('ul', 'unresolved');
      unresolved.forEach(function (entry) {
        var li = el('li');
        li.appendChild(el('span', 'u-line', entry.line));
        li.appendChild(el('span', 'u-reason', entry.reason));
        list.appendChild(li);
      });
      box.appendChild(list);
    }
    return box;
  }

  function summarise(payload, prefix) {
    var plan = asList(payload.plan) || [];
    var shopping = typeof payload.shopping === 'string' ? groupsFromText(payload.shopping).reduce(function (n, g) { return n + g.lines.length; }, 0)
      : (asList(payload.shopping) || []).length;
    var unresolved = unresolvedOf(payload);
    var link = safeHref(firstOf(payload, ['cart_link', 'cartLink', 'cart_url', 'cartUrl']));
    return (prefix || 'Built') + ': ' + plural(plan.length, 'dinner', 'dinners')
      + ', ' + plural(shopping, 'list line', 'list lines')
      + ', ' + (unresolved.length ? plural(unresolved.length, 'line that did not resolve', 'lines that did not resolve') : 'nothing unresolved')
      + ', ' + (link && !unresolved.length ? 'a cart link' : 'no cart link') + '.';
  }

  function renderRun(payload, meta) {
    var out = [runHead(payload, meta)];
    var imported = importsFor(payload);
    if (meta.sample && imported && imported.length) {
      var box = el('div', 'block');
      box.appendChild(el('h3', 'block-title', 'How those links were read'));
      var holder = el('div', 'imports');
      renderImports(holder, imported);
      box.appendChild(holder.firstChild);
      out.push(box);
    }
    out.push(planBlock(payload));
    out.push(listBlock(payload));
    out.push(budgetBlock(payload, meta));
    out.push(cartBlock(payload));
    if (meta.sample) {
      out.push(el('p', 'block-note', summarise(payload, 'That saved run produced') + ' It ends without a cart link because three lines did not resolve, which is the designed behaviour rather than a failure of the page.'));
    }
    return out;
  }

  function mountRun(payload, meta) {
    var result = $('result');
    var previous = result.querySelector('.live-run');
    if (previous) { result.removeChild(previous); }
    var run = el('div', 'live-run');
    renderRun(payload, meta).forEach(function (node) { run.appendChild(node); });
    result.insertBefore(run, result.firstChild);
    $('empty-state').hidden = true;
    $('sample-block').open = false;
    var heading = run.querySelector('.block-title');
    if (heading) {
      heading.setAttribute('tabindex', '-1');
      heading.focus();
    }
    return run;
  }

  function mountNothingBuilt(error) {
    var result = $('result');
    var previous = result.querySelector('.live-run');
    if (previous) { result.removeChild(previous); }
    var run = el('div', 'live-run');
    var head = el('div', 'run-head');
    var row = el('div', 'run-head-row');
    row.appendChild(chip('Nothing built', 'chip-warn'));
    row.appendChild(el('span', 'run-where', agentUrl()));
    head.appendChild(row);
    head.appendChild(el('p', 'verdict', 'Nothing was built, and nothing was sent anywhere.'));
    head.appendChild(el('p', 'cart-note', 'The page asked the agent at ' + agentUrl() + ' and got no answer: ' + error.message + '. Your links and this card were not read, no week was planned, and no cart exists.'));
    head.appendChild(el('p', 'cart-note', 'Start the agent and press Build my week again. Until then the saved example below shows the shape of a real result, clearly marked as an example.'));
    run.appendChild(head);
    result.insertBefore(run, result.firstChild);
    $('empty-state').hidden = true;
    $('sample-block').open = true;
    return run;
  }

  // ------------------------------------------------------------------ form

  function formPayload() {
    return {
      servings: numberOrNull($('servings').value),
      dinners: numberOrNull($('plan-type').value),
      budget_weekly: numberOrNull($('budget').value),
      allergies: listFrom($('allergies').value),
      dislikes: listFrom($('dislikes').value)
    };
  }

  function linksFromField() {
    return listFrom($('links').value);
  }

  // ------------------------------------------------------------- the flows

  function readLinks() {
    var button = $('read-links');
    var results = $('import-results');
    var all = linksFromField();
    if (!all.length) {
      clear(results).appendChild(el('p', 'empty-note', 'There is nothing to read yet. Paste one recipe link per line, then press Read these links.'));
      setStatus('No links to read.');
      return Promise.resolve();
    }
    var wanted = all.slice(0, MAX_LINKS);
    var ignored = all.slice(MAX_LINKS);
    clear(results);
    var list = el('ul', 'import-list');
    results.appendChild(list);
    setBusy(button, true, 'Reading...');

    var counts = { read: 0, partial: 0, none: 0, failed: 0, notlink: 0 };
    var chain = Promise.resolve();
    wanted.forEach(function (link, index) {
      chain = chain.then(function () {
        setStatus('Reading ' + plural(index + 1, 'link', 'links') + ' of ' + wanted.length + ' ...');
        if (!safeHref(link)) {
          counts.notlink += 1;
          list.appendChild(importRow({
            title: link, confidence: null,
            note: 'this is not a link this page can follow: it does not start with http:// or https://, so nothing was requested for it'
          }));
          return null;
        }
        return request('/import', { method: 'POST', body: { url: link } }, READ_TIMEOUT).then(function (result) {
          if (!result.ok) { throw new Error('the agent answered ' + result.status + result.detail); }
          var data = result.data || {};
          var confidence = numberOrNull(data.confidence);
          if (confidence === null) { counts.partial += 1; }
          else if (confidence === 0) { counts.none += 1; }
          else if (confidence < 0.6) { counts.partial += 1; }
          else { counts.read += 1; }
          list.appendChild(importRow({
            source: link, title: data.title, creator: data.creator,
            confidence: data.confidence, note: data.note, ingredients: data.ingredients
          }));
          return null;
        }, function (error) {
          counts.failed += 1;
          list.appendChild(importRow({ source: link, confidence: null, note: 'could not be read: ' + error.message }));
          return null;
        });
      });
    });

    return chain.then(function () {
      if (ignored.length) {
        list.appendChild(importRow({
          title: plural(ignored.length, 'more link was not read', 'more links were not read'),
          confidence: null,
          note: 'this page reads up to ' + MAX_LINKS + ' links in one go. These were left alone and are named here rather than quietly dropped: ' + ignored.join(', ')
        }));
      }
      setBusy(button, false, 'Read these links');
      setStatus('Read ' + plural(wanted.length, 'link', 'links') + ': '
        + counts.read + ' with a recipe, '
        + counts.partial + ' read only partly, '
        + counts.none + ' with no recipe in them, '
        + counts.failed + ' that could not be reached'
        + (counts.notlink ? ', ' + counts.notlink + ' that were not links' : '') + '.');
      return null;
    }, function (error) {
      setBusy(button, false, 'Read these links');
      setStatus('Reading stopped: ' + error.message);
      return null;
    });
  }

  function buildWeek(event) {
    if (event) { event.preventDefault(); }
    var button = $('build-week');
    var form = formPayload();
    var links = linksFromField().filter(safeHref).slice(0, MAX_LINKS);

    if (!links.length) {
      mountNothingBuilt({
        message: 'there is nothing to build from yet, because no usable recipe link has been pasted. '
          + 'This page ships no recipes of its own: the links you bring are the only ones it can plan with'
      });
      setStatus('Nothing was built: no links were pasted.');
      return;
    }

    setBusy(button, true, 'Building...');
    setStatus('Sending ' + plural(links.length, 'link', 'links') + ' and this card to ' + agentUrl() + ' ...');
    request('/plan', {
      method: 'POST',
      body: { profile: profileName, links: links, form: form }
    }, BUILD_TIMEOUT).then(function (result) {
      if (!result.ok) { throw new Error('the agent answered ' + result.status + result.detail); }
      var payload = result.data || {};
      mountRun(payload, { sample: false, agentUrl: agentUrl(), profile: profileName, form: form });
      var imported = importsFor(payload);
      if (imported && imported.length && !$('import-results').querySelector('.import-list')) {
        renderImports($('import-results'), imported);
      }
      setStatus(summarise(payload, 'Built'));
      return null;
    }, function (error) {
      mountNothingBuilt(error);
      setStatus('Nothing was built. ' + error.message);
      return null;
    }).then(function () {
      setBusy(button, false, 'Build my week');
    });
  }

  function mountSample() {
    var body = $('sample-body');
    if (!SAMPLE_RUN || body.childNodes.length) { return; }
    var form = (SAMPLE_RUN.form && typeof SAMPLE_RUN.form === 'object') ? SAMPLE_RUN.form : {};
    var meta = {
      sample: true,
      agentUrl: '',
      profile: textOf(SAMPLE_RUN.profile) || 'demo',
      form: {
        servings: numberOrNull(form.servings),
        dinners: numberOrNull(form.dinners),
        budget_weekly: numberOrNull(form.budget_weekly),
        allergies: asList(form.allergies) || [],
        dislikes: asList(form.dislikes) || []
      }
    };
    renderRun(SAMPLE_RUN, meta).forEach(function (node) { body.appendChild(node); });
  }

  // ------------------------------------------------------------------ boot

  function boot() {
    var agentField = $('agent-url');
    agentField.value = agentUrl();

    $('read-links').addEventListener('click', function () { readLinks(); });
    $('week-form').addEventListener('submit', buildWeek);
    $('save-agent').addEventListener('click', function () {
      var value = agentField.value.trim().replace(/\/+$/, '');
      if (!/^https?:\/\//i.test(value)) {
        $('agent-state').className = 'agent-state warn';
        $('agent-state').textContent = 'An agent address has to start with http:// or https://. Nothing was saved.';
        return;
      }
      storeAgentUrl(value);
      checkAgent().then(function (profiles) {
        if (profiles && profiles.length) {
          profileName = profiles.indexOf('demo') >= 0 ? 'demo' : profiles[0];
          $('sample-block').open = false;
        }
        mountSample();
      });
    });

    mountSample();
    checkAgent().then(function (profiles) {
      if (profiles && profiles.length) {
        profileName = profiles.indexOf('demo') >= 0 ? 'demo' : profiles[0];
        $('sample-block').open = false;
      } else {
        $('sample-block').open = true;
      }
      return null;
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
}());
