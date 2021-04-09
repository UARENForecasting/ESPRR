import pandas as pd
import pytest


from esprr_api import compute, models


def test_compute_ac_power(system_def):
    data = models.SystemData(
        location=dict(latitude=32.02, longitude=-110.9, altitude=800),
        fraction_of_total=0.2,
        weather_data=pd.DataFrame(
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
        ),
    )
    out = compute.compute_ac_power(system_def, data)
    assert isinstance(out, pd.Series)
    assert len(out) == 2
    assert out.iloc[0] == 2.0
    assert out.iloc[1] == 0.0


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
    single = mocker.spy(compute, "compute_ac_power")
    system_def.tracking = tracker
    out = compute.compute_total_system_power(system_def, ready_dataset)
    assert isinstance(out, pd.Series)
    assert abs(out.max() - 10.0) < 1e-6
    assert out.min() == 0.0
    assert single.call_count == 12
