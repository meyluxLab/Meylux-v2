"""Deterministic database configuration for Meylux V2 foundation.

This module only derives configuration from explicit environment inputs. It does
not connect to the database or perform I/O at import time.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class DatabaseConfig:
    host: str
    port: int
    name: str
    user: str
    timezone: str = "UTC"
    application_name: str = "meylux-v2"


def load_database_config() -> DatabaseConfig:
    return DatabaseConfig(
        host=os.getenv("MEYLUX_DB_HOST", "localhost"),
        port=int(os.getenv("MEYLUX_DB_PORT", "5432")),
        name=os.getenv("MEYLUX_DB_NAME", "meylux"),
        user=os.getenv("MEYLUX_DB_USER", "meylux_admin"),
    )
