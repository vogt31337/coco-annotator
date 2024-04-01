from werkzeug.security import generate_password_hash

from backend.database import UserModel
from backend.webserver.variables import responses, PageDataModel

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..util.query_util import fix_ids

# api = Namespace('admin', description='Admin related operations')
#
# users = reqparse.RequestParser()
# users.add_argument('limit', type=int, default=50)
# users.add_argument('page', type=int, default=1)
#
# create_user = reqparse.RequestParser()
# create_user.add_argument('name', default="", location='json')
# create_user.add_argument('password', default="", location='json')
#
# register = reqparse.RequestParser()
# register.add_argument('username', required=True, location='json')
# register.add_argument('password', required=True, location='json')
# register.add_argument('email', location='json')
# register.add_argument('name', location='json')
# register.add_argument('isAdmin', type=bool, default=False, location='json')

router = APIRouter()


@router.get('/admin/users', responses=responses)
async def get_users(page_data: PageDataModel):
    """ Get list of all users """

    if not current_user.is_admin:
        raise HTTPException(status_code=401, detail="Access denied")
        # return {"success": False, "message": "Access denied"}, 401

    per_page = page_data.limit
    page = page_data.page - 1

    user_model = UserModel.objects
    total = user_model.count()
    pages = int(total/per_page) + 1

    user_model = user_model.skip(page*per_page).limit(per_page).exclude("preferences", "password")

    return {
        "total": total,
        "pages": pages,
        "page": page,
        "per_page": per_page,
        "users": fix_ids(user_model.all())
    }


class Register(BaseModel):
    username: str
    password: str
    email: str | None = None
    name: str | None = None
    isAdmin: bool = False


@router.post('/admin/user', responses=responses)
async def create_user(user: Register):
        """ Create a new user """

        if not current_user.is_admin:
            raise HTTPException(status_code=401, detail="Access denied")
            #return {"success": False, "message": "Access denied"}, 401

        if UserModel.objects(username__iexact=user.username).first():
            raise HTTPException(status_code=400, detail='Username already exists.')
            #return {'success': False, 'message': 'Username already exists.'}, 400

        usermodel = UserModel()
        usermodel.username = user.username
        usermodel.password = generate_password_hash(user.password, method='sha256')
        usermodel.name = user.name
        usermodel.email = user.email
        usermodel.is_admin = user.isAdmin
        usermodel.save()

        user_json = fix_ids(current_user)
        del user_json['password']

        return {'success': True, 'user': user_json}


@router.get('/admin/user/{username}')
async def get_user(username: str):
    """ Get a users """

    if not current_user.is_admin:
        raise HTTPException(status_code=401, detail="Access denied")
        #return {"success": False, "message": "Access denied"}, 401

    user = UserModel.objects(username__iexact=username).first()
    if user is None:
        raise HTTPException(status_code=400, detail='Username already exists.')
        #return {"success": False, "message": "User not found"}, 400

    return fix_ids(user)


class UserData(BaseModel):
    name: str = ""
    password: str = ""


#@api.expect(create_user)
#@login_required
@router.patch('/admin/user/{username}')
async def update_user(username: str, user_data: UserData):
    """ Edit a user """

    if not current_user.is_admin:
        raise HTTPException(status_code=401, detail="Access denied")
        #return {"success": False, "message": "Access denied"}, 401

    user = UserModel.objects(username__iexact=username).first()
    if user is None:
        raise HTTPException(status_code=400, detail='User not found')
        #return {"success": False, "message": "User not found"}, 400

    args = create_user.parse_args()
    name = user_data.name
    if len(name) > 0:
        user.name = name

    password = user_data.password
    if len(password) > 0:
        user.password = generate_password_hash(password, method='sha256')

    user.save()

    return fix_ids(user)


#@login_required
@router.delete('/admin/user/{username}')
async def delete_user(username: str):
    """ Delete a user """

    if not current_user.is_admin:
        raise HTTPException(status_code=401, detail="Access denied")
        #return {"success": False, "message": "Access denied"}, 401

    user = UserModel.objects(username__iexact=username).first()
    if user is None:
        raise HTTPException(status_code=400, detail='User not found')
        #return {"success": False, "message": "User not found"}, 400

    user.delete()
    return {"success": True}