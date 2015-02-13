from service import db
from sqlalchemy.dialects.postgresql import JSON

class TitleRegisterData(db.Model):
    title_number = db.Column(db.String(10), primary_key=True)
    register_data = db.Column(JSON)
    geometry_data = db.Column(JSON)

    def __str__(self):
        return '<TitleRegisterData {}>'.format(self.title_number)
