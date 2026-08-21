from decimal import Decimal

import pytest

from app.product.domain import ProductNotFound
from app.product.mock.repository import InMemoryProductRepository
from app.product.service import ProductService


@pytest.fixture
def product_service() -> ProductService:
    return ProductService(InMemoryProductRepository())


async def test_create_and_find_product(product_service: ProductService) -> None:
    created = await product_service.create_product(
        name="Keyboard",
        price=Decimal("199.90"),
        stock_quantity=10,
        created_by=1,
    )
    assert created.id is not None

    found = await product_service.find_product_by_id(created.id)

    assert found.id == created.id
    assert found.name == "Keyboard"
    assert found.stock_quantity == 10


async def test_list_products_excludes_deleted(product_service: ProductService) -> None:
    first = await product_service.create_product(
        name="Keyboard",
        price=Decimal("199.90"),
        stock_quantity=10,
        created_by=1,
    )
    second = await product_service.create_product(
        name="Mouse",
        price=Decimal("79.90"),
        stock_quantity=20,
        created_by=1,
    )
    assert first.id is not None
    assert second.id is not None

    await product_service.delete_product(product_id=first.id, deleted_by=1)
    products = await product_service.list_products(offset=0, limit=50)

    assert [product.id for product in products] == [second.id]


async def test_update_product(product_service: ProductService) -> None:
    created = await product_service.create_product(
        name="Keyboard",
        price=Decimal("199.90"),
        stock_quantity=10,
        created_by=1,
    )
    assert created.id is not None

    updated = await product_service.update_product(
        product_id=created.id,
        name="Mechanical Keyboard",
        price=Decimal("249.90"),
        stock_quantity=8,
        updated_by=2,
    )

    assert updated.name == "Mechanical Keyboard"
    assert updated.price == Decimal("249.90")
    assert updated.stock_quantity == 8
    assert updated.updated_by == 2


async def test_find_product_by_id_raises_when_missing(
    product_service: ProductService,
) -> None:
    with pytest.raises(ProductNotFound):
        await product_service.find_product_by_id(999)
