"""
CarbonIQ - Change Data Capture Service
Tracks all entity modifications for risk drift analysis and audit trails.
"""
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from models import CDCLog


def track_change(
    db: Session,
    entity_type: str,
    entity_id: str,
    action: str,
    changed_fields: list = None,
    old_values: dict = None,
    new_values: dict = None
):
    """
    Record a change event in the CDC log.
    
    Args:
        entity_type: 'project', 'vintage', 'risk_signal', 'audit'
        entity_id: ID of the entity
        action: 'create', 'update', 'delete'
        changed_fields: List of field names that changed
        old_values: Previous values dict
        new_values: New values dict
    """
    log_entry = CDCLog(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        changed_fields=changed_fields,
        old_values=old_values,
        new_values=new_values,
        timestamp=datetime.now(timezone.utc),
    )
    db.add(log_entry)
    db.flush()
    return log_entry


def get_entity_history(db: Session, entity_type: str, entity_id: str) -> list:
    """Get full change history for an entity."""
    return (
        db.query(CDCLog)
        .filter(CDCLog.entity_type == entity_type, CDCLog.entity_id == entity_id)
        .order_by(CDCLog.timestamp.desc())
        .all()
    )


def get_recent_changes(db: Session, limit: int = 50) -> list:
    """Get most recent changes across all entities."""
    return (
        db.query(CDCLog)
        .order_by(CDCLog.timestamp.desc())
        .limit(limit)
        .all()
    )


def compute_drift(db: Session, entity_type: str, entity_id: str) -> dict:
    """
    Analyze drift in an entity's values over time.
    Returns summary of how fields have changed.
    """
    history = get_entity_history(db, entity_type, entity_id)
    
    if not history:
        return {"entity_type": entity_type, "entity_id": entity_id, "total_changes": 0, "drift": {}}
    
    drift = {}
    for entry in history:
        if entry.changed_fields and entry.old_values and entry.new_values:
            for field in (entry.changed_fields if isinstance(entry.changed_fields, list) else []):
                if field not in drift:
                    drift[field] = {"changes": 0, "values": []}
                drift[field]["changes"] += 1
                old_val = entry.old_values.get(field) if isinstance(entry.old_values, dict) else None
                new_val = entry.new_values.get(field) if isinstance(entry.new_values, dict) else None
                drift[field]["values"].append({
                    "from": old_val,
                    "to": new_val,
                    "timestamp": entry.timestamp.isoformat() if entry.timestamp else None
                })
    
    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "total_changes": len(history),
        "drift": drift,
    }
