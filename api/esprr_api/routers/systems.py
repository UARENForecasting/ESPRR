import logging
from typing import List, Optional, Tuple, Type, Union


from accept_types import AcceptableType  # type: ignore
from fastapi import (
    APIRouter,
    Response,
    Request,
    Depends,
    Path,
    Header,
    HTTPException,
    BackgroundTasks,
)
from pydantic.types import UUID


from . import default_get_responses
from .. import models, utils
from ..auth import get_user_id
from ..queuing import QueueManager
from ..storage import StorageInterface


router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/", response_model=List[models.StoredPVSystem], responses=default_get_responses
)
async def list_systems(
    storage: StorageInterface = Depends(StorageInterface),
) -> List[models.StoredPVSystem]:
    """List available PV systems"""
    with storage.start_transaction() as st:
        out: List[models.StoredPVSystem] = st.list_systems()
        return out


system_links = {
    "Get System": {
        "operationId": "get_system_systems__system_id__get",
        "parameters": {"system_id": "$response.body#/object_id"},
    },
    "Delete System": {
        "operationId": "delete_system_systems__system_id__delete",
        "parameters": {"system_id": "$response.body#/object_id"},
    },
    "Update System": {
        "operationId": "update_system_systems__system_id__post",
        "parameters": {"system_id": "$response.body#/object_id"},
    },
}


@router.post(
    "/",
    response_model=models.StoredObjectID,
    responses={
        **default_get_responses,
        409: {},
        201: {"links": system_links},
    },
    status_code=201,
)
async def create_system(
    system: models.PVSystem,
    response: Response,
    request: Request,
    storage: StorageInterface = Depends(StorageInterface),
) -> models.StoredObjectID:
    """Create a new PV System"""
    with storage.start_transaction() as st:
        id_: models.StoredObjectID = st.create_system(system)
        response.headers["Location"] = request.url_for(
            "get_system", system_id=id_.object_id
        )
        return id_


@router.post(
    "/check",
    responses={401: {}, 403: {}},
    status_code=200,
)
async def check_system(
    system: models.PVSystem,
):
    """Check if the POSTed system is valid for modeling"""
    return


syspath = Path(..., description="ID of system to get", example=models.SYSTEM_ID)


@router.get(
    "/{system_id}",
    response_model=models.StoredPVSystem,
    responses={
        **default_get_responses,
        200: {"links": system_links},
    },
)
async def get_system(
    system_id: UUID = syspath,
    storage: StorageInterface = Depends(StorageInterface),
) -> models.StoredPVSystem:
    """Get a single PV System"""
    with storage.start_transaction() as st:
        out: models.StoredPVSystem = st.get_system(system_id)
    return out


@router.delete(
    "/{system_id}",
    response_class=Response,
    responses={**default_get_responses, 204: {}},
    status_code=204,
)
async def delete_system(
    system_id: UUID = syspath,
    storage: StorageInterface = Depends(StorageInterface),
):
    """Delete a PV system"""
    with storage.start_transaction() as st:
        st.delete_system(system_id)


@router.post(
    "/{system_id}",
    response_model=models.StoredObjectID,
    responses={
        **default_get_responses,
        409: {},
        201: {"links": system_links},
    },
    status_code=201,
)
async def update_system(
    system: models.PVSystem,
    response: Response,
    request: Request,
    system_id: UUID = syspath,
    storage: StorageInterface = Depends(StorageInterface),
) -> models.StoredObjectID:
    """Update a PV System"""
    with storage.start_transaction() as st:
        out: models.StoredObjectID = st.update_system(system_id, system)
        response.headers["Location"] = request.url_for(
            "get_system", system_id=system_id
        )
        return out


datasetpath = Path(
    ...,
    description="Background dataset used to compute expected power",
    example="NSRDB_2019",
)


@router.get(
    "/{system_id}/data/{dataset}",
    response_model=models.SystemDataMeta,
    responses=default_get_responses,
)
async def get_system_model_status(
    system_id: UUID = syspath,
    dataset: models.DatasetEnum = datasetpath,
    storage: StorageInterface = Depends(StorageInterface),
    qm: QueueManager = Depends(QueueManager),
) -> models.SystemDataMeta:
    with storage.start_transaction() as st:
        out: models.SystemDataMeta = st.get_system_model_meta(system_id, dataset)
    if out.status == "queued":
        # if queued/prepared and job started by q, "running"
        if qm.job_is_running(system_id, dataset):
            out.status = models.DataStatusEnum("running")
    return out


@router.post(
    "/{system_id}/data/{dataset}",
    status_code=202,
    responses={**default_get_responses, 202: {}},
)
async def run_system_model(
    background_tasks: BackgroundTasks,
    system_id: UUID = syspath,
    dataset: models.DatasetEnum = datasetpath,
    storage: StorageInterface = Depends(StorageInterface),
    user: str = Depends(get_user_id),
    qm: QueueManager = Depends(QueueManager),
):
    with storage.start_transaction() as st:
        st.create_system_model_data(system_id, dataset)
    background_tasks.add_task(qm.enqueue_job, system_id, dataset, user)


class ArrowResponse(Response):
    media_type = "application/vnd.apache.arrow.file"


class CSVResponse(Response):
    media_type = "text/csv"


def _get_return_type(
    accept: Optional[str],
) -> Tuple[Union[Type[CSVResponse], Type[ArrowResponse]], str]:
    if accept is None:
        accept = "*/*"
    type_ = AcceptableType(accept)

    if type_.matches("text/csv"):
        return CSVResponse, "text/csv"
    elif type_.matches("application/vnd.apache.arrow.file"):
        return ArrowResponse, "application/vnd.apache.arrow.file"
    else:
        raise HTTPException(
            status_code=406,
            detail="Only 'text/csv' or 'application/vnd.apache.arrow.file' acceptable",
        )


def _convert_data(
    data: bytes,
    requested_mimetype: str,
    response_class: Union[Type[ArrowResponse], Type[CSVResponse]],
) -> Union[ArrowResponse, CSVResponse]:
    if requested_mimetype == "application/vnd.apache.arrow.file":
        return response_class(data)
    else:
        try:
            df = utils.read_arrow(data)  # type: ignore
        except HTTPException:
            logger.exception("Read arrow failed")
            raise HTTPException(
                status_code=500,
                detail=(
                    "Unable to convert data saved as Apache Arrow format, "
                    "try retrieving as application/vnd.apache.arrow.file and converting"
                ),
            )
        if "time" in df.columns:
            df["time"] = df["time"].dt.tz_convert("Etc/GMT+7")  # type: ignore
        csv = df.to_csv(None, index=False)

        return response_class(csv)


@router.get(
    "/{system_id}/data/{dataset}/timeseries",
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
    response_model=None,
)
def get_system_model_timeseries(
    system_id: UUID = syspath,
    dataset: models.DatasetEnum = datasetpath,
    storage: StorageInterface = Depends(StorageInterface),
    accept: Optional[str] = Header(None),
) -> Union[CSVResponse, ArrowResponse, None]:
    resp, meta_type = _get_return_type(accept)
    with storage.start_transaction() as st:
        data = st.get_system_model_timeseries(system_id, dataset)
    return _convert_data(data, meta_type, resp)


@router.get(
    "/{system_id}/data/{dataset}/statistics",
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
    response_model=None,
)
def get_system_model_statistics(
    system_id: UUID = syspath,
    dataset: models.DatasetEnum = datasetpath,
    storage: StorageInterface = Depends(StorageInterface),
    accept: Optional[str] = Header(None),
) -> Union[CSVResponse, ArrowResponse]:
    resp, meta_type = _get_return_type(accept)
    with storage.start_transaction() as st:
        data = st.get_system_model_statistics(system_id, dataset)
    return _convert_data(data, meta_type, resp)
