from fastapi.testclient import TestClient

from app.http.dependencies import get_actor_id, get_product_service
from app.main import app
from app.product.mock.repository import InMemoryProductRepository
from app.product.service import ProductService


def _build_client() -> TestClient:
    service = ProductService(InMemoryProductRepository())
    app.dependency_overrides[get_product_service] = lambda: service
    app.dependency_overrides[get_actor_id] = lambda: 1
    return TestClient(app)


def test_product_crud_over_http() -> None:
    client = _build_client()
    try:
        created = client.post(
            "/products",
            json={"name": "Keyboard", "price": "199.90", "stock_quantity": 10},
        )
        assert created.status_code == 201
        product_id = created.json()["id"]

        listed = client.get("/products")
        assert listed.status_code == 200
        assert len(listed.json()) == 1

        found = client.get(f"/products/{product_id}")
        assert found.status_code == 200
        assert found.json()["name"] == "Keyboard"

        updated = client.put(
            f"/products/{product_id}",
            json={
                "name": "Mechanical Keyboard",
                "price": "249.90",
                "stock_quantity": 8,
            },
        )
        assert updated.status_code == 200
        assert updated.json()["name"] == "Mechanical Keyboard"

        deleted = client.delete(f"/products/{product_id}")
        assert deleted.status_code == 204

        missing = client.get(f"/products/{product_id}")
        assert missing.status_code == 404
    finally:
        app.dependency_overrides.clear()
