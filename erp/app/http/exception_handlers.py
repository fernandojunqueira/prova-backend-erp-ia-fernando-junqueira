from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.product.domain import InvalidProduct, ProductNotFound


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ProductNotFound)
    async def handle_product_not_found(
        _request: Request,
        exc: ProductNotFound,
    ) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(InvalidProduct)
    async def handle_invalid_product(
        _request: Request,
        exc: InvalidProduct,
    ) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})
