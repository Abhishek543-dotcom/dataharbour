"""
Catalog Routes — PostgreSQL Databases/Tables & Apache Iceberg
=============================================================
GET    /catalog/databases                       — List databases with sizes
POST   /catalog/databases/{name}                — Create database
DELETE /catalog/databases/{name}                — Drop database
GET    /catalog/databases/{db}/tables           — List tables in a database
POST   /catalog/databases/{db}/tables/{name}    — Create JSONB table
DELETE /catalog/databases/{db}/tables/{name}    — Drop table
GET    /catalog/iceberg/tables                  — List Iceberg tables
GET    /catalog/iceberg/tables/{name}           — Get Iceberg table metadata
"""

import json
import logging
import os

import psycopg2
from psycopg2 import sql
from fastapi import APIRouter, HTTPException

from api.helpers import get_db, release_db
from core.config import Config

logger = logging.getLogger("dataharbour.routes.catalog")
router = APIRouter(prefix="/catalog", tags=["Catalog (PostgreSQL & Iceberg)"])


# ══════════════════════════════════════════════════════════════
#  PostgreSQL Databases
# ══════════════════════════════════════════════════════════════

@router.get("/databases")
def list_databases():
    """List all user-created PostgreSQL databases with their sizes."""
    conn = cursor = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT datname,
                   pg_size_pretty(pg_database_size(datname)) AS size
            FROM   pg_database
            WHERE  datistemplate = false
                   AND datname NOT IN ('postgres')
            ORDER  BY datname
        """)
        databases = [{"name": r[0], "size": r[1]} for r in cursor.fetchall()]
        return {"databases": databases, "count": len(databases)}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    finally:
        if cursor:
            cursor.close()
        if conn:
            release_db(conn)


@router.post("/databases/{db_name}")
def create_database(db_name: str):
    """Create a new PostgreSQL database."""
    conn = cursor = None
    try:
        conn = get_db()
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
        logger.info("Database created: %s", db_name)
        return {"message": f"Database '{db_name}' created", "database": db_name}
    except psycopg2.errors.DuplicateDatabase:
        raise HTTPException(status_code=409, detail=f"Database '{db_name}' already exists")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    finally:
        if cursor:
            cursor.close()
        if conn:
            release_db(conn)


@router.delete("/databases/{db_name}")
def delete_database(db_name: str):
    """
    Drop a PostgreSQL database.

    Terminates active connections first to avoid lock errors.
    """
    conn = cursor = None
    try:
        conn = get_db()
        conn.autocommit = True
        cursor = conn.cursor()
        # Terminate existing connections to the target database
        cursor.execute(
            "SELECT pg_terminate_backend(pid) "
            "FROM pg_stat_activity "
            "WHERE datname = %s AND pid <> pg_backend_pid()",
            (db_name,),
        )
        cursor.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(db_name)))
        logger.info("Database deleted: %s", db_name)
        return {"message": f"Database '{db_name}' deleted"}
    except psycopg2.errors.InvalidCatalogName:
        raise HTTPException(status_code=404, detail=f"Database '{db_name}' not found")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    finally:
        if cursor:
            cursor.close()
        if conn:
            release_db(conn)


# ══════════════════════════════════════════════════════════════
#  PostgreSQL Tables
# ══════════════════════════════════════════════════════════════

@router.get("/databases/{db_name}/tables")
def list_tables(db_name: str):
    """List all tables in a PostgreSQL database with their sizes."""
    conn = cursor = None
    try:
        conn = get_db(db_name)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT table_name,
                   pg_size_pretty(pg_total_relation_size(quote_ident(table_name))) AS size
            FROM   information_schema.tables
            WHERE  table_schema = 'public'
                   AND table_type = 'BASE TABLE'
            ORDER  BY table_name
        """)
        tables = [{"name": r[0], "size": r[1]} for r in cursor.fetchall()]
        return {"tables": tables, "database": db_name, "count": len(tables)}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    finally:
        if cursor:
            cursor.close()
        if conn:
            release_db(conn, db_name)


@router.post("/databases/{db_name}/tables/{table_name}")
def create_table(db_name: str, table_name: str):
    """Create a JSONB table in a PostgreSQL database."""
    conn = cursor = None
    try:
        conn = get_db(db_name)
        cursor = conn.cursor()
        cursor.execute(
            sql.SQL(
                "CREATE TABLE IF NOT EXISTS {} "
                "(id SERIAL PRIMARY KEY, data JSONB, created_at TIMESTAMP DEFAULT NOW())"
            ).format(sql.Identifier(table_name))
        )
        conn.commit()
        logger.info("Table created: %s.%s", db_name, table_name)
        return {"message": f"Table '{table_name}' created in '{db_name}'", "table": table_name}
    except HTTPException:
        raise
    except Exception as exc:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=400, detail=str(exc))
    finally:
        if cursor:
            cursor.close()
        if conn:
            release_db(conn, db_name)


@router.delete("/databases/{db_name}/tables/{table_name}")
def delete_table(db_name: str, table_name: str):
    """Drop a table from a PostgreSQL database."""
    conn = cursor = None
    try:
        conn = get_db(db_name)
        cursor = conn.cursor()
        cursor.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(table_name)))
        conn.commit()
        logger.info("Table deleted: %s.%s", db_name, table_name)
        return {"message": f"Table '{table_name}' deleted from '{db_name}'"}
    except HTTPException:
        raise
    except Exception as exc:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=400, detail=str(exc))
    finally:
        if cursor:
            cursor.close()
        if conn:
            release_db(conn, db_name)


# ══════════════════════════════════════════════════════════════
#  Apache Iceberg
# ══════════════════════════════════════════════════════════════

ICEBERG_NAMESPACE = "dataharbour"


@router.get("/iceberg/tables")
def list_iceberg_tables():
    """List all Iceberg tables in the warehouse."""
    tables_path = os.path.join(Config.iceberg_warehouse, ICEBERG_NAMESPACE)
    try:
        if not os.path.exists(tables_path):
            return {"tables": [], "count": 0}

        tables = []
        with os.scandir(tables_path) as it:
            for entry in it:
                if entry.is_dir():
                    tables.append({
                        "name": entry.name,
                        "path": entry.path,
                        "hasMetadata": os.path.exists(os.path.join(entry.path, "metadata")),
                    })
        return {"tables": tables, "count": len(tables)}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/iceberg/tables/{table_name}")
def get_iceberg_table_details(table_name: str):
    """Return the latest Iceberg metadata JSON for a table."""
    metadata_path = os.path.join(
        Config.iceberg_warehouse, ICEBERG_NAMESPACE, table_name, "metadata"
    )
    try:
        if not os.path.exists(metadata_path):
            raise HTTPException(status_code=404, detail=f"Iceberg table '{table_name}' not found")

        metadata_files = sorted(
            f for f in os.listdir(metadata_path) if f.endswith(".metadata.json")
        )
        if not metadata_files:
            return {"table": table_name, "metadata": None}

        with open(os.path.join(metadata_path, metadata_files[-1]), "r") as f:
            metadata = json.load(f)

        return {"table": table_name, "metadata": metadata}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

