import asyncio
import logging
from pathlib import Path

from psycopg import AsyncConnection

from app.config.settings import get_settings

logger = logging.getLogger(__name__)

MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "migrations"

CREATE_SCHEMA_MIGRATIONS = """
    CREATE TABLE IF NOT EXISTS schema_migrations (
        version VARCHAR(255) PRIMARY KEY,
        applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
"""

SELECT_APPLIED_VERSIONS = "SELECT version FROM schema_migrations"

INSERT_APPLIED_VERSION = "INSERT INTO schema_migrations (version) VALUES (%(version)s)"


async def run_migrations() -> None:
    async with (
        await AsyncConnection.connect(get_settings().database_url) as connection,
        connection.cursor() as cursor,
    ):
        await cursor.execute(CREATE_SCHEMA_MIGRATIONS)
        await cursor.execute(SELECT_APPLIED_VERSIONS)
        applied = {row[0] for row in await cursor.fetchall()}

        for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
            if path.stem in applied:
                continue
            logger.info("Applying migration %s", path.stem)
            await cursor.execute(path.read_text(encoding="utf-8"))
            await cursor.execute(INSERT_APPLIED_VERSION, {"version": path.stem})


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_migrations())


if __name__ == "__main__":
    main()
