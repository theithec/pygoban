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

## Before Opening a Pull/Merge Request

- Keep changes focused and consistent with the existing architecture and formatting.
- Add or update tests for behavior changes. Run the relevant tests with `uv run pytest`; run the full suite when practical.
- Run coverage with `uv run pytest --cov=pygoban tests`.
- Run Ruff and Pyrefly on changed Python code when available in the local `uv` environment.
- GUI tests may need an offscreen Qt platform in headless environments, for example `QT_QPA_PLATFORM=offscreen uv run pytest`.
- Describe the motivation, behavior, and validation in the pull/merge request. Call out any remaining limitations or environment-specific test gaps.
- Do not include unrelated local changes in a contribution.
