from __future__ import annotations

import os

import uvicorn


def get_server_config() -> tuple[str, int]:
    host = os.getenv("HOST", "0.0.0.0").strip() or "0.0.0.0"
    port_value = os.getenv("PORT", "8000").strip()
    try:
        port = int(port_value)
    except ValueError:
        port = 8000
    return host, port


def main() -> None:
    host, port = get_server_config()
    uvicorn.run("pycallingagent.webapp.app:create_app", factory=True, host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
