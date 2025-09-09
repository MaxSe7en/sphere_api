# from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
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

# class Bill(Base):
#     __tablename__ = "bills"
#     id = Column(Integer, primary_key=True)  # bill_id from API
#     bill_number = Column(String, nullable=False)
#     title = Column(Text)
#     description = Column(Text)
#     summary = Column(String)  # AI-generated summary
#     raw_data = Column(JSON)  # Original API response
#     ai_analysis = Column(JSON)  # {summary: "", impacts: [], pro_con: []}
#     last_updated = Column(DateTime, default=datetime.datetime.utcnow)
#     status = Column(String)
#     status_date = Column(DateTime)
#     state = Column(String)
#     url = Column(String)
#     state_link = Column(String)

#     session_id = Column(Integer, ForeignKey("sessions.id"))
#     session = relationship("Session", back_populates="bills")

#     sponsors = relationship("Sponsor", back_populates="bill")
#     referrals = relationship("Referral", back_populates="bill")
#     history = relationship("BillHistory", back_populates="bill")
#     texts = relationship("BillText", back_populates="bill")
#     calendar = relationship("CalendarEvent", back_populates="bill")
#     posts = relationship("Post", back_populates="bill")

# class Sponsor(Base):
#     __tablename__ = "sponsors"
#     id = Column(Integer, primary_key=True)
#     people_id = Column(Integer)
#     name = Column(String)
#     party = Column(String)
#     role = Column(String)
#     district = Column(String)

#     bill_id = Column(Integer, ForeignKey("bills.id"))
#     bill = relationship("Bill", back_populates="sponsors")

# class Referral(Base):
#     __tablename__ = "referrals"
#     id = Column(Integer, primary_key=True)
#     date = Column(DateTime)
#     committee_id = Column(Integer)
#     chamber = Column(String)
#     name = Column(String)

#     bill_id = Column(Integer, ForeignKey("bills.id"))
#     bill = relationship("Bill", back_populates="referrals")


# class BillHistory(Base):
#     __tablename__ = "bill_history"
#     id = Column(Integer, primary_key=True)
#     date = Column(DateTime)
#     action = Column(Text)
#     chamber = Column(String)
#     importance = Column(Integer)

#     bill_id = Column(Integer, ForeignKey("bills.id"))
#     bill = relationship("Bill", back_populates="history")


# class BillText(Base):
#     __tablename__ = "bill_texts"
#     id = Column(Integer, primary_key=True)
#     doc_id = Column(Integer)
#     date = Column(DateTime)
#     type = Column(String)
#     url = Column(String)
#     state_link = Column(String)

#     bill_id = Column(Integer, ForeignKey("bills.id"))
#     bill = relationship("Bill", back_populates="texts")


# class CalendarEvent(Base):
#     __tablename__ = "calendar_events"
#     id = Column(Integer, primary_key=True)
#     type = Column(String)
#     date = Column(DateTime)
#     time = Column(String)
#     description = Column(Text)

#     bill_id = Column(Integer, ForeignKey("bills.id"))
#     bill = relationship("Bill", back_populates="calendar")

# class FollowedBill(Base):
#     __tablename__ = "followed_bills"

#     id = Column(Integer, primary_key=True, index=True)
#     user_id = Column(Integer, ForeignKey("users.id"))
#     bill_id = Column(Integer, ForeignKey("bills.id"))

#     user = relationship("User", back_populates="followed_bills")

# models.py (Rewritten to include all relevant fields from LegiScan API response)

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
import datetime

from app.models.base import Base

class Session(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True)
    state_id = Column(Integer)
    year_start = Column(Integer)
    year_end = Column(Integer)
    prefile = Column(Integer)
    sine_die = Column(Integer)
    prior = Column(Integer)
    special = Column(Integer)
    session_tag = Column(String)
    session_title = Column(String)
    session_name = Column(String)

    bills = relationship("Bill", back_populates="session")

class Bill(Base):
    __tablename__ = "bills"
    id = Column(Integer, primary_key=True)  # bill_id from API
    bill_number = Column(String, nullable=False)
    change_hash = Column(String)  # For detecting updates
    title = Column(Text)
    description = Column(Text)
    ai_summary = Column(Text)  # AI-generated plain-English summary
    ai_impacts = Column(JSON)  # List of who/what affected
    ai_pro_con = Column(JSON)  # Pro/con arguments
    raw_data = Column(JSON)  # Full original API response for reference
    last_updated = Column(DateTime)  # Derived from status_date or latest history date
    status = Column(Integer)
    status_date = Column(DateTime)
    state = Column(String)
    url = Column(String)
    state_link = Column(String)
    completed = Column(Integer)
    bill_type = Column(String)
    bill_type_id = Column(Integer)
    body = Column(String)
    body_id = Column(Integer)
    current_body = Column(String)
    current_body_id = Column(Integer)
    pending_committee_id = Column(Integer)

    session_id = Column(Integer, ForeignKey("sessions.id"))
    session = relationship("Session", back_populates="bills")

    sponsors = relationship("Sponsor", back_populates="bill")
    referrals = relationship("Referral", back_populates="bill")
    history = relationship("BillHistory", back_populates="bill")
    texts = relationship("BillText", back_populates="bill")
    calendar = relationship("CalendarEvent", back_populates="bill")
    votes = relationship("Vote", back_populates="bill")  # Placeholder for votes
    amendments = relationship("Amendment", back_populates="bill")  # Placeholder
    supplements = relationship("Supplement", back_populates="bill")  # Placeholder
    sasts = relationship("Sast", back_populates="bill")  # Similar bills
    posts = relationship("Post", back_populates="bill")  # Community posts

class Sponsor(Base):
    __tablename__ = "sponsors"
    id = Column(Integer, primary_key=True)
    people_id = Column(Integer)
    person_hash = Column(String)
    party_id = Column(Integer)
    party = Column(String)
    role_id = Column(Integer)
    role = Column(String)
    name = Column(String)
    first_name = Column(String)
    middle_name = Column(String)
    last_name = Column(String)
    suffix = Column(String)
    nickname = Column(String)
    district = Column(String)
    ftm_eid = Column(Integer)
    votesmart_id = Column(Integer)
    opensecrets_id = Column(String)
    knowwho_pid = Column(Integer)
    ballotpedia = Column(String)
    bioguide_id = Column(String)
    sponsor_type_id = Column(Integer)
    sponsor_order = Column(Integer)
    committee_sponsor = Column(Integer)
    committee_id = Column(Integer)
    state_federal = Column(Integer)

    bill_id = Column(Integer, ForeignKey("bills.id"))
    bill = relationship("Bill", back_populates="sponsors")

class Referral(Base):
    __tablename__ = "referrals"
    id = Column(Integer, primary_key=True)
    date = Column(DateTime)
    committee_id = Column(Integer)
    chamber = Column(String)
    chamber_id = Column(Integer)
    name = Column(String)

    bill_id = Column(Integer, ForeignKey("bills.id"))
    bill = relationship("Bill", back_populates="referrals")

class BillHistory(Base):
    __tablename__ = "bill_history"
    id = Column(Integer, primary_key=True)
    date = Column(DateTime)
    action = Column(Text)
    chamber = Column(String)
    chamber_id = Column(Integer)
    importance = Column(Integer)

    bill_id = Column(Integer, ForeignKey("bills.id"))
    bill = relationship("Bill", back_populates="history")

class BillText(Base):
    __tablename__ = "bill_texts"
    id = Column(Integer, primary_key=True)
    doc_id = Column(Integer)
    date = Column(DateTime)
    type = Column(String)
    type_id = Column(Integer)
    mime = Column(String)
    mime_id = Column(Integer)
    url = Column(String)
    state_link = Column(String)
    text_size = Column(Integer)
    text_hash = Column(String)

    bill_id = Column(Integer, ForeignKey("bills.id"))
    bill = relationship("Bill", back_populates="texts")

class CalendarEvent(Base):
    __tablename__ = "calendar_events"
    id = Column(Integer, primary_key=True)
    type_id = Column(Integer)
    type = Column(String)
    event_hash = Column(String)
    date = Column(DateTime)
    time = Column(String)
    location = Column(String)
    description = Column(Text)

    bill_id = Column(Integer, ForeignKey("bills.id"))
    bill = relationship("Bill", back_populates="calendar")

class Vote(Base):
    __tablename__ = "votes"
    id = Column(Integer, primary_key=True)
    # Fields can be expanded when votes data is available, e.g.:
    # roll_call_id = Column(Integer)
    # date = Column(DateTime)
    # etc.

    bill_id = Column(Integer, ForeignKey("bills.id"))
    bill = relationship("Bill", back_populates="votes")

class Amendment(Base):
    __tablename__ = "amendments"
    id = Column(Integer, primary_key=True)
    # Placeholder; expand as needed (e.g., amendment_id, date, title, url)

    bill_id = Column(Integer, ForeignKey("bills.id"))
    bill = relationship("Bill", back_populates="amendments")

class Supplement(Base):
    __tablename__ = "supplements"
    id = Column(Integer, primary_key=True)
    # Placeholder; expand as needed (e.g., supplement_id, type, date, title, url)

    bill_id = Column(Integer, ForeignKey("bills.id"))
    bill = relationship("Bill", back_populates="supplements")

class Sast(Base):
    __tablename__ = "sasts"
    id = Column(Integer, primary_key=True)
    type_id = Column(Integer)
    type = Column(String)
    sast_bill_number = Column(String)
    sast_bill_id = Column(Integer)

    bill_id = Column(Integer, ForeignKey("bills.id"))
    bill = relationship("Bill", back_populates="sasts")

class FollowedBill(Base):
    __tablename__ = "followed_bills"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    bill_id = Column(Integer, ForeignKey("bills.id"))

    user = relationship("User", back_populates="followed_bills")
    bill = relationship("Bill")  # Added for easier querying