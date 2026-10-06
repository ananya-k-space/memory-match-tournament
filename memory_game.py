import json
import os
import random
import time
from typing import List, Tuple, Optional, Dict
from enum import Enum

# Scoring rules and difficulty levels live in scoring.json (shared with index.html)
SCORING_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scoring.json")
with open(SCORING_FILE, "r", encoding="utf-8") as _f:
    _SCORING = json.load(_f)

# Builds EASY, MEDIUM, HARD, EXPERT from the JSON file
Difficulty = Enum("Difficulty", {
    key.upper(): {"rows": v["rows"], "cols": v["cols"], "name": key.capitalize(), "time_bonus": v["multiplier"]}
    for key, v in _SCORING["difficulties"].items()
})


# ---- Scoring rules (loaded from scoring.json) ----
BASE_POINTS = _SCORING["base_points"]        # multiplied by the difficulty multiplier
STREAK_BONUS = _SCORING["streak_bonus"]      # extra per consecutive match (2nd = +25, 3rd = +50, ...)
MISS_PENALTY = _SCORING["miss_penalty"]      # lost on a wrong guess (score never drops below 0)
FAST_POINTS = _SCORING["speed_bonus"]["fast_points"]
QUICK_POINTS = _SCORING["speed_bonus"]["quick_points"]
# Typing coordinates takes longer than clicking, so the CLI gets its own time limits.
FAST_SECONDS = _SCORING["speed_seconds"]["cli"]["fast"]
QUICK_SECONDS = _SCORING["speed_seconds"]["cli"]["quick"]
HIGH_SCORE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "high_scores.json")


def speed_bonus(seconds: float) -> int:
    """Bonus points for matching quickly (measured from first flip to second flip)"""
    if seconds <= FAST_SECONDS:
        return FAST_POINTS
    if seconds <= QUICK_SECONDS:
        return QUICK_POINTS
    return 0


class Card:
    """Represents a single card in the memory game"""
    def __init__(self, value: str, card_id: int):
        self.value = value
        self.card_id = card_id
        self.is_matched = False
        self.is_flipped = False
    
    def flip(self):
        """Flip the card"""
        self.is_flipped = not self.is_flipped
    
    def match(self):
        """Mark card as matched"""
        self.is_matched = True
        self.is_flipped = True
    
    def reset(self):
        """Reset card state"""
        self.is_matched = False
        self.is_flipped = False
    
    def __repr__(self):
        if self.is_matched:
            return f"[{self.value}]"
        elif self.is_flipped:
            return f" {self.value} "
        else:
            return " ? "


class Player:
    """Represents a player in the game"""
    def __init__(self, name: str, player_id: int):
        self.name = name
        self.player_id = player_id
        self.score = 0
        self.matches = 0
        self.attempts = 0
        self.total_time = 0.0
        self.games_played = 0
        self.streak = 0
        self.best_streak = 0
    
    def add_match(self, time_taken: float, difficulty_multiplier: float = 1.0) -> int:
        """Add a successful match; returns the points gained"""
        self.matches += 1
        self.streak += 1
        self.best_streak = max(self.best_streak, self.streak)
        gained = (int(BASE_POINTS * difficulty_multiplier)
                  + STREAK_BONUS * (self.streak - 1)
                  + speed_bonus(time_taken))
        self.score += gained
        return gained
    
    def add_attempt(self):
        """Record a failed attempt: streak resets, score never goes below 0"""
        self.attempts += 1
        self.streak = 0
        self.score = max(0, self.score - MISS_PENALTY)
    
    def get_accuracy(self) -> float:
        """Calculate match accuracy"""
        total = self.matches + self.attempts
        return (self.matches / total * 100) if total > 0 else 0
    
    def __repr__(self):
        return f"{self.name} - Score: {self.score} | Matches: {self.matches} | Accuracy: {self.get_accuracy():.1f}% | Best streak: {self.best_streak}"


class MemoryGame:
    """Main game logic for Memory Match - Multiplayer Edition"""
    
    def __init__(self, difficulty: Difficulty = Difficulty.MEDIUM, theme: str = "emoji"):
        config = difficulty.value
        self.rows = config["rows"]
        self.cols = config["cols"]
        self.difficulty = difficulty
        self.time_bonus_multiplier = config["time_bonus"]
        self.total_cards = self.rows * self.cols
        
        self.theme = theme
        self.cards: List[List[Card]] = []
        self.total_pairs = self.total_cards // 2
        self.matches_found = 0
        
        self.players: List[Player] = []
        self.current_player_idx = 0
        self.round_number = 1
        
        self.start_time = None
        self.move_start_time = None
        self.first_flip_time = None  # set when the first card of a turn is flipped
        
        self._initialize_board()
    
    def _get_card_values(self) -> List[str]:
        """Generate card values based on theme"""
        themes = {
            "emoji": ["🐶", "🐱", "🐭", "🐹", "🐰", "🦊", "🐻", "🐼", 
                     "🐨", "🐯", "🦁", "🐮", "🐷", "🐸", "🐵", "🐔",
                     "🦄", "🐝", "🦋", "🐞", "🐢", "🦆", "🦉", "🦅"],
            "numbers": [str(i) for i in range(1, 25)],
            "letters": [chr(i) for i in range(65, 90)],
            "fruits": ["🍎", "🍊", "🍋", "🍌", "🍉", "🍇", "🍓", "🍒",
                      "🍑", "🥝", "🍍", "🥥", "🥭", "🍏", "🍈", "🫐",
                      "🍐", "🥑", "🍅", "🥕", "🌽", "🥒", "🥦", "🍄"],
            "animals": ["🐕", "🐈", "🐎", "🐖", "🐄", "🐓", "🐑", "🐐",
                       "🦌", "🦘", "🦒", "🐘", "🦏", "🦛", "🦙", "🐪",
                       "🦝", "🦡", "🦦", "🦨", "🦔", "🐿️", "🦫", "🐁"],
            "space": ["🌟", "⭐", "🌙", "☀️", "🪐", "🌍", "🌈", "☄️",
                     "🛸", "🚀", "👽", "🛰️", "🌌", "🔭", "🌠", "💫",
                     "🌕", "🌖", "🌗", "🌘", "🌑", "🌒", "🌓", "🌔"]
        }
        
        values = themes.get(self.theme, themes["emoji"])
        needed_pairs = self.total_pairs
        
        if needed_pairs > len(values):
            values = values * ((needed_pairs // len(values)) + 1)
        
        return values[:needed_pairs]
    
    def _initialize_board(self):
        """Create and shuffle the game board"""
        card_values = self._get_card_values()
        deck = card_values * 2
        random.shuffle(deck)
        
        self.cards = []
        card_id = 0
        for i in range(self.rows):
            row = []
            for j in range(self.cols):
                card = Card(deck[card_id], card_id)
                row.append(card)
                card_id += 1
            self.cards.append(row)
    
    def add_player(self, name: str) -> Player:
        """Add a player to the game"""
        player = Player(name, len(self.players))
        self.players.append(player)
        return player
    
    def get_current_player(self) -> Optional[Player]:
        """Get the current player"""
        if self.players:
            return self.players[self.current_player_idx]
        return None
    
    def next_player(self):
        """Switch to next player"""
        self.current_player_idx = (self.current_player_idx + 1) % len(self.players)
    
    def start_game(self):
        """Start the game timer"""
        self.start_time = time.time()
        self.move_start_time = time.time()
    
    def get_card(self, row: int, col: int) -> Optional[Card]:
        """Get card at specific position"""
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return self.cards[row][col]
        return None
    
    def flip_card(self, row: int, col: int) -> bool:
        """Flip a card at given position"""
        card = self.get_card(row, col)
        if card and not card.is_matched and not card.is_flipped:
            if self.first_flip_time is None:
                self.first_flip_time = time.time()
            card.flip()
            return True
        return False
    
    def check_match(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> bool:
        """Check if two cards match and update current player's score"""
        card1 = self.get_card(*pos1)
        card2 = self.get_card(*pos2)
        
        if not card1 or not card2:
            return False
        
        current_player = self.get_current_player()
        # Time from first flip to now (thinking time before the turn is not counted)
        move_time = time.time() - (self.first_flip_time or time.time())
        self.first_flip_time = None
        
        if card1.value == card2.value:
            card1.match()
            card2.match()
            self.matches_found += 1
            
            if current_player:
                current_player.add_match(move_time, self.time_bonus_multiplier)
            
            self.move_start_time = time.time()
            return True
        else:
            card1.flip()
            card2.flip()
            
            if current_player:
                current_player.add_attempt()
            
            self.next_player()
            self.move_start_time = time.time()
            return False
    
    def is_game_over(self) -> bool:
        """Check if all pairs are found"""
        return self.matches_found == self.total_pairs
    
    def get_winner(self) -> Optional[Player]:
        """Get the player with highest score"""
        if not self.players:
            return None
        return max(self.players, key=lambda p: p.score)
    
    def get_winners(self) -> List[Player]:
        """All players tied for the highest score"""
        if not self.players:
            return []
        top = max(p.score for p in self.players)
        return [p for p in self.players if p.score == top]
    
    def get_leaderboard(self) -> List[Player]:
        """Get players sorted by score"""
        return sorted(self.players, key=lambda p: p.score, reverse=True)
    
    def display_board(self) -> str:
        """Return string representation of the board"""
        board_str = "\n"
        board_str += "    " + "  ".join(str(i) for i in range(self.cols)) + "\n"
        board_str += "   " + "---" * self.cols + "\n"
        
        for i, row in enumerate(self.cards):
            board_str += f"{i} | "
            for card in row:
                board_str += str(card) + " "
            board_str += "\n"
        
        return board_str
    
    def display_scores(self) -> str:
        """Display current scores"""
        scores_str = "\n" + "="*50 + "\n"
        scores_str += "🏆 LEADERBOARD 🏆\n"
        scores_str += "="*50 + "\n"
        
        for i, player in enumerate(self.get_leaderboard(), 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "  "
            scores_str += f"{medal} {i}. {player}\n"
        
        scores_str += "="*50 + "\n"
        return scores_str
    
    def reset_board(self):
        """Reset board for a new round (keep player scores)"""
        self.matches_found = 0
        self.round_number += 1
        self._initialize_board()
        self.move_start_time = time.time()


def load_high_scores() -> List[Dict]:
    """Read saved high scores (empty list if none or file is unreadable)"""
    try:
        with open(HIGH_SCORE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return []


def save_high_scores(players: List[Player], difficulty_name: str) -> List[Dict]:
    """Merge this game's scores into the top 5 and save them"""
    entries = load_high_scores() + [
        {"name": p.name, "score": p.score, "difficulty": difficulty_name} for p in players
    ]
    top = sorted(entries, key=lambda e: e["score"], reverse=True)[:5]
    try:
        with open(HIGH_SCORE_FILE, "w", encoding="utf-8") as f:
            json.dump(top, f, indent=2)
    except OSError:
        print("(Could not save high scores)")
    return top


class GameManager:
    """Manages the overall game flow and tournaments"""
    
    def __init__(self):
        self.game = None
        self.available_themes = ["emoji", "numbers", "letters", "fruits", "animals", "space"]
        self.available_difficulties = list(Difficulty)
    
    def setup_game(self):
        """Interactive setup for the game"""
        print("="*60)
        print("🎮 WELCOME TO MEMORY MATCH TOURNAMENT! 🎮")
        print("="*60)
        
        # Get number of players
        while True:
            try:
                num_players = int(input("\n👥 How many players? (2-6): "))
                if 2 <= num_players <= 6:
                    break
                print("Please enter a number between 2 and 6.")
            except ValueError:
                print("Please enter a valid number.")
        
        # Get player names
        players = []
        for i in range(num_players):
            name = input(f"Enter name for Player {i+1}: ").strip()
            if not name:
                name = f"Player {i+1}"
            players.append(name)
        
        # Choose difficulty
        print("\n🎯 Choose Difficulty Level:")
        for i, diff in enumerate(self.available_difficulties, 1):
            config = diff.value
            print(f"  {i}. {config['name']} - {config['rows']}x{config['cols']} grid")
        
        while True:
            try:
                choice = int(input("Select difficulty (1-4): "))
                if 1 <= choice <= 4:
                    difficulty = self.available_difficulties[choice - 1]
                    break
                print("Please choose 1-4.")
            except ValueError:
                print("Please enter a valid number.")
        
        # Choose theme
        print("\n🎨 Choose Theme:")
        for i, theme in enumerate(self.available_themes, 1):
            print(f"  {i}. {theme.capitalize()}")
        
        while True:
            try:
                choice = int(input(f"Select theme (1-{len(self.available_themes)}): "))
                if 1 <= choice <= len(self.available_themes):
                    theme = self.available_themes[choice - 1]
                    break
                print(f"Please choose 1-{len(self.available_themes)}.")
            except ValueError:
                print("Please enter a valid number.")
        
        # Create game
        self.game = MemoryGame(difficulty, theme)
        
        # Add players
        for name in players:
            self.game.add_player(name)
        
        print("\n" + "="*60)
        print(f"🎮 Game Setup Complete!")
        print(f"Difficulty: {difficulty.value['name']}")
        print(f"Theme: {theme.capitalize()}")
        print(f"Players: {', '.join(players)}")
        print("="*60)
        
        return self.game
    
    def play_turn(self):
        """Play a single turn (2 card flips)"""
        if not self.game:
            return False
        
        current = self.game.get_current_player()
        print(f"\n👤 {current.name}'s turn!")
        print(self.game.display_board())
        
        # First card
        while True:
            try:
                row1 = int(input("Enter row for first card: "))
                col1 = int(input("Enter column for first card: "))
                if self.game.flip_card(row1, col1):
                    break
                print("Invalid selection or card already matched!")
            except (ValueError, IndexError):
                print("Invalid input! Try again.")
        
        print(self.game.display_board())
        
        # Second card
        while True:
            try:
                row2 = int(input("Enter row for second card: "))
                col2 = int(input("Enter column for second card: "))
                if (row1, col1) != (row2, col2) and self.game.flip_card(row2, col2):
                    break
                print("Invalid selection or same card!")
            except (ValueError, IndexError):
                print("Invalid input! Try again.")
        
        print(self.game.display_board())
        
        # Check match
        if self.game.check_match((row1, col1), (row2, col2)):
            streak_text = f" 🔥 Streak x{current.streak}!" if current.streak > 1 else ""
            print(f"✅ MATCH! {current.name} gets points!{streak_text}")
        else:
            print(f"❌ No match. Next player's turn.")
        
        time.sleep(1)
        return True
    
    def run_game(self):
        """Run complete game loop"""
        self.setup_game()
        self.game.start_game()
        
        print("\n🎮 Game starting...\n")
        time.sleep(1)
        
        while not self.game.is_game_over():
            self.play_turn()
        
        # Game over
        print("\n" + "="*60)
        print("🎉 GAME OVER! 🎉")
        print("="*60)
        print(self.game.display_scores())
        
        winners = self.game.get_winners()
        if len(winners) > 1:
            print(f"\n🤝 IT'S A TIE between {' & '.join(w.name for w in winners)} with {winners[0].score} points!\n")
        else:
            print(f"\n👑 WINNER: {winners[0].name} with {winners[0].score} points! 👑\n")
        
        top = save_high_scores(self.game.players, self.game.difficulty.value["name"])
        print("🏅 HIGH SCORES")
        for i, e in enumerate(top, 1):
            print(f"  {i}. {e['name']} - {e['score']} ({e['difficulty']})")
        
        winner = winners[0]
        return winner


# Run the game
if __name__ == "__main__":
    manager = GameManager()
    manager.run_game()
