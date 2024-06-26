from LarpBook import db
from LarpBook.Utils.serialise_models import SerializerMixin

class PaymentMethod(db.Model, SerializerMixin):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    payment_method = db.Column(db.String(100), nullable=False)
    card_number = db.Column(db.String(100), nullable=False)
    expiry_date = db.Column(db.String(100), nullable=False)
    cvv = db.Column(db.String(100), nullable=False)
    billing_address = db.Column(db.String(100), nullable=False)
    billing_postcode = db.Column(db.String(100), nullable=False)
    billing_city = db.Column(db.String(100), nullable=False)
    billing_country = db.Column(db.String(100), nullable=False)