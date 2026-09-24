# Scout Meal Planner

An AI-agent skill for planning group camping meals (Scouts, youth groups,
family camps): menu, quantities from a headcount, dietary coverage, a
build-your-own serving line, a prep timeline, and a shopping list for the
stores you actually use.

- **Works with any agent that can read files and run `python3`.** It uses the
  plain `SKILL.md` format and has no dependencies beyond the standard library.
- **Dietary requirements are on/off switches:** vegetarian, halal, kosher,
  gluten-free, nut-free. Guessed counts are allowed and flagged.
- **Plans for reality:** walk-ups, big eaters, prep accidents, and all prep
  happening at camp right before the meal.
- **Store-agnostic:** Costco, Sam's Club, BJ's, Kroger, Walmart, etc.
  Optional browser price-checks.

- **Plans the whole trip at once:** every meal and snack is combined into one
  shopping list. Each item gets one safety cushion instead of one per meal,
  one buyer group with hand-offs, and a leftover forecast (so no more bags of
  uneaten apples).

- **Printable packets for each group:** menu, crew roles, special diets,
  equipment checklist, a step-by-step prep and cooking countdown with real
  quantities, serving line, food safety, cleanup, and that group's shopping
  list with hand-offs (see `examples/handouts/`).

Menus so far: s'mores, egg breakfast burritos, sandwich lunch, pasta dinner,
coffee + breakfast bars. New menus are small JSON files.

## Layout

```
skills/scout-meal-planner/   the skill (SKILL.md, references/, scripts/)
.claude/skills/…             symlink for Claude Code
.agents/skills/…             symlink for agents that read .agents/skills
AGENTS.md                    pointer for agents without skill support
skills/…/menus/              one JSON file per menu
skills/…/references/ingredients.json   ingredient catalog (units, packs, stores)
tests/                       python3 -m unittest discover tests
examples/                    worked examples (a full weekend, and a single lunch)
plans/                       your own event plans (git-ignored)
```

## Quick start

Ask your agent to "plan meals for a weekend campout: 30 kids, 20 adults". Or run the
calculator directly:

```
python3 skills/scout-meal-planner/scripts/plan_trip.py --profile examples/fall-campout.json --handouts /tmp/handouts
```

See `skills/scout-meal-planner/README.md` for install locations, and
`SKILL.md` for the full workflow and profile format.

On Windows, or anywhere symlinks don't survive, copy
`skills/scout-meal-planner/` into your agent's skills folder instead.

## License

MIT
