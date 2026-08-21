from collections.abc import AsyncIterator

from psycopg import AsyncConnection
from psycopg_pool import AsyncConnectionPool

from app.config.settings import get_settings

pool = AsyncConnectionPool(get_settings().database_url, open=False)


async def open_pool() -> None:
    await pool.open()


async def close_pool() -> None:
    await pool.close()


async def get_connection() -> AsyncIterator[AsyncConnection]:
    async with pool.connection() as connection:
        yield connection
