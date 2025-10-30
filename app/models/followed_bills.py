from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base

class FollowedBill(Base):
    __tablename__ = "followed_bills"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    bill_id = Column(Integer, ForeignKey("bills.id"), nullable=False)

    user = relationship("User", back_populates="watchlist")
    bill = relationship("Bill")