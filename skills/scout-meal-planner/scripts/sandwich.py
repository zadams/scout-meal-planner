"""Sandwich lunch (PB&J + deli line, chips, fruit) as a menu for plan_trip.

The sandwich mix has logic the JSON menus can't express (PB&J share,
restricted-group carve-outs, certified sandwiches), so it lives in code.
Returns raw needs; plan_trip applies buffers, pooling and pack rounding.
"""

RESTRICTED_SW_PER_PERSON = 1.6  # full allotment for groups with no fallback option
RESTRICTED_BUFFER = 1.15        # buffer more than deli: they can't switch to turkey

# Toppings: share of deli/veg/certified sandwiches that take it, amount each,
# catalog key, and units-per-amount conversion into the catalog unit.
TOPPINGS = {
    "lettuce":        (1.0, 1, "lettuce", 1),
    "tomato":         (0.5, 1, "tomato", 1),
    "pickles":        (0.5, 3, "pickles", 1),
    "onion":          (0.3, 2, "onion", 1 / 20),   # ~20 thin rings per onion
    "banana_peppers": (0.25, 4, "banana_peppers", 1),
}
DEFAULT_TOPPINGS = ["lettuce", "tomato", "pickles"]

MENU = {
    "name": "Sandwich lunch (PB&J + build-your-own deli) + chips + fruit",
    "meal_type": "lunch",
    "hot": False,
    "equipment": ["2 prep tables", "foil pans + lids", "tongs", "bowls for toppings"],
}


def needs(ctx, opts):
    """ctx: trip-level people/requirements (see plan_trip.Context). opts: meal options."""
    toppings = opts.get("toppings", DEFAULT_TOPPINGS)
    unknown = set(toppings) - set(TOPPINGS)
    if unknown:
        raise SystemExit(f"Unknown topping(s): {', '.join(sorted(unknown))}. Known: {', '.join(TOPPINGS)}")
    pbj_kids = opts.get("pbj_share_kids", 0.6)
    pbj_adults = opts.get("pbj_share_adults", 0.25)

    bump = ctx.bump
    per = RESTRICTED_SW_PER_PERSON * bump
    kid_sw = ctx.kids * 1.25 * bump
    adult_sw = ctx.adults * 1.75 * bump
    base_pbj = kid_sw * pbj_kids + adult_sw * pbj_adults
    big = ctx.big_eaters * 1.5 * bump

    veg, halal, kosher = ctx.req("vegetarian"), ctx.req("halal"), ctx.req("kosher")
    deli = max(0, kid_sw + adult_sw - base_pbj - (veg + halal + kosher) * per) + big / 2
    pbj = base_pbj + ctx.walkups * 1.5 * bump + big / 2
    veg_sw = veg * per * RESTRICTED_BUFFER
    halal_sw = halal * per * RESTRICTED_BUFFER
    kosher_sw = kosher * per * RESTRICTED_BUFFER
    topped = deli + veg_sw + halal_sw + kosher_sw
    people = ctx.people

    n = []  # (key, qty, buffer, loss) where loss True = trip prep_loss
    n.append(("bread_sandwich", (pbj + deli + veg_sw + halal_sw + kosher_sw) * 2, 0.15, True))
    if ctx.req("gluten_free"):
        n.append(("bread_gf", ctx.req("gluten_free") * 2 * 2 * bump, 0, False))
    spread = "sunbutter" if ctx.nut_free else "peanut_butter"
    n.append((spread, pbj * 1.25, 0.15, True))
    n.append(("jelly", pbj * 0.8, 0.15, True))
    n.append(("turkey_deli", deli * 2.5 / 16, 0.08, True))
    if halal_sw:
        n.append(("turkey_halal", halal_sw * 2.5 / 16, 0, True))
    if kosher_sw:
        n.append(("turkey_kosher", kosher_sw * 2.5 / 16, 0, True))
    n.append(("cheese_sliced", deli * 1.5 + veg_sw * 2 + halal_sw * 1.5, 0.08, True))
    if veg_sw:
        n.append(("hummus", veg_sw * 1.0, 0.08, True))
    for t in toppings:
        share, each, key, conv = TOPPINGS[t]
        n.append((key, topped * share * each * conv, 0.08, False))
    n.append(("mayo_packets", topped * 0.75, 0, False))
    n.append(("mustard_packets", topped * 0.75, 0, False))
    n.append(("chips", people, 0.1, False))
    n.append(("fruit", people * bump, 0.25, False))
    n.append(("plates", people, 0.2, False))
    n.append(("napkins", people * 3, 0, False))
    if halal_sw or kosher_sw:
        n.append(("sandwich_bags", halal_sw + kosher_sw, 0, False))
    if opts.get("water_bottles"):
        n.append(("water", people * opts["water_bottles"], 0, False))

    mix = [f"{pbj:.0f} PB&J", f"{deli:.0f} turkey"]
    if veg_sw:
        mix.append(f"{veg_sw:.0f} veg (hummus + cheese)")
    if halal_sw:
        mix.append(f"{halal_sw:.0f} halal")
    if kosher_sw:
        mix.append(f"{kosher_sw:.0f} kosher (no cheese)")
    notes = ["Sandwiches: " + " + ".join(mix),
             "Toppings: " + ", ".join(t.replace("_", " ") for t in toppings)]
    return n, notes
