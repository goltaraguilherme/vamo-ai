from flask_sqlalchemy import SQLAlchemy
import datetime

db = SQLAlchemy()

class BaseModel(db.Model):
    """Base data model for all objects"""
    __abstract__ = True
    def __init__(self, *args):
            super().__init__(*args)
    def __repr__(self):
            """Define a base way to print models"""
            return '%s(%s)' % (self.__class__.__name__, {
                column: value
                for column, value in self._to_dict().items()
            })
    def json(self):
            """
                    Define a base way to jsonify models, dealing with datetime objects
            """
            return {
                column: value if not isinstance(value, datetime.date) else value.strftime('%Y-%m-%d')
                for column, value in self._to_dict().items()
            }
    
class Chats(db.Model):
    __tablename__ = 'chats'
    id = db.Column(db.Integer, primary_key=True)
    state = db.Column(db.Integer, nullable=False)
    number = db.Column(db.String, nullable=False)
    preferences = db.Column(db.String, nullable=True)
    company = db.Column(db.String, nullable=True)
    days = db.Column(db.String, nullable=True)
    cities = db.Column(db.String, nullable=True)
    path_roteiro = db.Column(db.String, nullable=True)

    def __init__(self, state, number, preferences=None, company=None, days=None, cities=None, path_roteiro=None):
        self.state = state
        self.number = number
        self.preferences = preferences
        self.company = company
        self.days = days
        self.cities = cities
        self.path_roteiro = path_roteiro

    def to_dict(self):
        return {
            'id': self.id,
            'state': self.state,
            'number': self.number,
            'preferences': self.preferences,
            'company': self.company,
            'days': self.days,
            'cities': self.cities,
            'path_roteiro': self.path_roteiro
        }

class Messages(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    wpp_id = db.Column(db.String, nullable=False)

    def __init__(self, wpp_id):
        self.wpp_id = wpp_id
    
    def to_dict(self):
        return {
             'id': self.id,
             'wpp_id': self.wpp_id
        }