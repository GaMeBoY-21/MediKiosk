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

    existing = []
    for path in (db_path, db_path.with_suffix(db_path.suffix + "-shm"),
                 db_path.with_suffix(db_path.suffix + "-wal")):
        if path.exists():
            existing.append(path)

    if existing:
        total = sum(p.stat().st_size for p in existing)
        print(f"about to delete {len(existing)} file(s), {total/1024:.0f} KB:")
        for p in existing:
            print(f"  {p}")
    else:
        print(f"no database at {db_path} — nothing to delete, will create the schema")

    if existing and not args.yes:
        if input("type 'reset' to confirm: ").strip().lower() != "reset":
            print("cancelled, nothing deleted")
            return 1

    for p in existing:
        p.unlink()

    # Recreate the schema so the backend does not have to be restarted to
    # find its tables.
    from app.database import init_db

    init_db()
    print(f"\ndatabase reset: {db_path}")
    print("the queue is now empty. Seed it with:  python3 scripts/seed_demo.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
