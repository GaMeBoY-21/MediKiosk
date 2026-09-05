#!/usr/bin/env python3
# Owner: Nikki
"""Empty the local database and recreate the schema.

Run this before a demo. Two hundred half-finished sessions from testing make
the queue unreadable — a doctor scrolling past two hundred rows of "ABC" is
not a demonstration of anything — and they all carried the same token, which
made the token search useless.

Local SQLite only, on purpose. It refuses to run against Postgres and against
APP_ENV=production: this deletes patient records, and the one thing it must
never be is convenient to point at something real.

    python3 scripts/reset_db.py           # asks first
    python3 scripts/reset_db.py --yes     # for scripting
"""

import argparse
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="Wipe the local demo database.")
    parser.add_argument("--yes", action="store_true", help="skip the confirmation")
    args = parser.parse_args()

    from app.config import settings

    if not settings.using_sqlite:
        print("refusing: DATABASE_URL points at a real database, not the SQLite fallback.")
        print("This script only ever resets the local demo file.")
        return 2
    if settings.APP_ENV == "production":
        print("refusing: APP_ENV=production.")
        return 2

    # sqlite:///./medikiosk.db -> ./medikiosk.db, resolved against the repo.
    relative = settings.database_url.split("sqlite:///", 1)[-1]
    db_path = (ROOT / relative.lstrip("./")).resolve()

    # Work on the file in place; never delete it.
    #
    # Deleting it while the backend is running is silently catastrophic on
    # SQLite: the running process keeps its handle on the now-unlinked inode
    # and carries on writing there, while everything started afterwards opens
    # a fresh file. The queue then shows rows that no script can find and the
    # seeder appears to succeed against nothing. Dropping and recreating the
    # tables inside the same file is visible to every connection immediately,
    # including the live backend's.
    from sqlalchemy import func, select

    from app.database import SessionLocal, engine
    from app.models import Base

    # Count what is about to go, for the report.
    counts = {}
    db = SessionLocal()
    try:
        for table in Base.metadata.sorted_tables:
            try:
                n = db.execute(select(func.count()).select_from(table)).scalar() or 0
            except Exception:
                n = 0  # table does not exist yet, or is an older shape
            if n:
                counts[table.name] = n
    finally:
        db.close()

    # DROP and recreate, rather than DELETE FROM.
    #
    # Emptying rows leaves the old COLUMNS in place, and create_all never
    # alters an existing table — so a schema change (a new consent field, a
    # document's provenance) would be invisible until someone deleted the file
    # by hand, and every query would fail with "no such column". Dropping the
    # tables applies the current schema and empties them in one step.
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    if counts:
        print("cleared:")
        for name, n in sorted(counts.items()):
            print(f"  {n:5} rows from {name}")
    else:
        print("database was already empty")
    print("  schema recreated from app/models.py")

    # Uploaded images are PHI and belong to the sessions just removed. Leaving
    # them behind means orphaned patient documents on disk after a "reset".
    uploads = ROOT / "uploads"
    removed = 0
    if uploads.is_dir():
        for f in uploads.iterdir():
            if f.is_file() and f.name != ".gitkeep":
                f.unlink()
                removed += 1
    if removed:
        print(f"  {removed:5} uploaded file(s) deleted from uploads/")

    print(f"\ndatabase reset: {db_path}")
    print("the queue is now empty. Seed it with:  python3 scripts/seed_demo.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
