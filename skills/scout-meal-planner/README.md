# scout-meal-planner

A portable agent skill for planning group camping meals: menu, quantities,
dietary toggles (vegetarian, halal, kosher, gluten-free, nut-free), a DIY
serving line, and a shopping list for whatever stores the planner uses.

It uses the plain `SKILL.md` format (a `name` + `description` header plus
Markdown), so it isn't tied to one AI tool. The calculator needs only `python3`.

## Install

Copy or symlink this folder to wherever your agent looks for skills:

| Agent | Project-level | User-level |
|---|---|---|
| Claude Code | `.claude/skills/scout-meal-planner` | `~/.claude/skills/scout-meal-planner` |
| Tools that read `.agents/skills` (e.g. Codex) | `.agents/skills/scout-meal-planner` | per tool docs |
| Anything else | Point the agent at `SKILL.md` via `AGENTS.md` or its system prompt | |

Check your tool's docs for its current skills location.

## Use without an agent

```
python3 scripts/sandwich_lunch.py --profile path/to/event.json
python3 scripts/sandwich_lunch.py --help
```

See `SKILL.md` step 3 for the profile format.
