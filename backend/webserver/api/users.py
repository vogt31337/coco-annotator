# from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
# from flask_restplus import Namespace, Resource, reqparse

from backend.webserver.variables import responses, PageDataModel

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.database import UserModel
import backend.config as Config
from ..util.query_util import fix_ids

import logging
logger = logging.getLogger('gunicorn.error')

# api = Namespace('user', description='User related operations')
#
# register = reqparse.RequestParser()
# register.add_argument('username', required=True, location='json')
# register.add_argument('password', required=True, location='json')
# register.add_argument('email', location='json')
# register.add_argument('name', location='json')
#
# login = reqparse.RequestParser()
# login.add_argument('password', required=True, location='json')
# login.add_argument('username', required=True, location='json')
#
# set_password = reqparse.RequestParser()
# set_password.add_argument('password', required=True, location='json')
# set_password.add_argument('new_password', required=True, location='json')


router = APIRouter()

#@api.route('/')
#@login_required
@router.get('/user', responses=responses)
async def get_user():
    """ Get information of current user """
    if Config.LOGIN_DISABLED:
        return current_user.to_json()

    user_json = fix_ids(current_user)
    del user_json['password']

    return {'user': user_json}


class SetPasswordModel(BaseModel):
    password: str
    new_password: str

#@api.route('/password')
#@login_required
#@api.expect(register)
@router.post('/user', responses=responses)
def post_new_password(set_password: SetPasswordModel):
    """ Set password of current user """
    args = set_password.parse_args()

    if check_password_hash(current_user.password, args.get('password')):
        current_user.update(password=generate_password_hash(args.get('new_password'), method='sha256'), new=False)
        return {'success': True}

    return {'success': False, 'message': 'Password does not match current passowrd'}, 400


class RegisterModelData(BaseModel):
    username: str
    password: str
    email: str
    name: str

#@api.route('/register')
#@api.expect(register)
@router.post('/user/register', responses=responses)
def create_user(register: RegisterModelData):
    """ Creates user """

    users = UserModel.objects.count()

    if not Config.ALLOW_REGISTRATION and users != 0:
        return {'success': False, 'message': 'Registration of new accounts is disabled.'}, 400

    username = register.username

    if UserModel.objects(username__iexact=username).first():
        return {'success': False, 'message': 'Username already exists.'}, 400

    user = UserModel()
    user.username = register.username
    user.password = generate_password_hash(register.password, method='sha256')
    user.name = register.name
    user.email = register.email
    if users == 0:
        user.is_admin = True
    user.save()

    login_user(user)

    user_json = fix_ids(current_user)
    del user_json['password']

    return {'success': True, 'user': user_json}


class LoginDataModel(BaseModel):
    username: str
    password: str

#@api.route('/login')
#@api.expect(login)
@router.post('/user/login', responses=responses)
def login(login: LoginDataModel):
    """ Logs user in """
    username = login.username

    user = UserModel.objects(username__iexact=username).first()
    if user is None:
        return {'success': False, 'message': 'Could not authenticate user'}, 400

    if check_password_hash(user.password, login.password):
        login_user(user)

        user_json = fix_ids(current_user)
        del user_json['password']

        logger.info(f'User {current_user.username} has LOGIN')

        return {'success': True, 'user': user_json}

    return {'success': False, 'message': 'Could not authenticate user'}, 400


#@api.route('/logout')
#@login_required
@router.get('/users/logout', responses=responses)
def logout():
    """ Logs user out """
    logger.info(f'User {current_user.username} has LOGOUT')
    logout_user()
    return {'success': True}

