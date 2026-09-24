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

Currently supports **sandwich lunches** end to end. More meal types and
multi-meal coordination are planned.

## Layout

```
skills/scout-meal-planner/   the skill (SKILL.md, references/, scripts/)
.claude/skills/…             symlink for Claude Code
.agents/skills/…             symlink for agents that read .agents/skills
AGENTS.md                    pointer for agents without skill support
examples/                    a worked example (83-person trial-run lunch)
plans/                       your own event plans (git-ignored)
```

## Quick start

Ask your agent to "plan a camp lunch for 30 kids and 20 adults". Or run the
calculator directly:

```
python3 skills/scout-meal-planner/scripts/sandwich_lunch.py --profile examples/trial-run-lunch.json
```

See `skills/scout-meal-planner/README.md` for install locations, and
`SKILL.md` for the full workflow and profile format.

On Windows, or anywhere symlinks don't survive, copy
`skills/scout-meal-planner/` into your agent's skills folder instead.

## License

MIT
