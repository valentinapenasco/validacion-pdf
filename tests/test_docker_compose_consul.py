from pathlib import Path

COMPOSE = Path(__file__).resolve().parents[1] / "docker-compose.yml"


def test_compose_conecta_validacion_a_consul_sin_exponer_el_token():
    text = COMPOSE.read_text(encoding="utf-8")
    assert "CONSUL_HTTP_ADDR: http://consul:8500" in text
    assert "CONSUL_HTTP_TOKEN_FILE: /run/secrets/consul_microservices_token" in text
    assert "name: redutn" in text
    assert "consul_microservices_token:" in text
