"""
Cluster Monitoring Routes
=========================
GET /cluster/status        — Spark cluster health (cores, memory, apps)
GET /cluster/workers       — List registered workers
GET /cluster/applications  — Active and completed Spark apps
"""

import logging

import requests
from fastapi import APIRouter

from core.config import Config

logger = logging.getLogger("dataharbour.routes.cluster")
router = APIRouter(prefix="/cluster", tags=["Cluster Monitoring"])


@router.get("/status")
def get_cluster_status():
    """
    Fetch live Spark cluster status from the master Web UI JSON API.

    Returns ``status: "unavailable"`` instead of an error when the cluster
    is down — **graceful degradation**.
    """
    try:
        resp = requests.get(f"{Config.spark_rest_url}/json/", timeout=5)
        if resp.ok:
            d = resp.json()
            return {
                "status": "running",
                "masterUrl": Config.spark_master_url,
                "workers": len(d.get("workers", [])),
                "cores": d.get("cores", 0),
                "coresUsed": d.get("coresused", 0),
                "memory": d.get("memory", "0 MB"),
                "memoryUsed": d.get("memoryused", "0 MB"),
                "activeApps": len(d.get("activeapps", [])),
                "completedApps": len(d.get("completedapps", [])),
            }
    except Exception as exc:
        logger.debug("Spark cluster unreachable: %s", exc)

    return {
        "status": "unavailable",
        "masterUrl": Config.spark_master_url,
        "workers": 0,
        "cores": 0,
        "coresUsed": 0,
        "memory": "0 MB",
        "memoryUsed": "0 MB",
        "activeApps": 0,
        "completedApps": 0,
    }


@router.get("/workers")
def get_cluster_workers():
    """Return the list of registered Spark workers with detailed info."""
    try:
        resp = requests.get(f"{Config.spark_rest_url}/json/", timeout=5)
        if resp.ok:
            workers = resp.json().get("workers", [])
            return {"workers": workers, "count": len(workers)}
    except Exception as exc:
        logger.debug("Spark cluster unreachable: %s", exc)

    return {"workers": [], "count": 0}


@router.get("/applications")
def get_cluster_applications():
    """Return active and completed Spark applications from the master."""
    try:
        resp = requests.get(f"{Config.spark_rest_url}/json/", timeout=5)
        if resp.ok:
            d = resp.json()
            active = d.get("activeapps", [])
            completed = d.get("completedapps", [])
            return {
                "active": active,
                "completed": completed,
                "activeCount": len(active),
                "completedCount": len(completed),
            }
    except Exception as exc:
        logger.debug("Spark cluster unreachable: %s", exc)

    return {"active": [], "completed": [], "activeCount": 0, "completedCount": 0}

