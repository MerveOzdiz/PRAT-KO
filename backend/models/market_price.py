import datetime
from .db import db

class MarketPrice(db.Model):
    __tablename__ = 'market_price'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'), nullable=False)
    price = db.Column(db.Float, nullable=False)
    original_price = db.Column(db.Float, nullable=True)
    currency = db.Column(db.String(10), default='TRY')
    is_in_stock = db.Column(db.Boolean, default=True)
    is_mock = db.Column(db.Boolean, default=True)
    source = db.Column(db.String(100), default='DEMO_MOCK_DATA')
    last_updated = db.Column(db.DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'branch_id': self.branch_id,
            'price': self.price,
            'original_price': self.original_price,
            'currency': self.currency,
            'is_in_stock': self.is_in_stock,
            'is_mock': self.is_mock,
            'source': self.source,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }
