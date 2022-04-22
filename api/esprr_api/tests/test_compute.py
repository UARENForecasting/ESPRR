import pandas as pd
import numpy as np
import pytest


from esprr_api import compute, models, settings
from esprr_api.data import nsrdb


@pytest.mark.parametrize(
    "args,kwargs",
    (
        ((), {}),
        ((0,), {}),
        ((9,), {"a": "b"}),
        ((), {"pressure": 883232}),
        ((), {"temperature": pd.Series([0, 1, 2])}),
    ),
)
def test_cachedlocation(mocker, args, kwargs):
    solpos = mocker.spy(compute.Location, "get_solarposition")
    loc = compute.CachedLocation(32, -110)
    times = pd.date_range("2019-01-01T00:00Z", freq="5min", periods=3)
    assert solpos.call_count == 0
    t1 = loc.get_solarposition(times, *args, **kwargs)
    assert solpos.call_count == 1
    t2 = loc.get_solarposition(times, *args, **kwargs)
    assert solpos.call_count == 1
    pd.testing.assert_frame_equal(t1, t2)

    loc.get_solarposition(times[:-1])
    assert solpos.call_count == 2
    loc.get_solarposition(times[:-1])
    assert solpos.call_count == 2
    loc.get_solarposition(times, *args, **kwargs)
    assert solpos.call_count == 3


def test_compute_single_location(system_def, mocker):
    solpos = mocker.spy(compute.Location, "get_solarposition")
    df = pd.DataFrame(
        {
            "ghi": [1100, 0],
            "dni": [1000, 0],
            "dhi": [100, 0],
            "temp_air": [25, 25],
            "wind_speed": [10, 10],
        },
        index=pd.DatetimeIndex(
            [pd.Timestamp("2021-05-03T19:00Z"), pd.Timestamp("2021-05-04T07:00Z")]
        ),
    )
    data = models.SystemData(
        location=dict(latitude=32.02, longitude=-110.9, altitude=800),
        fraction_of_total=0.2,
        weather_data=df,
        clearsky_data=df,
    )
    out = compute.compute_single_location(system_def, data)
    assert isinstance(out, pd.DataFrame)
    assert len(out) == 2
    assert set(out.columns) == {"ac_power", "clearsky_ac_power"}
    assert out.ac_power.iloc[0] == 2.0
    assert out.ac_power.iloc[1] == 0.0
    assert out.clearsky_ac_power.iloc[0] == 2.0
    assert out.clearsky_ac_power.iloc[1] == 0.0
    assert solpos.call_count == 1  # cachelocation working


@pytest.mark.parametrize(
    "tracker",
    [
        models.FixedTracking(tilt=20, azimuth=180),
        models.SingleAxisTracking(
            axis_tilt=20, axis_azimuth=180, gcr=0.3, backtracking=True
        ),
    ],
)
def test_compute_total_system_power(ready_dataset, system_def, mocker, tracker):
    single = mocker.spy(compute, "compute_single_location")
    system_def.tracking = tracker
    out = compute.compute_total_system_power(system_def, ready_dataset)
    assert isinstance(out, pd.DataFrame)
    assert set(out.columns) == {"ac_power", "clearsky_ac_power"}

    assert abs(out.ac_power.max() - 10.0) < 1e-6
    assert abs(out.clearsky_ac_power.max() - 10.0) < 1e-6
    assert out.ac_power.min() == 0.0
    assert single.call_count == 12


def test_daytime_limits():
    ind = pd.date_range("2020-01-01T00:00Z", freq="5min", periods=10)
    zen = pd.Series([100, 95, 90, 85, 80, 80, 90, 95, 100, 120], index=ind)
    exp = pd.Series([0, 0, 1, 1, 1, 1, 1, 1, 0, 0], index=ind).astype(bool)
    out = compute._daytime_limits(5, zen)
    pd.testing.assert_series_equal(out, exp)

    ten = pd.Series(
        [0, 1, 1, 1, 1],
        index=pd.date_range("2020-01-01T00:00Z", freq="10min", periods=5),
    ).astype(bool)
    tenout = compute._daytime_limits(10, zen)
    pd.testing.assert_series_equal(ten, tenout)

    pd.testing.assert_series_equal(
        pd.Series(list(range(5)) + list(range(5, 0, -1)), index=ind).diff()[exp],
        pd.Series(
            [1.0] * 4 + [-1.0] * 2,  # 90, 95
            index=pd.date_range("2020-01-01T00:10Z", freq="5min", periods=6),
        ),
    )


def test_compute_statistics(system_def):
    data = pd.DataFrame(
        {"ac_power": [10, 11, 12, 11], "clearsky_ac_power": [12, 11, 12, 11]},
        index=pd.DatetimeIndex(
            [
                "2019-04-01T12:00-07:00",
                "2019-04-01T13:00-07:00",
                "2019-05-01T12:00-07:00",
                "2019-05-01T13:00-07:00",
            ]
        ),
    )
    out = compute.compute_statistics(system_def, data)
    assert isinstance(out, pd.DataFrame)
    assert len(out.columns) == 4
    assert len(out) == 5 * 6 * 2


def test_get_dataset(nsrdb_data, dataset_name):
    settings.nsrdb_data_path["NSRDB_2019"] = nsrdb_data
    ds = compute._get_dataset(dataset_name)
    assert isinstance(ds, nsrdb.NSRDBDataset)
    ds.grid


def test_run_job_no_data(system_id, dataset_name, auth0_id, mocker, ready_dataset):
    mocker.patch("esprr_api.compute._get_dataset", return_value=ready_dataset)
    update = mocker.patch("esprr_api.storage.StorageInterface.update_system_model_data")
    compute.run_job(system_id, dataset_name, auth0_id)
    assert update.call_count == 0


def test_run_job(
    system_id, dataset_name, auth0_id, mocker, ready_dataset, add_example_db_data
):
    mocker.patch("esprr_api.compute._get_dataset", return_value=ready_dataset)
    update = mocker.patch("esprr_api.storage.StorageInterface.update_system_model_data")
    compute.run_job(system_id, dataset_name, auth0_id)
    assert update.call_count == 1
    cargs = update.call_args[0]
    assert cargs[0] == system_id
    assert cargs[1] == dataset_name
    assert cargs[3].startswith(b"ARROW")
    assert cargs[4].startswith(b"ARROW")


def test_run_job_badid(
    other_system_id, dataset_name, auth0_id, mocker, ready_dataset, add_example_db_data
):
    mocker.patch("esprr_api.compute._get_dataset", return_value=ready_dataset)
    update = mocker.patch("esprr_api.storage.StorageInterface.update_system_model_data")
    compute.run_job(other_system_id, dataset_name, auth0_id)
    assert update.call_count == 0


def test_run_job_error(
    system_id,
    dataset_name,
    auth0_id,
    mocker,
    ready_dataset,
    add_example_db_data,
):
    update = mocker.patch("esprr_api.storage.StorageInterface.update_system_model_data")
    mocker.patch("esprr_api.compute._get_dataset", return_value=ready_dataset)
    mocker.patch(
        "esprr_api.compute.compute_statistics", side_effect=ValueError("test err")
    )
    with pytest.raises(ValueError):
        compute.run_job(system_id, dataset_name, auth0_id)

    assert update.call_count == 1
    cargs = update.call_args[0]
    assert cargs[0] == system_id
    assert cargs[1] == dataset_name
    assert cargs[3] is None
    assert cargs[4] is None
    assert cargs[5] == {"message": "test err"}


variable_mult_df = pd.DataFrame(
    {
        "ac_power": (
            [0] * (12 * 6)
            + [5] * (12 * 6)
            + [6] * (12 * 6)
            + [0] * (12 * 6)
            + [0] * (12 * 6)
            + [12] * (12 * 6)
            + [13] * (12 * 6)
            + [0] * (12 * 6)
            + [0] * (12 * 6)
            + [8] * (12 * 3)
            + [4] * (12 * 3)
            + [10] * (12 * 3)
            + [11] * (12 * 3)
            + [0] * (12 * 6)
            + [0] * (12 * 6)
            + [8] * (12 * 3)
            + [4] * (12 * 3)
            + [13] * (12 * 3)
            + [13] * (12 * 3)
            + [0] * (12 * 6)
            + [0]
        ),
        "clearsky_ac_power": (
            [0] * (12 * 6)
            + [12] * (12 * 6)
            + [13] * (12 * 6)
            + [0] * (12 * 6)
            + [0] * (12 * 6)
            + [12] * (12 * 6)
            + [13] * (12 * 6)
            + [0] * (12 * 6)
            + [0] * (12 * 6)
            + [12] * (12 * 6)
            + [13] * (12 * 6)
            + [0] * (12 * 6)
            + [0] * (12 * 6)
            + [12] * (12 * 6)
            + [13] * (12 * 6)
            + [0] * (12 * 6)
            + [0]
        ),
    },
    index=pd.date_range("2019-01-01", "2019-01-05", freq="5T", tz="utc"),
)


@pytest.mark.parametrize("data", [variable_mult_df])
def test_calculate_variable_multiplier(data):
    m = compute.calculate_variable_multiplier(data)
    expected_result = pd.DataFrame(
        {"ac_power": [1.0, np.nan, 0.66981919, 0.5, np.nan]}, index=m.index
    )
    assert isinstance(m, pd.Series)
    assert len(m) == (len(data) - 1) / (12 * 24) + 1
    assert m.between(0.5, 1).any()
    pd.testing.assert_series_equal(m, expected_result["ac_power"])
