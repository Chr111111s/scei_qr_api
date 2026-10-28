from datetime import UTC, datetime

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def utcnow() -> datetime:
    """Naive UTC timestamp, matching Prisma's TIMESTAMP(3) columns."""
    return datetime.now(UTC).replace(tzinfo=None)
