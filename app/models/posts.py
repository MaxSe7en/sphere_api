from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean, ForeignKey
from sqlalchemy.orm import relationship
import datetime

from app.models.base import Base



class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    bill_id = Column(Integer, ForeignKey("bills.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    content = Column(String)
    upvotes = Column(Integer, default=0)
    downvotes = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    bill = relationship("Bill", back_populates="posts")
    user = relationship("User", back_populates="posts")