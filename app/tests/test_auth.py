# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
from datetime import datetime, timedelta
from time import sleep as delay
import pytest

from jose import jwt
from fastapi import status, Depends, HTTPException
from fastapi.testclient import TestClient
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.sql.expression import delete, select

from app.main import app
from app.auth import models as m_auth
from app.config import settings
from app.core.database import AsyncSession, Base, engine, SessionLocal
from app.dependecies import authenticate_user, get_async_db
from app.services.security import Password

client = TestClient(app)
url = f'http://{settings.SERVER_HOST}:{settings.SERVER_PORT}'


@pytest.fixture(scope='module', autouse=True)
def setup_teardown_database():
    """
    Handles creation and cleanup of database
    """
    # Create database tables
    Base.metadata.create_all(engine)

    # Create test users
    admin_user = m_auth.User()
    admin_user.username = 'admin'
    admin_user.email = 'admin@example.com'
    admin_user.password = Password.hash('password')
    admin_user.is_admin = True

    test_user = m_auth.User()
    test_user.username = 'test'
    test_user.email = 'test@example.com'
    test_user.password = Password.hash('password')
    with SessionLocal() as db:
        db.add(admin_user)
        db.add(test_user)
        db.commit()

    yield None
    Base.metadata.drop_all(engine)


@ pytest.fixture(scope='function')
def signup_cleanup():
    yield None
    stmt = delete(m_auth.User).where(
        ~m_auth.User.username.in_(['admin', 'test']))
    with SessionLocal() as db:
        db.execute(stmt)
        db.commit()


@pytest.fixture(scope='function')
def shorten_token_validity():
    """
    Shorten token life for token expiry testing
    """
    async def test_authenticate_user(
            db: AsyncSession = Depends(get_async_db),
            form_data: OAuth2PasswordRequestForm = Depends()) -> str:
        username = form_data.username
        password = form_data.password
        exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

        stmt = select(m_auth.User).where(m_auth.User.username == username)
        result = (await db.execute(stmt)).one_or_none()
        if result is None:
            raise exception

        db_user: m_auth.User = result.User
        if not Password.verify(password, db_user.password):
            raise exception

        payload = {
            'sub': db_user.username,
            'exp': datetime.utcnow() + timedelta(seconds=2)}
        return jwt.encode(
            payload, settings.SECRET_KEY, settings.SECRET_ALGORITHM)

    app.dependency_overrides[authenticate_user] = test_authenticate_user
    yield
    app.dependency_overrides[authenticate_user] = authenticate_user


class TestUsers:

    url = f'{url}/users'

    def test_users__read_me__auth(self):
        with TestClient(app) as c:
            resp = c.post(f'{url}/auth/signin', data={
                'username': 'test',
                'password': 'password'
            })
            assert resp.status_code == status.HTTP_202_ACCEPTED
            token = resp.json().get('access_token')
            assert token is not None
            print(token)

            resp = c.get(f'{self.url}/me',
                         headers={'Authorization': f'Bearer {token}'})
            assert resp.status_code == status.HTTP_200_OK
            assert resp.json().get('username') == 'test'

    def test_users__read_me__no_auth(self):
        resp = client.get(f'{self.url}/me')
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
        assert resp.json().get('username') is None

    def test_users__read_all__admin(self):
        with TestClient(app) as c:
            resp = c.post(f'{url}/auth/signin', data={
                'username': 'admin',
                'password': 'password'})
            assert resp.status_code == status.HTTP_202_ACCEPTED
            token = resp.json().get('access_token')

            resp = c.get(self.url, headers={
                'Authorization': f'Bearer {token}'})
            assert resp.status_code == status.HTTP_200_OK
            assert len(resp.json()) == 2

    def test_users__read_all__non_admin(self):
        with TestClient(app) as c:
            resp = c.post(f'{url}/auth/signin', data={
                'username': 'test',
                'password': 'password'})
            assert resp.status_code == status.HTTP_202_ACCEPTED
            token = resp.json().get('access_token')

            resp = c.get(self.url, headers={
                'Authorization': f'Bearer {token}'})
            assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_users__delete__with_admin_access(self, signup_cleanup):
        # create a new user then delete it using admin account
        with TestClient(app) as c:
            resp = c.post(f'{url}/auth/signup', json={
                'username': 'new_user',
                'email': 'new_user@example.com',
                'password': 'test1234',
                'password2': 'test1234'})
            assert resp.status_code == status.HTTP_201_CREATED
            new_user_token = resp.json().get('access_token')

            # get user details
            resp = c.get(f'{self.url}/me',
                         headers={'Authorization': f'Bearer {new_user_token}'})
            assert resp.status_code == status.HTTP_200_OK
            new_user_id = resp.json().get('id')

            # admin signin
            resp = c.post(f'{url}/auth/signin', data={
                'username': 'admin',
                'password': 'password'})
            assert resp.status_code == status.HTTP_202_ACCEPTED
            token = resp.json().get('access_token')

            # delete user
            resp = c.delete(f'{self.url}/{new_user_id}',
                            headers={'Authorization': f'Bearer {token}'})
            assert resp.status_code == status.HTTP_204_NO_CONTENT

    def test_users__delete__no_admin_access(self, signup_cleanup):
        # create a new user then delete it using non admin account
        with TestClient(app) as c:
            resp = c.post(f'{url}/auth/signup', json={
                'username': 'new_user',
                'email': 'new_user@example.com',
                'password': 'test1234',
                'password2': 'test1234'})
            assert resp.status_code == status.HTTP_201_CREATED
            new_user_token = resp.json().get('access_token')

            # get user details
            resp = c.get(f'{self.url}/me',
                         headers={'Authorization': f'Bearer {new_user_token}'})
            assert resp.status_code == status.HTTP_200_OK
            new_user_id = resp.json().get('id')

            # non admin signin
            resp = c.post(f'{url}/auth/signin', data={
                'username': 'test',
                'password': 'password'})
            assert resp.status_code == status.HTTP_202_ACCEPTED
            token = resp.json().get('access_token')

            # delete user
            resp = c.delete(f'{self.url}/{new_user_id}',
                            headers={'Authorization': f'Bearer {token}'})
            assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_users__change_password(self):
        with TestClient(app) as c:
            resp = c.post(f'{url}/auth/signin', data={
                'username': 'test',
                'password': 'password'})
            assert resp.status_code == status.HTTP_202_ACCEPTED
            token = resp.json().get('access_token')

            resp = c.patch(f'{self.url}/me/password',
                           json={'password': 'test12345',
                                 'password2': 'test12345'},
                           headers={'Authorization': f'Bearer {token}'})
            assert resp.status_code == status.HTTP_200_OK

            resp = c.patch(f'{self.url}/me/password',
                           json={'password': 'password',
                                 'password2': 'password'},
                           headers={'Authorization': f'Bearer {token}'})
            assert resp.status_code == status.HTTP_200_OK

    def test_users__change_password__dont_match(self):
        with TestClient(app) as c:
            resp = c.post(f'{url}/auth/signin', data={
                'username': 'test',
                'password': 'password'})
            assert resp.status_code == status.HTTP_202_ACCEPTED
            token = resp.json().get('access_token')

            resp = c.patch(f'{self.url}/me/password',
                           json={'password': 'test12345',
                                 'password2': 'test123'},
                           headers={'Authorization': f'Bearer {token}'})
            assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestSignIn:

    url = f'{url}/auth/signin'

    def test_signin__test_user(self):
        resp = client.post(self.url, data={
            'username': 'test',
            'password': 'password'
        })
        assert resp.status_code == status.HTTP_202_ACCEPTED

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
        resp = client.post(self.url, data={
            'username': 'randomuser',
            'password': 'password'
        })
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_signin__expired_token(self, shorten_token_validity):
        with TestClient(app) as c:
            resp = c.post(self.url, data={
                'username': 'test',
                'password': 'password'
            })
            assert resp.status_code == status.HTTP_202_ACCEPTED
            token = resp.json().get('access_token')

            resp = c.get(f'{url}/users/me',
                         headers={'Authorization': f'Bearer {token}'})
            assert resp.status_code == status.HTTP_200_OK

            delay(3)  # simulate token aging
            resp = c.get(f'{url}/users/me',
                         headers={'Authorization': f'Bearer {token}'})
            assert resp.status_code == status.HTTP_401_UNAUTHORIZED


class TestSignUp:

    url = f'{url}/auth/signup'

    def test_signup__passwords_dont_match(self):
        resp = client.post(self.url, json={
            'username': 'testx',
            'email': 'testx@example.com',
            'password': 'test1234',
            'password2': 'test1233'})
        detail = resp.json().get('detail')
        assert detail == "passwords don't match"
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_signup__taken_username(self):
        resp = client.post(self.url, json={
            'username': 'test',
            'email': 'testx@example.com',
            'password': 'test1234',
            'password2': 'test1234'})
        detail = resp.json().get('detail')
        assert detail == 'username and/or email is not available'
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_signup__taken_email(self):
        resp = client.post(self.url, json={
            'username': 'testx',
            'email': 'test@example.com',
            'password': 'test1234',
            'password2': 'test1234'})
        detail = resp.json().get('detail')
        assert detail == 'username and/or email is not available'
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_signup__valid_inputs(self, signup_cleanup):
        resp = client.post(self.url, json={
            'username': 'new_user',
            'email': 'new_user@example.com',
            'password': 'test1234',
            'password2': 'test1234'})
        assert resp.status_code == status.HTTP_201_CREATED

        resp = client.post(f'{url}/auth/signin', data={
            'username': 'new_user',
            'password': 'test1234'
        })
        assert resp.status_code == status.HTTP_202_ACCEPTED


class TestSignOut:

    url = f'{url}/auth/signout'

    def test_signout__signedin_user(self):
        with TestClient(app) as c:
            # Signin
            resp = c.post(f'{url}/auth/signin', data={
                'username': 'test',
                'password': 'password'
            })
            assert resp.status_code == status.HTTP_202_ACCEPTED
            token = resp.json().get('access_token')  # Get token

            # Access an auth protected endpoint
            resp = c.get(f'{url}/users/me',
                         headers={'Authorization': f'Bearer {token}'})
            assert resp.status_code == status.HTTP_200_OK

            # Signout
            resp = c.post(self.url,
                          headers={'Authorization': f'Bearer {token}'})
            assert resp.status_code == status.HTTP_204_NO_CONTENT

            # Retry access on auth protected input.
            # Request should be rejected
            resp = c.get(f'{url}/users/me',
                         headers={'Authorization': f'Bearer {token}'})
            assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_signout__not_authenticated_user(self):
        with TestClient(app) as c:
            resp = c.post(self.url)
            assert resp.status_code == status.HTTP_401_UNAUTHORIZED
