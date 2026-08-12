import os

from dotenv import load_dotenv

from db.connection import get_connection, parse_database_url


def main() -> None:
    """Test ket noi Postgres that tu DATABASE_URL, in ra thong tin ket noi an toan (khong password)."""
    load_dotenv()

    conn = get_connection()
    conn.close()

    info = parse_database_url(os.environ["DATABASE_URL"])
    print(f"connected: host={info['host']} port={info['port']} dbname={info['dbname']} user={info['user']}")


if __name__ == "__main__":
    main()
