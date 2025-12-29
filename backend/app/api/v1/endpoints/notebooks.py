from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from fastapi.responses import JSONResponse
from typing import List, Optional
from sqlalchemy.orm import Session
import logging

from app.models.schemas import (
    Notebook, NotebookCreate, NotebookUpdate, NotebookCell,
    CellExecuteRequest, CellExecuteResponse, APIResponse, User
)
from app.services.notebook_service import notebook_service
from app.db.session import get_db
from app.api.dependencies import get_optional_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[Notebook])
async def get_notebooks(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Get all notebooks"""
    try:
        user_id = str(current_user.id) if current_user else None
        notebooks = await notebook_service.get_all_notebooks(db, user_id)
        return notebooks
    except Exception as e:
        logger.error(f"Error getting notebooks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{notebook_id}", response_model=Notebook)
async def get_notebook(
    notebook_id: str,
    db: Session = Depends(get_db)
):
    """Get specific notebook"""
    try:
        notebook = await notebook_service.get_notebook(db, notebook_id)
        if not notebook:
            raise HTTPException(status_code=404, detail=f"Notebook {notebook_id} not found")
        return notebook
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting notebook {notebook_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=Notebook)
async def create_notebook(
    notebook_data: NotebookCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Create a new notebook"""
    try:
        user_id = str(current_user.id) if current_user else None
        notebook = await notebook_service.create_notebook(db, notebook_data, user_id)
        return notebook
    except Exception as e:
        logger.error(f"Error creating notebook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{notebook_id}", response_model=Notebook)
async def update_notebook(
    notebook_id: str,
    update_data: NotebookUpdate,
    db: Session = Depends(get_db)
):
    """Update a notebook"""
    try:
        notebook = await notebook_service.update_notebook(db, notebook_id, update_data)
        return notebook
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating notebook {notebook_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{notebook_id}", response_model=APIResponse)
async def delete_notebook(
    notebook_id: str,
    db: Session = Depends(get_db)
):
    """Delete a notebook"""
    try:
        success = await notebook_service.delete_notebook(db, notebook_id)
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
async def add_cell(
    notebook_id: str,
    cell: NotebookCell,
    db: Session = Depends(get_db)
):
    """Add a cell to a notebook"""
    try:
        notebook = await notebook_service.add_cell(db, notebook_id, cell)
        return notebook
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding cell to notebook {notebook_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{notebook_id}/cells/{cell_id}", response_model=Notebook)
async def delete_cell(
    notebook_id: str,
    cell_id: str,
    db: Session = Depends(get_db)
):
    """Delete a cell from a notebook"""
    try:
        notebook = await notebook_service.delete_cell(db, notebook_id, cell_id)
        return notebook
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting cell from notebook {notebook_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{notebook_id}/cells/{cell_id}/execute", response_model=CellExecuteResponse)
async def execute_cell(
    notebook_id: str,
    cell_id: str,
    request: CellExecuteRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Execute a notebook cell"""
    try:
        user_id = str(current_user.id) if current_user else None
        result = await notebook_service.execute_cell(db, notebook_id, cell_id, request.code, user_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error executing cell {cell_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import", response_model=Notebook)
async def import_notebook(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Import a notebook from file"""
    try:
        content = await file.read()
        user_id = str(current_user.id) if current_user else None
        notebook = await notebook_service.import_notebook(
            db,
            content.decode('utf-8'),
            file.filename,
            user_id
        )
        return notebook
    except Exception as e:
        logger.error(f"Error importing notebook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{notebook_id}/export")
async def export_notebook(
    notebook_id: str,
    db: Session = Depends(get_db)
):
    """Export a notebook to Jupyter format"""
    try:
        ipynb = await notebook_service.export_notebook(db, notebook_id)
        return JSONResponse(content=ipynb)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error exporting notebook {notebook_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
