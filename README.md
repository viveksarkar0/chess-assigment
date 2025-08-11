
# Chess Pins & Skewers Detector

This project analyzes chess games in PGN format and detects **tactical patterns**:
- **Pins** (executed, missed, allowed)
- **Skewers** (executed, missed, allowed)

It uses the [python-chess](https://python-chess.readthedocs.io/en/latest/) library and the **Stockfish chess engine** to evaluate positions and find tactical opportunities.

---

## 📦 Requirements

- Python 3.8+
- `python-chess` Python package
- Stockfish chess engine binary
- A `.pgn` file containing **at least 5 chess games**

---

## ⚙️ Installation

1. **Clone this repository** (or place `detect_pins_skewers.py` in a folder):
   ```bash
   git clone https://github.com/yourusername/chess-pins-skewers.git
   cd chess-pins-skewers
````

2. **Create a virtual environment**:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:

   ```bash
   pip install python-chess
   ```

4. **Install Stockfish** (Mac example with Homebrew):

   ```bash
   brew install stockfish
   ```

   For Windows, download from: [https://stockfishchess.org/download/](https://stockfishchess.org/download/)
   For Linux (Ubuntu/Debian):

   ```bash
   sudo apt install stockfish
   ```

---

## ♟️ Preparing Your PGN File

You need a `.pgn` file with **5 games**.

You can download from:

* [Lichess PGN Database](https://database.lichess.org/)
* Chess.com game export
* Lichess.org "Export PGN"

**Example `games.pgn` with multiple games**:

```pgn
[Event "Game 1"]
[Site "Chess.com"]
[Date "2025.01.01"]
[Round "?"]
[White "PlayerA"]
[Black "PlayerB"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 6. Re1 b5 7. Bb3 O-O 8. c3 d5 9. exd5 Nxd5 10. Nxe5 Nxe5 11. Rxe5 Bb7 1-0

[Event "Game 2"]
[Site "Chess.com"]
[Date "2025.01.02"]
[Round "?"]
[White "PlayerC"]
[Black "PlayerD"]
[Result "0-1"]

1. d4 Nf6 2. c4 e6 3. Nc3 Bb4 4. e3 O-O 5. Bd3 d5 6. Nf3 c5 7. O-O Nc6 8. a3 Bxc3 9. bxc3 dxc4 10. Bxc4 Qc7 0-1
```

📌 Put **all 5 games** in `games.pgn` in the same format.
The script will automatically read the first 5 games from the file.

---

## 🚀 Running the Script

From the project directory:

```bash
source venv/bin/activate
python3 detect_pins_skewers.py
```

---

## 📤 Output

The script:

* Prints progress in the terminal
* Saves results in `pins_skewers_results.json`

**Example terminal output:**

```
Analyzing game 1 ...
 Game 1: Executed 2, Missed 1, Allowed 0
Analyzing game 2 ...
 Game 2: Executed 1, Missed 0, Allowed 1
Saved pins_skewers_results.json
```

**Example JSON output:**

```json
{
  "game_1": {
    "executed": [
      {"ply": 10, "tactic": "pin", "pinner": "d4", "pinned": "f6"}
    ],
    "missed": [],
    "allowed": []
  },
  "game_2": {
    "executed": [],
    "missed": [
      {"ply": 15, "tactic": "skewer", "attacker": "b2"}
    ],
    "allowed": []
  }
}
```

---

## 🛠️ Options & Notes

* **Stockfish Path**
  By default, the script will try:

  1. `STOCKFISH_PATH` environment variable
  2. `/opt/homebrew/bin/stockfish` (Mac)
  3. `"stockfish"` from system PATH

* **Engine Time**
  The engine is limited to `0.12s` per move for speed. Increase `ENGINE_TIME` in the script for deeper analysis.

* **PGN File Names**
  The script looks for `games.pgn` or `game.pgn` in the current directory.

---

## 📄 License

MIT License — you may modify and use freely.

```


