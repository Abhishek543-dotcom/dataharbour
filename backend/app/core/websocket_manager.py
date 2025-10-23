from typing import Dict
from fastapi import WebSocket
import json
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"Client {client_id} disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(message)
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {e}")
                self.disconnect(client_id)

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        message_text = json.dumps(message)
        disconnected_clients = []

        for client_id, connection in self.active_connections.items():
            try:
                await connection.send_text(message_text)
            except Exception as e:
                logger.error(f"Error broadcasting to {client_id}: {e}")
                disconnected_clients.append(client_id)

        # Clean up disconnected clients
        for client_id in disconnected_clients:
            self.disconnect(client_id)

    async def broadcast_job_update(self, job_data: dict):
        """Broadcast job status update to all clients"""
        await self.broadcast({
            "type": "job_update",
            "data": job_data
        })

    async def broadcast_metrics_update(self, metrics_data: dict):
        """Broadcast system metrics update to all clients"""
        await self.broadcast({
            "type": "metrics_update",
            "data": metrics_data
        })


manager = ConnectionManager()
