from sqlalchemy.orm import Session

from app.database import get_db


def test_get_db_yields_session() -> None:
    db_gen = get_db()
    session = next(db_gen)

    assert isinstance(session, Session)

    db_gen.close()
