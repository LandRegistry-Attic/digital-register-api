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
    lr_uprns = db.Column(ARRAY(db.String), default=[], nullable=True)


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

    # As several users may be searching at the same time, we need a compound primary key.
    # Note that WebSeal prevents a user from being logged in from multiple places concurrently.
    search_datetime = db.Column(db.DateTime(), nullable=False, primary_key=True)
    user_id = db.Column(db.String(20), nullable=False, primary_key=True)
    title_number = db.Column(db.String(20), nullable=False)
    search_type = db.Column(db.String(20), nullable=False)
    purchase_type = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.String(10), nullable=False)
    cart_id = db.Column(db.String(30), nullable=True)

    # Post-payment items: these (or the like) are also held in the 'transaction_data' DB.
    # TODO: Ideally they should be fetched from there instead, via the 'search_datetime' key.
    lro_trans_ref = db.Column(db.String(30), nullable=True)                # Reconciliation: 'transId' from Worldpay.
    viewed_datetime = db.Column(db.DateTime(), nullable=True)              # If null, user has yet to view the results.
    valid = db.Column(db.Boolean, default=False)

    def __init__(self,
                 search_datetime,
                 user_id,
                 title_number,
                 search_type,
                 purchase_type,
                 amount,
                 cart_id,
                 lro_trans_ref,
                 viewed_datetime,
                 valid
                 ):
        self.search_datetime = search_datetime
        self.user_id = user_id
        self.title_number = title_number
        self.search_type = search_type
        self.purchase_type = purchase_type
        self.amount = amount
        self.cart_id = cart_id

        self.lro_trans_ref = lro_trans_ref
        self.viewed_datetime = viewed_datetime
        self.valid = valid

    # This is for serialisation purposes; it returns the arguments used and their values as a dict.
    # Note that __dict__ only works well in this case if no other local variables are defined.
    # "marshmallow" may be an alternative: https://marshmallow.readthedocs.org/en/latest.
    def get_dict(self):
        return self.__dict__

    def id(self):
        return '<lro_trans_ref {}>'.format(self.lro_trans_ref)


Index('idx_title_number', UserSearchAndResults.title_number)


class Validation(db.Model):  # type: ignore
    """ Store of price etc., for anti-fraud purposes """

    __tablename__ = 'validation'
    price = db.Column(db.Integer, nullable=False, default=300, primary_key=True)
    product = db.Column(db.String(20), default="drvSummary")        # purchase_type
