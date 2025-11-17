"""
Database service for PostgreSQL operations
Provides database exploration, table browsing, and query execution
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any, Optional
import logging
from ..core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class DatabaseService:
    """Service for managing PostgreSQL database operations"""

    def __init__(self):
        self.connection_params = {
            'host': settings.POSTGRES_HOST,
            'port': settings.POSTGRES_PORT,
            'user': settings.POSTGRES_USER,
            'password': settings.POSTGRES_PASSWORD,
            'database': settings.POSTGRES_DB
        }

    def _get_connection(self, database: Optional[str] = None):
        """Create a database connection"""
        params = self.connection_params.copy()
        if database:
            params['database'] = database
        return psycopg2.connect(**params)

    async def list_databases(self) -> List[Dict[str, Any]]:
        """List all databases in PostgreSQL"""
        try:
            conn = self._get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            query = """
                SELECT
                    datname as name,
                    pg_size_pretty(pg_database_size(datname)) as size,
                    pg_encoding_to_char(encoding) as encoding,
                    datcollate as collation,
                    pg_stat_get_db_numbackends(oid) as connections
                FROM pg_database
                WHERE datistemplate = false
                ORDER BY datname
            """

            cur.execute(query)
            databases = cur.fetchall()

            cur.close()
            conn.close()

            return [dict(db) for db in databases]
        except Exception as e:
            logger.error(f"Error listing databases: {str(e)}")
            raise

    async def list_tables(self, database: str = None) -> List[Dict[str, Any]]:
        """List all tables in a database"""
        try:
            conn = self._get_connection(database)
            cur = conn.cursor(cursor_factory=RealDictCursor)

            query = """
                SELECT
                    schemaname as schema,
                    tablename as name,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                    (SELECT COUNT(*)
                     FROM information_schema.columns
                     WHERE table_schema = schemaname
                     AND table_name = tablename) as column_count
                FROM pg_tables
                WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
                ORDER BY schemaname, tablename
            """

            cur.execute(query)
            tables = cur.fetchall()

            cur.close()
            conn.close()

            return [dict(table) for table in tables]
        except Exception as e:
            logger.error(f"Error listing tables: {str(e)}")
            raise

    async def get_table_schema(self, database: str, schema: str, table: str) -> Dict[str, Any]:
        """Get detailed schema information for a table"""
        try:
            conn = self._get_connection(database)
            cur = conn.cursor(cursor_factory=RealDictCursor)

            # Get column information
            column_query = """
                SELECT
                    column_name as name,
                    data_type as type,
                    character_maximum_length as max_length,
                    is_nullable,
                    column_default as default_value
                FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position
            """

            cur.execute(column_query, (schema, table))
            columns = [dict(col) for col in cur.fetchall()]

            # Get primary key information
            pk_query = """
                SELECT a.attname as column_name
                FROM pg_index i
                JOIN pg_attribute a ON a.attrelid = i.indrelid
                    AND a.attnum = ANY(i.indkey)
                WHERE i.indrelid = %s::regclass
                    AND i.indisprimary
            """

            cur.execute(pk_query, (f"{schema}.{table}",))
            primary_keys = [row['column_name'] for row in cur.fetchall()]

            # Get foreign key information
            fk_query = """
                SELECT
                    kcu.column_name,
                    ccu.table_schema AS foreign_table_schema,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_schema = %s
                    AND tc.table_name = %s
            """

            cur.execute(fk_query, (schema, table))
            foreign_keys = [dict(fk) for fk in cur.fetchall()]

            # Get row count
            count_query = f"SELECT COUNT(*) as count FROM {schema}.{table}"
            cur.execute(count_query)
            row_count = cur.fetchone()['count']

            cur.close()
            conn.close()

            return {
                'schema': schema,
                'table': table,
                'columns': columns,
                'primary_keys': primary_keys,
                'foreign_keys': foreign_keys,
                'row_count': row_count
            }
        except Exception as e:
            logger.error(f"Error getting table schema: {str(e)}")
            raise

    async def preview_table_data(
        self,
        database: str,
        schema: str,
        table: str,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get preview data from a table"""
        try:
            conn = self._get_connection(database)
            cur = conn.cursor(cursor_factory=RealDictCursor)

            # Get total count
            count_query = f"SELECT COUNT(*) as count FROM {schema}.{table}"
            cur.execute(count_query)
            total_count = cur.fetchone()['count']

            # Get data
            data_query = f"""
                SELECT * FROM {schema}.{table}
                LIMIT %s OFFSET %s
            """

            cur.execute(data_query, (limit, offset))
            rows = [dict(row) for row in cur.fetchall()]

            # Get column names
            columns = [desc[0] for desc in cur.description] if cur.description else []

            cur.close()
            conn.close()

            return {
                'columns': columns,
                'rows': rows,
                'total_count': total_count,
                'limit': limit,
                'offset': offset
            }
        except Exception as e:
            logger.error(f"Error previewing table data: {str(e)}")
            raise

    async def execute_query(
        self,
        database: str,
        query: str,
        limit: int = 1000
    ) -> Dict[str, Any]:
        """Execute a SELECT query (read-only)"""
        try:
            # Basic SQL injection prevention - only allow SELECT statements
            query_upper = query.strip().upper()
            if not query_upper.startswith('SELECT'):
                raise ValueError("Only SELECT queries are allowed")

            # Prevent multiple statements
            if ';' in query[:-1]:  # Allow semicolon at the end
                raise ValueError("Multiple statements are not allowed")

            conn = self._get_connection(database)
            cur = conn.cursor(cursor_factory=RealDictCursor)

            # Add LIMIT if not present
            if 'LIMIT' not in query_upper:
                query = f"{query.rstrip(';')} LIMIT {limit}"

            cur.execute(query)
            rows = [dict(row) for row in cur.fetchall()]

            # Get column names
            columns = [desc[0] for desc in cur.description] if cur.description else []

            cur.close()
            conn.close()

            return {
                'columns': columns,
                'rows': rows,
                'row_count': len(rows)
            }
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            raise


# Singleton instance
_database_service = None

def get_database_service() -> DatabaseService:
    """Get or create database service instance"""
    global _database_service
    if _database_service is None:
        _database_service = DatabaseService()
    return _database_service
