from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal


class ProductNotFound(Exception):
    def __init__(self, product_id: int) -> None:
        super().__init__(f"Product {product_id} was not found.")
        self.product_id = product_id


class InvalidProduct(Exception):
    pass


@dataclass
class Product:
    name: str
    price: Decimal
    stock_quantity: int
    created_by: int
    created_at: datetime
    updated_at: datetime
    updated_by: int | None = None
    is_deleted: bool = False
    id: int | None = None

    def __post_init__(self) -> None:
        self.name = self.name.strip()
        self._validate()

    @classmethod
    def create(
        cls,
        name: str,
        price: Decimal,
        stock_quantity: int,
        created_by: int,
    ) -> Product:
        now = datetime.now(UTC)
        return cls(
            name=name,
            price=price,
            stock_quantity=stock_quantity,
            created_by=created_by,
            created_at=now,
            updated_at=now,
            updated_by=None,
            is_deleted=False,
            id=None,
        )

    def update(
        self,
        name: str,
        price: Decimal,
        stock_quantity: int,
        updated_by: int,
    ) -> None:
        self.name = name.strip()
        self.price = price
        self.stock_quantity = stock_quantity
        self.updated_by = updated_by
        self.updated_at = datetime.now(UTC)
        self._validate()

    def mark_as_deleted(self, deleted_by: int) -> None:
        self.is_deleted = True
        self.updated_by = deleted_by
        self.updated_at = datetime.now(UTC)

    def _validate(self) -> None:
        if not self.name:
            raise InvalidProduct("Product name is required.")
        if self.price < 0:
            raise InvalidProduct("Product price must be greater than or equal to zero.")
        if self.stock_quantity < 0:
            raise InvalidProduct(
                "Product stock quantity must be greater than or equal to zero."
            )
