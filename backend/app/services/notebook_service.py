import logging
from typing import List, Optional, Dict
from datetime import datetime
import uuid
import json
from sqlalchemy.orm import Session

from app.models.schemas import Notebook, NotebookCreate, NotebookUpdate, NotebookCell, CellExecuteRequest, CellExecuteResponse
from app.services.spark_service import spark_service
from app.db.repositories.notebook_repository import NotebookRepository
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)


class NotebookService:
    def __init__(self):
        self.repository = NotebookRepository()

    def _notebook_db_to_schema(self, notebook_db) -> Notebook:
        """Convert database model to Notebook schema"""
        cells = []
        if notebook_db.cells:
            # Convert JSONB cells to NotebookCell objects
            for cell_data in notebook_db.cells:
                cells.append(NotebookCell(**cell_data))

        return Notebook(
            id=notebook_db.id,
            name=notebook_db.name,
            description=notebook_db.description,
            cells=cells,
            created_at=notebook_db.created_at,
            updated_at=notebook_db.updated_at,
            path=notebook_db.path
        )

    async def get_all_notebooks(
        self,
        db: Session,
        user_id: Optional[str] = None
    ) -> List[Notebook]:
        """Get all notebooks"""
        if user_id:
            notebooks_db = self.repository.get_recent_notebooks(db, user_id=user_id, limit=1000)
        else:
            notebooks_db = self.repository.get_recent_notebooks(db, limit=1000)

        return [self._notebook_db_to_schema(nb) for nb in notebooks_db]

    async def get_notebook(self, db: Session, notebook_id: str) -> Optional[Notebook]:
        """Get specific notebook by ID"""
        notebook_db = self.repository.get_by_id(db, notebook_id)
        if notebook_db:
            return self._notebook_db_to_schema(notebook_db)
        return None

    async def create_notebook(
        self,
        db: Session,
        notebook_data: NotebookCreate,
        user_id: Optional[str] = None
    ) -> Notebook:
        """Create a new notebook"""
        try:
            notebook_id = f"nb_{uuid.uuid4().hex[:12]}"

            notebook_dict = {
                "id": notebook_id,
                "name": notebook_data.name,
                "description": notebook_data.description,
                "cells": [],
                "user_id": user_id,
                "path": f"/notebooks/{notebook_id}.ipynb"
            }

            notebook_db = self.repository.create(db, notebook_dict)
            logger.info(f"Notebook {notebook_id} created")
            return self._notebook_db_to_schema(notebook_db)
        except Exception as e:
            logger.error(f"Error creating notebook: {e}")
            raise

    async def update_notebook(
        self,
        db: Session,
        notebook_id: str,
        update_data: NotebookUpdate
    ) -> Notebook:
        """Update a notebook"""
        try:
            notebook_db = self.repository.get_by_id(db, notebook_id)
            if not notebook_db:
                raise ValueError(f"Notebook {notebook_id} not found")

            update_dict = {}
            if update_data.name:
                update_dict["name"] = update_data.name
            if update_data.description is not None:
                update_dict["description"] = update_data.description
            if update_data.cells is not None:
                # Convert cells to JSON-serializable format
                update_dict["cells"] = [cell.model_dump() for cell in update_data.cells]

            updated_notebook = self.repository.update(db, notebook_id, update_dict)
            logger.info(f"Notebook {notebook_id} updated")
            return self._notebook_db_to_schema(updated_notebook)
        except Exception as e:
            logger.error(f"Error updating notebook {notebook_id}: {e}")
            raise

    async def delete_notebook(self, db: Session, notebook_id: str) -> bool:
        """Delete a notebook"""
        try:
            success = self.repository.delete(db, notebook_id)
            if success:
                logger.info(f"Notebook {notebook_id} deleted")
            return success
        except Exception as e:
            logger.error(f"Error deleting notebook {notebook_id}: {e}")
            raise

    async def add_cell(self, db: Session, notebook_id: str, cell: NotebookCell) -> Notebook:
        """Add a cell to a notebook"""
        try:
            notebook_db = self.repository.get_by_id(db, notebook_id)
            if not notebook_db:
                raise ValueError(f"Notebook {notebook_id} not found")

            # Get current cells and add new one
            cells = notebook_db.cells or []
            cells.append(cell.model_dump())

            updated_notebook = self.repository.update(db, notebook_id, {"cells": cells})
            logger.info(f"Cell added to notebook {notebook_id}")
            return self._notebook_db_to_schema(updated_notebook)
        except Exception as e:
            logger.error(f"Error adding cell to notebook {notebook_id}: {e}")
            raise

    async def delete_cell(self, db: Session, notebook_id: str, cell_id: str) -> Notebook:
        """Delete a cell from a notebook"""
        try:
            notebook_db = self.repository.get_by_id(db, notebook_id)
            if not notebook_db:
                raise ValueError(f"Notebook {notebook_id} not found")

            # Filter out the cell to delete
            cells = [c for c in (notebook_db.cells or []) if c.get("id") != cell_id]

            updated_notebook = self.repository.update(db, notebook_id, {"cells": cells})
            logger.info(f"Cell {cell_id} deleted from notebook {notebook_id}")
            return self._notebook_db_to_schema(updated_notebook)
        except Exception as e:
            logger.error(f"Error deleting cell from notebook {notebook_id}: {e}")
            raise

    async def execute_cell(
        self,
        db: Session,
        notebook_id: str,
        cell_id: str,
        code: str,
        user_id: Optional[str] = None
    ) -> CellExecuteResponse:
        """Execute a notebook cell"""
        try:
            notebook_db = self.repository.get_by_id(db, notebook_id)
            if not notebook_db:
                raise ValueError(f"Notebook {notebook_id} not found")

            # Find the cell
            cells = notebook_db.cells or []
            cell_index = next((i for i, c in enumerate(cells) if c.get("id") == cell_id), None)
            if cell_index is None:
                raise ValueError(f"Cell {cell_id} not found in notebook {notebook_id}")

            # Execute code using Spark service
            result = await spark_service.execute_code(code)

            # Update cell with execution results
            cell = cells[cell_index]
            cell["execution_count"] = (cell.get("execution_count") or 0) + 1
            cell["outputs"] = [{
                "output_type": "stream",
                "text": result["output"]
            }]

            # Update notebook in database
            self.repository.update(db, notebook_id, {"cells": cells})

            # Create a job for tracking
            from app.services.job_service import job_service
            from app.models.schemas import JobCreate

            job_data = JobCreate(
                name=f"Notebook {notebook_db.name} - Cell {cell_id}",
                code=code
            )
            job = await job_service.create_job(db, job_data, user_id)

            return CellExecuteResponse(
                output=result["output"],
                execution_time=result["execution_time"],
                status=result["status"],
                job_id=job.id
            )
        except Exception as e:
            logger.error(f"Error executing cell {cell_id}: {e}")
            return CellExecuteResponse(
                output=str(e),
                execution_time=0,
                status="failed",
                job_id=None
            )

    async def import_notebook(
        self,
        db: Session,
        file_content: str,
        filename: str,
        user_id: Optional[str] = None
    ) -> Notebook:
        """Import a notebook from JSON/ipynb file"""
        try:
            data = json.loads(file_content)

            # Handle both .ipynb and custom format
            if "cells" in data and "metadata" in data:
                # Jupyter notebook format
                cells = [
                    {
                        "id": f"cell_{i}",
                        "cell_type": cell.get("cell_type", "code"),
                        "source": "".join(cell.get("source", [])),
                        "outputs": cell.get("outputs", []),
                        "execution_count": cell.get("execution_count")
                    }
                    for i, cell in enumerate(data["cells"])
                ]
                name = filename.replace(".ipynb", "").replace(".json", "")
            else:
                # Custom format
                cells = data.get("cells", [])
                name = data.get("name", filename)

            notebook_data = NotebookCreate(
                name=name,
                description=f"Imported from {filename}"
            )
            notebook = await self.create_notebook(db, notebook_data, user_id)

            # Update with cells
            self.repository.update(db, notebook.id, {"cells": cells})

            # Fetch updated notebook
            updated_notebook = self.repository.get_by_id(db, notebook.id)

            logger.info(f"Notebook imported from {filename}")
            return self._notebook_db_to_schema(updated_notebook)
        except Exception as e:
            logger.error(f"Error importing notebook: {e}")
            raise

    async def export_notebook(self, db: Session, notebook_id: str) -> dict:
        """Export notebook to Jupyter format"""
        try:
            notebook_db = self.repository.get_by_id(db, notebook_id)
            if not notebook_db:
                raise ValueError(f"Notebook {notebook_id} not found")

            # Convert to Jupyter notebook format
            ipynb = {
                "cells": [
                    {
                        "cell_type": cell.get("cell_type", "code"),
                        "execution_count": cell.get("execution_count"),
                        "metadata": {},
                        "source": cell.get("source", "").split("\n"),
                        "outputs": cell.get("outputs", [])
                    }
                    for cell in (notebook_db.cells or [])
                ],
                "metadata": {
                    "kernelspec": {
                        "display_name": "PySpark",
                        "language": "python",
                        "name": "pyspark"
                    },
                    "language_info": {
                        "name": "python",
                        "version": "3.9"
                    }
                },
                "nbformat": 4,
                "nbformat_minor": 4
            }

            return ipynb
        except Exception as e:
            logger.error(f"Error exporting notebook {notebook_id}: {e}")
            raise

    async def get_notebook_count(self, db: Session, user_id: Optional[str] = None) -> int:
        """Get total count of notebooks"""
        if user_id:
            return self.repository.count_by_user(db, user_id)
        return self.repository.count(db)


# Singleton instance
notebook_service = NotebookService()
