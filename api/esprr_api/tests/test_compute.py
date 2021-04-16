import pandas as pd
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


def test_get_dataset(nsrdb_data, dataset_name):
    settings.nsrdb_data_path = nsrdb_data
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


def test_run_job_badid(
    other_system_id, dataset_name, auth0_id, mocker, ready_dataset, add_example_db_data
):
    mocker.patch("esprr_api.compute._get_dataset", return_value=ready_dataset)
    update = mocker.patch("esprr_api.storage.StorageInterface.update_system_model_data")
    compute.run_job(other_system_id, dataset_name, auth0_id)
    assert update.call_count == 0
