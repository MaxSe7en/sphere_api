# from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean, ForeignKey
# from sqlalchemy.orm import relationship
# import datetime

# from app.models.base import Base

# class Session(Base):
#     __tablename__ = "sessions"
#     id = Column(Integer, primary_key=True)
#     state_id = Column(Integer)
#     year_start = Column(Integer)
#     year_end = Column(Integer)
#     session_tag = Column(String)
#     session_title = Column(String)
#     session_name = Column(String)

#     bills = relationship("Bill", back_populates="session")