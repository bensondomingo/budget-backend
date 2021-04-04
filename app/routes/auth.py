from fastapi import APIRouter, Depends

from app.database import schemas as s
from app.dependecies import authenticate_user, create_user
from app.services.security import ban_token, create_access_token, oauth2_scheme

router = APIRouter(prefix='/auth', tags=['auth'])


@router.post('/signin', response_model=s.Token)
def signin(user: s.User = Depends(authenticate_user)):
    access_token = create_access_token(data={'sub': user.username})
    token = s.Token(access_token=access_token, token_type='bearer')
    return token


@router.post('/signup', response_model=s.Token)
def signup(user: s.User = Depends(create_user)):
    access_token = create_access_token(data={'sub': user.username})
    token = s.Token(access_token=access_token, token_type='bearer')
    return token


@router.post('/signout')
async def signout(token: str = Depends(oauth2_scheme)):
    t = s.BanToken(access_token=token, reason='signout')
    ban_token(t)
    return 'You have been successfully signed out'
