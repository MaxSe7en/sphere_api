from sqlalchemy import Column, String
from app.models.base import Base

class State(Base):
    __tablename__ = "states"

    code = Column(String, primary_key=True, index=True)  # e.g. "MN"
    name = Column(String, nullable=False)                # e.g. "Minnesota"
