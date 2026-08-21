from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.http.dependencies import get_actor_id, get_product_service
from app.http.schemas.products import (
    CreateProductRequest,
    ProductResponse,
    UpdateProductRequest,
)
from app.product.domain import Product
from app.product.service import ProductService

router = APIRouter(prefix="/products", tags=["products"])


def to_product_response(product: Product) -> ProductResponse:
    if product.id is None:
        raise RuntimeError("Persisted product must have an id.")
    return ProductResponse(
        id=product.id,
        name=product.name,
        price=product.price,
        stock_quantity=product.stock_quantity,
        created_at=product.created_at,
        created_by=product.created_by,
        updated_at=product.updated_at,
        updated_by=product.updated_by,
    )


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: CreateProductRequest,
    actor_id: Annotated[int, Depends(get_actor_id)],
    product_service: Annotated[ProductService, Depends(get_product_service)],
) -> ProductResponse:
    product = await product_service.create_product(
        name=payload.name,
        price=payload.price,
        stock_quantity=payload.stock_quantity,
        created_by=actor_id,
    )
    return to_product_response(product)


@router.get("", response_model=list[ProductResponse])
async def list_products(
    product_service: Annotated[ProductService, Depends(get_product_service)],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[ProductResponse]:
    products = await product_service.list_products(offset=offset, limit=limit)
    return [to_product_response(product) for product in products]


@router.get("/{product_id}", response_model=ProductResponse)
async def find_product_by_id(
    product_id: int,
    product_service: Annotated[ProductService, Depends(get_product_service)],
) -> ProductResponse:
    product = await product_service.find_product_by_id(product_id)
    return to_product_response(product)


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    payload: UpdateProductRequest,
    actor_id: Annotated[int, Depends(get_actor_id)],
    product_service: Annotated[ProductService, Depends(get_product_service)],
) -> ProductResponse:
    product = await product_service.update_product(
        product_id=product_id,
        name=payload.name,
        price=payload.price,
        stock_quantity=payload.stock_quantity,
        updated_by=actor_id,
    )
    return to_product_response(product)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    actor_id: Annotated[int, Depends(get_actor_id)],
    product_service: Annotated[ProductService, Depends(get_product_service)],
) -> Response:
    await product_service.delete_product(product_id=product_id, deleted_by=actor_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
