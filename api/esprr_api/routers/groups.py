import logging
from tkinter import W
from typing import List, Optional, Union
import weakref


from fastapi import (
    APIRouter,
    Header,
    Response,
    Request,
    Depends,
    Path,
    HTTPException
)
import pandas as pd
from pydantic.types import UUID


from . import default_get_responses
from .. import models, utils
from ..storage import StorageInterface
from ..queuing import QueueManager


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


datasetpath = Path(
    ...,
    description="Background dataset used to compute expected power",
    example="NSRDB_2019",
)


@router.get(
    "/{group_id}/data/{dataset}",
    response_model=models.SystemGroupDataMeta,
    responses=default_get_responses,
)
async def get_group_model_status(
    group_id: UUID = grouppath,
    dataset: models.DatasetEnum = datasetpath,
    storage: StorageInterface = Depends(StorageInterface),
    qm: QueueManager = Depends(QueueManager),
) -> models.SystemGroupDataMeta:
    """Get status of model data for each system in the group"""
    with storage.start_transaction() as st:
        group: models.StoredSystemGroup = st.get_system_group(group_id)
    data_status = {}
    for system in group.definition.systems:
        system_id = system.object_id
        with storage.start_transaction() as st:
            try:
                out: models.SystemDataMeta = st.get_system_model_meta(system_id, dataset)
            except HTTPException as e:
                continue
        if out.status == "queued":
            # if queued/prepared and job started by q, "running"
            if qm.job_is_running(system_id, dataset):
                out.status = models.DataStatusEnum("running")
        data_status[system_id] = out.dict()
    group_data_meta = models.SystemGroupDataMeta(
      modified_at=group.modified_at,
      created_at=group.created_at,
      object_id=group.object_id,
      system_data_status=data_status,
    )
    return group_data_meta


@router.get(
    "/{group_id}/data/{dataset}/timeseries",
    responses={
        **default_get_responses,
        406: {},
        200: {
            "content": {
                "application/vnd.apache.arrow.file": {},
                "text/csv": {
                    "example": """time,ac
2019-01-01 00:00:00-07:00,10.2
2019-02-01 00:00:00-07:00,8.2
"""
                },
            },
            "description": (
                "Return the timeseries data as an Apache Arrow file or a CSV."
            ),
        },
    },
)
def get_group_model_timeseries(
    group_id: UUID = grouppath,
    dataset: models.DatasetEnum = datasetpath,
    storage: StorageInterface = Depends(StorageInterface),
    accept: Optional[str] = Header(None),
) -> Union[utils.CSVResponse, utils.ArrowResponse]:
    resp, meta_type = utils._get_return_type(accept)
    with storage.start_transaction() as st:
        group: models.StoredSystemGroup = st.get_system_group(group_id)
    group_data = []
    for system in group.definition.systems:
        system_id = system.object_id
        with storage.start_transaction() as st:
            data = st.get_system_model_timeseries(system_id, dataset)
            data = utils.read_arrow(data)
            data = data.set_index("time")
            csv_safe_name = system.definition.name.replace(",", "").replace(" ", "_")
            data = data.rename(
                columns={col: f"{csv_safe_name}_{col}" for col in data.columns})
            group_data.append(data)
    group_df = pd.concat(group_data, axis=1)

    clearsky_cols = [col for col in group_df.columns if "_clearsky_ac_power" in col]
    ac_power_cols = [col for col in group_df.columns if col not in clearsky_cols]

    group_df["ac_power"] = group_df[ac_power_cols].sum(axis=1)
    group_df["clearsky_ac_power"] = group_df[clearsky_cols].sum(axis=1)
    group_df["time"] = group_df.index.tz_convert(
        "Etc/GMT+7"
    )  # type: ignore
    if meta_type == "application/vnd.apache.arrow.file":
        resp_data = utils.dump_arrow_bytes(utils.convert_to_arrow(group_df))
        return resp(resp_data)
    else:
        csv = group_df.to_csv(None, index=False)
        return resp(csv)


@router.get(
    "/{group_id}/data/{dataset}/statistics",
    responses={
        **default_get_responses,
        406: {},
        200: {
            "content": {
                "application/vnd.apache.arrow.file": {},
                "text/csv": {},
            },
            "description": (
                "Return the statistics of the data as an Apache Arrow file or a CSV."
            ),
        },
    },
)
def get_group_model_statistics(
    group_id: UUID = grouppath,
    dataset: models.DatasetEnum = datasetpath,
    storage: StorageInterface = Depends(StorageInterface),
    accept: Optional[str] = Header(None),
) -> Union[utils.CSVResponse, utils.ArrowResponse]:
    resp, meta_type = utils._get_return_type(accept)
    with storage.start_transaction() as st:
        group: models.StoredSystemGroup = st.get_system_group(group_id)
    group_data = []
    for system in group.definition.systems:
        with storage.start_transaction() as st:
            system_id = system.object_id
            data = st.get_system_model_statistics(system_id, dataset)
            data = utils.read_arrow(data)
            group_data.append(data)
    group_df = pd.concat(group_data, axis=1)

    if meta_type == "application/vnd.apacke.arrow.file":
        resp_data = utils.convert_to_arrow(group_df)
        return resp(resp_data)
    else:
        if "time" in group_df.columns:
            group_df["time"] = group_df["time"].dt.tz_convert(
                "Etc/GMT+7"
            )  # type: ignore
        csv = group_df.to_csv(None, index=False)
        return resp(csv)
