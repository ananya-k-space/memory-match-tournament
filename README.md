# 🎮 Memory Match Tournament

A multiplayer memory card-matching game with two versions:

- **Web version** (`index.html`): play in the browser, no install needed.
- **Terminal version** (`memory_game.py`): play in the command line with Python.

- https://ananya-k-space.github.io/memory-match-tournament/

Flip two cards per turn. Find a matching pair to score points and keep your turn. Miss, and the turn passes to the next player. Whoever has the highest score when all pairs are found wins.

## ✨ Features

- 2 to 6 players with custom names
- 4 difficulty levels in both versions: Easy (2×4), Medium (4×4), Hard (4×6), Expert (6×6)
- Multiple card themes (emoji, numbers, letters, fruits, animals, space)
- Scoring with difficulty multiplier, streak bonus, speed bonus and miss penalty
- Tie handling, accuracy and best-streak stats
- Saved top-5 high scores
- Live scoreboard and a winner podium (web version)

## 🚀 How to Run

### Web version

1. Download or clone this repo.
2. Open `index.html` in any modern browser (double-click it).

### Terminal version

Requires **Python 3.8+** and no external libraries.

```bash
python memory_game.py
```

Then follow the prompts: number of players, names, difficulty, theme. During a turn, enter the row and column numbers (starting from 0) of the card you want to flip.

## 🧮 Scoring

| Event | Points |
|---|---|
| Correct match | 100 × difficulty multiplier |
| Streak bonus | +25 for each consecutive match (2nd = +25, 3rd = +50, ...) |
| Speed bonus | +20 for a very fast match, +10 for a quick one |
| Wrong guess | −10 (score never goes below 0) and your streak resets |

Speed is measured from your first flip to your second flip. The terminal version gives more time because you type coordinates instead of clicking.

If players tie for the top score, the game declares a tie. The top 5 scores are saved (browser storage for the web version, `high_scores.json` for the terminal version).

## 📁 Project Structure

```
memory-match-tournament/
├── index.html        # Web version (HTML + CSS + JavaScript in one file)
├── memory_game.py    # Terminal version (Python)
├── scoring.json      # Single source of truth for scoring rules + difficulty levels
├── scoring.js        # Generated from scoring.json for the web version
├── sync_scoring.py   # Regenerates scoring.js after you edit scoring.json
├── test_scoring.py   # Unit tests
├── high_scores.json  # Created automatically after the first terminal game
└── README.md
```

## 🧪 Tests

```bash
python -m unittest test_scoring -v
```

To change scoring or difficulty, edit `scoring.json`, then run `python sync_scoring.py` so the web version picks up the change.

## 🛠️ Built With

- Python (classes, enums, type hints)
- HTML, CSS, JavaScript (no frameworks)

## 💡 Concepts Used

- Object-oriented design (`Card`, `Player`, `MemoryGame`, `GameManager`)
- Fisher-Yates shuffle for the deck
- One shared config file (`scoring.json`) powering both versions
- Unit testing with `unittest`
- Escaping user input to prevent HTML injection
- DOM manipulation and event handling
- CSS grid and flip animations

## 🔮 Future Improvements

- Add sound effects
- Add a single-player mode with a timer
- Host the web version with GitHub Pages

## 👩‍💻 Author

Made by **Ananya**
"# memory-match-tournament" 
