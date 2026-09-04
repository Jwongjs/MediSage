import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import httpx
from fastapi import Depends, FastAPI

from rate_limit import rate_limit


def _stub_app(name: str, limit: int, window_seconds: int = 60) -> FastAPI:
    app = FastAPI()

    @app.get("/limited", dependencies=[Depends(rate_limit(name, limit, window_seconds))])
    async def limited():
        return {"ok": True}

    return app


def _client(app: FastAPI) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


async def test_allows_requests_up_to_the_limit():
    app = _stub_app("allow_up_to_limit", limit=3)
    async with _client(app) as client:
        for _ in range(3):
            response = await client.get("/limited")
            assert response.status_code == 200


async def test_blocks_once_the_limit_is_exceeded():
    app = _stub_app("blocks_over_limit", limit=2)
    async with _client(app) as client:
        for _ in range(2):
            await client.get("/limited")
        response = await client.get("/limited")

    assert response.status_code == 429


async def test_different_route_names_get_independent_buckets():
    app = FastAPI()

    @app.get("/a", dependencies=[Depends(rate_limit("bucket_a", 1, 60))])
    async def a():
        return {"ok": True}

    @app.get("/b", dependencies=[Depends(rate_limit("bucket_b", 1, 60))])
    async def b():
        return {"ok": True}

    async with _client(app) as client:
        exhaust_a = await client.get("/a")
        still_allowed_b = await client.get("/b")

    assert exhaust_a.status_code == 200
    assert still_allowed_b.status_code == 200
