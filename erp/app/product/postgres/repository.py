from typing import Any

from psycopg import AsyncConnection
from psycopg.rows import dict_row

from app.product.domain import Product, ProductNotFound

COLUMNS = """
    id,
    name,
    price,
    stock_quantity,
    created_at,
    created_by,
    updated_at,
    updated_by,
    is_deleted
"""

INSERT_PRODUCT = f"""
    INSERT INTO products (
        name,
        price,
        stock_quantity,
        created_at,
        created_by,
        updated_at,
        updated_by,
        is_deleted
    )
    VALUES (
        %(name)s,
        %(price)s,
        %(stock_quantity)s,
        %(created_at)s,
        %(created_by)s,
        %(updated_at)s,
        %(updated_by)s,
        %(is_deleted)s
    )
    RETURNING {COLUMNS}
"""

UPDATE_PRODUCT = f"""
    UPDATE products
    SET
        name = %(name)s,
        price = %(price)s,
        stock_quantity = %(stock_quantity)s,
        created_at = %(created_at)s,
        created_by = %(created_by)s,
        updated_at = %(updated_at)s,
        updated_by = %(updated_by)s,
        is_deleted = %(is_deleted)s
    WHERE id = %(id)s
    RETURNING {COLUMNS}
"""

SELECT_PRODUCT_BY_ID = f"""
    SELECT {COLUMNS}
    FROM products
    WHERE id = %(id)s
      AND is_deleted IS FALSE
"""

SELECT_PRODUCTS = f"""
    SELECT {COLUMNS}
    FROM products
    WHERE is_deleted IS FALSE
    ORDER BY id
    OFFSET %(offset)s
    LIMIT %(limit)s
"""


class PostgresProductRepository:
    def __init__(self, connection: AsyncConnection) -> None:
        self._connection = connection

    async def save(self, product: Product) -> Product:
        parameters = {
            "id": product.id,
            "name": product.name,
            "price": product.price,
            "stock_quantity": product.stock_quantity,
            "created_at": product.created_at,
            "created_by": product.created_by,
            "updated_at": product.updated_at,
            "updated_by": product.updated_by,
            "is_deleted": product.is_deleted,
        }
        statement = INSERT_PRODUCT if product.id is None else UPDATE_PRODUCT

        async with self._connection.cursor(row_factory=dict_row) as cursor:
            await cursor.execute(statement, parameters)
            row = await cursor.fetchone()

        if row is None:
            raise ProductNotFound(product.id or 0)
        return self._to_domain(row)

    async def find_by_id(self, product_id: int) -> Product | None:
        async with self._connection.cursor(row_factory=dict_row) as cursor:
            await cursor.execute(SELECT_PRODUCT_BY_ID, {"id": product_id})
            row = await cursor.fetchone()

        if row is None:
            return None
        return self._to_domain(row)

    async def list_all(self, offset: int, limit: int) -> list[Product]:
        async with self._connection.cursor(row_factory=dict_row) as cursor:
            await cursor.execute(SELECT_PRODUCTS, {"offset": offset, "limit": limit})
            rows = await cursor.fetchall()

        return [self._to_domain(row) for row in rows]

    def _to_domain(self, row: dict[str, Any]) -> Product:
        return Product(
            id=row["id"],
            name=row["name"],
            price=row["price"],
            stock_quantity=row["stock_quantity"],
            created_at=row["created_at"],
            created_by=row["created_by"],
            updated_at=row["updated_at"],
            updated_by=row["updated_by"],
            is_deleted=row["is_deleted"],
        )
