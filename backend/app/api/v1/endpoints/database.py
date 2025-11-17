"""
Database API endpoints
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging

from ....services.database_service import get_database_service

logger = logging.getLogger(__name__)
router = APIRouter()


class QueryRequest(BaseModel):
    """Request model for query execution"""
    query: str
    limit: Optional[int] = 1000


@router.get("/databases")
async def list_databases() -> Dict[str, Any]:
    """List all databases"""
    try:
        service = get_database_service()
        databases = await service.list_databases()
        return {
            'success': True,
            'databases': databases,
            'count': len(databases)
        }
    except Exception as e:
        logger.error(f"Error listing databases: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/databases/{database}/tables")
async def list_tables(database: str) -> Dict[str, Any]:
    """List all tables in a database"""
    try:
        service = get_database_service()
        tables = await service.list_tables(database)
        return {
            'success': True,
            'database': database,
            'tables': tables,
            'count': len(tables)
        }
    except Exception as e:
        logger.error(f"Error listing tables: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/databases/{database}/tables/{schema}/{table}/schema")
async def get_table_schema(database: str, schema: str, table: str) -> Dict[str, Any]:
    """Get detailed schema information for a table"""
    try:
        service = get_database_service()
        schema_info = await service.get_table_schema(database, schema, table)
        return {
            'success': True,
            **schema_info
        }
    except Exception as e:
        logger.error(f"Error getting table schema: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/databases/{database}/tables/{schema}/{table}/preview")
async def preview_table_data(
    database: str,
    schema: str,
    table: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
) -> Dict[str, Any]:
    """Preview data from a table"""
    try:
        service = get_database_service()
        data = await service.preview_table_data(database, schema, table, limit, offset)
        return {
            'success': True,
            'database': database,
            'schema': schema,
            'table': table,
            **data
        }
    except Exception as e:
        logger.error(f"Error previewing table data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/databases/{database}/query")
async def execute_query(database: str, request: QueryRequest) -> Dict[str, Any]:
    """Execute a SELECT query"""
    try:
        service = get_database_service()
        result = await service.execute_query(database, request.query, request.limit)
        return {
            'success': True,
            'database': database,
            **result
        }
    except ValueError as e:
        # Handle validation errors (e.g., non-SELECT queries)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error executing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
