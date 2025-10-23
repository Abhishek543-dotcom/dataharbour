import logging
from typing import List, Optional, Dict
from datetime import datetime
import uuid
import json
import os
from pathlib import Path

from app.models.schemas import Notebook, NotebookCreate, NotebookUpdate, NotebookCell, CellExecuteRequest, CellExecuteResponse
from app.services.spark_service import spark_service
from app.services.job_service import job_service
from app.models.schemas import JobCreate

logger = logging.getLogger(__name__)


class NotebookService:
    def __init__(self):
        self._notebooks: Dict[str, Notebook] = {}
        self._notebooks_dir = Path("/data/notebooks")
        self._notebooks_dir.mkdir(parents=True, exist_ok=True)
        self._load_notebooks()

    def _load_notebooks(self):
        """Load existing notebooks from filesystem"""
        try:
            for file_path in self._notebooks_dir.glob("*.json"):
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    notebook = Notebook(**data)
                    self._notebooks[notebook.id] = notebook
            logger.info(f"Loaded {len(self._notebooks)} notebooks")
        except Exception as e:
            logger.error(f"Error loading notebooks: {e}")

    def _save_notebook_to_file(self, notebook: Notebook):
        """Save notebook to filesystem"""
        try:
            file_path = self._notebooks_dir / f"{notebook.id}.json"
            with open(file_path, 'w') as f:
                json.dump(notebook.model_dump(), f, indent=2, default=str)
            logger.info(f"Notebook {notebook.id} saved to {file_path}")
        except Exception as e:
            logger.error(f"Error saving notebook {notebook.id}: {e}")
            raise

    async def get_all_notebooks(self) -> List[Notebook]:
        """Get all notebooks"""
        return sorted(
            list(self._notebooks.values()),
            key=lambda x: x.updated_at,
            reverse=True
        )

    async def get_notebook(self, notebook_id: str) -> Optional[Notebook]:
        """Get specific notebook by ID"""
        return self._notebooks.get(notebook_id)

    async def create_notebook(self, notebook_data: NotebookCreate) -> Notebook:
        """Create a new notebook"""
        try:
            notebook_id = f"nb_{uuid.uuid4().hex[:12]}"

            notebook = Notebook(
                id=notebook_id,
                name=notebook_data.name,
                description=notebook_data.description,
                cells=[],
                created_at=datetime.now(),
                updated_at=datetime.now(),
                path=str(self._notebooks_dir / f"{notebook_id}.json")
            )

            self._notebooks[notebook_id] = notebook
            self._save_notebook_to_file(notebook)

            logger.info(f"Notebook {notebook_id} created")
            return notebook
        except Exception as e:
            logger.error(f"Error creating notebook: {e}")
            raise

    async def update_notebook(self, notebook_id: str, update_data: NotebookUpdate) -> Notebook:
        """Update a notebook"""
        try:
            notebook = self._notebooks.get(notebook_id)
            if not notebook:
                raise ValueError(f"Notebook {notebook_id} not found")

            if update_data.name:
                notebook.name = update_data.name
            if update_data.description is not None:
                notebook.description = update_data.description
            if update_data.cells is not None:
                notebook.cells = update_data.cells

            notebook.updated_at = datetime.now()
            self._save_notebook_to_file(notebook)

            logger.info(f"Notebook {notebook_id} updated")
            return notebook
        except Exception as e:
            logger.error(f"Error updating notebook {notebook_id}: {e}")
            raise

    async def delete_notebook(self, notebook_id: str) -> bool:
        """Delete a notebook"""
        try:
            if notebook_id not in self._notebooks:
                return False

            # Delete file
            file_path = self._notebooks_dir / f"{notebook_id}.json"
            if file_path.exists():
                file_path.unlink()

            del self._notebooks[notebook_id]
            logger.info(f"Notebook {notebook_id} deleted")
            return True
        except Exception as e:
            logger.error(f"Error deleting notebook {notebook_id}: {e}")
            raise

    async def add_cell(self, notebook_id: str, cell: NotebookCell) -> Notebook:
        """Add a cell to a notebook"""
        try:
            notebook = self._notebooks.get(notebook_id)
            if not notebook:
                raise ValueError(f"Notebook {notebook_id} not found")

            notebook.cells.append(cell)
            notebook.updated_at = datetime.now()
            self._save_notebook_to_file(notebook)

            logger.info(f"Cell added to notebook {notebook_id}")
            return notebook
        except Exception as e:
            logger.error(f"Error adding cell to notebook {notebook_id}: {e}")
            raise

    async def delete_cell(self, notebook_id: str, cell_id: str) -> Notebook:
        """Delete a cell from a notebook"""
        try:
            notebook = self._notebooks.get(notebook_id)
            if not notebook:
                raise ValueError(f"Notebook {notebook_id} not found")

            notebook.cells = [c for c in notebook.cells if c.id != cell_id]
            notebook.updated_at = datetime.now()
            self._save_notebook_to_file(notebook)

            logger.info(f"Cell {cell_id} deleted from notebook {notebook_id}")
            return notebook
        except Exception as e:
            logger.error(f"Error deleting cell from notebook {notebook_id}: {e}")
            raise

    async def execute_cell(self, notebook_id: str, cell_id: str, code: str) -> CellExecuteResponse:
        """Execute a notebook cell"""
        try:
            notebook = self._notebooks.get(notebook_id)
            if not notebook:
                raise ValueError(f"Notebook {notebook_id} not found")

            # Find the cell
            cell = next((c for c in notebook.cells if c.id == cell_id), None)
            if not cell:
                raise ValueError(f"Cell {cell_id} not found in notebook {notebook_id}")

            # Execute code using Spark service
            result = await spark_service.execute_code(code)

            # Update cell with execution results
            cell.execution_count = (cell.execution_count or 0) + 1
            cell.outputs = [{
                "output_type": "stream",
                "text": result["output"]
            }]

            notebook.updated_at = datetime.now()
            self._save_notebook_to_file(notebook)

            # Create a job for tracking
            job_data = JobCreate(
                name=f"Notebook {notebook.name} - Cell {cell_id}",
                code=code
            )
            job = await job_service.create_job(job_data)

            return CellExecuteResponse(
                output=result["output"],
                execution_time=result["execution_time"],
                status=result["status"],
                job_id=job.id
            )
        except Exception as e:
            logger.error(f"Error executing cell {cell_id}: {e}")
            return CellExecuteResponse(
                output="",
                execution_time=0,
                status="failed",
                job_id=None
            )

    async def import_notebook(self, file_content: str, filename: str) -> Notebook:
        """Import a notebook from JSON/ipynb file"""
        try:
            data = json.loads(file_content)

            # Handle both .ipynb and custom format
            if "cells" in data and "metadata" in data:
                # Jupyter notebook format
                cells = [
                    NotebookCell(
                        id=f"cell_{i}",
                        cell_type=cell.get("cell_type", "code"),
                        source="".join(cell.get("source", [])),
                        outputs=cell.get("outputs", [])
                    )
                    for i, cell in enumerate(data["cells"])
                ]
                name = filename.replace(".ipynb", "").replace(".json", "")
            else:
                # Custom format
                cells = [NotebookCell(**cell) for cell in data.get("cells", [])]
                name = data.get("name", filename)

            notebook_data = NotebookCreate(name=name, description=f"Imported from {filename}")
            notebook = await self.create_notebook(notebook_data)

            # Add cells
            notebook.cells = cells
            self._save_notebook_to_file(notebook)

            logger.info(f"Notebook imported from {filename}")
            return notebook
        except Exception as e:
            logger.error(f"Error importing notebook: {e}")
            raise

    async def export_notebook(self, notebook_id: str) -> dict:
        """Export notebook to Jupyter format"""
        try:
            notebook = self._notebooks.get(notebook_id)
            if not notebook:
                raise ValueError(f"Notebook {notebook_id} not found")

            # Convert to Jupyter notebook format
            ipynb = {
                "cells": [
                    {
                        "cell_type": cell.cell_type,
                        "execution_count": cell.execution_count,
                        "metadata": {},
                        "source": cell.source.split("\n"),
                        "outputs": cell.outputs or []
                    }
                    for cell in notebook.cells
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


# Singleton instance
notebook_service = NotebookService()
