"""
PostgreSQL Connection Pool
==========================
Thread-safe connection pool using psycopg2.pool.ThreadedConnectionPool.

- Default database connections are served from the pool (1–10 connections).
- Custom database connections are created on-demand and closed after use.
"""

import logging
import psycopg2
from psycopg2 import pool
from core.config import Config

logger = logging.getLogger("dataharbour.db")

_pg_pool = None


def init_db_pool():
    """Initialize the PostgreSQL connection pool. Called once at app startup."""
    global _pg_pool
    try:
        _pg_pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=10,
            host=Config.postgres_host,
            port=Config.postgres_port,
            user=Config.postgres_user,
            password=Config.postgres_password,
            database=Config.postgres_db,
        )
        logger.info(
            "PostgreSQL pool initialized (host=%s, db=%s, pool=1-10)",
            Config.postgres_host,
            Config.postgres_db,
        )
    except Exception as e:
        logger.error("Failed to initialize PostgreSQL connection pool: %s", e)


def get_db_connection(db_name: str = None):
    """
    Return a psycopg2 connection.

    - If *db_name* is ``None`` or matches the default DB ➜ use the pool.
    - Otherwise ➜ create a fresh connection to the requested database.
    """
    if db_name and db_name != Config.postgres_db:
        return psycopg2.connect(
            host=Config.postgres_host,
            port=Config.postgres_port,
            user=Config.postgres_user,
            password=Config.postgres_password,
            database=db_name,
        )

    if _pg_pool:
        return _pg_pool.getconn()

    # Fallback — pool not yet initialised
    logger.warning("Connection pool not initialized, creating ad-hoc connection")
    return psycopg2.connect(
        host=Config.postgres_host,
        port=Config.postgres_port,
        user=Config.postgres_user,
        password=Config.postgres_password,
        database=Config.postgres_db,
    )


def release_db_connection(conn, db_name: str = None):
    """Return *conn* to the pool or close it (custom-db connections)."""
    if conn is None:
        return
    try:
        if db_name and db_name != Config.postgres_db:
            conn.close()
        elif _pg_pool:
            _pg_pool.putconn(conn)
        else:
            conn.close()
    except Exception:
        pass


def close_db_pool():
    """Shutdown the connection pool. Called once at app shutdown."""
    global _pg_pool
    if _pg_pool:
        _pg_pool.closeall()
        _pg_pool = None
        logger.info("PostgreSQL connection pool closed")
