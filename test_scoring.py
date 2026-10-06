"""Run with:  python -m unittest test_scoring -v"""
import json
import re
import unittest
from pathlib import Path

import memory_game as mg

ROOT = Path(__file__).parent
CONFIG = json.loads((ROOT / "scoring.json").read_text(encoding="utf-8"))
HTML = (ROOT / "index.html").read_text(encoding="utf-8")


class SharedConfigTests(unittest.TestCase):
    def test_scoring_js_matches_scoring_json(self):
        js = (ROOT / "scoring.js").read_text(encoding="utf-8")
        data = json.loads(js.split("const SCORING = ", 1)[1].rstrip().rstrip(";"))
        self.assertEqual(data, CONFIG, "Run: python sync_scoring.py")

    def test_python_difficulties_match_config(self):
        self.assertEqual({d.name.lower() for d in mg.Difficulty}, set(CONFIG["difficulties"]))

    def test_every_difficulty_has_a_button_in_html(self):
        for key in CONFIG["difficulties"]:
            self.assertIn(f'data-difficulty="{key}"', HTML)

    def test_web_themes_have_enough_cards_for_biggest_board(self):
        biggest = max(d["rows"] * d["cols"] // 2 for d in CONFIG["difficulties"].values())
        for body in re.findall(r"^\s+\w+: \[(.*?)\],?$", HTML, re.M):
            if '"' in body:
                self.assertGreaterEqual(len(body.split(",")), biggest)

    def test_player_names_are_escaped_in_html(self):
        self.assertNotIn("${player.name}", HTML.replace("${escapeHtml(player.name)}", ""))


class ScoringTests(unittest.TestCase):
    def test_match_streak_and_speed(self):
        p = mg.Player("A", 0)
        self.assertEqual(p.add_match(100, 1.0), 100)   # slow, first match
        self.assertEqual(p.add_match(100, 1.0), 125)   # +25 streak
        self.assertEqual(p.add_match(0, 1.0), 100 + 50 + CONFIG["speed_bonus"]["fast_points"])
        self.assertEqual(p.best_streak, 3)

    def test_miss_resets_streak_and_never_goes_negative(self):
        p = mg.Player("A", 0)
        p.add_match(100, 1.0)
        p.add_attempt()
        self.assertEqual((p.streak, p.score), (0, 90))
        for _ in range(20):
            p.add_attempt()
        self.assertEqual(p.score, 0)

    def test_speed_bonus_thresholds(self):
        s = CONFIG["speed_seconds"]["cli"]
        self.assertEqual(mg.speed_bonus(s["fast"]), CONFIG["speed_bonus"]["fast_points"])
        self.assertEqual(mg.speed_bonus(s["quick"]), CONFIG["speed_bonus"]["quick_points"])
        self.assertEqual(mg.speed_bonus(s["quick"] + 1), 0)

    def test_ties_return_all_top_players(self):
        g = mg.MemoryGame(mg.Difficulty.EASY)
        a, b, c = g.add_player("A"), g.add_player("B"), g.add_player("C")
        a.score = b.score = 50
        c.score = 10
        self.assertEqual({w.name for w in g.get_winners()}, {"A", "B"})

    def test_expert_board_is_6x6_with_18_pairs(self):
        g = mg.MemoryGame(mg.Difficulty.EXPERT)
        self.assertEqual((g.rows, g.cols, g.total_pairs), (6, 6, 18))


if __name__ == "__main__":
    unittest.main()
