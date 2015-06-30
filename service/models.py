from service import db
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy import Index


class TitleRegisterData(db.Model):
    title_number = db.Column(db.String(10), primary_key=True)
    register_data = db.Column(JSON)
    geometry_data = db.Column(JSON)
    official_copy_data = db.Column(JSON)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    last_modified = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now(),
                              nullable=False)

Index('idx_last_modified_and_title_number', TitleRegisterData.last_modified,
      TitleRegisterData.title_number)
