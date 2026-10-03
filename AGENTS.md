# Guidance for AI Contributors

This project welcomes thoughtful improvements, bug fixes, and feature extensions. AI contributors exploring the repository are encouraged to propose and implement useful changes and open a GitHub Pull Request or Merge Request for review.

## Project Setup

- This is a Python 3.12+ project using `uv` for environment and dependency management.
- The GUI is built with PyQt6 and Qt 6. Preserve the existing Qt/PyQt patterns and keep GUI changes compatible with the project's PyQt6 dependencies.
- The project uses `uv_build` to build the root-level `pygoban/` package.
- Sync dependencies with `uv sync` and run commands in the project environment with `uv run`.
- Start the application with `uv run python -m pygoban.gui`.
- Use Ruff for linting and formatting (`uv run ruff check .` and `uv run ruff format --check .`).
- Use Pyrefly for type checking (`uv run pyrefly check`).
- Do not use Black, isort, or Pylint; Ruff replaces those tools in the contributor workflow.

## Refactoring Opportunities

When working in these areas, consider focused refactors that clarify ownership and behavior. These are investigation targets, not a mandate for broad cleanup; add behavior tests first and keep changes incremental.

- SGF parsing and writing (`pygoban/sgf/reader.py`, `pygoban/sgf/writer.py`): parsing, tree construction, property interpretation, and serialization currently share stateful paths. Consider separating tokenization, tree/property representation, and model conversion while preserving unknown properties and variations.
- GTP lifecycle and protocol handling (`pygoban/gtp.py`): process management, reader-thread lifecycle, GTP parsing, role state, and game updates are coupled. Consider separating the process/session from role orchestration and extracting protocol parsing into testable functions. Cover restart, shutdown, and output handling with fake-process tests.
- GUI intersection behavior (`pygoban/gui/intersections.py`, `pygoban/gui/gamewidget.py`): painting, input dispatch, annotations, analysis overlays, and hover-preview timers have overlapping responsibilities. Consider separating rendering and preview state from interaction handling; protect behavior with focused GUI tests.
- Game, node replay, and rulesets (`pygoban/game.py`, `pygoban/nodescontroller.py`, `pygoban/rulesets/`): move transitions, board mutation, replay, captures, scoring, validation, and events cross these boundaries. Clarify and test the move/reset contract before extracting shared transition logic.

## Before Opening a Pull/Merge Request

- Keep changes focused and consistent with the existing architecture and formatting.
- Add or update tests for behavior changes. Run the relevant tests with `uv run pytest`; run the full suite when practical.
- Run coverage with `uv run pytest --cov=pygoban tests`.
- Run Ruff and Pyrefly on changed Python code when available in the local `uv` environment.
- GUI tests may need an offscreen Qt platform in headless environments, for example `QT_QPA_PLATFORM=offscreen uv run pytest`.
- Describe the motivation, behavior, and validation in the pull/merge request. Call out any remaining limitations or environment-specific test gaps.
- Do not include unrelated local changes in a contribution.
