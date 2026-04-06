from sqlalchemy import Column, Integer, String, Text, DateTime, func
from app.db import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String(500), nullable=False)
    summary = Column(Text, nullable=True)
    link = Column(String(1000), nullable=False)

    published = Column(DateTime(timezone=True), nullable=True)

    source = Column(String(500), nullable=False)

    score = Column(Integer, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)