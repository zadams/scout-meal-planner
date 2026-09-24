"""Printable per-group handouts: each group's meals with prep and serving
instructions, plus its own shopping list and hand-offs. One HTML file per
group; each meal starts on a new printed page. Standard library only.
"""
import datetime
import html
import os
import re

CSS = """
:root { --ink:#1d1d1f; --muted:#5f6368; --line:#d9dce1; --accent:#1f5f3f; --tint:#f3f6f4; --warn:#8a4b00; --warnbg:#fff6e8; }
* { box-sizing: border-box; }
body { font: 14px/1.45 -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; color: var(--ink);
       background: #fff; margin: 0 auto; max-width: 8.5in; padding: 24px 16px; }
h1 { font-size: 24px; margin: 0 0 4px; }
h2 { font-size: 20px; margin: 0 0 2px; color: var(--accent); }
h3 { font-size: 13px; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); margin: 18px 0 6px; }
.sub { color: var(--muted); margin: 0 0 12px; }
.meal, .shop { border-top: 3px solid var(--accent); padding-top: 14px; margin-top: 28px; }
.cols { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
@media (max-width: 640px) { .cols { grid-template-columns: 1fr; } }
ul { margin: 0; padding-left: 18px; }
ul.check { list-style: none; padding-left: 0; }
ul.check li::before { content: "\\2610"; margin-right: 8px; }
table { width: 100%; border-collapse: collapse; }
td, th { border-bottom: 1px solid var(--line); padding: 5px 6px; text-align: left; vertical-align: top; }
th { font-size: 12px; color: var(--muted); font-weight: 600; }
td.t { white-space: nowrap; font-weight: 600; width: 64px; }
td.box { width: 22px; }
td.box::before { content: "\\2610"; }
.diet { background: var(--tint); border-radius: 6px; padding: 8px 12px; }
.diet b { display: inline-block; min-width: 92px; }
.warn { background: var(--warnbg); color: var(--warn); border-radius: 6px; padding: 8px 12px; margin-top: 8px; }
.line { font-weight: 600; }
footer { color: var(--muted); font-size: 12px; margin-top: 28px; }
@media print {
  body { max-width: none; padding: 0; font-size: 12px; }
  .meal, .shop { break-before: page; margin-top: 0; }
  .meal:first-of-type { break-before: auto; }
  table, .diet, ul { break-inside: avoid; }
  @page { margin: 0.5in; }
}
"""

REQ_LABEL = {"vegetarian": "Vegetarian", "halal": "Halal", "kosher": "Kosher",
             "gluten_free": "Gluten-free", "nut_free": "Nut-free"}


def e(s):
    return html.escape(str(s))


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "group"


def _ul(items, check=False):
    if not items:
        return ""
    cls = ' class="check"' if check else ""
    return f"<ul{cls}>" + "".join(f"<li>{e(i)}</li>" for i in items) + "</ul>"


def _meal(m, result, catalog, fmt_qty):
    items = catalog["items"]
    out = [f'<section class="meal"><h2>{e((m["day"] + " " + m["name"]).strip())}</h2>',
           f'<p class="sub">{e(m["menu"])} · planned for about {m["people"]} people</p>']
    if m["diet"]:
        rows = "".join(f"<div><b>{e(REQ_LABEL.get(r, r))}</b> {e(t)}</div>" for r, t in m["diet"].items())
        out.append(f'<h3>Special diets at this meal</h3><div class="diet">{rows}</div>')
    crew = ", ".join(f"{n} {w}" for w, n in m.get("crew", {}).items() if n)
    out.append('<div class="cols"><div>')
    out.append(f"<h3>Crew{(' (' + e(crew) + ')') if crew else ''}</h3>" + (_ul(m["roles"]) or "<p>1-2 adults.</p>"))
    out.append("<h3>Equipment</h3>" + _ul(m["equipment"], check=True))
    out.append("</div><div><h3>Food &amp; supplies for this meal</h3><table>")
    for k, q in m["needs"]:
        out.append(f'<tr><td class="box"></td><td>{e(items[k]["name"])}</td><td>{e(fmt_qty(q, items[k]["unit"]))}</td></tr>')
    out.append("</table></div></div>")
    if m["steps"]:
        out.append("<h3>Prep &amp; cooking (T = serving time)</h3><table>")
        for st in m["steps"]:
            out.append(f'<tr><td class="box"></td><td class="t">{e(st["t"])}</td><td>{e(st["text"])}</td></tr>')
        out.append("</table>")
    if m["line"] or m["serving"]:
        out.append("<h3>Serving</h3>")
        if m["line"]:
            out.append(f'<p class="line">{" → ".join(e(x) for x in m["line"])}</p>')
        out.append(_ul(m["serving"]))
    if m["food_safety"]:
        out.append("<h3>Food safety</h3>" + _ul(m["food_safety"]))
    carry_out = [c for c in result.get("carry", []) if c["from"] == m["id"]]
    carry_in = [c for c in result.get("carry", []) if c["to"] == m["id"]]
    cleanup = list(m["cleanup"]) + [f"Save leftover {c['item'].lower()} for {c['to']}"
                                    + ("" if c["item"] == c["into"] else f" (use with the {c['into'].lower()})")
                                    + ": bag, label, date, into the cooler." for c in carry_out]
    if cleanup:
        out.append("<h3>Cleanup &amp; leftovers</h3>" + _ul(cleanup, check=True))
    if carry_in:
        out.append('<div class="warn">Leftovers may come to you: '
                   + "; ".join(f"{e(c['item'].lower())} from {e(c['from'])} ({e(c['group'])})" for c in carry_in)
                   + ". Use them if they're labeled, dated and cold. The plan doesn't count on them.</div>")
    other = [n for n in m["notes"] if not n.startswith(("Prep crew:", "Storage:", "Crew:"))]
    if other:
        out.append("<h3>Planner notes</h3>" + _ul(other))
    out.append("</section>")
    return "\n".join(out)


def _shopping(group, result, catalog, trip, fmt_qty):
    stores = trip.get("stores", {})
    label = {"warehouse": " / ".join(stores.get("warehouse", [])) or "Warehouse club",
             "grocery": stores.get("grocery", "Grocery store"),
             "specialty": stores.get("specialty", "Specialty"),
             "supply": "Supplies (check the pack's supply bin first)"}
    mine = [l for l in result["lines"] if l["buyer"] == group]
    out = ['<section class="shop"><h2>Shopping list</h2>',
           '<p class="sub">Everything this group buys, including shared items for other groups (below).</p>']
    for st in ("warehouse", "grocery", "specialty", "supply"):
        rows = [l for l in mine if l["store"] == st]
        if not rows:
            continue
        out.append(f"<h3>{e(label[st])}</h3><table><tr><th></th><th>Item</th><th>Buy</th><th>For</th></tr>")
        for l in rows:
            if l["key"] == "fruit" and result["fruit"]:
                for fr in result["fruit"]:
                    out.append(f'<tr><td class="box"></td><td>{e(fr["type"])}</td>'
                               f'<td>{fr["packs"]} × {e(fr["pack_label"])}</td><td>{e(", ".join(l["meals"]))}</td></tr>')
                continue
            buy = f'{l["packs"]} × {l["pack"]} {l["pack_label"]}' if l["packs"] \
                else f'{fmt_qty(l["amount"], l["unit"])} {l["pack_label"]}'.strip()
            name = l["name"] + (" (staple: check the chuck box first)" if l.get("staple") else "")
            out.append(f'<tr><td class="box"></td><td>{e(name)}</td><td>{e(buy)}</td><td>{e(", ".join(l["meals"]))}</td></tr>')
        out.append("</table>")
    give = [(l, g, q) for l in mine for g, q in l["by_group"].items() if g != group]
    get = [(l, q) for l in result["lines"] if l["buyer"] != group and group in l["by_group"]
           for g, q in l["by_group"].items() if g == group]
    if trip.get("shopping", "per_group") != "per_pack" and (give or get):
        out.append("<h3>Hand-offs</h3><ul class=\"check\">")
        for l, g, q in give:
            what = "share" if (l.get("staple") or l["store"] == "supply") else f"~{fmt_qty(q, l['unit'])}"
            out.append(f"<li>Give {e(g)}: {e(l['name'].lower())} ({e(what)})</li>")
        for l, q in get:
            what = "share" if (l.get("staple") or l["store"] == "supply") else f"~{fmt_qty(q, l['unit'])}"
            out.append(f"<li>Get from {e(l['buyer'])}: {e(l['name'].lower())} ({e(what)})</li>")
        out.append("</ul>")
    out.append("</section>")
    return "\n".join(out)


def write_handouts(result, trip, catalog, outdir, fmt_qty):
    os.makedirs(outdir, exist_ok=True)
    groups = []
    for m in result["meals"]:
        if m["group"] not in groups:
            groups.append(m["group"])
    est = trip.get("_estimated", [])
    paths = []
    for g in groups:
        meals = [m for m in result["meals"] if m["group"] == g]
        names = ", ".join((m["day"] + " " + m["name"]).strip() for m in meals)
        body = [f"<h1>{e(result['trip'])}: {e(g)}</h1>",
                f'<p class="sub">Your meals: {e(names)}</p>']
        if est:
            body.append(f'<div class="warn">Some diet counts are estimates ({e(", ".join(est))}); '
                        "the sealed/labeled items cover the planned numbers. Ask the planner if a family isn't covered.</div>")
        body += [_meal(m, result, catalog, fmt_qty) for m in meals]
        if trip.get("shopping", "per_group") != "per_pack":
            body.append(_shopping(g, result, catalog, trip, fmt_qty))
        body.append(f"<footer>Generated {datetime.date.today():%Y-%m-%d} by scout-meal-planner. "
                    "Quantities include cushions for walk-ups, big eaters and prep accidents.</footer>")
        doc = ("<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
               "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
               f"<title>{e(g)} Meal Packet</title><style>{CSS}</style></head><body>"
               + "\n".join(body) + "</body></html>")
        path = os.path.join(outdir, f"{slug(g)}.html")
        with open(path, "w") as f:
            f.write(doc)
        paths.append(path)
    if trip.get("shopping", "per_group") == "per_pack":
        doc = ("<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
               "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
               f"<title>Pack Shopping List</title><style>{CSS}</style></head><body>"
               f"<h1>{e(result['trip'])}: pack shopping list</h1>"
               + _shopping("Pack shopper", result, catalog, trip, fmt_qty) + "</body></html>")
        path = os.path.join(outdir, "pack-shopping-list.html")
        with open(path, "w") as f:
            f.write(doc)
        paths.append(path)
    return paths
