from decimal import Decimal

import pytest

from app.product.domain import InvalidProduct, Product


def test_create_product_with_valid_data() -> None:
    product = Product.create(
        name="  Keyboard  ",
        price=Decimal("199.90"),
        stock_quantity=10,
        created_by=1,
    )

    assert product.name == "Keyboard"
    assert product.price == Decimal("199.90")
    assert product.stock_quantity == 10
    assert product.is_deleted is False
    assert product.id is None


def test_create_product_rejects_blank_name() -> None:
    with pytest.raises(InvalidProduct):
        Product.create(
            name="   ",
            price=Decimal("10.00"),
            stock_quantity=1,
            created_by=1,
        )


def test_create_product_rejects_negative_price() -> None:
    with pytest.raises(InvalidProduct):
        Product.create(
            name="Mouse",
            price=Decimal("-1.00"),
            stock_quantity=1,
            created_by=1,
        )


def test_create_product_rejects_negative_stock() -> None:
    with pytest.raises(InvalidProduct):
        Product.create(
            name="Mouse",
            price=Decimal("10.00"),
            stock_quantity=-1,
            created_by=1,
        )


def test_mark_as_deleted() -> None:
    product = Product.create(
        name="Monitor",
        price=Decimal("900.00"),
        stock_quantity=3,
        created_by=1,
    )

    product.mark_as_deleted(deleted_by=2)

    assert product.is_deleted is True
    assert product.updated_by == 2
