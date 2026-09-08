"""Minimal bounded process entrypoint for Docker Foundation services.

This module provides only a long-running process boundary for the P1 service
containers. It does not implement API, collection, worker, market, database,
or trading functionality.
"""

from __future__ import annotations

import os
import signal
import time

_ALLOWED_SERVICES = {"api", "collector", "worker-quant", "worker-ai"}
_running = True


def _stop(_signum: int, _frame: object) -> None:
    global _running
    _running = False


def main() -> int:
    service = os.environ.get("MEYLUX_SERVICE", "")
    if service not in _ALLOWED_SERVICES:
        raise SystemExit(f"unsupported foundation service: {service!r}")

    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)

    print(f"meylux-v2 foundation service started: {service}", flush=True)
    while _running:
        time.sleep(1)

    print(f"meylux-v2 foundation service stopped: {service}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
