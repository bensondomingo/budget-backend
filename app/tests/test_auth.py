# pylint: disable=unused-argument
import pytest
from datetime import datetime

from jose import jwt
from fastapi.testclient import TestClient
from sqlalchemy.sql.expression import delete

from app.main import app
from app.auth import models as m_auth
from app.config import settings
from app.core.database import Base, engine, SessionLocal
from app.services.security import Password

client = TestClient(app)
url = 'http://localhost:8000'


@pytest.fixture(scope='module', autouse=True)
def setup_teardown_database():
    """
    Handles creation and cleanup of database
    """
    # Create database tables
    Base.metadata.create_all(engine)

    # Create test user
    user = m_auth.User()
    user.username = 'test'
    user.email = 'test@example.com'
    user.password = Password.hash('password')
    user.is_admin = True
    with SessionLocal() as db:
        db.add(user)
        db.commit()

    yield None
    Base.metadata.drop_all(engine)


class TestSignIn:

    def test_signin__test_user(self):
        resp = client.post(f'{url}/auth/signin', data={
            'username': 'test',
            'password': 'password'
        })
        assert resp.status_code == 202

        # test token payload
        data = resp.json()
        token = data.get('access_token')
        payload = jwt.decode(token, settings.SECRET_KEY,
                             settings.SECRET_ALGORITHM)
        # decode username
        assert payload.get('sub') == 'test'
        # decode token expiry
        exp = datetime.fromtimestamp(payload.get('exp')) - datetime.utcnow()
        assert exp.seconds // 60 >= settings.ACCESS_TOKEN_EXPIRE_MINUTES - 5

    def test_signin__user_not_registered(self):
        resp = client.post(f'{url}/auth/signin', data={
            'username': 'randomuser',
            'password': 'password'
        })
        assert resp.status_code == 401


class TestSignUp:

    @pytest.fixture(scope='function')
    def signup_cleanup(self):
        yield None
        stmt = delete(m_auth.User).where(m_auth.User.username != 'test')
        with SessionLocal() as db:
            db.execute(stmt)
            db.commit()

    def test_signup__passwords_mismatched(self):
        resp = client.post(f'{url}/auth/signup', json={
            'username': 'testx',
            'email': 'testx@example.com',
            'password': 'test1234',
            'password2': 'test1233'})
        detail = resp.json().get('detail')
        assert detail == "passwords don't match"
        assert resp.status_code == 400

    def test_signup__taken_username(self):
        resp = client.post(f'{url}/auth/signup', json={
            'username': 'test',
            'email': 'testx@example.com',
            'password': 'test1234',
            'password2': 'test1234'})
        detail = resp.json().get('detail')
        assert detail == 'username and/or email is not available'
        assert resp.status_code == 400

    def test_signup__taken_email(self):
        resp = client.post(f'{url}/auth/signup', json={
            'username': 'testx',
            'email': 'test@example.com',
            'password': 'test1234',
            'password2': 'test1234'})
        detail = resp.json().get('detail')
        assert detail == 'username and/or email is not available'
        assert resp.status_code == 400

    def test_signup__valid_inputs(self, signup_cleanup):
        resp = client.post(f'{url}/auth/signup', json={
            'username': 'new_user',
            'email': 'new_user@example.com',
            'password': 'test1234',
            'password2': 'test1234'})
        assert resp.status_code == 201

        resp = client.post(f'{url}/auth/signin', data={
            'username': 'new_user',
            'password': 'test1234'
        })
        assert resp.status_code == 202
