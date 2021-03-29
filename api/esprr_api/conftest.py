from base64 import b64decode
from contextlib import contextmanager
from copy import deepcopy
import datetime as dt
from uuid import UUID, uuid1


from fakeredis import FakeRedis  # type: ignore
from fastapi.testclient import TestClient
import httpx
from pvlib.pvsystem import PVSystem  # type: ignore
from pvlib.tracking import SingleAxisTracker  # type: ignore
import pymysql
import pytest
from rq import Queue  # type: ignore


from esprr_api.main import app
from esprr_api import settings, models, storage


@pytest.fixture(scope="session")
def auth_token():
    token_req = httpx.post(
        settings.auth_token_url,
        headers={"content-type": "application/json"},
        data=(
            '{"grant_type": "password", '
            '"username": "testing@esprr.x.energy.arizona.edu", '
            '"password": "Thepassword123!", '
            f'"audience": "{settings.auth_audience}", '
            f'"client_id": "{settings.auth_client_id}"'
            "}"
        ),
    )
    if token_req.status_code != 200:  # pragma: no cover
        pytest.skip("Cannot retrieve valid Auth0 token")
    else:
        token = token_req.json()["access_token"]
        return token


@pytest.fixture(scope="module")
def client(auth_token):
    out = TestClient(app)
    out.headers.update({"Authorization": f"Bearer {auth_token}"})
    return out


@pytest.fixture(scope="module")
def noauthclient():
    return TestClient(app)


@pytest.fixture(scope="module")
def root_conn():
    conn = storage._make_sql_connection_partial(user="root", password="testpassword")()
    yield conn
    conn.close()


@pytest.fixture(scope="module")
def add_example_db_data(root_conn):
    curs = root_conn.cursor()
    curs.callproc("add_example_data")
    root_conn.commit()
    yield curs
    curs.callproc("remove_example_data")
    root_conn.commit()


@pytest.fixture()
def nocommit_transaction(mocker):
    conn = storage.engine.connect()

    @contextmanager
    def start_transaction(cls):
        cls._cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
        yield cls
        cls._cursor = None

    mocker.patch.object(
        storage.StorageInterface, "start_transaction", new=start_transaction
    )
    yield
    conn.rollback()


@pytest.fixture(scope="module")
def auth0_id():
    return "auth0|5fa9596ccf64f9006e841a3a"


@pytest.fixture(scope="module")
def user_id():
    return UUID("17fbf1c6-34bd-11eb-af43-f4939feddd82")


@pytest.fixture(scope="module")
def system_id():
    return models.SYSTEM_ID


@pytest.fixture(scope="module")
def other_system_id():
    return "6513485a-34cd-11eb-8f13-f4939feddd82"


@pytest.fixture()
def system_def():
    return models.PVSystem(**models.SYSTEM_EXAMPLE)


@pytest.fixture()
def stored_system(system_def, system_id):
    extime = dt.datetime(2020, 12, 1, 1, 23, tzinfo=dt.timezone.utc)
    return models.StoredPVSystem(
        object_id=system_id,
        object_type="system",
        created_at=extime,
        modified_at=extime,
        definition=system_def,
    )


@pytest.fixture()
def fixed_tracking():
    return models.FixedTracking(tilt=32, azimuth=180.9)


@pytest.fixture()
def single_axis_tracking():
    return models.SingleAxisTracking(
        axis_tilt=0, axis_azimuth=179.8, backtracking=False, gcr=1.8
    )


@pytest.fixture(params=["fixed_axis", "single_axis", "multi_array_fixed"])
def either_tracker(request, system_def, fixed_tracking, single_axis_tracking):
    inv = system_def.inverters[0]
    if request.param == "fixed_axis":
        inv.arrays[0].tracking = fixed_tracking
        return inv, PVSystem, False
    elif request.param == "multi_array_fixed":
        inv.arrays[0].tracking = fixed_tracking
        arr1 = deepcopy(inv.arrays[0])
        arr1.name = "Array 2"
        inv.arrays.append(arr1)
        return inv, PVSystem, True
    else:
        inv.arrays[0].tracking = single_axis_tracking
        return inv, SingleAxisTracker, False
