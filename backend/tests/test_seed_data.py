import types
import pytest

from scripts import seed_data


class _FakeResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


class _FakeSession:
    def __init__(self):
        self._admin = types.SimpleNamespace(id="admin-id")
        self._execute_calls = 0

    async def execute(self, _query):
        self._execute_calls += 1
        if self._execute_calls == 1:
            return _FakeResult(self._admin)
        return _FakeResult(object())

    def add(self, _instance):
        return None

    async def commit(self):
        return None

    async def refresh(self, _instance):
        return None


class _FakeSessionContext:
    def __init__(self, ensure_called_ref):
        self._ensure_called_ref = ensure_called_ref
        self._session = _FakeSession()

    async def __aenter__(self):
        assert self._ensure_called_ref["called"] is True
        return self._session

    async def __aexit__(self, exc_type, exc, tb):
        return False


@pytest.mark.asyncio
async def test_seed_ensures_property_code_column_before_db_session(monkeypatch):
    ensure_called_ref = {"called": False}

    async def fake_ensure_property_code_column():
        ensure_called_ref["called"] = True

    def fake_session_local():
        return _FakeSessionContext(ensure_called_ref)

    monkeypatch.setattr(seed_data, "ensure_property_code_column", fake_ensure_property_code_column)
    monkeypatch.setattr(seed_data, "AsyncSessionLocal", fake_session_local)

    await seed_data.seed()
