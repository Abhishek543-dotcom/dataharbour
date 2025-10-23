from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from typing import List
import logging

from app.models.schemas import (
    Notebook, NotebookCreate, NotebookUpdate, NotebookCell,
    CellExecuteRequest, CellExecuteResponse, APIResponse
)
from app.services.notebook_service import notebook_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[Notebook])
async def get_notebooks():
    """Get all notebooks"""
    try:
        notebooks = await notebook_service.get_all_notebooks()
        return notebooks
    except Exception as e:
        logger.error(f"Error getting notebooks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{notebook_id}", response_model=Notebook)
async def get_notebook(notebook_id: str):
    """Get specific notebook"""
    try:
        notebook = await notebook_service.get_notebook(notebook_id)
        if not notebook:
            raise HTTPException(status_code=404, detail=f"Notebook {notebook_id} not found")
        return notebook
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting notebook {notebook_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=Notebook)
async def create_notebook(notebook_data: NotebookCreate):
    """Create a new notebook"""
    try:
        notebook = await notebook_service.create_notebook(notebook_data)
        return notebook
    except Exception as e:
        logger.error(f"Error creating notebook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{notebook_id}", response_model=Notebook)
async def update_notebook(notebook_id: str, update_data: NotebookUpdate):
    """Update a notebook"""
    try:
        notebook = await notebook_service.update_notebook(notebook_id, update_data)
        return notebook
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating notebook {notebook_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{notebook_id}", response_model=APIResponse)
async def delete_notebook(notebook_id: str):
    """Delete a notebook"""
    try:
        success = await notebook_service.delete_notebook(notebook_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Notebook {notebook_id} not found")

        return APIResponse(
            success=True,
            message=f"Notebook {notebook_id} deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting notebook {notebook_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{notebook_id}/cells", response_model=Notebook)
async def add_cell(notebook_id: str, cell: NotebookCell):
    """Add a cell to a notebook"""
    try:
        notebook = await notebook_service.add_cell(notebook_id, cell)
        return notebook
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding cell to notebook {notebook_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{notebook_id}/cells/{cell_id}", response_model=Notebook)
async def delete_cell(notebook_id: str, cell_id: str):
    """Delete a cell from a notebook"""
    try:
        notebook = await notebook_service.delete_cell(notebook_id, cell_id)
        return notebook
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting cell from notebook {notebook_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{notebook_id}/cells/{cell_id}/execute", response_model=CellExecuteResponse)
async def execute_cell(notebook_id: str, cell_id: str, request: CellExecuteRequest):
    """Execute a notebook cell"""
    try:
        result = await notebook_service.execute_cell(notebook_id, cell_id, request.code)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error executing cell {cell_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import", response_model=Notebook)
async def import_notebook(file: UploadFile = File(...)):
    """Import a notebook from file"""
    try:
        content = await file.read()
        notebook = await notebook_service.import_notebook(
            content.decode('utf-8'),
            file.filename
        )
        return notebook
    except Exception as e:
        logger.error(f"Error importing notebook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{notebook_id}/export")
async def export_notebook(notebook_id: str):
    """Export a notebook to Jupyter format"""
    try:
        ipynb = await notebook_service.export_notebook(notebook_id)
        return JSONResponse(content=ipynb)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error exporting notebook {notebook_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
