from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from app.api.v1.audit import serialize_audit_log


def test_serialize_audit_log_marks_naive_created_at_as_utc():
    log = SimpleNamespace(
        id=uuid4(),
        user_id=uuid4(),
        action="UPDATE",
        entity_type="revenue",
        entity_id=uuid4(),
        old_values={"field": "old"},
        new_values={"field": "new"},
        ip_address=None,
        user_agent=None,
        created_at=datetime(2026, 4, 9, 14, 24, 0),
    )

    serialized = serialize_audit_log(log)

    assert serialized.created_at.tzinfo == timezone.utc
    assert serialized.created_at.isoformat() == "2026-04-09T14:24:00+00:00"
