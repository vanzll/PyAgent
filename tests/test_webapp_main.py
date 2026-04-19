from __future__ import annotations

from pycallingagent.webapp.__main__ import get_server_config


def test_get_server_config_uses_defaults(monkeypatch) -> None:
    monkeypatch.delenv("HOST", raising=False)
    monkeypatch.delenv("PORT", raising=False)

    assert get_server_config() == ("0.0.0.0", 8000)


def test_get_server_config_reads_environment(monkeypatch) -> None:
    monkeypatch.setenv("HOST", "127.0.0.1")
    monkeypatch.setenv("PORT", "11000")

    assert get_server_config() == ("127.0.0.1", 11000)


def test_get_server_config_falls_back_when_port_is_invalid(monkeypatch) -> None:
    monkeypatch.delenv("HOST", raising=False)
    monkeypatch.setenv("PORT", "not-a-port")

    assert get_server_config() == ("0.0.0.0", 8000)
