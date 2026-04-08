from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def test_alembic_revision_ids_fit_version_column():
    migrations_dir = Path(__file__).resolve().parents[1] / "alembic" / "versions"

    for migration_path in migrations_dir.glob("*.py"):
        spec = spec_from_file_location(migration_path.stem, migration_path)
        assert spec is not None and spec.loader is not None

        module = module_from_spec(spec)
        spec.loader.exec_module(module)

        revision = getattr(module, "revision", "")
        assert isinstance(revision, str)
        assert len(revision) <= 32, f"{migration_path.name} has revision longer than 32 characters"
