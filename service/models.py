from service import db
from sqlalchemy.dialects.postgresql import JSON


class TitleRegisterData(db.Model):
    title_number = db.Column(db.String(10), primary_key=True)
    register_data = db.Column(JSON)
    geometry_data = db.Column(JSON)


class TitleNumbersUprns(db.Model):
    __tablename__ = 'title_numbers_uprns'
    title_number = db.Column(db.String(10))
    uprn = db.Column(db.Integer, primary_key=True)
