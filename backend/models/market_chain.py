from .db import db

class MarketChain(db.Model):
    __tablename__ = 'market_chain'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(50), nullable=False, unique=True)
    logo_url = db.Column(db.String(255), nullable=True)
    website = db.Column(db.String(255), nullable=True)

    branches = db.relationship('Branch', backref='market_chain', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'logo_url': self.logo_url,
            'website': self.website
        }
