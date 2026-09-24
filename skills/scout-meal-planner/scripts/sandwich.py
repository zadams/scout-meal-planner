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
    # Bears/Webelos-age scouts can work the PB&J assembly line with adults
    "crew": {"adults": 5, "kids": 6},
    "glove_changes": {"adults": 4, "kids": 3},
    "roles": [
        "Certified sandwiches (1 adult): kosher, then halal, before anything else is opened; then slices tomatoes/onions",
        "PB&J assembly line (3 adults + scouts): bread → PB → jelly → close → cut",
        "Line lead (1 adult): sets out the build-your-own line, refills from the cooler",
    ],
    "steps": [
        {"t": "T-60", "text": "Handwash station up. Set up tables and trash. Wipe down two prep surfaces: a small one for certified sandwiches, a long one for PB&J."},
        {"t": "T-50", "if": "kosher", "text": "KOSHER FIRST, before any regular turkey is opened: fresh gloves, new disposable knife, wiped surface. Make {kosher_count} sandwiches with kosher bread + kosher turkey ({turkey_kosher}) + lettuce and pickles from freshly opened containers. NO cheese. Seal, label \"KOSHER, no dairy\", own cooler bag."},
        {"t": "T-45", "if": "halal", "text": "HALAL: wipe down, fresh gloves, new knife. Make {halal_count} sandwiches with halal turkey ({turkey_halal}) + cheese + lettuce and pickles. Seal, label \"HALAL\", own cooler bag."},
        {"t": "T-45", "text": "PB&J assembly line: lay out bread → peanut butter → jelly → close → cut in half. Make {pbj_count} sandwiches using about {peanut_butter} of peanut butter and {jelly} of jelly. Halves go on foil trays; cover them."},
        {"t": "T-35", "text": "Toppings: on the certified surface (after those sandwiches are sealed and away), slice the tomatoes and red onions thin. Covered pans, into the cooler."},
        {"t": "T-10", "text": "Build-your-own line: bread, hummus in a bowl with its own spoon, one tray each of turkey ({turkey_deli} total) and cheese, then toppings (each with its own tongs or fork), then mayo/mustard packets. Keep backup trays in the cooler."},
    ],
    "line": ["hand sanitizer", "grab-and-go bins: PB&J · HALAL · KOSHER", "bread", "hummus (own spoon)",
             "turkey (tongs)", "cheese (tongs)", "toppings", "mayo/mustard packets", "chips", "fruit", "napkins"],
    "serving": [
        "One sandwich to start (PB&J halves count as one); seconds once everyone has gone through.",
        "An adult stands by the certified bins and hands those sandwiches to the right families.",
        "One chip bag and one piece of fruit each to start.",
    ],
    "food_safety": [
        "Turkey, cheese, hummus and cut toppings stay in the cooler (40°F or colder) until serving; out no more than 2 hours (1 hour above 90°F).",
        "Put out one tray at a time and refill from the cooler rather than setting everything out.",
        "Gloves change between the certified batches and regular food, and after touching anything else.",
    ],
    "cleanup": [
        "Bag and label opened turkey, cheese, bread and cut toppings; back in the cooler (see carry-forwards).",
        "Wipe tables; pack out trash.",
    ],
    "diet": {
        "vegetarian": "Hummus + cheese + lettuce sandwich on the build-your-own line (a full allotment is planned for them).",
        "halal": "Pre-made, sealed HALAL turkey + cheese sandwich from the labeled bin.",
        "kosher": "Pre-made, sealed KOSHER turkey sandwich (no dairy) from the labeled bin.",
        "gluten_free": "Pre-made GF sandwiches, bagged and labeled, made first.",
        "nut_free": "SunButter instead of peanut butter, labeled.",
    },
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
    n.append(("paper_towels", people * 0.02, 0.25, False))
    # opened turkey, cheese, bread, sliced toppings; a container for hummus/sliced tomatoes
    n.append(("zip_gallon", 4, 0, False))
    n.append(("storage_containers", 1, 0, False))
    if halal_sw or kosher_sw:  # fresh pairs for the kosher and halal batches
        n.append(("gloves_adult", 4, 0.25, False))
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
    counts = {"pbj_count": f"{pbj:.0f}", "deli_count": f"{deli:.0f}", "veg_count": f"{veg_sw:.0f}",
              "halal_count": f"{halal_sw:.0f}", "kosher_count": f"{kosher_sw:.0f}"}
    notes = ["Sandwiches: " + " + ".join(mix),
             "Storage: bag opened turkey, cheese, bread and sliced toppings; label, date, back in the cooler.",
             "Toppings: " + ", ".join(t.replace("_", " ") for t in toppings)]
    return n, notes, counts
