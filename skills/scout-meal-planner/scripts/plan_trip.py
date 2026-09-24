#!/usr/bin/env python3
"""Plan every meal of a camping trip and produce ONE coordinated shopping list.

Why pooling matters: planning meals separately stacks a safety cushion onto
every meal and rounds each one up to whole packs, which is how a trip ends
with far too many apples. Here each ingredient is summed across meals first,
gets a single cushion sized to its biggest meal, and is rounded to packs once.
Meals marked "from_leftovers" (e.g. Sunday fruit) draw on that spare instead
of adding to the purchase.

Usage:
  plan_trip.py --profile plans/<trip>.json          # markdown report
  plan_trip.py --profile plans/<trip>.json --json   # structured output
A single-meal profile without a "meals" list is treated as a sandwich lunch
(the original sandwich_lunch.py format).
"""
import argparse
import json
import math
import os
import sys
from collections import OrderedDict, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import sandwich  # noqa: E402

REQUIREMENTS = ["vegetarian", "halal", "kosher", "gluten_free", "nut_free"]
DEFAULT_FRUIT_MIX = {"clementine": 0.4, "banana": 0.3, "apple": 0.3}
BIG_EATER_SHARE_OF_ADULT = 0.85  # a big eater's extra, as a fraction of an adult portion
INTEGER_UNITS = {"egg", "packet", "bag", "plate", "bowl", "napkin", "bottle", "tortilla",
                 "cup", "bar", "sheet", "mallow", "can", "meal", "chip", "ring", "leaf",
                 "slice", "onion", "pepper", "serving"}
# Old sandwich_lunch.py "packs" keys -> catalog keys
LEGACY_PACK_KEYS = {"pb_jar_oz": "peanut_butter", "jelly_jar_oz": "jelly",
                    "turkey_pack_lb": "turkey_deli", "cheese_pack_slices": "cheese_sliced",
                    "chips_pack": "chips", "water_pack": "water", "hummus_tub_oz": "hummus"}


def load_json(path):
    with open(path) as f:
        return json.load(f)


class Context:
    """People and requirements for one meal (trip defaults + meal overrides)."""

    def __init__(self, trip, meal):
        g = lambda k, d=0: meal.get(k, trip.get(k, d))  # noqa: E731
        self.kids, self.adults = g("kids"), g("adults")
        self.walkups, self.big_eaters = g("walkups"), g("big_eaters")
        self.prep_loss = g("prep_loss", 0.05)
        self.bump = 1.2 if g("hungry", False) else 1.0
        self.reqs = dict(trip["_reqs"])
        self.nut_free = trip["_nut_free"]

    @property
    def people(self):
        return self.kids + self.adults + self.walkups

    def req(self, name):
        return self.reqs.get(name, 0)

    def without_kosher(self):
        """Hot meals: kosher eaters get a sealed certified meal instead."""
        k = self.req("kosher")
        if k and self.kids + self.adults:
            frac = self.kids / (self.kids + self.adults)
            self.kids -= k * frac
            self.adults -= k * (1 - frac)
            self.reqs["kosher"] = 0
        return k


def parse_requirements(trip):
    reqs, estimated = {}, []
    raw = trip.get("requirements", {})
    unknown = set(raw) - set(REQUIREMENTS)
    if unknown:
        sys.exit(f"Unknown requirement(s): {', '.join(sorted(unknown))}")
    for name in REQUIREMENTS:
        r = raw.get(name, {})
        on = r.get("enabled", False)
        if name == "nut_free":
            trip["_nut_free"] = on
            continue
        if on and "count" not in r:
            sys.exit(f'"{name}" is enabled but has no "count" — use a best guess and set "estimated": true.')
        reqs[name] = r.get("count", 0) if on else 0
        if on and r.get("estimated"):
            estimated.append(name)
    trip["_reqs"] = reqs
    trip["_estimated"] = estimated


def normalize(profile):
    """Accept a trip profile or a legacy single sandwich-lunch profile."""
    trip = dict(profile)
    if "meals" not in trip:
        opts = {k: trip.pop(k) for k in ("pbj_share_kids", "pbj_share_adults", "toppings",
                                         "water_bottles") if k in trip}
        trip["meals"] = [{"id": "lunch", "name": trip.get("event", "Lunch"),
                          "menu": "sandwich_lunch", "options": opts}]
    packs = {}
    for k, v in trip.get("packs", {}).items():
        packs[LEGACY_PACK_KEYS.get(k, k)] = v
    trip["packs"] = packs
    parse_requirements(trip)
    return trip


def template_needs(menu, ctx):
    """Raw needs from a JSON menu: list of (key, qty, buffer, loss, from_leftovers)."""
    out = []
    for it in menu["items"]:
        kid, adult = it.get("kid", 0), it.get("adult", 0)
        avg = (kid + adult) / 2
        share = it.get("share", 1.0)
        if "only" in it:
            q = sum(ctx.req(g) for g in it["only"]) * avg
        else:
            q = ctx.kids * kid + ctx.adults * adult
            q -= sum(ctx.req(g) for g in it.get("except", [])) * avg
            if it.get("walkups", True):
                q += ctx.walkups * avg
            if it.get("main"):
                q += ctx.big_eaters * BIG_EATER_SHARE_OF_ADULT * adult
        q = max(0, q) * share * ctx.bump
        loss = it.get("loss", 0)
        loss = ctx.prep_loss if loss is True else float(loss)
        out.append((it["key"], q, it.get("buffer", 0), loss, it.get("from_leftovers", False)))
    return out


def merge_needs(raw):
    merged = OrderedDict()
    for k, q, *_ in raw:
        if q > 0:
            merged[k] = merged.get(k, 0) + q
    return list(merged.items())


def plan(trip, catalog):
    items = catalog["items"]
    meals_out, uses = [], defaultdict(list)  # key -> [(meal_idx, group, qty, buffer, loss, leftovers)]
    for idx, meal in enumerate(trip["meals"]):
        ctx = Context(trip, meal)
        mname = meal.get("menu") or meal.get("template")
        if mname == "sandwich_lunch":
            menu = dict(sandwich.MENU)
            raw, notes = sandwich.needs(ctx, meal.get("options", {}))
            raw = [(k, q, b, ctx.prep_loss if l else 0, False) for k, q, b, l in raw]
        else:
            path = os.path.join(SKILL, "menus", f"{mname}.json")
            if not os.path.exists(path):
                sys.exit(f"No menu named {mname!r} (looked for {path})")
            menu = load_json(path)
            notes = list(menu.get("notes", []))
            kosher_alt = ctx.without_kosher() if menu.get("hot") else 0
            raw = template_needs(menu, ctx)
            if kosher_alt:
                raw.append(("kosher_sealed_meal", kosher_alt, 0, 0, False))
                notes.append(f"{kosher_alt} kosher eater(s) get a sealed certified meal; hot food from shared pots/griddles usually isn't kosher. Ask the families.")
        for k, q, b, l, lo in raw:
            if k not in items:
                sys.exit(f"Menu {mname!r} uses unknown ingredient {k!r}; add it to references/ingredients.json")
            if q > 0:
                uses[k].append((idx, meal.get("group", "(unassigned)"), q, b, l, lo))
        meals_out.append({"id": meal.get("id", f"meal{idx+1}"), "day": meal.get("day", ""),
                          "name": meal.get("name", menu["name"]), "menu": menu["name"],
                          "group": meal.get("group", "(unassigned)"), "people": round(ctx.people),
                          "equipment": menu.get("equipment", []), "notes": notes,
                          "prep": menu.get("prep", []), "line": menu.get("line", []),
                          "needs": merge_needs(raw)})

    on_hand = trip.get("on_hand", {})
    lines = OrderedDict()
    for key in sorted(uses, key=lambda k: min(u[0] for u in uses[k])):
        u = uses[key]
        regular = [x for x in u if not x[5]]
        from_left = sum(x[2] for x in u if x[5])
        used = sum(q * (1 + l) for _, _, q, _, l, _ in regular)
        cushion = max((q * b * (1 + l) for _, _, q, b, l, _ in regular), default=0)
        need = used + cushion  # leftover-only uses (from_left) never add to the purchase
        if not regular:
            continue
        need = max(0, need - on_hand.get(key, 0))
        by_group = defaultdict(float)
        for _, grp, q, _, l, _ in regular:
            by_group[grp] += q * (1 + l)
        buyer = max(by_group, key=lambda g: (by_group[g], -min(x[0] for x in regular if x[1] == g)))
        info = items[key]
        pack = trip["packs"].get(key, info.get("pack"))
        unit = info["unit"]
        amount = math.ceil(need - 1e-9) if unit in INTEGER_UNITS else round(need, 1)
        packs = math.ceil(need / pack - 1e-9) if pack else None
        bought = packs * pack if packs else amount
        lines[key] = {"key": key, "name": info["name"], "unit": unit, "amount": amount,
                      "packs": packs, "pack": pack, "pack_label": info.get("pack_label", ""),
                      "store": info.get("store", "warehouse"), "buyer": buyer,
                      "meals": [meals_out[i]["id"] for i in sorted({x[0] for x in u})],
                      "by_group": dict(by_group), "consumed": used, "from_leftovers": from_left,
                      "leftover": max(0, bought - used), "perishable": info.get("perishable", False),
                      "check": info.get("check", [])}

    fruit = None
    if "fruit" in lines:
        mix = trip.get("fruit_mix", DEFAULT_FRUIT_MIX)
        types = catalog["fruit_types"]
        f = lines["fruit"]
        fruit, servings_bought = [], 0
        for name, frac in mix.items():
            t = types[name]
            pieces = f["amount"] * frac * t["per_serving"]
            n = math.ceil(pieces / t["pack"] - 1e-9)
            servings_bought += n * t["pack"] / t["per_serving"]
            fruit.append({"type": t["name"], "pieces": math.ceil(pieces), "packs": n, "pack_label": t["pack_label"]})
        f["leftover"] = max(0, servings_bought - f["consumed"])
    return {"trip": trip.get("trip", trip.get("event", "Trip")), "meals": meals_out,
            "lines": list(lines.values()), "fruit": fruit}


PLURAL = {"leaf": "leaves"}


def fmt_qty(q, unit):
    if unit not in INTEGER_UNITS:
        return f"{q:.1f} {unit}"
    return f"{q:.0f} {unit if round(q) == 1 else PLURAL.get(unit, unit + 's')}"


def report(result, trip, catalog):
    items, out = catalog["items"], []
    p = lambda s="": out.append(s)  # noqa: E731
    reqs = trip["_reqs"]
    people = trip.get("kids", 0) + trip.get("adults", 0)
    p(f"# {result['trip']}")
    p()
    p(f"Headcount: {trip.get('kids', 0)} kids + {trip.get('adults', 0)} adults = {people}"
      + (f" (+{trip.get('walkups')} walk-ups" if trip.get("walkups") else "")
      + (f", {trip.get('big_eaters')} big eaters" if trip.get("big_eaters") else "")
      + (")" if trip.get("walkups") else "") + ". Everyone planned for every meal.")
    on = [f"{k.replace('_', '-')} {v}" for k, v in reqs.items() if v] + (["nut-free"] if trip["_nut_free"] else [])
    p(f"Requirements on: {', '.join(on) if on else 'none'}")
    if trip["_estimated"]:
        p(f"**Estimated counts (confirm if possible):** {', '.join(trip['_estimated'])}")
    p()

    p("## Meals")
    for m in result["meals"]:
        p()
        p(f"### {m['day']} {m['name']}".replace("###  ", "### "))
        p(f"*{m['menu']}* · **{m['group']}** · planned for ~{m['people']}")
        for n in m["notes"]:
            p(f"- {n}")
        if m["equipment"]:
            p(f"- Equipment: {', '.join(m['equipment'])}")
        if m["line"]:
            p(f"- Line: {' → '.join(m['line'])}")
        for s in m["prep"]:
            p(f"- Prep {s}")
        p("- Uses: " + "; ".join(f"{items[k]['name'].lower()} {fmt_qty(q, items[k]['unit'])}" for k, q in m["needs"]))

    p()
    p("## Shopping list (all meals combined)")
    order = ["warehouse", "grocery", "specialty", "supply"]
    stores = trip.get("stores", {})
    label = {"warehouse": " / ".join(stores.get("warehouse", [])) or "Warehouse club",
             "grocery": stores.get("grocery", "Grocery store"),
             "specialty": stores.get("specialty", "Specialty"),
             "supply": "Supplies (check the pack's supply bin first)"}
    for st in order:
        rows = [l for l in result["lines"] if l["store"] == st and l["key"] != "fruit"]
        if st == "warehouse" and result["fruit"]:
            rows.append(None)
        if not rows:
            continue
        p()
        p(f"**{label[st]}**")
        p()
        p("| Item | Need | Buy | Buyer | Used at |")
        p("|---|---|---|---|---|")
        for l in rows:
            if l is None:
                f = next(x for x in result["lines"] if x["key"] == "fruit")
                for fr in result["fruit"]:
                    p(f"| {fr['type']} | {fr['pieces']} | {fr['packs']} × {fr['pack_label']} | {f['buyer']} | {', '.join(f['meals'])} |")
                continue
            buy = f"{l['packs']} × {l['pack']} {l['pack_label']}" if l["packs"] else f"{fmt_qty(l['amount'], l['unit'])} {l['pack_label']}".strip()
            p(f"| {l['name']} | {fmt_qty(l['amount'], l['unit'])} | {buy} | {l['buyer']} | {', '.join(l['meals'])} |")

    shared = [l for l in result["lines"] if len(l["by_group"]) > 1]
    if shared:
        p()
        p("## Shared items: one buyer, hand off the rest")
        for l in shared:
            others = [f"~{fmt_qty(q, l['unit'])} to {g}" for g, q in l["by_group"].items() if g != l["buyer"]]
            p(f"- **{l['name']}**: {l['buyer']} buys all; hands {', '.join(others)}.")

    served_later = [l for l in result["lines"] if l["from_leftovers"]]
    if served_later:
        p()
        p("## Served from leftovers (nothing extra bought)")
        for l in served_later:
            avail = l["leftover"]
            enough = "enough for everyone" if avail >= l["from_leftovers"] else \
                f"not enough for everyone (~{fmt_qty(l['from_leftovers'], l['unit'])} if all took one); that's intentional"
            p(f"- {l['name']}: ~{fmt_qty(avail, l['unit'])} expected to be left; {enough}.")

    def leftovers(perishable):
        rows = [l for l in result["lines"] if l["perishable"] == perishable and l["store"] != "supply"
                and l["leftover"] >= 1 and not l["from_leftovers"]]
        for l in sorted(rows, key=lambda l: -l["leftover"] / max(l["consumed"], 1e-9)):
            pct = 100 * l["leftover"] / max(l["consumed"], 1e-9)
            p(f"- {l['name']}: ~{fmt_qty(l['leftover'], l['unit'])} ({pct:.0f}% over expected use)")
    p()
    p("## Expected leftovers: waste risk (perishable)")
    p("Mostly pack rounding plus the one-per-trip cushion. Big percentages here are worth a smaller pack.")
    leftovers(True)
    p()
    p("## Expected leftovers: keeps for the next trip")
    leftovers(False)

    checks = defaultdict(list)
    for l in result["lines"]:
        for c in l["check"]:
            checks[c].append(l["name"])
    active = {"kosher": bool(reqs.get("kosher")), "nuts": True,
              "gelatin": any(reqs.get(k) for k in ("vegetarian", "halal", "kosher"))}
    shown = [c for c in checks if active.get(c)]
    if shown:
        p()
        p("## Label checks")
        for c in shown:
            p(f"- {catalog['checks'][c]} → {', '.join(checks[c])}")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--profile", required=True)
    ap.add_argument("--json", action="store_true", help="print structured output")
    for k in ("kids", "adults", "walkups", "big_eaters"):
        ap.add_argument("--" + k.replace("_", "-"), type=int)
    for r in ("vegetarian", "halal", "kosher", "gluten_free"):
        ap.add_argument("--" + r.replace("_", "-"), type=int, help=f"override {r} count (0 = off)")
    ap.add_argument("--nut-free", action="store_true")
    a = ap.parse_args()

    profile = load_json(a.profile)
    for k in ("kids", "adults", "walkups", "big_eaters"):
        if getattr(a, k) is not None:
            profile[k] = getattr(a, k)
    reqs = profile.setdefault("requirements", {})
    for r in ("vegetarian", "halal", "kosher", "gluten_free"):
        v = getattr(a, r)
        if v is not None:
            reqs[r] = {"enabled": v > 0, "count": v}
    if a.nut_free:
        reqs["nut_free"] = {"enabled": True}

    catalog = load_json(os.path.join(SKILL, "references", "ingredients.json"))
    trip = normalize(profile)
    result = plan(trip, catalog)
    if a.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print(report(result, trip, catalog))


if __name__ == "__main__":
    main()
