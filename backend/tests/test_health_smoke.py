from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app


async def test_health_shallow_returns_200() -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.integration
async def test_health_deep_reports_every_component_ok() -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health/deep")

    body = response.json()

    assert response.status_code == 200, f"Non-200 response. Body: {body}"
    assert body["status"] == "ok", f"Overall status not ok. Body: {body}"

    expected_components = {
        "auth",
        "database",
        "llm",
        "cache",
        "rate_limiter",
        "telemetry",
        "secrets",
    }
    actual_components = set(body["components"].keys())
    assert actual_components == expected_components, (
        f"Component set mismatch. "
        f"Missing: {expected_components - actual_components}. "
        f"Unexpected: {actual_components - expected_components}."
    )

    for name, component in body["components"].items():
        assert component["status"] == "ok", (
            f"Component {name!r} is not healthy: {component}"
        )


@pytest.mark.integration
async def test_health_deep_returns_503_when_a_component_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MONGO_URI", "mongodb://127.0.0.1:1")
    from app.config.settings import get_settings

    get_settings.cache_clear()

    try:
        app = create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health/deep")

        body = response.json()
        assert response.status_code == 503, f"Expected 503, got {response.status_code}. Body: {body}"
        assert body["status"] == "error"
        assert body["components"]["database"]["status"] == "error"
    finally:
        get_settings.cache_clear()