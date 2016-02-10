from sqlalchemy.dialects.postgresql import JSON, ARRAY  # type: ignore
from sqlalchemy import Index                     # type: ignore

from service import db

# N.B.: 'Index' is only used if *additional* index required!
#       [Index is created automatically per 'primary_key' setting].


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


class UprnMapping(db.Model):  # type: ignore
    uprn = db.Column(db.String(20), primary_key=True)
    lr_uprn = db.Column(db.String(20), nullable=False)


class TitleSummaryView(db.Model):  # type: ignore
    """
    User can only access results of query if view is paid for, user is logged in and has not already viewed.
    """

    transaction_id = db.Column(db.String(30), nullable=False, primary_key=True)     # 'transId' from Worldpay.
    title_number = db.Column(db.String(20), nullable=False)
    viewed_time = db.Column(db.DateTime(timezone=True), nullable=True)
    user_id = db.Column(db.String(20), nullable=False)
