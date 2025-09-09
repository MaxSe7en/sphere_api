from sqlalchemy import text
from app.db.session import get_db

def get_state_bills_raw_model(db, state: str, limit: int, offset: int):
    sql = text("""
        SELECT 
            b.id AS bill_id,
            b.bill_number AS number,
            b.change_hash,
            b.url,
            b.status_date,
            b.status,
            b.title,
            b.description,
            h.date AS last_action_date,
            h.action AS last_action
        FROM bills b
        LEFT JOIN bill_history h
            ON h.bill_id = b.id
           AND h.date = (
               SELECT MAX(date)
               FROM bill_history
               WHERE bill_id = b.id
           )
        WHERE b.state = :state
        ORDER BY b.id
        LIMIT :limit OFFSET :offset;
    """)
    result = db.execute(sql, {"state": state, "limit": limit, "offset": offset})
    return [dict(row._mapping) for row in result]
