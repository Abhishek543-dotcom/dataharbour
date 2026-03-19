import psycopg2
from psycopg2 import pool
from core.config import Config

# Thread-safe connection pool
_pg_pool = None

def init_db_pool():
    global _pg_pool
    try:
        _pg_pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=10,
            host=Config.postgres_host,
            port=Config.postgres_port,
            user=Config.postgres_user,
            password=Config.postgres_password,
            database=Config.postgres_db
        )
    except Exception as e:
        print(f"Failed to initialize PostgreSQL connection pool: {e}")

def get_db_connection(db_name: str = None):
    # If a specific db_name is provided, we can't easily use the global pool
    # unless we create a pool per database. For now, create a new connection.
    if db_name and db_name != Config.postgres_db:
        return psycopg2.connect(
            host=Config.postgres_host,
            port=Config.postgres_port,
            user=Config.postgres_user,
            password=Config.postgres_password,
            database=db_name
        )

    # Use pool for default DB
    if _pg_pool:
        return _pg_pool.getconn()
    else:
        # Fallback if pool is uninitialized
        return psycopg2.connect(
            host=Config.postgres_host,
            port=Config.postgres_port,
            user=Config.postgres_user,
            password=Config.postgres_password,
            database=Config.postgres_db
        )

def release_db_connection(conn, db_name: str = None):
    if db_name and db_name != Config.postgres_db:
        conn.close()
    elif _pg_pool:
        _pg_pool.putconn(conn)
    else:
        conn.close()

def close_db_pool():
    if _pg_pool:
        _pg_pool.closeall()
