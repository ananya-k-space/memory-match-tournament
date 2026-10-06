// AUTO-GENERATED from scoring.json by sync_scoring.py - do not edit by hand
const SCORING = {
  "base_points": 100,
  "streak_bonus": 25,
  "miss_penalty": 10,
  "speed_bonus": {
    "fast_points": 20,
    "quick_points": 10
  },
  "speed_seconds": {
    "web": {
      "fast": 3,
      "quick": 6
    },
    "cli": {
      "fast": 8,
      "quick": 15
    }
  },
  "difficulties": {
    "easy": {
      "rows": 2,
      "cols": 4,
      "multiplier": 1.0
    },
    "medium": {
      "rows": 4,
      "cols": 4,
      "multiplier": 1.5
    },
    "hard": {
      "rows": 4,
      "cols": 6,
      "multiplier": 2.0
    },
    "expert": {
      "rows": 6,
      "cols": 6,
      "multiplier": 3.0
    }
  }
};
