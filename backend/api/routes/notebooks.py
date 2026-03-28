"""
Notebook Routes
===============
GET    /notebooks                        — List all notebooks
POST   /notebooks                        — Create new notebook
GET    /notebooks/{name}                 — Get notebook content
PUT    /notebooks/{name}                 — Save/update notebook
DELETE /notebooks/{name}                 — Delete notebook
POST   /notebooks/{name}/execute         — Execute notebook as Spark job
"""

import json
import logging
import os
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException

from api.helpers import NotebookContent, upsert_job
from core.config import Config
from core.spark_client import spark_submit

logger = logging.getLogger("dataharbour.routes.notebooks")
router = APIRouter(prefix="/notebooks", tags=["Notebooks"])


@router.get("")
def list_notebooks():
    """List all Jupyter notebooks sorted by last-modified date."""
    try:
        if not os.path.exists(Config.notebooks_dir):
            return {"notebooks": [], "count": 0}

        notebooks = []
        with os.scandir(Config.notebooks_dir) as it:
            for entry in it:
                if entry.is_file() and entry.name.endswith(".ipynb"):
                    stat = entry.stat()
                    notebooks.append({
                        "id": entry.name,
                        "name": entry.name,
                        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "lastModified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    })
        notebooks.sort(key=lambda n: n["lastModified"], reverse=True)
        return {"notebooks": notebooks, "count": len(notebooks)}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("")
def create_notebook(name: str):
    """
    Create a new empty notebook with a PySpark starter cell.

    If the name doesn't end with ``.ipynb``, the extension is appended automatically.
    """
    if not name.endswith(".ipynb"):
        name = f"{name}.ipynb"

    path = os.path.join(Config.notebooks_dir, name)

    try:
        if os.path.exists(path):
            raise HTTPException(status_code=409, detail=f"Notebook '{name}' already exists")

        os.makedirs(Config.notebooks_dir, exist_ok=True)
        empty = {
            "cells": [
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": [
                        "# New DataHarbour Notebook\n",
                        "from pyspark.sql import SparkSession\n",
                        "\n",
                        "spark = SparkSession.builder.appName('DataHarbour').getOrCreate()\n",
                        "print('Spark session created')\n",
                    ],
                }
            ],
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3",
                }
            },
            "nbformat": 4,
            "nbformat_minor": 5,
        }
        with open(path, "w") as f:
            json.dump(empty, f, indent=2)

        logger.info("Notebook created: %s", name)
        return {"message": f"Notebook '{name}' created", "notebook": name}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/{notebook_name}")
def get_notebook(notebook_name: str):
    """Return the full JSON content of a notebook."""
    path = os.path.join(Config.notebooks_dir, notebook_name)
    try:
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail="Notebook not found")
        with open(path, "r") as f:
            content = json.load(f)
        return {"notebook": notebook_name, "content": content}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid notebook format")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.put("/{notebook_name}")
def save_notebook(notebook_name: str, content: NotebookContent):
    """Save (overwrite) a notebook's content."""
    path = os.path.join(Config.notebooks_dir, notebook_name)
    try:
        os.makedirs(Config.notebooks_dir, exist_ok=True)
        with open(path, "w") as f:
            json.dump(content.dict(), f, indent=2)
        logger.info("Notebook saved: %s", notebook_name)
        return {"message": "Notebook saved", "notebook": notebook_name}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/{notebook_name}")
def delete_notebook(notebook_name: str):
    """Delete a notebook."""
    path = os.path.join(Config.notebooks_dir, notebook_name)
    try:
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail="Notebook not found")
        os.remove(path)
        logger.info("Notebook deleted: %s", notebook_name)
        return {"message": f"Notebook '{notebook_name}' deleted"}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{notebook_name}/execute")
def execute_notebook(notebook_name: str):
    """
    Extract all code cells from a notebook, write them as a ``.py`` file,
    and submit to the Spark cluster.

    Returns a ``job_id`` for ``/jobs/{id}/status`` and ``/jobs/{id}/logs`` polling.
    """
    nb_path = os.path.join(Config.notebooks_dir, notebook_name)
    try:
        if not os.path.exists(nb_path):
            raise HTTPException(status_code=404, detail="Notebook not found")

        with open(nb_path, "r") as f:
            notebook = json.load(f)

        # Extract code cells
        code = "\n\n".join(
            "".join(cell.get("source", []))
            for cell in notebook.get("cells", [])
            if cell.get("cell_type") == "code"
        )
        if not code.strip():
            raise HTTPException(status_code=400, detail="Notebook has no executable code cells")

        os.makedirs(Config.jobs_dir, exist_ok=True)
        os.makedirs(Config.logs_dir, exist_ok=True)

        job_id = str(uuid.uuid4())
        script = notebook_name.replace(".ipynb", ".py")
        file_path = os.path.join(Config.jobs_dir, f"{job_id}_{script}")
        app_name = f"DataHarbour-nb-{job_id[:8]}"

        with open(file_path, "w") as f:
            f.write(f"# Generated from notebook: {notebook_name}\n\n{code}")

        try:
            spark_resp = spark_submit(job_id, file_path, app_name)
        except RuntimeError as exc:
            os.remove(file_path)
            raise HTTPException(status_code=503, detail=str(exc))

        submission_id = spark_resp.get("submissionId")
        record = upsert_job(
            job_id,
            filename=script,
            file_path=file_path,
            submitted_at=datetime.utcnow().isoformat(),
            status="SUBMITTED",
            spark_submission_id=submission_id,
            worker_host_port=None,
        )

        logger.info("Notebook executed: %s → job %s", notebook_name, job_id)

        return {
            "message": f"Notebook '{notebook_name}' submitted as Spark job",
            "job_id": job_id,
            "spark_submission_id": submission_id,
            "submitted_at": record.get("submitted_at"),
            "status": "SUBMITTED",
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

