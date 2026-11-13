import pytest
from app import create_app
from models.db import db

class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GOOGLE_MAPS_API_KEY = 'test_dummy_key'
    SECRET_KEY = 'test-only-secret-that-is-long-enough'

@pytest.fixture
def app():
    app_inst = create_app(TestConfig)
    with app_inst.app_context():
        db.create_all()
        yield app_inst
        db.session.remove()
        db.engine.dispose()

@pytest.fixture
def client(app):
    return app.test_client()
