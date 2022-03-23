import logging
from typing import List


from fastapi import (
    APIRouter,
    Response,
    Request,
    Depends,
    Path,
)
from pydantic.types import UUID


from . import default_get_responses
from .. import models
from ..storage import StorageInterface


router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/", response_model=List[models.StoredSystemGroup], responses=default_get_responses
)
async def list_system_groups(
    storage: StorageInterface = Depends(StorageInterface),
) -> List[models.StoredPVSystem]:
    """List available system groups"""
    with storage.start_transaction() as st:
        out: List[models.StoredSystemGroup] = st.list_system_groups()
        return out


system_group_links = {
    "Get System Group": {
        "operationId": "get_system_group_groups__group_id__get",
        "parameters": {"system_id": "$response.body#/object_id"},
    },
    "Delete System Group": {
        "operationId": "delete_system_group_groups__group_id__delete",
        "parameters": {"system_id": "$response.body#/object_id"},
    },
    "Update System Group": {
        "operationId": "update_group_groups__group_id__post",
        "parameters": {"system_id": "$response.body#/object_id"},
    },
}


@router.post(
    "/",
    response_model=models.StoredObjectID,
    responses={
        **default_get_responses,
        409: {},
        201: {"links": system_group_links},
    },
    status_code=201,
)
async def create_system_group(
    system_group: models.BaseSystemGroup,
    response: Response,
    request: Request,
    storage: StorageInterface = Depends(StorageInterface),
) -> models.StoredObjectID:
    """Create a new System Group"""
    with storage.start_transaction() as st:
        name = system_group.name
        id_: models.StoredObjectID = st.create_system_group(name)
        response.headers["Location"] = request.url_for(
            "get_system_group", group_id=id_.object_id
        )
        return id_


grouppath = Path(..., description="ID of system group to get", example=models.SYSTEM_ID)
syspath = Path(..., description="ID of a system", example=models.SYSTEM_ID)


@router.get(
    "/{group_id}",
    response_model=models.StoredSystemGroup,
    responses={
        **default_get_responses,
        200: {"links": system_group_links},
    },
)
async def get_system_group(
    group_id: UUID = grouppath,
    storage: StorageInterface = Depends(StorageInterface),
) -> models.StoredSystemGroup:
    """Get a single System Group"""
    with storage.start_transaction() as st:
        out: models.StoredSystemGroup = st.get_system_group(group_id)
    return out


@router.delete(
    "/{group_id}",
    response_class=Response,
    responses={**default_get_responses, 204: {}},
    status_code=204,
)
async def delete_system_group(
    group_id: UUID = grouppath,
    storage: StorageInterface = Depends(StorageInterface),
):
    """Delete a System Group"""
    with storage.start_transaction() as st:
        st.delete_system_group(group_id)


@router.post(
    "/{group_id}",
    response_model=models.StoredObjectID,
    responses={
        **default_get_responses,
        409: {},
        201: {"links": system_group_links},
    },
    status_code=201,
)
async def update_system_group(
    system_group: models.BaseSystemGroup,
    response: Response,
    request: Request,
    group_id: UUID = grouppath,
    storage: StorageInterface = Depends(StorageInterface),
) -> models.StoredObjectID:
    """Update a System Group"""
    name = system_group.name
    with storage.start_transaction() as st:
        out: models.StoredObjectID = st.update_system_group(group_id, name)
        response.headers["Location"] = request.url_for(
            "get_system_group", group_id=group_id
        )
        return out


@router.post(
    "/{group_id}/systems/{system_id}",
    response_model=models.StoredObjectID,
    responses={
        **default_get_responses,
        409: {},
        201: {"links": system_group_links},
    },
    status_code=201,
)
async def add_system_to_group(
    response: Response,
    request: Request,
    group_id: UUID = grouppath,
    system_id: UUID = syspath,
    storage: StorageInterface = Depends(StorageInterface),
) -> models.StoredObjectID:
    """Add a system to a system group"""
    with storage.start_transaction() as st:
        out: models.StoredObjectID = st.add_system_to_group(system_id, group_id)
        response.headers["Location"] = request.url_for(
            "get_system_group", group_id=group_id
        )
        return out


@router.delete(
    "/{group_id}/systems/{system_id}",
    response_model=models.StoredObjectID,
    responses={
        **default_get_responses,
        409: {},
        201: {"links": system_group_links},
    },
    status_code=201,
)
async def remove_system_from_group(
    response: Response,
    request: Request,
    group_id: UUID = grouppath,
    system_id: UUID = syspath,
    storage: StorageInterface = Depends(StorageInterface),
) -> models.StoredObjectID:
    """Remove a system from a system group"""
    with storage.start_transaction() as st:
        out: models.StoredObjectID = st.remove_system_from_group(system_id, group_id)
        response.headers["Location"] = request.url_for(
            "get_system_group", group_id=group_id
        )
        return out
