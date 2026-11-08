import json
from collections.abc import Callable
from pathlib import Path

import httpx

FIXTURES = Path(__file__).parent / "fixtures"


def fixture(name: str):
    return json.loads((FIXTURES / f"{name}.json").read_text())


def fake_client(routes: dict[str, Callable[[httpx.Request], httpx.Response] | object]) -> httpx.AsyncClient:
    """An AsyncClient whose requests are answered from `routes`, keyed by '<host><path>'.

    A value is either a JSON body (served with 200), an int status code, or a handler function.
    Unknown URLs get a 404 so a test fails loudly instead of touching the network.
    """

    def handle(request: httpx.Request) -> httpx.Response:
        route = routes.get(f"{request.url.host}{request.url.path}")
        if route is None:
            return httpx.Response(404, json={"error": "no fixture"})
        if callable(route):
            response = route(request)
            assert isinstance(response, httpx.Response)
            return response
        if isinstance(route, int):
            return httpx.Response(route)
        return httpx.Response(200, json=route)

    return httpx.AsyncClient(transport=httpx.MockTransport(handle))
