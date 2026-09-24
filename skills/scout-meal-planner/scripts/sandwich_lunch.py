#!/usr/bin/env python3
"""Quantity calculator for a DIY sandwich lunch (PB&J + deli line, chips, fruit).

Portions come from references/portions.md; keep the two in sync.

Usage:
  sandwich_lunch.py --profile plans/<event>.json   # recommended
  sandwich_lunch.py --kids 35 --adults 38 [...]     # CLI flags override the profile
"""
import argparse
import json
import math
import sys

# Per-sandwich amounts
PB_OZ = 1.25
JELLY_OZ = 0.8
TURKEY_OZ = 2.5
CHEESE_SLICES = 1.5
VEG_CHEESE_SLICES = 2
HUMMUS_OZ = 1.0
SLICES_PER_LOAF = 20
RESTRICTED_SW_PER_PERSON = 1.6  # full allotment for groups with no fallback option
RESTRICTED_BUFFER = 1.15        # buffer more than deli: they can't switch to turkey

# Typical warehouse-club pack sizes. Override per event with the profile's
# "packs" block once the real sizes at the chosen store are known.
DEFAULT_PACKS = {
    "pb_jar_oz": 40,
    "jelly_jar_oz": 32,
    "turkey_pack_lb": 2,
    "cheese_pack_slices": 64,
    "chips_pack": 40,
    "water_pack": 40,
    "hummus_tub_oz": 32,
}

# Toppings: share of deli/veg/certified sandwiches that take it, amount each,
# and how it's bought. Enabled via the profile's "toppings" list.
TOPPINGS = {
    "lettuce":        (1.0, 1, "leaves",  None, "pre-washed bag/clamshell"),
    "tomato":         (0.5, 1, "slices",  6,    "tomatoes (~6 slices each; slice at camp)"),
    "pickles":        (0.5, 3, "chips",   150,  "46 oz jar (~150 chips)"),
    "onion":          (0.3, 2, "rings",   20,   "red onions (~20 thin rings each; slice at camp)"),
    "banana_peppers": (0.25, 4, "rings",  150,  "32 oz jar (~150 rings)"),
}
DEFAULT_TOPPINGS = ["lettuce", "tomato", "pickles"]

SHELF_BUFFER = 1.15
PERISHABLE_BUFFER = 1.08
FRUIT_BUFFER = 1.25

# Toggleable requirements in a profile's "requirements" block
REQUIREMENTS = ["vegetarian", "halal", "kosher", "gluten_free", "nut_free"]


def packs(amount, size):
    return math.ceil(amount / size)


def load_profile(path):
    """Flatten a profile into argparse defaults.

    Each entry under "requirements" is {"enabled": bool, "count": int,
    "estimated": bool}. Disabled requirements count as 0; enabled ones must
    give a count (a guess is fine if marked "estimated"). nut_free needs no
    count — it's all-or-nothing.
    Returns (argparse defaults, packs, stores, names of estimated counts).
    """
    with open(path) as f:
        prof = json.load(f)
    reqs = prof.pop("requirements", {})
    packs_cfg = {**DEFAULT_PACKS, **prof.pop("packs", {})}
    stores = prof.pop("stores", {})
    toppings = prof.pop("toppings", DEFAULT_TOPPINGS)
    bad = set(toppings) - set(TOPPINGS)
    if bad:
        sys.exit(f"Unknown topping(s): {', '.join(sorted(bad))}. Known: {', '.join(TOPPINGS)}")
    estimated = []
    unknown = set(reqs) - set(REQUIREMENTS)
    if unknown:
        sys.exit(f"Unknown requirement(s) in profile: {', '.join(sorted(unknown))}")
    for name in REQUIREMENTS:
        r = reqs.get(name, {})
        on = r.get("enabled", False)
        if name == "nut_free":
            prof["nut_free"] = on
            continue
        if on and "count" not in r:
            sys.exit(f'"{name}" is enabled but has no "count" — '
                     'use a best guess and set "estimated": true.')
        prof[name] = r.get("count", 0) if on else 0
        if on and r.get("estimated"):
            estimated.append(name)
    prof.pop("event", None)
    return prof, packs_cfg, stores, estimated, toppings


def main():
    pre = argparse.ArgumentParser(add_help=False)
    pre.add_argument("--profile")
    known, _ = pre.parse_known_args()

    p = argparse.ArgumentParser(description=__doc__, parents=[pre],
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--kids", type=int)
    p.add_argument("--adults", type=int)
    p.add_argument("--pbj-share-kids", type=float, default=0.6,
                   help="fraction of kid sandwiches that are PB&J")
    p.add_argument("--pbj-share-adults", type=float, default=0.25)
    p.add_argument("--walkups", type=int, default=0,
                   help="last-minute extras; covered with shelf-stable PB&J, not deli")
    p.add_argument("--big-eaters", type=int, default=0,
                   help="very hungry guests; each eats +1.5 sandwiches, split PB&J/turkey")
    p.add_argument("--prep-loss", type=float, default=0.05,
                   help="fraction lost to prep mishaps on bread, spreads, deli, cheese")
    p.add_argument("--hungry", action="store_true", help="+20%% after strenuous activity")
    p.add_argument("--water-bottles", type=float, default=0, help="bottles per person")
    # Requirements (0 / absent = off)
    p.add_argument("--vegetarian", type=int, default=0,
                   help="full hummus-and-cheese allotment each; never assumed to eat PB&J")
    p.add_argument("--halal", type=int, default=0,
                   help="pre-made, labeled halal turkey + cheese")
    p.add_argument("--kosher", type=int, default=0,
                   help="pre-made, sealed kosher turkey, NO cheese")
    p.add_argument("--gluten-free", type=int, default=0, help="people needing GF bread")
    p.add_argument("--nut-free", action="store_true", help="swap PB for SunButter")
    pk, stores, estimated, toppings = DEFAULT_PACKS, {}, [], DEFAULT_TOPPINGS
    if known.profile:
        defaults, pk, stores, estimated, toppings = load_profile(known.profile)
        p.set_defaults(**defaults)
    a = p.parse_args()
    grocery = stores.get("grocery", "grocery store")
    specialty = stores.get("specialty", "halal/kosher grocer")
    if a.kids is None or a.adults is None:
        p.error("--kids and --adults are required (directly or via --profile)")

    bump = 1.2 if a.hungry else 1.0
    per = RESTRICTED_SW_PER_PERSON * bump
    kid_sw = a.kids * 1.25 * bump
    adult_sw = a.adults * 1.75 * bump
    base_pbj = kid_sw * a.pbj_share_kids + adult_sw * a.pbj_share_adults
    big = a.big_eaters * 1.5 * bump

    # Restricted groups get their own full allotment, carved out of the deli share
    restricted = a.vegetarian + a.halal + a.kosher
    deli = max(0, kid_sw + adult_sw - base_pbj - restricted * per) + big / 2
    pbj = base_pbj + a.walkups * 1.5 * bump + big / 2
    veg_sw = a.vegetarian * per * RESTRICTED_BUFFER
    halal_sw = a.halal * per * RESTRICTED_BUFFER
    kosher_sw = a.kosher * per * RESTRICTED_BUFFER
    loss = 1 + a.prep_loss
    people = a.kids + a.adults + a.walkups

    gf_loaves = packs(a.gluten_free * 2 * 2 * bump, 16) if a.gluten_free else 0
    reg_slices = (pbj + deli + veg_sw + halal_sw + kosher_sw) * 2 * SHELF_BUFFER * loss
    loaves = packs(reg_slices, SLICES_PER_LOAF)
    spread = "SunButter" if a.nut_free else "Peanut butter"
    pb_oz = pbj * PB_OZ * SHELF_BUFFER * loss
    jelly_oz = pbj * JELLY_OZ * SHELF_BUFFER * loss
    turkey_lb = deli * TURKEY_OZ * PERISHABLE_BUFFER * loss / 16
    halal_lb = halal_sw * TURKEY_OZ * loss / 16
    kosher_lb = kosher_sw * TURKEY_OZ * loss / 16
    cheese = (deli * CHEESE_SLICES + veg_sw * VEG_CHEESE_SLICES
              + halal_sw * CHEESE_SLICES) * PERISHABLE_BUFFER * loss
    hummus_oz = veg_sw * HUMMUS_OZ * PERISHABLE_BUFFER * loss
    topped_sw = deli + veg_sw + halal_sw + kosher_sw
    chips = people * 1.1
    fruit = people * FRUIT_BUFFER * bump

    mix = [f"{pbj:.0f} PB&J", f"{deli:.0f} turkey"]
    if veg_sw:
        mix.append(f"{veg_sw:.0f} veg (hummus + cheese)")
    if halal_sw:
        mix.append(f"{halal_sw:.0f} halal")
    if kosher_sw:
        mix.append(f"{kosher_sw:.0f} kosher (no cheese)")

    rows = [("Sandwiches planned", " + ".join(mix), ""),
            ("Bread", f"{reg_slices:.0f} slices", f"{loaves} loaves")]
    if gf_loaves:
        rows.append(("Gluten-free bread", f"{a.gluten_free} people", f"{gf_loaves} loaf ({grocery})"))
    rows += [
        (spread, f"{pb_oz:.0f} oz", f"{packs(pb_oz, pk['pb_jar_oz'])} × {pk['pb_jar_oz']} oz jar"),
        ("Jelly", f"{jelly_oz:.0f} oz", f"{packs(jelly_oz, pk['jelly_jar_oz'])} × {pk['jelly_jar_oz']} oz jar"),
        ("Deli turkey", f"{turkey_lb:.1f} lb", f"{packs(turkey_lb, pk['turkey_pack_lb'])} × {pk['turkey_pack_lb']} lb pack"),
    ]
    if halal_sw:
        rows.append(("Halal turkey", f"{halal_lb:.1f} lb", f"{specialty} or {grocery}; + 1 sealed backup pack if estimated"))
    if kosher_sw:
        rows.append(("Kosher turkey (sealed)", f"{kosher_lb:.1f} lb", f"{grocery} kosher section; + 1 sealed backup pack if estimated"))
    rows.append(("Sliced cheese", f"{cheese:.0f} slices",
                 f"{packs(cheese, pk['cheese_pack_slices'])} × {pk['cheese_pack_slices']}-slice pack"))
    if veg_sw:
        rows.append(("Hummus", f"{hummus_oz:.0f} oz", f"{packs(hummus_oz, pk['hummus_tub_oz'])} × {pk['hummus_tub_oz']} oz tub"))
    for name in toppings:
        share, each, unit, per_pack, how = TOPPINGS[name]
        qty = topped_sw * share * each * PERISHABLE_BUFFER
        buy = f"{packs(qty, per_pack)} × {how}" if per_pack else f"1–2 × {how}"
        rows.append((f"Topping: {name.replace('_', ' ')}", f"{qty:.0f} {unit}", buy))
    rows += [
        ("Mayo / mustard packets", f"{math.ceil((deli + veg_sw + halal_sw + kosher_sw) * 0.75)} each", ""),
        ("Chips (snack bags)", f"{math.ceil(chips)}", f"{packs(chips, pk['chips_pack'])} × {pk['chips_pack']}-ct variety"),
        ("Whole fruit", f"{math.ceil(fruit)} pieces", "e.g. half clementines (×2 each), half bananas/apples"),
        ("Plates / napkins", f"{math.ceil(people * 1.2)} / {people * 3}", ""),
    ]
    if a.halal or a.kosher:
        rows.append(("Sandwich bags + labels", f"{math.ceil(halal_sw + kosher_sw)}+",
                     "for sealed, labeled certified sandwiches"))
    if a.water_bottles:
        w = people * a.water_bottles
        rows.append(("Water bottles", f"{math.ceil(w)}", f"{packs(w, pk['water_pack'])} × {pk['water_pack']}-pack"))

    active = [f"vegetarian {a.vegetarian}" if a.vegetarian else None,
              f"halal {a.halal}" if a.halal else None,
              f"kosher {a.kosher}" if a.kosher else None,
              f"gluten-free {a.gluten_free}" if a.gluten_free else None,
              "nut-free" if a.nut_free else None]
    active = [x for x in active if x]

    print(f"Headcount: {a.kids} kids + {a.adults} adults"
          + (f" + {a.walkups} walk-ups" if a.walkups else "") + f" = {people}"
          + (f", {a.big_eaters} big eaters" if a.big_eaters else "")
          + (f", {a.prep_loss:.0%} prep loss" if a.prep_loss else "")
          + (" (hungry +20%)" if a.hungry else ""))
    print(f"Requirements on: {', '.join(active) if active else 'none'}")
    if estimated:
        print(f"ESTIMATED counts (confirm if possible): {', '.join(estimated)}")
    if a.kosher:
        print("Kosher on → buy kosher-certified shared items (bread, cheese, spreads, packets); "
              "see references/religious-diets.md")
    elif a.halal:
        print("Halal on → cheese must use microbial/vegetable enzymes; "
              "see references/religious-diets.md")
    print()
    print("| Item | Amount | Buy |")
    print("|---|---|---|")
    for item, amount, buy in rows:
        print(f"| {item} | {amount} | {buy} |")


if __name__ == "__main__":
    main()
