from sqlalchemy.dialects.postgresql import JSON, ARRAY  # type: ignore
from sqlalchemy import Index                     # type: ignore

from service import db


class TitleRegisterData(db.Model):  # type: ignore
    title_number = db.Column(db.String(10), primary_key=True)
    register_data = db.Column(JSON)
    geometry_data = db.Column(JSON)
    official_copy_data = db.Column(JSON)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    last_modified = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now(), nullable=False)
    lr_uprns = db.Column(ARRAY(db.String), default=[], nullable=False)


Index('idx_last_modified_and_title_number', TitleRegisterData.last_modified,
      TitleRegisterData.title_number)

Index('idx_title_uprns', TitleRegisterData.lr_uprns, postgresql_using='gin')
