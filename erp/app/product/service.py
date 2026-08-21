from decimal import Decimal

from app.product.domain import Product, ProductNotFound
from app.product.repository import ProductRepository


class ProductService:
    def __init__(self, product_repository: ProductRepository) -> None:
        self._product_repository = product_repository

    async def create_product(
        self,
        name: str,
        price: Decimal,
        stock_quantity: int,
        created_by: int,
    ) -> Product:
        product = Product.create(
            name=name,
            price=price,
            stock_quantity=stock_quantity,
            created_by=created_by,
        )
        return await self._product_repository.save(product)

    async def find_product_by_id(self, product_id: int) -> Product:
        product = await self._product_repository.find_by_id(product_id)
        if product is None:
            raise ProductNotFound(product_id)
        return product

    async def list_products(self, offset: int, limit: int) -> list[Product]:
        return await self._product_repository.list_all(offset=offset, limit=limit)

    async def update_product(
        self,
        product_id: int,
        name: str,
        price: Decimal,
        stock_quantity: int,
        updated_by: int,
    ) -> Product:
        product = await self.find_product_by_id(product_id)
        product.update(
            name=name,
            price=price,
            stock_quantity=stock_quantity,
            updated_by=updated_by,
        )
        return await self._product_repository.save(product)

    async def delete_product(self, product_id: int, deleted_by: int) -> None:
        product = await self.find_product_by_id(product_id)
        product.mark_as_deleted(deleted_by)
        await self._product_repository.save(product)
