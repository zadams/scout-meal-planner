---
name: scout-meal-planner
description: Plan the meals and snacks for a group camping trip (Scouts, youth groups, family camps) from a headcount — menus, quantities, dietary coverage with on/off toggles (vegetarian, halal, kosher, gluten-free, nut-free), service lines, prep timelines, and ONE combined shopping list across all meals so supplies aren't duplicated, with buyer assignments per group and a leftover forecast. Use when asked to plan, scale, or shop for any camp meal, snack, or whole trip, or to price-check the grocery list.
---

# Scout Meal Planner

Plan one group meal so a couple of volunteers can shop, set up, and serve it
without stress. Simplicity beats variety: every extra option costs shopping
time, cooler space, line time, and cross-contact risk.

This skill is agent-agnostic. It needs only the ability to read these files,
write a plan file, and run `python3` (standard library only). Browser or web
tools are optional. Every path below is **relative to this skill's
directory** unless it starts with `plans/`, which is relative to the user's
working directory.

## 1. Gather inputs (ask only for what's missing)

Required:
- **Headcount split**: kids vs. adults (siblings count as kids). For Cub Scouts
  (ages 5–10), a 5-year-old eats a lot less than a 10-year-old.
- **Every meal and snack on the trip**, with the group (den/patrol) that
  cooks and buys each one. Plan them together (step 3), even if you were
  only asked about one. Note what happens before a meal (a hike or run means
  hungrier people; set `"hungry": true` on that meal).
- **Cooking gear** on site (griddles, burners, pots, Dutch ovens). This
  decides which menus are realistic.
- **Dietary needs**: which requirements apply and roughly how many people
  (see the toggles in step 3).
- **Allergies: always ask about peanut/tree nut explicitly.** Never assume
  "none" just because nobody mentioned it. "It was fine last time" is a
  reasonable basis for keeping PB; still recommend an allergy question on the RSVP.
- **Stores**: which warehouse clubs (Costco, Sam's Club, BJ's, …) the planner
  belongs to, and their usual grocery store (Kroger, Walmart, H-E-B, Publix,
  Meijer, …). Don't assume any particular chain.

Defaults (state them in the plan, adjustable):
- **Walk-up buffer**: ~10–15% of confirmed. Cover walk-ups with shelf-stable
  food (PB&J, chips, fruit), never extra perishables.
- **Big eaters**: ~10% of headcount at +1.5 sandwiches each.
- **Prep loss**: 5% on bread, spreads, deli, cheese (dropped, torn, squished).
  Kept separate from leftover buffers so each allowance is visible.
- **Prep timing**: all prep happens at camp, immediately before the meal,
  unless the planner says otherwise. Plan crew size and a T-minus timeline
  around that (see step 4).
- Cooler + ice: yes.
- Budget: under ~$5/person for lunch.

If the user recalls past-trip patterns (e.g. "PB&J was popular with kids"),
use them to set the mix. They beat generic averages.

### When counts are unknown
Planners rarely have exact dietary counts. Don't block on them:
- Make a best guess from what the planner remembers, record it with
  `"estimated": true`, and list it under Open Questions.
- For groups with **no substitute** on the line (halal, kosher, gluten-free),
  round the guess **up**. A few extra pre-made sandwiches cost ~$2 each; a
  family with nothing to eat costs far more.
- For certified meat, buy **one extra sealed pack** as backup. It stays
  unopened in the cooler and goes home if unused.
- Recommend adding the question to the RSVP/sign-up for next time.

## 2. Design the menu: fewest variations that cover everyone

Pick the smallest set of options where **every person has at least one full
option they can eat**:

1. List each enabled dietary group and which option covers it. Each
   restricted group needs a **planned, full allotment** of an option built
   for them. Never count the kid-favorite option (PB&J, hot dogs) as their
   meal just because it happens to be compliant. Vegetarians get a real
   vegetarian entrée (e.g. hummus + cheese + lettuce).
2. Drop any option that doesn't uniquely cover someone or isn't a crowd favorite.
3. Prefer one protein that covers the most restrictions (turkey covers
   no-beef and no-pork; ham and roast beef add nothing and exclude people).
4. Prefer shelf-stable, no-cook items. Hot items need a cook, a griddle,
   fuel, and batch time. Include them only if a hot station already exists.
5. Sides are zero-prep: bagged chips, whole fruit (clementines, bananas, apples).

Toppings: offer 3–4 on the build-your-own line (profile `"toppings"`; the
calculator knows `lettuce`, `tomato`, `pickles`, `onion` and
`banana_peppers`, and defaults to the first three). Favor no-prep toppings
(pre-washed lettuce, jarred pickles or peppers). Tomato and red onion are
worth slicing on-site; budget ~15 min for one person. Each
topping gets its own bowl and utensil. Certified sandwiches get toppings from
freshly opened containers before the shared line is set up.

Variations are fine **only** as DIY on a buffet line, never as made-to-order
work for volunteers.

Requirement rules (apply only the ones that are enabled):
- **Nut-free**: any peanut allergy among young kids doing DIY makes the whole
  meal nut-free (SunButter, labeled). Don't run a "careful" PB line.
- **Gluten-free**: pre-make GF servings first, bag and label.
- **Halal / kosher**: ask whether a no-pork / no-beef restriction is religious.
  If so, enable the toggle and follow `references/religious-diets.md`. If both
  are off, don't read that file or add certified items.

## 3. Plan the whole trip, not one meal at a time

Planning meals separately stacks a cushion on every meal and rounds each up
to whole packs. That is how a trip ends with far too many apples. Always put
every meal of the trip in **one profile**, `plans/<trip>.json`, and let the
planner combine them:

```json
{
  "trip": "Fall campout",
  "kids": 35, "adults": 38,
  "walkups": 10, "big_eaters": 8, "prep_loss": 0.05, "hungry": false,
  "requirements": {
    "vegetarian":  { "enabled": true,  "count": 10, "estimated": true },
    "halal":       { "enabled": true,  "count": 5,  "estimated": true },
    "kosher":      { "enabled": false },
    "gluten_free": { "enabled": false },
    "nut_free":    { "enabled": false }
  },
  "stores": { "warehouse": ["Sam's Club"], "grocery": "Kroger", "specialty": "local halal/kosher grocer" },
  "packs": { "peanut_butter": 96, "cheese_sliced": 160, "onion": 10 },
  "fruit_mix": { "clementine": 0.4, "banana": 0.3, "apple": 0.3 },
  "on_hand": { "napkins": 500, "mustard_packets": 400 },
  "mess_kits": true,
  "shopping": "per_group",
  "meals": [
    { "id": "fri-smores",    "day": "Fri", "menu": "smores",             "group": "Group 1 – AOLs" },
    { "id": "sat-breakfast", "day": "Sat", "menu": "breakfast_burritos", "group": "Group 2" },
    { "id": "sat-lunch",     "day": "Sat", "menu": "sandwich_lunch",     "group": "Group 3",
      "extras": ["cold_drink"],
      "options": { "pbj_share_kids": 0.7, "toppings": ["lettuce", "tomato", "pickles", "onion"] } },
    { "id": "sun-breakfast", "day": "Sun", "menu": "coffee_bars",        "group": "Group 1 – AOLs",
      "kids": 30 }
  ]
}
```

- **Headcount**: plan for everyone at every meal unless the planner says a
  meal is smaller; a meal can override `kids`, `adults`, `walkups`, `hungry`.
- **Requirements**: an enabled requirement must have a count; a guess is fine
  if marked `"estimated"`.
- **group**: who cooks and buys for that meal (den, patrol, family).
- **packs**: real pack sizes by ingredient key, once known. Defaults live in
  `references/ingredients.json`.
- **on_hand**: what's already in the supply bin or left from the last trip, by
  ingredient key. It's subtracted before buying.
- **fruit_mix**: fruit is planned as generic servings, then split by this mix.
  That's the variety rule: no meal gets "all apples".
- **mess_kits**: `true` when campers bring their own plates, bowls, cups and
  utensils. Disposable items are then dropped (napkins and paper towels stay).
- **shopping**: `"per_group"` (default) gives each group its own list, with one
  buyer per shared item and hand-offs. `"per_pack"` gives one combined list for
  a single shopper.
- **extras**: add-on menus for a meal, usually drinks: `cold_drink` (bulk
  lemonade/Kool-Aid), `hot_drinks` (coffee/tea packets + creamer, sugar,
  sweetener), `hot_cocoa` (bulk mix made in a large Igloo). Menus can also `"include"` other menus
  (`coffee_bars` includes hot drinks and cocoa).

Run it:

```
python3 scripts/plan_trip.py --profile plans/<trip>.json          # report
python3 scripts/plan_trip.py --profile plans/<trip>.json --json   # data
```

Printable packets, one per group, each with its meals (menu, crew roles,
special diets, equipment checklist, that meal's quantities, a prep and
cooking countdown with real quantities, serving line, food safety, cleanup
and carry-forwards) plus its shopping list and hand-offs:

```
python3 scripts/plan_trip.py --profile plans/<trip>.json --handouts plans/handouts
```

In per-pack mode, a single `pack-shopping-list.html` is written too. Open
the HTML in a browser and print; each meal starts on a new page.

CLI flags override the profile for what-ifs (`--kosher 0`, `--kids 40`,
`--nut-free`; see `--help`). A profile without `meals` is treated as a single
sandwich lunch (the original format).

How the planner combines meals:
- Each ingredient is summed across meals, gets **one cushion sized to its
  biggest single meal** (not one per meal), then is rounded to packs once.
- Expected losses (burnt marshmallows, dropped bread) count as *used*, not
  as leftovers.
- Menu items marked `"from_leftovers"` (e.g. Sunday fruit) never add to the
  purchase. The report says how much should be left for them.
- Each shared item gets **one buyer** (the group using the most), with
  hand-off amounts for the other groups.
- **Carry-forwards:** when a later meal uses something an earlier one leaves
  over (breakfast onions → dinner sauce, lunch lettuce/tomato → dinner
  salad, fruit → the next meal), the report lists it and adds a labeled
  gallon bag. Matches come from the `reuse` map in `ingredients.json`.
  Purchases are not reduced for them.
- Leftovers are forecast in two lists: **waste risk** (perishables; shrink
  packs or on-hand) and **keeps for next trip** (record them in `on_hand`
  next time).

### Menus

`menus/*.json` are data files; add a meal type by adding one:

```json
{
  "name": "Pancake breakfast", "meal_type": "breakfast", "hot": true,
  "equipment": ["griddles"], "notes": ["..."], "prep": ["T-30: ..."], "line": ["plates", "..."],
  "items": [
    { "key": "pancake_mix", "kid": 2.5, "adult": 3.5, "main": true, "buffer": 0.15, "loss": true },
    { "key": "fruit", "kid": 1, "adult": 1, "buffer": 0.25 }
  ]
}
```

Instruction fields (these become the group's printed packet):
`roles` (crew jobs), `steps` (a countdown: `{"t": "T-45", "text": "Crack
{eggs} into bowls..."}`, where `{ingredient_key}` fills in this meal's
quantity and `"if": "kosher"` (or a list) shows a step only when that
requirement is on), `line` (serving order), `serving` (portion guidance),
`food_safety`, `cleanup`, and `diet` (what each requirement group eats at
this meal; only enabled ones print). Write steps for the volunteer who has
never cooked for 80: temperatures, batch sizes, who does what, and when.
Add-on menus' steps merge into the meal's countdown in time order.

Item fields: `kid`/`adult` = amount per person in the ingredient's unit;
`share` = fraction of people who take it; `main` = big eaters get extra;
`buffer` = cushion rate; `loss` = `true` (trip prep_loss) or a rate such as
0.5 for marshmallows; `only` / `except` = requirement groups it's for or not
for (`vegetarian`, `halal`, `kosher`); `walkups: false` = walk-ups don't
count; `fixed` = a set quantity that doesn't scale with headcount; `from_leftovers` = served only from leftovers. Every `key` must exist
in `references/ingredients.json`; add new ingredients there with their unit,
pack size, store, `perishable`, and label `check`s. **Hot** menus
automatically give kosher eaters a sealed certified meal.

Available menus: `smores`, `breakfast_burritos`, `sandwich_lunch` (code, in
`scripts/sandwich.py`, because its mix logic doesn't fit the data format),
`pasta_dinner`, `coffee_bars`; add-ons `cold_drink`, `hot_drinks`,
`hot_cocoa`.

**Every menu must include what it takes to cook it,** not just the food:
butter or oil, salt, pepper, seasonings, sauces, paper towels (groups
tend to run short), **storage for leftovers** (zip-top bags and a few disposable
containers as `fixed` items for opened packages), and nitrile food-prep
gloves (latex-free) in **adult and kid sizes**. Gloves come from the menu's `"crew": {"adults": 4, "kids": 4}` and
`"glove_changes"` (crew × changes × 2 hands, +25%); a meal can override
`"crew"` in the trip profile when a den brings more or fewer helpers. Mark pantry basics `"staple": true` in the catalog; the
report tags them "check chuck box" so groups don't rebuy salt every trip.
Drinks: coffee and tea as single-serve packets, always with creamer, sugar
and a no-sugar sweetener. Run `python3 -m unittest discover tests` from
the repo root after changing the planner or menus.

Principles for new menus:
- Bias **up** on shelf-stable items; leftovers go to the next campout.
- Stay **tight** on perishables; leftovers get tossed.
- Put generous-but-realistic loss rates where kids are involved (s'mores).

## 4. Plan the service line

Order: handwash → plates → grab-and-go bins (pre-made PB&J, then any
certified/GF sandwiches, sealed and labeled) → build-your-own (bread → spreads
with their own spoons → deli with tongs → cheese → toppings, each with its own
utensil → condiment packets)
→ chips → fruit → napkins/trash. Use a two-sided table above ~50 people.

Streamlining defaults (prep happens right before the meal):
- Buy ingredients that need **no washing or cutting at camp**: pre-washed
  lettuce, whole fruit, pre-sliced deli and cheese, bagged chips.
- **Pre-make PB&J** on an assembly line just before serving: about 2–2.5
  sandwiches per minute with 4 volunteers. Put halves on covered trays; skip
  bagging.
- Certified/GF sandwiches are made **first**, on a separate surface, then sealed.
- Write the prep as a T-minus timeline with crew assignments, and state the
  crew size needed. If the crew is too small, start earlier or make the
  item build-your-own.
- Deli stays in the cooler; put out one tray at a time.
- Individual condiment packets, not squeeze bottles.
- Food safety: perishables at or below 40°F; out of the cooler no more than
  2 hours (1 hour above 90°F).

## 5. Shopping list by store

Use `references/stores.md` to split items between the planner's warehouse
club and grocery store. Rules:
- **One warehouse club per trip**, even if the planner has several
  memberships. Pick by price check or pickup convenience. Don't split to save
  a few dollars.
- Grocery store for specialty items (SunButter, GF bread, certified meat),
  small quantities, and last-minute fills.
- Mark every price as an estimate unless it was just checked.

## 6. Optional: price-check / build carts

Only if the user wants it and the agent has browser or web tools:
- Look up each item on the chosen stores' sites; record price and pack size;
  put real sizes into the profile's `packs` block and rerun.
- Adding to cart is fine when asked. **Never check out, schedule pickup, or
  pay** without the user's explicit go-ahead at that moment.
- Stop and hand back to the user at login walls or CAPTCHAs.

Without browser tools, skip this step and leave prices marked as estimates.

## 7. Output

Write the plan to `plans/<trip>.md`, next to its profile, using the
planner's report as the source of numbers:
1. **Summary**: headcount, requirements on (flag estimated counts), menu in
   one line, estimated total cost and $/person, recalc command.
2. **Dietary coverage**: group → what they eat. Enabled requirements only;
   disabled ones get no rows, items, or prep steps.
3. **Per meal**: group, menu, equipment, prep, line.
4. **Shopping list by store**: one combined list with buyer group per item,
   plus hand-offs for shared items.
5. **Leftover forecast**: waste-risk items first.
6. **Open questions**: every estimate or assumption to confirm.

Always generate the group packets (`--handouts`) too, and review them before
handing them over. Read each countdown as the volunteer would: steps in
order, quantities filled in, nothing duplicated, every enabled diet covered.

Keep it to one page a volunteer could print.
