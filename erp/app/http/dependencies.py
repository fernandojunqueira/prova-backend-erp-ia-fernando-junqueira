from typing import Annotated

from fastapi import Depends, Header
from psycopg import AsyncConnection

from app.config.database import get_connection
from app.product.postgres.repository import PostgresProductRepository
from app.product.repository import ProductRepository
from app.product.service import ProductService


def get_actor_id(x_actor_id: Annotated[int, Header()]) -> int:
    return x_actor_id


def get_product_repository(
    connection: Annotated[AsyncConnection, Depends(get_connection)],
) -> ProductRepository:
    return PostgresProductRepository(connection)


def get_product_service(
    product_repository: Annotated[ProductRepository, Depends(get_product_repository)],
) -> ProductService:
    return ProductService(product_repository)
