"""One-page review of a whole trip plan (for the planner or a committee):
open questions, schedule, what pooling saved, decisions, every meal's
countdown, each group's shopping list, and the leftover plan. Self-contained
HTML (Google Fonts only) that works as a shareable artifact.

Trip-specific prose comes from the profile: "decisions" ([title, text] pairs),
"questions" (list), and "group_notes" ({group: note shown on its list}).
"""
import copy
import html

REQ = {"vegetarian": "Vegetarian", "no_pork": "No pork", "no_red_meat": "No red meat",
       "halal": "Halal", "kosher": "Kosher", "gluten_free": "Gluten-free", "nut_free": "Nut-free"}
STORE = {"warehouse": None, "grocery": None, "specialty": None, "supply": "Supplies (check the bin first)"}


def e(s):
    return html.escape(str(s))


def _short(g):
    return g.split("–")[-1].strip() if "–" in g else g


def _gtag(g):
    n = g.split("–")[0].strip().replace("Group ", "G") if "–" in g else ""
    return (f'<span class="gtag">{e(n)}</span> ' if n else "") + e(_short(g))


def _ul(xs):
    return "<ul>" + "".join(f"<li>{e(x)}</li>" for x in xs) + "</ul>" if xs else ""


def savings(pt, trip, catalog, result):
    """Bought-if-planned-separately vs. bought-together, for items used at 2+ meals."""
    types = catalog["fruit_types"]
    mix = trip.get("fruit_mix", pt.DEFAULT_FRUIT_MIX)

    def bought(res, key):
        if key == "fruit":
            return sum(x["packs"] * types[k]["pack"] / types[k]["per_serving"]
                       for k, x in zip(mix, res["fruit"] or []))
        line = next((l for l in res["lines"] if l["key"] == key), None)
        if not line:
            return 0
        return line["packs"] * line["pack"] if line["packs"] else line["amount"]

    out = []
    for l in result["lines"]:
        if len(l["meals"]) < 2 or l["store"] == "supply" or l.get("staple"):
            continue
        separate = 0
        for m in trip["meals"]:
            one = copy.deepcopy(trip)
            one["meals"] = [m]
            separate += bought(pt.plan(one, catalog), l["key"])
        together = bought(result, l["key"])
        if separate > together:
            out.append((l, separate, together))
    # fruit first (the classic over-buy), then biggest relative savings
    out.sort(key=lambda x: (x[0]["key"] != "fruit", -(x[1] - x[2]) / max(x[1], 1e-9)))
    return out


def build(result, trip, catalog, pt):
    items, fq = catalog["items"], pt.fmt_qty
    r = result
    stores = trip.get("stores", {})
    store = {"warehouse": " / ".join(stores.get("warehouse", [])) or "Warehouse club",
             "grocery": stores.get("grocery", "Grocery"), "specialty": stores.get("specialty", "Specialty"),
             "supply": STORE["supply"]}
    groups = []
    for m in r["meals"]:
        if m["group"] not in groups:
            groups.append(m["group"])
    reqs, est = trip["_reqs"], set(trip["_estimated"])
    chips = "".join(f'<span class="chip{" est" if k in est else ""}">{e(REQ.get(k, k))} {v}{" · est." if k in est else ""}</span>'
                    for k, v in reqs.items() if v)
    if trip["_nut_free"]:
        chips += '<span class="chip">Nut-free</span>'
    if trip.get("mess_kits"):
        chips += '<span class="chip">Mess kits</span>'
    chips += f'<span class="chip">{"One shopper per group" if trip.get("shopping", "per_group") == "per_group" else "One pack shopper"}</span>'

    sched = "".join(f'<tr><td class="when">{e(m["day"])}</td><td><b>{e(m["name"])}</b><div class="dim">{e(m["menu"])}</div></td>'
                    f'<td>{_gtag(m["group"])}</td><td class="num">{m["people"]}</td></tr>' for m in r["meals"])
    decisions = "".join(f"<div class='dec'><dt>{e(a)}</dt><dd>{e(b)}</dd></div>" for a, b in trip.get("decisions", []))
    questions = trip.get("questions", [])

    sv = savings(pt, trip, catalog, r)
    sv_rows = "".join(
        f"<tr><td>{e(l['name'])}</td><td class='num'>{e(fq(s, l['unit']))}</td><td class='num'><b>{e(fq(t, l['unit']))}</b></td>"
        f"<td class='dim'>{e(', '.join(l['meals']))}</td></tr>" for l, s, t in sv[:8])

    def meal_card(m):
        diet = "".join(f"<div class='drow'><span class='dlab'>{e(REQ.get(k, k))}</span><span>{e(v)}</span></div>"
                       for k, v in m["diet"].items())
        steps = "".join(f"<li><span class='t'>{e(s['t'])}</span><span>{e(s['text'])}</span></li>" for s in m["steps"])
        food = "".join(f"<tr><td>{e(items[k]['name'])}</td><td class='num'>{e(fq(q, items[k]['unit']))}</td></tr>"
                       for k, q in m["needs"])
        crew = ", ".join(f"{n} {w}" for w, n in m.get("crew", {}).items() if n)
        carry = [c for c in r["carry"] if c["from"] == m["id"]]
        cleanup = m["cleanup"] + [f"Save leftover {c['item'].lower()} for {c['to']}"
                                  + ("" if c["item"] == c["into"] else f" (use with the {c['into'].lower()})") for c in carry]
        line = " → ".join(e(x) for x in m["line"])
        return f"""<article class="meal" id="{e(m['id'])}">
  <div class="eyebrow">{e(m['day'])} · {_gtag(m['group'])}</div><h3>{e(m['name'])}</h3>
  <p class="dim">{e(m['menu'])} · planned for {m['people']}{(' · crew ' + e(crew)) if crew else ''}</p>
  {f"<div class='diet'>{diet}</div>" if diet else ""}
  <div class="mgrid">
    <section><h4>Countdown (T = serving time)</h4><ol class="steps">{steps}</ol>
      {f"<h4>Serving line</h4><p class='line'>{line}</p>" if line else ""}{_ul(m['serving'])}</section>
    <section>{"<h4>Crew</h4>" + _ul(m['roles']) if m['roles'] else ""}
      <h4>Equipment</h4>{_ul(m['equipment'])}<h4>Food safety</h4>{_ul(m['food_safety'])}
      <h4>Cleanup and leftovers</h4>{_ul(cleanup)}</section>
  </div>
  <details><summary>Food and supplies for this meal ({len(m['needs'])} items)</summary>
    <div class="tw"><table class="qty">{food}</table></div></details>
</article>"""

    def buy_of(l):
        return f"{l['packs']} × {l['pack']} {l['pack_label']}" if l["packs"] else f"{fq(l['amount'], l['unit'])} {l['pack_label']}".strip()

    shop = ""
    buyers = groups if trip.get("shopping", "per_group") == "per_group" else ["Pack shopper"]
    for g in buyers:
        mine = [l for l in r["lines"] if l["buyer"] == g]
        rows = ""
        for st in ("warehouse", "grocery", "specialty", "supply"):
            for l in [x for x in mine if x["store"] == st]:
                if l["key"] == "fruit" and r["fruit"]:
                    for fr in r["fruit"]:
                        rows += (f"<tr><td>{e(fr['type'])}</td><td>{fr['packs']} × {e(fr['pack_label'])}</td>"
                                 f"<td class='st'>{e(store[st])}</td><td class='dim'>{e(', '.join(l['meals']))}</td></tr>")
                    continue
                tag = " <span class='mini'>staple</span>" if l.get("staple") else ""
                rows += (f"<tr><td>{e(l['name'])}{tag}</td><td>{e(buy_of(l))}</td><td class='st'>{e(store[st])}</td>"
                         f"<td class='dim'>{e(', '.join(l['meals']))}</td></tr>")
        gives = "".join(
            f"<li>{e(l['name'])} → {e(_short(gg))} ({'share' if (l.get('staple') or l['store'] == 'supply') else '~' + e(fq(q, l['unit']))})</li>"
            for l in mine for gg, q in l["by_group"].items() if gg != g and g != "Pack shopper")
        note = trip.get("group_notes", {}).get(g)
        shop += (f"<section class='shop'><h3>{_gtag(g)}</h3>{f'<p class=note>{e(note)}</p>' if note else ''}"
                 f"<div class='tw'><table class='list'><thead><tr><th>Item</th><th>Buy</th><th>Store</th><th>For</th></tr></thead>"
                 f"<tbody>{rows}</tbody></table></div>"
                 + (f"<h4>Hands to other groups</h4><ul class='cols2'>{gives}</ul>" if gives else "") + "</section>")

    carry = "".join(f"<li><b>{e(c['from'])}</b> → <b>{e(c['to'])}</b>: {e(c['item'].lower())}"
                    + ("" if c["item"] == c["into"] else f" (use with the {e(c['into'].lower())})") + "</li>" for c in r["carry"])

    def lo(perishable):
        rows = [l for l in r["lines"] if l["perishable"] == perishable and l["store"] != "supply"
                and l["leftover"] >= 1 and not l["from_leftovers"]]
        rows.sort(key=lambda l: -l["leftover"] / max(l["consumed"], 1e-9))
        out = ""
        for l in rows[:12]:
            pct = 100 * l["leftover"] / max(l["consumed"], 1e-9)
            out += (f"<tr><td>{e(l['name'])}</td><td class='num'>~{e(fq(l['leftover'], l['unit']))}</td>"
                    f"<td class='bar'><span style='width:{min(100, pct / 3):.0f}%'></span><em>{pct:.0f}%</em></td></tr>")
        return out

    later = [l for l in r["lines"] if l["from_leftovers"]]
    later_html = "".join(f"<li>{e(l['name'])}: ~{e(fq(l['leftover'], l['unit']))} expected for later meals; nothing extra bought.</li>" for l in later)
    people = trip.get("kids", 0) + trip.get("adults", 0)

    return f"""<title>{e(r['trip'])} Meals</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bitter:wght@600;700&family=Source+Sans+3:wght@400;600;700&display=swap">
<style>{CSS}</style>
<div class="wrap">
<header>
  <div class="eyebrow">Pack meal plan · for review</div>
  <h1>{e(r['trip'])} Meals</h1>
  <p class="lede">{len(r['meals'])} meals and snacks planned together so supplies aren't bought twice. Each group gets a printable packet with its menu, countdown and shopping list.</p>
  <div class="facts">
    <div><b>{people}</b><span class="dim">campers ({trip.get('kids', 0)} kids, {trip.get('adults', 0)} adults)</span></div>
    <div><b>+{trip.get('walkups', 0)} / +{trip.get('big_eaters', 0)}</b><span class="dim">walk-ups / big eaters</span></div>
    <div><b>{len(r['meals'])}</b><span class="dim">meals and snacks</span></div>
    <div><b>{len(groups)}</b><span class="dim">cooking groups</span></div>
  </div>
  <div class="chips">{chips}</div>
</header>
<nav class="tabs" role="tablist" aria-label="Plan sections">
  <button role="tab" id="tab-overview" aria-controls="overview" aria-selected="true">Overview</button>
  <button role="tab" id="tab-meals" aria-controls="meals" aria-selected="false">Meals</button>
  <button role="tab" id="tab-shopping" aria-controls="shopping" aria-selected="false">Shopping</button>
  <button role="tab" id="tab-leftovers" aria-controls="leftovers" aria-selected="false">Leftovers</button>
</nav>
<div class="panel" id="overview" role="tabpanel" aria-labelledby="tab-overview">
  {f'<div class="warnbox"><h2>Needs answers before the packets go out</h2>{_ul(questions)}</div>' if questions else ''}
  <section class="card"><h2>The weekend</h2><div class="tw"><table><thead><tr><th>Day</th><th>Meal</th><th>Group</th><th class="num">Planned for</th></tr></thead><tbody>{sched}</tbody></table></div></section>
  {f'<section class="card"><h2>What planning together saved</h2><p class="dim">Items used at more than one meal: what separate plans would buy vs. one combined purchase (one cushion, rounded to packages once).</p><div class="tw"><table><thead><tr><th>Item</th><th class="num">Separately</th><th class="num">Together</th><th>Meals</th></tr></thead><tbody>{sv_rows}</tbody></table></div></section>' if sv_rows else ''}
  {f'<section class="card"><h2>Decisions built into the plan</h2><dl class="dl">{decisions}</dl></section>' if decisions else ''}
</div>
<div class="panel" id="meals" role="tabpanel" aria-labelledby="tab-meals" hidden>{"".join(meal_card(m) for m in r["meals"])}</div>
<div class="panel" id="shopping" role="tabpanel" aria-labelledby="tab-shopping" hidden>
  <p class="lede dim">Each shopper buys their meals plus the shared items assigned to them, then hands off the rest. Items marked <span class="mini">staple</span> are often already in the chuck box.</p>
  {shop}
</div>
<div class="panel" id="leftovers" role="tabpanel" aria-labelledby="tab-leftovers" hidden>
  <section class="card"><h2>Carry forward</h2><p class="dim">Bag, label, date, back in the cooler. A bonus only: no later meal counts on these.</p><ul>{carry}{later_html}</ul></section>
  <div class="two">
    <section class="card"><h2>Waste risk</h2><p class="dim">Perishables left after the last meal, as a share of what's used. Mostly package rounding.</p><div class="tw"><table>{lo(True)}</table></div></section>
    <section class="card"><h2>Keeps for next trip</h2><p class="dim">Shelf-stable extras. Record them as on-hand next time.</p><div class="tw"><table>{lo(False)}</table></div></section>
  </div>
</div>
</div>
<script>{JS}</script>
"""


CSS = """
:root { --bg:#F5F6F2; --surface:#FFFFFF; --ink:#1C2320; --muted:#5B665F; --line:#DCE1DA;
  --accent:#2F5D46; --accent-soft:#E4EEE7; --amber:#A85B16; --amber-soft:#FBEEDD; --bar:#9BB8A6; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { color-scheme: dark;
  --bg:#121714; --surface:#1A211D; --ink:#E4EAE5; --muted:#9AA59E; --line:#2C3530;
  --accent:#8CC4A1; --accent-soft:#213229; --amber:#E7A866; --amber-soft:#33271A; --bar:#4F7B62; } }
:root[data-theme="dark"] { color-scheme: dark; --bg:#121714; --surface:#1A211D; --ink:#E4EAE5; --muted:#9AA59E; --line:#2C3530;
  --accent:#8CC4A1; --accent-soft:#213229; --amber:#E7A866; --amber-soft:#33271A; --bar:#4F7B62; }
* { box-sizing:border-box; }
body { background:var(--bg); color:var(--ink); font:15px/1.55 "Source Sans 3", "Segoe UI", system-ui, sans-serif; padding-inline:16px; padding-block:24px 64px; }
.wrap { max-width:1060px; margin:0 auto; display:grid; gap:28px; }
h1,h2,h3 { font-family:Bitter, Georgia, serif; text-wrap:balance; margin:0; }
h1 { font-size:clamp(28px,4vw,38px); line-height:1.15; } h2 { font-size:22px; } h3 { font-size:19px; }
h4 { font-size:12px; letter-spacing:.06em; text-transform:uppercase; color:var(--muted); margin:18px 0 6px; }
.dim { color:var(--muted); }
.num { font-variant-numeric:tabular-nums; text-align:right; white-space:nowrap; }
.eyebrow { font-size:12px; letter-spacing:.06em; text-transform:uppercase; color:var(--muted); }
.lede { max-width:68ch; margin:8px 0 0; }
.facts { display:flex; flex-wrap:wrap; gap:8px 24px; margin-top:14px; font-variant-numeric:tabular-nums; }
.facts b { font-size:22px; font-family:Bitter, Georgia, serif; display:block; }
.chips { display:flex; flex-wrap:wrap; gap:6px; margin-top:12px; }
.chip { border:1px solid var(--line); background:var(--surface); border-radius:999px; padding:2px 10px; font-size:13px; }
.chip.est { border-color:var(--amber); color:var(--amber); }
.gtag { display:inline-block; font-size:11px; font-weight:700; color:var(--accent); background:var(--accent-soft); border-radius:4px; padding:0 5px; }
nav.tabs { position:sticky; top:env(safe-area-inset-top,0px); z-index:5; background:var(--bg); display:flex; gap:4px; flex-wrap:wrap; border-bottom:1px solid var(--line); padding-block:8px; }
nav.tabs button { font:inherit; font-weight:600; color:var(--muted); background:none; border:0; padding:6px 12px; border-radius:6px; cursor:pointer; }
nav.tabs button[aria-selected="true"] { color:var(--accent); background:var(--accent-soft); }
nav.tabs button:focus-visible, summary:focus-visible { outline:2px solid var(--accent); outline-offset:2px; }
.panel { display:grid; gap:24px; }
.card, .meal, .shop { background:var(--surface); border:1px solid var(--line); border-radius:10px; padding:18px 20px; }
.tw { overflow-x:auto; }
table { width:100%; border-collapse:collapse; }
td, th { padding:7px 8px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }
th { font-size:12px; color:var(--muted); font-weight:600; letter-spacing:.04em; text-transform:uppercase; }
td.when { font-weight:700; white-space:nowrap; } td.st { white-space:nowrap; color:var(--muted); }
.dl { display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:14px 28px; margin:0; }
.dec dt { font-weight:700; } .dec dd { margin:2px 0 0; color:var(--muted); }
.warnbox { background:var(--amber-soft); border-left:3px solid var(--amber); border-radius:6px; padding:12px 16px; }
.warnbox h2 { color:var(--amber); font-size:18px; margin-bottom:6px; }
.warnbox ul { margin:0; padding-left:20px; display:grid; gap:4px; }
.meal p { margin:2px 0 0; }
.diet { margin-top:12px; background:var(--accent-soft); border-radius:8px; padding:10px 14px; display:grid; gap:4px; }
.drow { display:grid; grid-template-columns:110px 1fr; gap:10px; } .dlab { font-weight:700; color:var(--accent); }
.mgrid { display:grid; grid-template-columns:3fr 2fr; gap:8px 28px; }
@media (max-width:760px) { .mgrid, .two { grid-template-columns:1fr !important; } .drow { grid-template-columns:1fr; gap:0; } }
ol.steps { list-style:none; margin:0; padding:0; display:grid; gap:8px; }
ol.steps li { display:grid; grid-template-columns:52px 1fr; gap:10px; }
.t { font-weight:700; font-variant-numeric:tabular-nums; color:var(--accent); }
.line { font-weight:600; margin:0 0 6px; }
ul { margin:0; padding-left:18px; } ul li + li { margin-top:3px; }
details { margin-top:14px; border-top:1px solid var(--line); padding-top:10px; }
summary { cursor:pointer; font-weight:600; color:var(--accent); }
table.qty td:first-child { width:70%; }
.shop h3 { margin-bottom:10px; }
.note { background:var(--accent-soft); border-radius:6px; padding:8px 12px; margin:0 0 10px; }
.mini { font-size:11px; color:var(--amber); border:1px solid var(--amber); border-radius:4px; padding:0 4px; margin-left:4px; }
.cols2 { columns:2 260px; }
.bar { width:40%; position:relative; }
.bar span { display:block; height:10px; background:var(--bar); border-radius:3px; margin-top:6px; }
.bar em { position:absolute; right:8px; top:7px; font-style:normal; font-size:12px; color:var(--muted); font-variant-numeric:tabular-nums; }
.two { display:grid; grid-template-columns:1fr 1fr; gap:24px; }
"""

JS = """(function () {
  var tabs = Array.prototype.slice.call(document.querySelectorAll('nav.tabs button'));
  function show(id) {
    tabs.forEach(function (b) {
      var on = b.getAttribute('aria-controls') === id;
      b.setAttribute('aria-selected', on ? 'true' : 'false');
      document.getElementById(b.getAttribute('aria-controls')).hidden = !on;
    });
    try { localStorage.setItem('trip-review-tab', id); } catch (err) {}
  }
  tabs.forEach(function (b) { b.addEventListener('click', function () { show(b.getAttribute('aria-controls')); }); });
  var ids = tabs.map(function (b) { return b.getAttribute('aria-controls'); });
  var start = (location.hash || '').slice(1);
  if (ids.indexOf(start) < 0) { try { start = localStorage.getItem('trip-review-tab'); } catch (err) {} }
  show(ids.indexOf(start) < 0 ? 'overview' : start);
})();"""
