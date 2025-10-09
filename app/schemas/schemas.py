# from pydantic import BaseModel
# from datetime import datetime
# from typing import Optional, List


# class BillBase(BaseModel):
#     id: str
#     state: str
#     title: str
#     status: str

# class BillCreate(BillBase):
#     raw_data: dict

# class Bill(BillBase):
#     summary: Optional[str] = None
#     ai_analysis: Optional[dict] = None
#     last_updated: datetime

#     class Config:
#         from_attributes = True

# class PostBase(BaseModel):
#     content: str
#     bill_id: str

# class PostCreate(PostBase):
#     pass

# class Post(PostBase):
#     id: int
#     user_id: int
#     upvotes: int
#     downvotes: int
#     created_at: datetime

#     class Config:
#         from_attributes = True

# class UserBase(BaseModel):
#     email: str
#     full_name: str

# class UserCreate(UserBase):
#     password: str

# class User(UserBase):
#     id: int
#     is_active: bool

#     class Config:
#         from_attributes = True



# # ========== Session ==========
# class SessionBase(BaseModel):
#     id: int
#     state_id: Optional[int]
#     year_start: Optional[int]
#     year_end: Optional[int]
#     session_tag: Optional[str]
#     session_title: Optional[str]
#     session_name: Optional[str]

#     class Config:
#         from_attributes = True


# # ========== Sponsor ==========
# class SponsorBase(BaseModel):
#     id: int
#     people_id: Optional[int]
#     name: Optional[str]
#     party: Optional[str]
#     role: Optional[str]
#     district: Optional[str]

#     class Config:
#         from_attributes = True


# # ========== Referral ==========
# class ReferralBase(BaseModel):
#     id: int
#     date: Optional[datetime]
#     committee_id: Optional[int]
#     chamber: Optional[str]
#     name: Optional[str]

#     class Config:
#         from_attributes = True


# # ========== Bill History ==========
# class BillHistoryBase(BaseModel):
#     id: int
#     date: Optional[datetime]
#     action: Optional[str]
#     chamber: Optional[str]
#     importance: Optional[int]

#     class Config:
#         from_attributes = True


# # ========== Bill Text ==========
# class BillTextBase(BaseModel):
#     id: int
#     doc_id: Optional[int]
#     date: Optional[datetime]
#     type: Optional[str]
#     url: Optional[str]
#     state_link: Optional[str]

#     class Config:
#         from_attributes = True


# # ========== Calendar Event ==========
# class CalendarEventBase(BaseModel):
#     id: int
#     type: Optional[str]
#     date: Optional[datetime]
#     time: Optional[str]
#     description: Optional[str]

#     class Config:
#         from_attributes = True


# # ========== Bill (Main Schema) ==========
# class BillBase(BaseModel):
#     id: int
#     bill_number: str
#     title: Optional[str]
#     description: Optional[str]
#     status: Optional[str]
#     status_date: Optional[datetime]
#     state: Optional[str]
#     url: Optional[str]
#     state_link: Optional[str]

#     session: Optional[SessionBase]
#     sponsors: List[SponsorBase] = []
#     referrals: List[ReferralBase] = []
#     history: List[BillHistoryBase] = []
#     texts: List[BillTextBase] = []
#     calendar: List[CalendarEventBase] = []

#     class Config:
#         from_attributes = True


# schemas.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime, date

class Session(BaseModel):
    id: int
    state_id: int
    year_start: int
    year_end: int
    prefile: int
    sine_die: int
    prior: int
    special: int
    session_tag: str
    session_title: str
    session_name: str

    class Config:
        from_attributes = True

class Sponsor(BaseModel):
    id: int
    people_id: int
    person_hash: str
    party_id: int
    party: str
    role_id: int
    role: str
    name: str
    first_name: str
    middle_name: str
    last_name: str
    suffix: str
    nickname: str
    district: str
    ftm_eid: int
    votesmart_id: int
    opensecrets_id: str
    knowwho_pid: int
    ballotpedia: str
    bioguide_id: str
    sponsor_type_id: int
    sponsor_order: int
    committee_sponsor: int
    committee_id: int
    state_federal: int

    class Config:
        from_attributes = True

class Referral(BaseModel):
    id: int
    date: Optional[datetime]
    committee_id: int
    chamber: str
    chamber_id: int
    name: str

    class Config:
        from_attributes = True

class BillHistory(BaseModel):
    id: int
    date: Optional[datetime]
    action: str
    chamber: str
    chamber_id: int
    importance: int

    class Config:
        from_attributes = True

class BillText(BaseModel):
    id: int
    doc_id: int
    date: Optional[datetime]
    type: str
    type_id: int
    mime: str
    mime_id: int
    url: str
    state_link: str
    text_size: int
    text_hash: str

    class Config:
        from_attributes = True

class CalendarEvent(BaseModel):
    id: int
    type_id: int
    type: str
    event_hash: str
    date: Optional[datetime]
    time: str
    location: str
    description: str

    class Config:
        from_attributes = True

class Sast(BaseModel):
    id: int
    type_id: int
    type: str
    sast_bill_number: str
    sast_bill_id: int

    class Config:
        from_attributes = True

class Bill(BaseModel):
    id: int  # Changed from str to int
    bill_number: str
    change_hash: str
    title: str
    description: str
    ai_summary: Optional[str] = None
    ai_impacts: Optional[List[Dict]] = None
    ai_pro_con: Optional[List[Dict]] = None
    raw_data: Dict
    last_updated: Optional[datetime] = None
    status: int  # Changed from str to int
    status_date: Optional[datetime] = None
    state: str
    url: str
    state_link: str
    completed: int
    bill_type: str
    bill_type_id: int
    body: str
    body_id: int
    current_body: str
    current_body_id: int
    pending_committee_id: int
    session: Optional[Session] = None
    sponsors: Optional[List[Sponsor]] = None
    referrals: Optional[List[Referral]] = None
    history: Optional[List[BillHistory]] = None
    texts: Optional[List[BillText]] = None
    calendar: Optional[List[CalendarEvent]] = None
    sasts: Optional[List[Sast]] = None

    class Config:
        from_attributes = True

class BillOut(BaseModel):
    bill_id: int = Field(..., alias="id") # Changed from id to bill_id as is from db
    number: str = Field(..., alias="bill_number")# Changed from bill_number to number as is from db
    change_hash: str
    url: str
    status_date: Optional[date]
    status: int
    last_action_date: Optional[date] = None
    last_action: Optional[str] = None
    title: str
    description: str

    class Config:
        from_attributes = True
        populate_by_name = True

class PaginatedBills(BaseModel):
    total: int
    limit: int
    offset: int
    next_offset: Optional[int]
    prev_offset: Optional[int]
    bills: List[BillOut]

class StateBillCount(BaseModel):
    state: str
    name: str
    active_bills: int