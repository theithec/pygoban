# Pygoban

Pygoban is a desktop application for playing and reviewing Go games. It is built
with Python, PyQt6, and Qt 6, and supports SGF files, board editing, game
variations, scoring, and optional GTP engines.

> **Work in progress:** Pygoban is under active development. Features and
> behavior may change, and the project is not yet feature-complete.

## Features

- Create a game or open an existing SGF file.
- Play a game or edit a board, including comments, labels, markers, arrows, and
  lines.
- Navigate the game tree and review variations and engine analysis.
- Configure board size, players, handicap, komi, rules, and time controls,
  including Byo-yomi.
- Score games using Japanese or Chinese rules.
- Configure external GTP engines for playing or analysis.
- Save games as SGF.

## Requirements

- Python 3.12 or newer
- [uv](https://docs.astral.sh/uv/)

PyQt6 and the other runtime dependencies are installed by uv from the project
configuration.

## Get Started

Clone the repository, then from its root directory sync the environment and
start Pygoban:

```bash
uv sync
uv run python -m pygoban.gui
```

From the welcome screen, choose **Play Game** to set up a game, **Edit Board**
to work on a position, or **Open File** to load an SGF file.

## Development

Run the test suite with:

```bash
uv run pytest
```

For headless environments, such as CI, run Qt tests with the offscreen platform:

```bash
QT_QPA_PLATFORM=offscreen uv run pytest
```

Build a wheel and source distribution with:

```bash
uv build
```
