"""Run with: python3 -m unittest discover tests"""
import copy
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "skills", "scout-meal-planner", "scripts")
sys.path.insert(0, SCRIPTS)
import plan_trip  # noqa: E402

CATALOG = plan_trip.load_json(os.path.join(ROOT, "skills", "scout-meal-planner", "references", "ingredients.json"))
EXAMPLE = plan_trip.load_json(os.path.join(ROOT, "examples", "trial-run-lunch.json"))


def run(profile):
    trip = plan_trip.normalize(copy.deepcopy(profile))
    return {l["key"]: l for l in plan_trip.plan(trip, CATALOG)["lines"]}


class TrialRunLunchRegression(unittest.TestCase):
    """The original sandwich_lunch.py numbers (2026-09-24) must not drift.
    Amounts may be 1 higher: counts now round up instead of to nearest."""

    BASELINE = {  # key: (amount, packs)
        "bread_sandwich": (342, 18), "peanut_butter": (113, 2), "jelly": (72, 2),
        "turkey_deli": (5.9, 5), "turkey_halal": (1.5, None), "turkey_kosher": (0.9, None),
        "cheese_sliced": (114, 1), "hummus": (21, 1), "lettuce": (72, None), "tomato": (36, 7),
        "pickles": (108, 1), "onion": (43 / 20, 3), "mayo_packets": (51, 1), "chips": (92, 2),
        "fruit": (104, None), "plates": (100, None), "napkins": (249, None), "sandwich_bags": (15, None),
    }

    def test_matches_baseline(self):
        got = run(EXAMPLE)
        for key, (amount, packs) in self.BASELINE.items():
            with self.subTest(key=key):
                self.assertAlmostEqual(got[key]["amount"], amount, delta=1.0)
                if packs is not None:
                    self.assertEqual(got[key]["packs"], packs)


def two_meal_trip(sunday_leftovers=False):
    meals = [{"id": "sat-breakfast", "menu": "breakfast_burritos", "group": "A"},
             {"id": "sat-lunch", "menu": "sandwich_lunch", "group": "B",
              "options": {"toppings": ["lettuce", "onion"]}}]
    if sunday_leftovers:
        meals.append({"id": "sun-breakfast", "menu": "coffee_bars", "group": "C"})
    return {"trip": "t", "kids": 30, "adults": 30, "walkups": 5, "meals": meals}


class Pooling(unittest.TestCase):
    def test_one_cushion_per_trip(self):
        pooled = run(two_meal_trip())["fruit"]["amount"]
        separate = sum(run({**two_meal_trip(), "meals": [m]})["fruit"]["amount"]
                       for m in two_meal_trip()["meals"])
        self.assertLess(pooled, separate)

    def test_leftover_meals_never_add_to_purchase(self):
        base = run(two_meal_trip())["fruit"]
        with_sunday = run(two_meal_trip(sunday_leftovers=True))["fruit"]
        self.assertEqual(with_sunday["amount"], base["amount"])
        self.assertGreater(with_sunday["from_leftovers"], 0)

    def test_expected_losses_are_not_leftovers(self):
        mallows = run({"kids": 20, "adults": 0, "meals": [{"menu": "smores", "group": "A"}]})["marshmallows"]
        # 20 kids x 3.5 = 70 eaten, +50% burned/dropped = 105 counted as used, not leftover
        self.assertAlmostEqual(mallows["consumed"], 105)

    def test_shared_item_has_one_buyer(self):
        onion = run(two_meal_trip())["onion"]
        self.assertEqual(set(onion["by_group"]), {"A", "B"})
        self.assertIn(onion["buyer"], {"A", "B"})


class Requirements(unittest.TestCase):
    def test_hot_meal_gives_kosher_sealed_meal(self):
        p = {"kids": 20, "adults": 20, "meals": [{"menu": "pasta_dinner", "group": "A"}],
             "requirements": {"kosher": {"enabled": True, "count": 3}}}
        self.assertEqual(run(p)["kosher_sealed_meal"]["amount"], 3)

    def test_vegan_marshmallows_only_when_needed(self):
        p = {"kids": 20, "adults": 20, "meals": [{"menu": "smores", "group": "A"}]}
        self.assertNotIn("marshmallows_vegan", run(p))
        p["requirements"] = {"vegetarian": {"enabled": True, "count": 4}}
        self.assertIn("marshmallows_vegan", run(p))

    def test_enabled_without_count_errors(self):
        p = copy.deepcopy(EXAMPLE)
        del p["requirements"]["halal"]["count"]
        with self.assertRaises(SystemExit):
            run(p)


class TripOptions(unittest.TestCase):
    def test_mess_kits_skip_disposables(self):
        p = {"kids": 10, "adults": 10, "meals": [{"menu": "pasta_dinner", "group": "A"}]}
        self.assertIn("plates", run(p))
        p["mess_kits"] = True
        got = run(p)
        self.assertNotIn("plates", got)
        self.assertIn("napkins", got)  # mess kits don't include napkins

    def test_gloves_scale_with_crew_not_headcount(self):
        small = run({"kids": 5, "adults": 5, "meals": [{"menu": "pasta_dinner", "group": "A"}]})
        big = run({"kids": 50, "adults": 50, "meals": [{"menu": "pasta_dinner", "group": "A"}]})
        for key in ("gloves_adult", "gloves_kid"):
            self.assertEqual(small[key]["amount"], big[key]["amount"])

    def test_meal_can_override_crew(self):
        base = {"kids": 10, "adults": 10, "meals": [{"menu": "pasta_dinner", "group": "A"}]}
        no_kids = {**base, "meals": [{"menu": "pasta_dinner", "group": "A", "crew": {"kids": 0}}]}
        self.assertIn("gloves_kid", run(base))
        self.assertNotIn("gloves_kid", run(no_kids))

    def test_shopping_mode(self):
        p = two_meal_trip()
        self.assertEqual({l["buyer"] for l in run(p).values()}, {"A", "B"})
        p["shopping"] = "per_pack"
        self.assertEqual({l["buyer"] for l in run(p).values()}, {"Pack shopper"})

    def test_extras_and_includes(self):
        p = {"kids": 10, "adults": 10, "meals": [
            {"menu": "sandwich_lunch", "group": "A", "extras": ["cold_drink"]},
            {"menu": "coffee_bars", "group": "B"}]}
        got = run(p)
        self.assertIn("drink_mix", got)       # meal-level extra
        self.assertIn("coffee_packets", got)  # included by coffee_bars
        self.assertIn("cocoa_mix", got)


if __name__ == "__main__":
    unittest.main()
