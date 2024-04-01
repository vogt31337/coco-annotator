#from flask_restplus import Namespace, Resource, reqparse
#from flask_login import login_required, current_user
from mongoengine.errors import NotUniqueError

from ..util.pagination_util import Pagination
from ..util import query_util
from backend.database import CategoryModel, AnnotationModel
from fastapi import APIRouter, HTTPException
from backend.webserver.variables import responses, PageDataModel
from pydantic import BaseModel

import datetime

# api = Namespace('category', description='Category related operations')
#
# create_category = reqparse.RequestParser()
# create_category.add_argument('name', required=True, location='json')
# create_category.add_argument('supercategory', location='json')
# create_category.add_argument('color', location='json')
# create_category.add_argument('metadata', type=dict, location='json')
# create_category.add_argument('keypoint_edges', type=list, default=[], location='json')
# create_category.add_argument('keypoint_labels', type=list, default=[], location='json')
# create_category.add_argument('keypoint_colors', type=list, default=[], location='json')
#
# update_category = reqparse.RequestParser()
# update_category.add_argument('name', required=True, location='json')
# update_category.add_argument('supercategory', location='json')
# update_category.add_argument('color', location='json')
# update_category.add_argument('metadata', type=dict, location='json')
# update_category.add_argument('keypoint_edges', type=list, location='json')
# update_category.add_argument('keypoint_labels', type=list, location='json')
# update_category.add_argument('keypoint_colors', type=list, location='json')
#
# page_data = reqparse.RequestParser()
# page_data.add_argument('page', default=1, type=int)
# page_data.add_argument('limit', default=20, type=int)

router = APIRouter()

#@login_required
@router.get('/category', responses=responses)
async def get_categories():
    """ Returns all categories """
    return query_util.fix_ids(current_user.categories.all())

class CategoryModel(BaseModel):
    name: str
    supercategory: str | None = None
    color: str | None = None
    metadata: dict | None = None
    keypoint_edges: list = []
    keypoint_labels: list = []
    keypoint_colors: list = []

#@api.expect(create_category)
#@login_required
@router.post('/category', responses=responses)
async def create_category(create_category: CategoryModel):
    """ Creates a category """

    name = create_category.name
    supercategory = create_category.supercategory
    metadata = create_category.metadata
    color = create_category.color
    keypoint_edges = create_category.keypoint_edges
    keypoint_labels = create_category.keypoint_labels
    keypoint_colors = create_category.keypoint_colors

    try:
        category = CategoryModel(
            name=name,
            supercategory=supercategory,
            color=color,
            metadata=metadata,
            keypoint_edges=keypoint_edges,
            keypoint_labels=keypoint_labels,
            keypoint_colors=keypoint_colors,
        )
        category.save()
    except NotUniqueError as e:
        return {'message': 'Category already exists. Check the undo tab to fully delete the category.'}, 400

    return query_util.fix_ids(category)


#@login_required
@router.get('/category/{category_id}', responses=responses)
async def get_category(category_id: int):
    """ Returns a category by ID """
    category = current_user.categories.filter(id=category_id).first()

    if category is None:
        return {'success': False}, 400

    return query_util.fix_ids(category)

#@login_required
@router.delete('/category/{category_id}', responses=responses)
async def delete_category(category_id: int):
    """ Deletes a category by ID """
    category = current_user.categories.filter(id=category_id).first()
    if category is None:
        return {"message": "Invalid image id"}, 400

    if not current_user.can_delete(category):
        return {"message": "You do not have permission to delete this category"}, 403

    category.update(set__deleted=True,
                    set__deleted_date=datetime.datetime.now())
    return {'success': True}

#@api.expect(update_category)
#@login_required
@router.put('/category/{category_id}', responses=responses)
async def update_category(update_category: CategoryModel, category_id: int):
    """ Updates a category name by ID """
    category = current_user.categories.filter(id=category_id).first()

    # check if the id exits
    if category is None:
        return {"message": "Invalid category id"}, 400

    name = update_category.name
    supercategory = update_category.supercategory
    metadata = update_category.metadata
    color = update_category.color
    keypoint_edges = update_category.keypoint_edges
    keypoint_labels = update_category.keypoint_labels
    keypoint_colors = update_category.keypoint_colors

    # check if there is anything to update
    if category.name == name \
            and category.supercategory == supercategory \
            and category.color == color \
            and category.keypoint_edges == keypoint_edges \
            and category.keypoint_labels == keypoint_labels \
            and category.keypoint_colors == keypoint_colors:
        return {"message": "Nothing to update"}, 200

    # check if the name is empty
    if not name:
        return {"message": "Invalid category name to update"}, 400

    # update name of the category
    # check if the name to update exits already in db
    # @ToDo: Is it necessary to allow equal category names among different creators?
    category.name = name
    category.supercategory = supercategory
    category.color = color
    category.keypoint_edges = keypoint_edges
    category.keypoint_labels = keypoint_labels
    category.keypoint_colors = keypoint_colors

    try:
        category.update(
            name=category.name,
            supercategory=category.supercategory,
            color=category.color,
            metadata=category.metadata,
            keypoint_edges=category.keypoint_edges,
            keypoint_labels=category.keypoint_labels,
            keypoint_colors=category.keypoint_colors,
        )
    except NotUniqueError:
        # it is only triggered when the name already exists and the creator is the same
        return {"message": "Category '" + category.name + "' already exits"}, 400

    return {"success": True}


#@login_required
@router.get("/category/data")
async def get_data(page_data: PageDataModel):
    """ Endpoint called by category viewer client """
    limit = page_data.limit
    page = page_data.page

    categories = current_user.categories.filter(deleted=False)

    pagination = Pagination(categories.count(), limit, page)
    categories = query_util.fix_ids(
        categories[pagination.start:pagination.end])

    for category in categories:
        category['numberAnnotations'] = AnnotationModel.objects(
            deleted=False, category_id=category.get('id')).count()

    return {
        "pagination": pagination.export(),
        "page": page,
        "categories": categories
    }
