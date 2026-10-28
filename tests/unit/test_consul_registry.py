import asyncio
import json
from pathlib import Path

import httpx

from app.core.config import Settings
from app.core.consul_registry import ConsulRegistry


def settings(tmp_path: Path) -> Settings:
    token = tmp_path / "consul.token"
    token.write_text("test-token", encoding="utf-8")
    return Settings(
        _env_file=None,
        consul_enabled=True,
        consul_http_addr="http://consul:8500",
        consul_http_token_file=str(token),
        consul_service_address="validacion-pdf",
        consul_service_port=8000,
    )


def test_register_and_deregister_validacion(tmp_path: Path):
    requests = []

    async def responder(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200)

    registry = ConsulRegistry(
        settings=settings(tmp_path),
        instance_id="validacion-pdf-instance-a",
        transport=httpx.MockTransport(responder),
    )

    asyncio.run(registry.register())
    asyncio.run(registry.deregister())

    assert requests[0].method == "PUT"
    assert str(requests[0].url) == "http://consul:8500/v1/agent/service/register"
    assert requests[0].headers["X-Consul-Token"] == "test-token"
    payload = json.loads(requests[0].content)
    assert payload["ID"] == "validacion-pdf-instance-a"
    assert payload["Name"] == "validacion-pdf"
    assert payload["Address"] == "validacion-pdf"
    assert payload["Port"] == 8000
    assert payload["Checks"][0]["HTTP"] == "http://validacion-pdf:8000/health"
    assert "traefik.enable=true" in payload["Tags"]
    assert str(requests[1].url).endswith(
        "/v1/agent/service/deregister/validacion-pdf-instance-a"
    )
