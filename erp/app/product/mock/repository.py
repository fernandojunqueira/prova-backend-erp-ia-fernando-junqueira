from app.product.domain import Product


class InMemoryProductRepository:
    def __init__(self) -> None:
        self._products: dict[int, Product] = {}
        self._next_id = 1

    async def save(self, product: Product) -> Product:
        if product.id is None:
            product.id = self._next_id
            self._next_id += 1
        self._products[product.id] = product
        return product

    async def find_by_id(self, product_id: int) -> Product | None:
        product = self._products.get(product_id)
        if product is None or product.is_deleted:
            return None
        return product

    async def list_all(self, offset: int, limit: int) -> list[Product]:
        products = [
            product for product in self._products.values() if not product.is_deleted
        ]
        products.sort(key=lambda item: item.id or 0)
        return products[offset : offset + limit]
