"""Test some select system endpoint interaction. The majority of testing
is done via schemathesis in ../../tests/test_app.py
"""
from io import BytesIO
import json
import string
from urllib.parse import quote
import uuid


from fastapi import HTTPException
import pandas as pd
import pytest


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
