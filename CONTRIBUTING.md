# Contributing

Contributions are welcome, especially small transformations backed by clear synthetic examples.

1. Fork the repository and create a branch from `main`.
2. Install the development environment with `pip install -e ".[dev]"`.
3. Run `ruff check .`, `ruff format --check .`, and `python -m pytest -q`.
4. Open a focused pull request and explain whether invalid values are preserved or rejected.

Never commit real customer data, production spreadsheets, personal identifiers, credentials, or proprietary business rules.
