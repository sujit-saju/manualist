"""Export the API schema for the UI generator."""

import json
from pathlib import Path

from src.main import create_app


def main() -> None:
    """Write the app's OpenAPI schema in the server directory."""
    target = Path(__file__).resolve().parents[2] / "openapi.json"
    target.write_text(
        json.dumps(create_app().openapi(), indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
