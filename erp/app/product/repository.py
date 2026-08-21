from typing import Protocol

from app.product.domain import Product


class ProductRepository(Protocol):
    async def save(self, product: Product) -> Product: ...

    async def find_by_id(self, product_id: int) -> Product | None: ...

    async def list_all(self, offset: int, limit: int) -> list[Product]: ...
