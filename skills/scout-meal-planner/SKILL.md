---
name: scout-meal-planner
description: Plan a group camping meal (Scouts, youth groups, family camps) from a headcount — menu, per-item quantities, dietary coverage with on/off requirement toggles (vegetarian, halal, kosher, gluten-free, nut-free), a DIY buffet service line, and a store-by-store shopping list for the planner's own warehouse club and grocery stores. Use when asked to plan, scale, or shop for a group or camp meal, or to price-check the grocery list.
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
- **Meal + event**: which meal, and what happens before it (a hike or run
  means hungrier people and more water; set `"hungry": true`).
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
- Cooking gear on site: none, so plan a cold meal. Cooler + ice: yes.
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

## 3. Compute quantities

Record the event in a profile, `plans/<event>.json`. Requirements are on/off
toggles, so a planner can rerun the same event as needs change:

```json
{
  "event": "Fall campout lunch",
  "kids": 35, "adults": 38,
  "walkups": 10, "big_eaters": 8, "prep_loss": 0.05,
  "pbj_share_kids": 0.7, "pbj_share_adults": 0.35,
  "hungry": false, "water_bottles": 0,
  "requirements": {
    "vegetarian":  { "enabled": true,  "count": 10, "estimated": true },
    "halal":       { "enabled": true,  "count": 5,  "estimated": true },
    "kosher":      { "enabled": false },
    "gluten_free": { "enabled": false },
    "nut_free":    { "enabled": false }
  },
  "stores": {
    "warehouse": ["Costco", "Sam's Club"],
    "grocery": "Kroger",
    "specialty": "local halal/kosher grocer"
  },
  "toppings": ["lettuce", "tomato", "pickles"],
  "packs": { "pb_jar_oz": 48, "cheese_pack_slices": 80 }
}
```

- An enabled requirement must have a count; a guess is fine if marked `"estimated"`.
- `stores` only changes the wording of the output; the math is store-independent.
- `packs` overrides default pack sizes once real sizes are known. Defaults
  and keys are in `DEFAULT_PACKS` in the script.

Run the calculator:

```
python3 scripts/sandwich_lunch.py --profile plans/<event>.json
```

CLI flags override the profile for quick what-ifs, e.g. `--halal 0`,
`--nut-free`, `--kids 40` (`--help` lists them all).

The calculator covers sandwich lunches. For other meals, reason from
`references/portions.md` with the same principles:
- Bias **up** on shelf-stable items; leftovers go to the next campout.
- Stay **tight** on perishables; leftovers get tossed.
- Round to real pack sizes, then sanity-check total cost.

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

Write the plan to `plans/<event>.md`, next to its profile:
1. **Summary**: headcount, requirements on (flag estimated counts), menu in
   one line, estimated total cost and $/person, recalc command.
2. **Dietary coverage**: group → what they eat. Enabled requirements only;
   disabled ones get no rows, items, or prep steps.
3. **Quantities**: item, amount, pack count.
4. **Shopping list by store**: checkboxes grouped by the planner's stores.
5. **Prep timeline**: T-minus schedule before the meal, with crew size.
6. **Service line**: ordered list plus supplies (tongs, gloves, labels).
7. **Open questions**: every estimate or assumption to confirm.

Keep it to one page a volunteer could print.
