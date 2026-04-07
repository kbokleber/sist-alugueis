from types import SimpleNamespace

import pytest

from app.schemas.user import UserPasswordChange
from app.services.user_service import UserService
from app.utils.security import hash_password, verify_password


class FakeAsyncSession:
    def __init__(self):
        self.deleted = []
        self.commit_calls = 0

    async def delete(self, instance):
        self.deleted.append(instance)

    async def commit(self):
        self.commit_calls += 1


@pytest.mark.asyncio
async def test_delete_user_without_closings_attribute_still_deletes():
    session = FakeAsyncSession()
    service = UserService(session)
    user = SimpleNamespace(
        properties=[],
        categories=[],
        revenues=[],
        expenses=[],
        audit_logs=[],
    )

    await service.delete(user)

    assert session.deleted == [user]
    assert session.commit_calls == 1


@pytest.mark.asyncio
async def test_superuser_password_change_does_not_require_current_password():
    session = FakeAsyncSession()
    service = UserService(session)
    user = SimpleNamespace(hashed_password=hash_password("old-password"))
    data = UserPasswordChange(new_password="new-password-123")

    success = await service.change_password(
        user,
        data,
        require_current_password=False,
    )

    assert success is True
    assert session.commit_calls == 1
    assert verify_password("new-password-123", user.hashed_password)
