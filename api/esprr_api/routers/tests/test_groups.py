"""Test some select system endpoint interaction. The majority of testing
is done via schemathesis in ../../tests/test_app.py
"""
from io import BytesIO

from fastapi import HTTPException
import pandas as pd
import pytest


from esprr_api import models


pytestmark = pytest.mark.usefixtures("add_example_db_data")


def test_list_groups(client, stored_system_group):
    response = client.get("/system_groups")
    groups = [models.StoredSystemGroup(**g) for g in response.json()]
    group = groups[0].dict()
    expected_dict = stored_system_group.copy(deep=True).dict()
    expected_dict["definition"].pop("systems")
    assert len(groups) == 1
    for key in ["object_id", "object_type"]:
        assert group[key] == expected_dict[key]


def test_get_group(client, group_id, stored_system_group):
    group = client.get(f"/system_groups/{group_id}").json()
    expected_dict = stored_system_group.dict()

    assert group["object_id"] == str(expected_dict["object_id"])
    assert group["object_type"] == expected_dict["object_type"]

    group_def = group["definition"]
    expected_def = expected_dict["definition"]

    assert len(group_def["systems"]) == 1

    group_sys = group_def["systems"][0]
    expected_sys = expected_def["systems"][0]

    assert group_sys["object_id"] == str(expected_sys["object_id"])


def test_get_group_dne(client, system_id, stored_system_group):
    group = client.get(f"/system_groups/{system_id}")
    assert group.status_code == 404


def test_create_delete_group(client):
    groups = client.get("system_groups/").json()
    assert len(groups) == 1
    new = client.post("/system_groups/", json={"name": "I'm a new group"})
    assert new.status_code == 201
    new_group = client.get(new.headers["Location"])
    assert new_group.status_code == 200
    ng = new_group.json()
    assert ng["definition"]["name"] == "I'm a new group"
    assert ng["definition"]["systems"] == []
    groups = client.get("system_groups/").json()
    assert len(groups) == 2
    delete = client.delete(new.headers["Location"])
    assert delete.status_code == 204
    groups = client.get("/system_groups/").json()
    assert len(groups) == 1
    group = client.get(new.headers["Location"])
    assert group.status_code == 404


def test_create_group_duplicate_name(client, group_name):
    new = client.post("/system_groups/", json={"name": group_name})
    assert new.status_code == 409


def test_delete_system_group_group_dne(client, system_id):
    delete = client.delete(f"/system_groups/{system_id}")
    assert delete.status_code == 404


def test_update_system_group(client):
    new = client.post("/system_groups/", json={"name": "I'm a new group"})
    assert new.status_code == 201
    new_group = client.get(new.headers["Location"])
    assert new_group.status_code == 200
    update = client.post(new.headers["Location"], json={"name": "I'm the old group"})
    assert update.status_code == 201
    new_group = client.get(new.headers["Location"])
    ng = new_group.json()
    assert ng["definition"]["name"] == "I'm the old group"
    delete = client.delete(new.headers["Location"])
    delete.status_code == 204


def test_add_system_to_group(client, group_id, nocommit_transaction, system_def):
    sys_def = system_def.dict()
    sys_def["name"] = "this other one"
    new_system = client.post("/systems/", json=sys_def).json()
    sys_id = new_system["object_id"]
    group = client.get(f"/system_groups/{group_id}").json()
    assert len(group["definition"]["systems"]) == 1
    added = client.post(f"/system_groups/{group_id}/systems/{sys_id}")
    assert added.status_code == 201
    group = client.get(f"/system_groups/{group_id}").json()
    assert len(group["definition"]["systems"]) == 2
    added_name = group["definition"]["systems"][1]["definition"]["name"]
    assert added_name == "this other one"


def test_add_system_to_group_system_dne(client, group_id, other_system_id):
    res = client.post(f"/system_groups/{group_id}/systems/{other_system_id}")
    assert res.status_code == 404


def test_add_system_to_group_group_dne(client, other_system_id, system_id):
    res = client.post(f"/system_groups/{other_system_id}/systems/{other_system_id}")
    assert res.status_code == 404


def test_remove_system_from_group(client, group_id, system_id, nocommit_transaction):
    removal = client.delete(f"/system_groups/{group_id}/systems/{system_id}")
    assert removal.status_code == 201
    group = client.get(f"/system_groups/{group_id}").json()
    assert len(group["definition"]["systems"]) == 0


def test_remove_system_from_group_system_dne(client, group_id, other_system_id):
    removal = client.delete(f"/system_groups/{group_id}/systems/{other_system_id}")
    assert removal.status_code == 404


def test_remove_system_from_group_group_dne(client, system_id, other_system_id):
    removal = client.delete(f"/system_groups/{system_id}/systems/{other_system_id}")
    assert removal.status_code == 404


@pytest.fixture()
def group_timeseries_df(timeseries_df, system_def, mocker):
    sys_name = system_def.name.replace(" ", "_")
    group_df = timeseries_df.rename(
        columns={
            "ac_power": sys_name + "_ac_power",
            "clearsky_ac_power": sys_name + "_clearsky_ac_power",
            "dc_power": sys_name + "_dc_power",
        }
    )
    group_df = group_df.set_index("time")
    ts_df = timeseries_df.set_index("time")
    all_df = pd.concat([ts_df, group_df], axis=1)
    all_df = all_df.tz_convert("Etc/GMT+7")
    all_df["time"] = all_df.index
    all_df = all_df[["time"] + [col for col in all_df.columns if col != "time"]]
    return all_df


def test_get_group_model_status(client, group_id, system_id):
    status = client.get(
        f"/system_groups/{group_id}/data/NSRDB_2019", headers={"accept": "text/csv"}
    ).json()
    assert "created_at" in status
    assert "modified_at" in status
    assert status["object_id"] == group_id
    assert status["object_type"] == "system_group"
    system_statuses = status["system_data_status"]
    assert len(system_statuses) == 1
    single_system_status = system_statuses[system_id]
    assert single_system_status["status"] == "complete"


def test_get_group_model_status_system_dne(client, group_id, system_id, mocker):
    mocker.patch(
        "esprr_api.storage.StorageInterface.get_system_model_meta",
        side_effect=HTTPException(404),
    )
    status = client.get(
        f"/system_groups/{group_id}/data/NSRDB_2019", headers={"accept": "text/csv"}
    ).json()
    system_statuses = status["system_data_status"]
    assert len(system_statuses) == 0


def test_get_group_model_status_running(client, group_id, mocker, system_id):
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
    status = client.get(
        f"/system_groups/{group_id}/data/NSRDB_2019", headers={"accept": "text/csv"}
    ).json()
    system_statuses = status["system_data_status"]
    assert len(system_statuses) == 1
    single_system_status = system_statuses[system_id]
    assert single_system_status["status"] == "running"


def test_get_group_timeseries_csv(client, group_id, group_timeseries_df, timeseries_df):
    csv = client.get(
        f"/system_groups/{group_id}/data/NSRDB_2019/timeseries",
        headers={"accept": "text/csv"},
    ).text
    expected = group_timeseries_df.tz_convert("America/Phoenix")
    expected = expected.to_csv(index=False)
    assert csv == expected


def test_get_group_timeseries_arrow(
    client, group_id, group_timeseries_df, timeseries_df
):
    resp = client.get(
        f"/system_groups/{group_id}/data/NSRDB_2019/timeseries",
        headers={"accept": "application/vnd.apache.arrow.file"},
    )
    iob = BytesIO(resp.content)
    iob.seek(0)
    df = pd.read_feather(iob)
    pd.testing.assert_frame_equal(
        df, group_timeseries_df.reset_index(drop=True), check_dtype=False
    )


def test_get_group_timeseries_no_systems(
    client, group_id, system_id, nocommit_transaction
):
    removal = client.delete(f"/system_groups/{group_id}/systems/{system_id}")
    assert removal.status_code == 201
    csv = client.get(
        f"/system_groups/{group_id}/data/NSRDB_2019/timeseries",
        headers={"accept": "text/csv"},
    ).text
    assert csv == "time,ac_power,clearsky_ac_power,dc_power\n"


def test_get_group_timeseries_group_dne(client, system_id):
    bad = client.get(f"/system_groups/{system_id}/data/NSRDB_2019/timeseries")
    assert bad.status_code == 404


expected_group_statistics_csv = """month,interval,statistic,value
January,5-min,p95 daytime ramp,10.0
January,5-min,p05 daytime ramp,10.0
January,5-min,worst case ramp up,10.0
January,5-min,worst case ramp down,10.0
January,5-min,typical sunrise ramp,10.0
January,5-min,typical sunset ramp,10.0
January,10-min,p95 daytime ramp,
January,10-min,p05 daytime ramp,
January,10-min,worst case ramp up,
January,10-min,worst case ramp down,
January,10-min,typical sunrise ramp,
January,10-min,typical sunset ramp,
January,15-min,p95 daytime ramp,
January,15-min,p05 daytime ramp,
January,15-min,worst case ramp up,
January,15-min,worst case ramp down,
January,15-min,typical sunrise ramp,
January,15-min,typical sunset ramp,
January,30-min,p95 daytime ramp,
January,30-min,p05 daytime ramp,
January,30-min,worst case ramp up,
January,30-min,worst case ramp down,
January,30-min,typical sunrise ramp,
January,30-min,typical sunset ramp,
January,60-min,p95 daytime ramp,
January,60-min,p05 daytime ramp,
January,60-min,worst case ramp up,
January,60-min,worst case ramp down,
January,60-min,typical sunrise ramp,
January,60-min,typical sunset ramp,
"""


def test_get_group_statistics_csv(client, group_id, mocker):
    df_index = pd.DatetimeIndex(
        [pd.Timestamp("2019-01-01T17:00-07:00"), pd.Timestamp("2019-01-01T17:05-07:00")]
    )
    # although this timeseries is not realistic in that for a group with one
    # system the columns should match, by having different values we can
    # test that the columns are selected correctly.
    group_timeseries = pd.DataFrame(
        {
            "time": df_index,
            "ac_power": [0, 10],
            "clearsky_ac_power": [0, 10],
            "Test_PV_System_ac_power": [10.2, 8.2],
            "Test_PV_System_clearsky_ac_power": [10.2, 8.2],
        },
        index=df_index,
    )
    mocker.patch(
        "esprr_api.routers.groups._get_group_timeseries_from_systems",
        return_value=group_timeseries,
    )

    csv = client.get(
        f"/system_groups/{group_id}/data/NSRDB_2019/statistics",
        headers={"accept": "text/csv"},
    ).text
    assert csv == expected_group_statistics_csv


def test_get_group_statistics_arrow(client, group_id, mocker):
    df_index = pd.DatetimeIndex(
        [pd.Timestamp("2019-01-01T17:00-07:00"), pd.Timestamp("2019-01-01T17:05-07:00")]
    )
    # although this timeseries is not realistic in that for a group with one
    # system the columns should match, by having different values we can
    # test that the columns are selected correctly.
    group_timeseries = pd.DataFrame(
        {
            "time": df_index,
            "ac_power": [0, 10],
            "clearsky_ac_power": [0, 10],
            "Test_PV_System_ac_power": [10.2, 8.2],
            "Test_PV_System_clearsky_ac_power": [10.2, 8.2],
        },
        index=df_index,
    )
    mocker.patch(
        "esprr_api.routers.groups._get_group_timeseries_from_systems",
        return_value=group_timeseries,
    )

    resp = client.get(
        f"/system_groups/{group_id}/data/NSRDB_2019/statistics",
        headers={"accept": "application/vnd.apache.arrow.file"},
    )
    iob = BytesIO(resp.content)
    iob.seek(0)
    df = pd.read_feather(iob)
    five_min = df[df["interval"] == "5-min"]
    # Test data contains only two five-minute values that describe
    # a 10mw ramp
    assert (five_min["value"] == 10.0).all()


def test_get_group_statistics_group_dne(client, system_id):
    bad = client.get(f"/system_groups/{system_id}/data/NSRDB_2019/statistics")
    assert bad.status_code == 404
