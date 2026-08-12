import os
from urllib.parse import unquote, urlsplit

import psycopg


VALID_SCHEMES = ("postgres", "postgresql")
DEFAULT_PORT = 5432


def parse_database_url(url: str) -> dict:
    """Trich host/port/dbname/user tu Postgres connection string, KHONG bao gio tra password."""
    parts = urlsplit(url)

    if parts.scheme not in VALID_SCHEMES:
        raise ValueError(f"Invalid Postgres connection string (scheme phai la postgres/postgresql): {url!r}")
    if not parts.hostname:
        raise ValueError(f"Invalid Postgres connection string (thieu host): {url!r}")
    if not parts.username:
        raise ValueError(f"Invalid Postgres connection string (thieu user): {url!r}")

    dbname = parts.path.lstrip("/")
    if not dbname:
        raise ValueError(f"Invalid Postgres connection string (thieu dbname): {url!r}")

    return {
        "host": parts.hostname,
        "port": parts.port if parts.port is not None else DEFAULT_PORT,
        "dbname": dbname,
        "user": unquote(parts.username),
    }


def get_connection(url: str | None = None) -> psycopg.Connection:
    """Mo ket noi Postgres that. Neu url khong truyen vao, doc tu bien moi truong DATABASE_URL."""
    if url is None:
        try:
            url = os.environ["DATABASE_URL"]
        except KeyError:
            raise RuntimeError("Thieu DATABASE_URL trong .env") from None

    return psycopg.connect(url)
