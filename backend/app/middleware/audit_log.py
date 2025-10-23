import logging
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime
import json

# Configure audit logger
audit_logger = logging.getLogger("audit")
audit_logger.setLevel(logging.INFO)

# Create file handler for audit logs
audit_handler = logging.FileHandler("/data/logs/audit.log")
audit_handler.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter(
    '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": %(message)s}'
)
audit_handler.setFormatter(formatter)
audit_logger.addHandler(audit_handler)


class AuditLogMiddleware(BaseHTTPMiddleware):
    """
    Audit logging middleware for tracking API access
    """

    async def dispatch(self, request: Request, call_next):
        # Start timer
        start_time = time.time()

        # Get request details
        client_ip = request.client.host
        method = request.method
        path = request.url.path
        user_agent = request.headers.get("user-agent", "unknown")

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Log audit entry
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "client_ip": client_ip,
            "method": method,
            "path": path,
            "status_code": response.status_code,
            "duration_ms": round(duration * 1000, 2),
            "user_agent": user_agent,
        }

        # Log sensitive operations
        sensitive_paths = ["/jobs", "/notebooks", "/clusters", "/monitoring"]
        if any(path.startswith(f"/api/v1{sp}") for sp in sensitive_paths):
            if method in ["POST", "PUT", "DELETE"]:
                audit_logger.info(json.dumps(audit_entry))

        return response
