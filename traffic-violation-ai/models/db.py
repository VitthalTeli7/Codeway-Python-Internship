from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Integer, String, Float, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

Base = declarative_base()


class Violation(Base):
    __tablename__ = "violations"

    id = Column(Integer, primary_key=True)
    vehicle_no = Column(String(32), nullable=True)
    violation_type = Column(String(64), nullable=False)
    speed_kmh = Column(Float, nullable=True)
    location = Column(String(128), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    evidence_path = Column(String(256), nullable=True)


def create_session(database_uri: str) -> Session:
    engine = create_engine(database_uri, echo=False, future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)()


def log_violation(
    session: Session,
    *,
    violation_type: str,
    vehicle_no: Optional[str] = None,
    speed_kmh: Optional[float] = None,
    location: Optional[str] = None,
    evidence_path: Optional[str] = None,
) -> Violation:
    violation = Violation(
        vehicle_no=vehicle_no,
        violation_type=violation_type,
        speed_kmh=speed_kmh,
        location=location,
        evidence_path=evidence_path,
    )
    session.add(violation)
    session.commit()
    return violation

