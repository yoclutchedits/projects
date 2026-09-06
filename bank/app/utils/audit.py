
from sqlalchemy.orm import Session
from fastapi import Request
from app.models.audit_logs import AuditLog


def log_action(
    db: Session,
    request: Request,
    action: str,
    entity_type: str,
    entity_id: str,
    user_id: int | None = None,
    changes: dict | None = None,
):
    ip = request.client.host
    log_entry = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        changes=changes,
        ip_address=ip,
    )
    db.add(log_entry)
