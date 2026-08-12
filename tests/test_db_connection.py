import pytest

from db.connection import get_connection, parse_database_url


def test_parse_valid_url():
    result = parse_database_url("postgresql://myuser:mypass@db.example.com:5432/mydb")

    assert result == {
        "host": "db.example.com",
        "port": 5432,
        "dbname": "mydb",
        "user": "myuser",
    }
    assert "password" not in result
    assert "mypass" not in result.values()


def test_parse_password_with_percent_encoded_at():
    result = parse_database_url(
        "postgresql://myuser:dummy%40pass123@db.example.com:5432/mydb"
    )

    assert result == {
        "host": "db.example.com",
        "port": 5432,
        "dbname": "mydb",
        "user": "myuser",
    }


def test_parse_invalid_url_raises():
    with pytest.raises(ValueError):
        parse_database_url("not-a-valid-url")


def test_get_connection_missing_database_url_raises(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        get_connection()


def test_parse_rejects_non_postgres_scheme():
    with pytest.raises(ValueError):
        parse_database_url("mysql://user:pass@host:3306/db")


def test_parse_missing_port_defaults_to_5432():
    result = parse_database_url("postgresql://myuser:mypass@db.example.com/mydb")

    assert result["port"] == 5432


def test_parse_missing_user_raises():
    with pytest.raises(ValueError):
        parse_database_url("postgresql://db.example.com:5432/mydb")


def test_parse_empty_dbname_raises():
    with pytest.raises(ValueError):
        parse_database_url("postgresql://myuser:mypass@db.example.com:5432/")


def test_parse_none_raises_value_error():
    with pytest.raises(ValueError):
        parse_database_url(None)
