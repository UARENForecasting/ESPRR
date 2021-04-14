"""Test some select system endpoint interaction. The majority of testing
is done via schemathesis in ../../tests/test_app.py
"""
from copy import deepcopy
from io import BytesIO
import json
import string
from urllib.parse import quote
import uuid


from fastapi import HTTPException
import pandas as pd
import pytest
from rq import SimpleWorker


from esprr_api import models, storage
from esprr_api.routers import systems


pytestmark = pytest.mark.usefixtures("add_example_db_data")


def test_list_systems(client, stored_system):
    response = client.get("/systems")
    systems = [models.StoredPVSystem(**j) for j in response.json()]
    assert len(systems) == 1
    assert systems[0] == stored_system


def test_get_system(client, system_id, stored_system):
    response = client.get(f"/systems/{system_id}")
    assert models.StoredPVSystem(**response.json()) == stored_system


def test_get_system_404(client):
    id_ = str(uuid.uuid1())
    response = client.get(f"/systems/{id_}")
    assert response.status_code == 404


def test_get_system_noauth(noauthclient):
    id_ = str(uuid.uuid1())
    response = noauthclient.get(f"/systems/{id_}")
    assert response.status_code == 403


def test_get_other_system(client, other_system_id):
    response = client.get(f"/systems/{other_system_id}")
    assert response.status_code == 404


def test_delete_other_system(client, other_system_id):
    response = client.delete(f"/systems/{other_system_id}")
    assert response.status_code == 404


@pytest.mark.parametrize("alter", [0, 1])
def test_update_system(
    client, system_def, system_id, mocker, alter, nocommit_transaction
):
    if alter:
        system_def.ac_capacity = 33.99
    update = mocker.spy(storage.StorageInterface, "update_system")
    response = client.post(f"/systems/{system_id}", data=system_def.json())
    assert response.status_code == 201
    assert response.json()["object_id"] == system_id
    update.assert_called()


def test_update_other_system(client, other_system_id, system_def):
    system_def.ac_capacity = 119.0
    system_def.name = "New Name"
    response = client.post(f"/systems/{other_system_id}", data=system_def.json())
    assert response.status_code == 404


@pytest.mark.parametrize(
    "change", [({}, 200), ({"ac_capacity": "notanumber"}, 422), ({"name": "ok"}, 200)]
)
def test_check_system(system_def, client, change):
    cd, code = change
    data = system_def.dict()
    data.update(cd)
    resp = client.post("/systems/check", data=json.dumps(data))
    assert resp.status_code == code


def test_get_create_delete_system(client, system_def, nocommit_transaction, system_id):
    r1 = client.get("/systems/")
    assert len(r1.json()) == 1
    assert r1.json()[0]["object_id"] == system_id
    r2 = client.delete(f"/systems/{system_id}")
    assert r2.status_code == 204
    resp = client.post("/systems/", json=system_def.dict())
    assert resp.status_code == 201
    r3 = client.get(resp.headers["Location"])
    assert r3.status_code == 200
    assert models.PVSystem(**r3.json()["definition"]) == system_def


def test_create_same_name(client, system_def, nocommit_transaction):
    resp = client.post("/systems/", json=system_def.dict())
    assert resp.status_code == 409


@pytest.mark.parametrize("char", string.whitespace)
def test_get_system_whitespace(client, char):
    resp = client.get(f"/systems/{quote(char)}")
    if char == "\n":  # newline goes to the list systems endpoint
        assert resp.status_code == 200
    else:
        assert resp.status_code == 422


@pytest.mark.parametrize(
    "inp,exp",
    [
        ("text/csv", (systems.CSVResponse, "text/csv")),
        ("text/*", (systems.CSVResponse, "text/csv")),
        ("*/*", (systems.CSVResponse, "text/csv")),
        (
            "application/vnd.apache.arrow.file",
            (systems.ArrowResponse, "application/vnd.apache.arrow.file"),
        ),
        ("application/*", (systems.ArrowResponse, "application/vnd.apache.arrow.file")),
        (None, (systems.CSVResponse, "text/csv")),
        pytest.param(
            "application/json",
            (),
            marks=pytest.mark.xfail(strict=True, raises=HTTPException),
        ),
    ],
)
def test_get_return_type(inp, exp):
    assert systems._get_return_type(inp) == exp


def test_convert_data(timeseries_bytes, timeseries_csv):
    out = systems._convert_data(
        b"thisiswrong",
        "application/vnd.apache.arrow.file",
        lambda x: x,
    )
    assert out == b"thisiswrong"
    out = systems._convert_data(timeseries_bytes, "text/csv", lambda x: x)
    assert out == timeseries_csv


def test_convert_job_data_invalid():
    with pytest.raises(HTTPException) as err:
        systems._convert_data(b"thisiswrong", "text/csv", lambda x: x)
    assert err.value.status_code == 500


def test_get_system_model_status(client, system_id, dataset_name):
    resp = client.get(f"/systems/{system_id}/data/{dataset_name}")
    assert resp.status_code == 200
    assert resp.json() == {
        "system_id": "6b61d9ac-2e89-11eb-be2a-4dc7a6bcd0d9",
        "dataset": "NSRDB_2019",
        "version": "v0.1",
        "system_modified": False,
        "status": "complete",
        "created_at": "2020-12-01T01:23:00+00:00",
        "modified_at": "2020-12-01T01:23:00+00:00",
    }


def test_get_system_model_status_running(client, system_id, dataset_name, mocker):
    val = models.SystemDataMeta(
        **{
            "system_id": "6b61d9ac-2e89-11eb-be2a-4dc7a6bcd0d9",
            "dataset": "NSRDB_2019",
            "version": "v0.1",
            "system_modified": False,
            "status": "queued",
            "created_at": "2020-12-01T01:23:00+00:00",
            "modified_at": "2020-12-01T01:23:00+00:00",
        }
    )
    mocker.patch(
        "esprr_api.storage.StorageInterface.get_system_model_meta", return_value=val
    )
    mocker.patch("esprr_api.queuing.QueueManager.job_is_running", return_value=True)
    resp = client.get(f"/systems/{system_id}/data/{dataset_name}")
    assert resp.status_code == 200
    exp = deepcopy(val)
    exp.status = "running"
    assert resp.json() == json.loads(exp.json())


def test_get_system_model_status_dne(client, other_system_id, dataset_name, system_id):
    resp = client.get(f"/systems/{other_system_id}/data/{dataset_name}")
    assert resp.status_code == 404


@pytest.mark.parametrize(
    "accept", ["application/*", "application/vnd.apache.arrow.file"]
)
def test_get_system_model_timeseries_arrow(
    client, system_id, dataset_name, accept, timeseries_df
):
    resp = client.get(
        f"/systems/{system_id}/data/{dataset_name}/timeseries",
        headers={"accept": accept},
    )
    assert resp.status_code == 200
    iob = BytesIO(resp.content)
    iob.seek(0)
    df = pd.read_feather(iob)
    pd.testing.assert_frame_equal(df, timeseries_df)


@pytest.mark.parametrize("accept", ["*/*", "text/csv"])
def test_get_system_model_timeseries_csv(
    client, system_id, dataset_name, accept, timeseries_csv
):
    resp = client.get(
        f"/systems/{system_id}/data/{dataset_name}/timeseries",
        headers={"accept": accept},
    )
    assert resp.status_code == 200
    assert resp.text == timeseries_csv


@pytest.mark.parametrize(
    "accept", ["application/*", "application/vnd.apache.arrow.file"]
)
def test_get_system_model_statistics_arrow(
    client, system_id, dataset_name, accept, statistics_df
):
    resp = client.get(
        f"/systems/{system_id}/data/{dataset_name}/statistics",
        headers={"accept": accept},
    )
    assert resp.status_code == 200
    iob = BytesIO(resp.content)
    iob.seek(0)
    df = pd.read_feather(iob)
    pd.testing.assert_frame_equal(df, statistics_df)


@pytest.mark.parametrize("accept", ["*/*", "text/csv"])
def test_get_system_model_statistics_csv(
    client, system_id, dataset_name, accept, statistics_csv
):
    resp = client.get(
        f"/systems/{system_id}/data/{dataset_name}/statistics",
        headers={"accept": accept},
    )
    assert resp.status_code == 200
    assert resp.text == statistics_csv


def test_get_create_run_system(
    client, system_def, nocommit_transaction, system_id, dataset_name, async_queue
):
    r1 = client.get("/systems/")
    assert len(r1.json()) == 1
    assert r1.json()[0]["object_id"] == system_id
    r2 = client.delete(f"/systems/{system_id}")
    assert r2.status_code == 204
    resp = client.post("/systems/", json=system_def.dict())
    assert resp.status_code == 201

    sysid = resp.json()["object_id"]

    r3 = client.get(f"/systems/{sysid}/data/{dataset_name}")
    assert r3.status_code == 404

    cmpr = client.post(f"/systems/{sysid}/data/{dataset_name}")
    assert cmpr.status_code == 202

    # multiple times, no effect
    cmpr = client.post(f"/systems/{sysid}/data/{dataset_name}")
    assert cmpr.status_code == 202

    r4 = client.get(f"/systems/{sysid}/data/{dataset_name}")
    assert r4.status_code == 200
    assert r4.json()["status"] == "queued"
    assert len(async_queue.jobs) == 1
    assert async_queue.jobs[0].id == f"{sysid}:{dataset_name}"


def test_run_system_model_simple(client, system_id, dataset_name, async_queue):
    assert len(async_queue.jobs) == 0
    resp = client.post(f"/systems/{system_id}/data/{dataset_name}")
    assert resp.status_code == 202

    assert len(async_queue.jobs) == 1
    assert async_queue.jobs[0].id == f"{system_id}:{dataset_name}"


def test_run_system_model_dne(client, other_system_id, dataset_name):
    resp = client.post(f"/systems/{other_system_id}/data/{dataset_name}")
    assert resp.status_code == 404


def test_full_run_through(client, dataset_name, async_queue, mocker, ready_dataset):
    mocker.patch("esprr_api.compute._get_dataset", return_value=ready_dataset)
    sys = models.PVSystem(
        name="Full",
        boundary=dict(
            nw_corner=dict(
                latitude=32.04,
                longitude=-110.9,
            ),
            se_corner=dict(latitude=32.03, longitude=-110.88),
        ),
        ac_capacity=20.5,
        dc_ac_ratio=1.3,
        albedo=0.2,
        tracking=dict(axis_tilt=0, axis_azimuth=180, backtracking=True, gcr=0.3),
    )

    resp = client.post("/systems/", json=sys.dict())
    assert resp.status_code == 201
    sysid = resp.json()["object_id"]

    chk = client.get(f"/systems/{sysid}/data/{dataset_name}")
    assert chk.status_code == 404
    ts = client.get(f"/systems/{sysid}/data/{dataset_name}/timeseries")
    assert ts.status_code == 404
    stat = client.get(f"/systems/{sysid}/data/{dataset_name}/statistics")
    assert stat.status_code == 404

    cmpt = client.post(f"/systems/{sysid}/data/{dataset_name}")
    assert cmpt.status_code == 202

    r4 = client.get(f"/systems/{sysid}/data/{dataset_name}")
    assert r4.status_code == 200
    assert r4.json()["status"] == "queued"
    assert len(async_queue.jobs) == 1
    ts = client.get(f"/systems/{sysid}/data/{dataset_name}/timeseries")
    assert ts.status_code == 404
    stat = client.get(f"/systems/{sysid}/data/{dataset_name}/statistics")
    assert stat.status_code == 404

    w = SimpleWorker([async_queue], connection=async_queue.connection)
    w.work(burst=True)

    r4 = client.get(f"/systems/{sysid}/data/{dataset_name}")
    assert r4.status_code == 200
    assert r4.json()["status"] == "complete"
    assert len(async_queue.jobs) == 0

    ts = client.get(f"/systems/{sysid}/data/{dataset_name}/timeseries")
    assert ts.status_code == 200
    stat = client.get(f"/systems/{sysid}/data/{dataset_name}/statistics")
    assert stat.status_code == 200

    delt = client.delete(f"/systems/{sysid}")
    assert delt.status_code == 204

    chk = client.get(f"/systems/{sysid}/data/{dataset_name}")
    assert chk.status_code == 404
    ts = client.get(f"/systems/{sysid}/data/{dataset_name}/timeseries")
    assert ts.status_code == 404
    stat = client.get(f"/systems/{sysid}/data/{dataset_name}/statistics")
    assert stat.status_code == 404
