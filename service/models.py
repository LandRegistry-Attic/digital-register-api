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


class UserSearchAndResults(db.Model):  # type: ignore
    """
    Store details of user view (for audit purposes) and update after payment (for reconciliation).
    """

    # As several users may be viewing at the same time, we need a compound primary key.
    # Note that WebSeal prevents a user from being logged in at multiple places concurrently.
    viewed_time = db.Column(db.DateTime(timezone=True), nullable=False, primary_key=True)
    user_id = db.Column(db.String(20), nullable=False, primary_key=True)
    title_number = db.Column(db.String(20), nullable=False)
    search_type = db.Column(db.String(20), nullable=False)
    purchase_type = db.Column(db.String(1), nullable=False)
    amount = db.Column(db.String(10), nullable=False)
    cart_id = db.Column(db.String(30), nullable=True)
    transaction_id = db.Column(db.String(30), nullable=True)     # Reconciliation: 'transId' from Worldpay.
