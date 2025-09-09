from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean, ForeignKey
from sqlalchemy.orm import relationship
import datetime
from app.models.base import Base   # 👈 shared Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)

    # Relationships
    posts = relationship("Post", back_populates="user")
    followed_bills = relationship("FollowedBill", back_populates="user")