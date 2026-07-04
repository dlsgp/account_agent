from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings
from app.core.database import get_engine


def main() -> None:
    with get_engine().connect() as connection:
        value = connection.execute(text("select 1")).scalar_one()
    print(f"Database connection ok: {value}")


if __name__ == "__main__":
    main()
