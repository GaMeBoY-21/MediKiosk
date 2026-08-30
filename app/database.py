# Owner: Tharun
"""SQLAlchemy engine and session dependency.

TODO: wire up the real engine/session once DATABASE_URL is finalized.
"""


def get_db():
    """FastAPI dependency that yields a database session.

    TODO: implement using SQLAlchemy sessionmaker.
    """
    raise NotImplementedError
