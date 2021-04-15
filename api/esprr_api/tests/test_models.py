from functools import partial
import re


from hypothesis import given, example, assume
from hypothesis.strategies import floats, booleans, composite, from_regex
import pandas as pd
from pydantic import BaseModel, ValidationError
import pytest


from esprr_api import models


fail_param = partial(
    pytest.param, marks=pytest.mark.xfail(strict=True, raises=ValidationError)
)


class UserStringModel(BaseModel):
    name: str = models.UserString(...)


@pytest.mark.parametrize(
    "inp",
    [
        "a&badString",
        "INSERT INTO;",
        "MoreBad?",
        "waytoolong" * 50,
        "  ",
        ",'",
        " ,'-()",
        "_",
        "0:",
    ],
)
def test_userstring_fail(inp):
    with pytest.raises(ValidationError):
        UserStringModel(name=inp)


def test_userstring_empty():
    assert UserStringModel(name="").name == ""


@given(
    inp=from_regex(
        re.compile(r"[a-z0-9 ,'\(\)_]+", re.IGNORECASE), fullmatch=True
    ).filter(lambda x: re.search(r"[0-9a-z]+", x, re.IGNORECASE) is not None)
)
def test_userstring_success(inp):
    assert UserStringModel(name=inp).name == inp


@given(
    azimuth=floats(min_value=0, max_value=360, exclude_max=True),
    tilt=floats(min_value=0, max_value=90),
)
@example(azimuth=359.999, tilt=90.0)
@example(azimuth=33.9, tilt="2.33")
@example(azimuth=49.823, tilt=179.83)
def test_fixed_tracking(azimuth, tilt):
    out = models.FixedTracking(azimuth=azimuth, tilt=tilt)
    assert out.azimuth == azimuth
    assert out.tilt == float(tilt)


@composite
def outside_az_tilt(draw):
    azimuth = draw(floats())
    tilt = draw(floats())
    assume((azimuth >= 360 or azimuth < 0) or (tilt > 180 or tilt < 0))
    return (azimuth, tilt)


@given(azt=outside_az_tilt())
@example(azt=(360.0, 2.0))
@example(azt=(33.0, "s"))
def test_fixed_tracking_outside(azt):
    azimuth, tilt = azt
    with pytest.raises(ValidationError):
        models.FixedTracking(azimuth=azimuth, tilt=tilt)


@given(
    azimuth=floats(min_value=0, max_value=360, exclude_max=True),
    tilt=floats(min_value=0, max_value=90),
    gcr=floats(min_value=0),
    backtracking=booleans(),
)
@example(azimuth=0.0, tilt=0.0, gcr="0.0", backtracking="no")
def test_singleaxis_tracking(tilt, azimuth, gcr, backtracking):
    out = models.SingleAxisTracking(
        axis_tilt=tilt, axis_azimuth=azimuth, gcr=gcr, backtracking=backtracking
    )
    assert out.axis_tilt == tilt
    assert out.axis_azimuth == azimuth
    assert out.gcr == float(gcr)
    assert out.backtracking == (False if backtracking == "no" else backtracking)


@composite
def outside_az_tilt_gcr(draw):
    azimuth = draw(floats())
    tilt = draw(floats())
    gcr = draw(floats())
    assume((azimuth >= 360 or azimuth < 0) or (tilt > 90 or tilt < 0) or gcr < 0)
    return (azimuth, tilt, gcr)


@given(atg=outside_az_tilt_gcr(), backtracking=booleans())
@example(atg=(9.0, 9.0, 0.0), backtracking="maybe")
@example(atg=(360.0, 0, 0), backtracking=True)
def test_singleaxis_tracking_outside(atg, backtracking):
    azimuth, tilt, gcr = atg
    with pytest.raises(ValidationError):
        models.SingleAxisTracking(
            axis_tilt=tilt, axis_azimuth=azimuth, gcr=gcr, backtracking=backtracking
        )


@pytest.mark.parametrize(
    "nw,se",
    [
        (dict(latitude=32.1, longitude=-110.0), dict(latitude=32.1, longitude=-110.0)),
        (dict(latitude=32.1, longitude=-110.0), dict(latitude=32.2, longitude=-110.0)),
        (dict(latitude=32.1, longitude=-110.0), dict(latitude=32.1, longitude=-110.3)),
        pytest.param(
            dict(latitude=32.1, longitude=-110.0),
            dict(latitude=32.1 - 1.1e-6, longitude=-110.0 + 1.1e-6),
            marks=pytest.mark.xfail(strict=True),
        ),
    ],
)
def test_boundingbox_limits(nw, se):
    with pytest.raises(ValidationError):
        models.BoundingBox(
            nw_corner=nw,
            se_corner=se,
        )


good_df = pd.DataFrame(
    {"ghi": 0, "dni": 0, "dhi": 0, "temp_air": 0, "wind_speed": 0},  # type: ignore
    index=pd.DatetimeIndex([pd.Timestamp("2021-04-04T00:00Z")]),  # type: ignore
)
clr_df = pd.DataFrame(
    {"aod700": 0, "precipitable_water": 0},  # type: ignore
    index=pd.DatetimeIndex([pd.Timestamp("2021-04-04T00:00Z")]),  # type: ignore
)


@pytest.mark.parametrize(
    "inp",
    [
        dict(),
        dict(
            location=dict(latitude=0, longitude=1.9, altitude="no"),
            fraction_of_total=0.1,
            weather_data=good_df,
            clearsky_data=clr_df,
        ),
        dict(
            location=dict(latitude=0, longitude=1.9, altitude=3818),
            fraction_of_total="invalid",
            weather_data=good_df,
            clearsky_data=clr_df,
        ),
        dict(
            location=dict(latitude=0, longitude=1.9, altitude=3818),
            fraction_of_total=0.38,
            weather_data=good_df.rename(columns={"ghi": "notok"}),
            clearsky_data=clr_df,
        ),
        dict(
            location=dict(latitude=0, longitude=1.9, altitude=3818),
            fraction_of_total=0.38,
            weather_data=good_df.reset_index(drop=True),
            clearsky_data=clr_df,
        ),
        dict(
            location=dict(latitude=0, longitude=1.9, altitude=3818),
            fraction_of_total=0.38,
            weather_data=0,
            clearsky_data=clr_df,
        ),
        dict(
            location=dict(latitude=0, longitude=1.9, altitude=3818),
            fraction_of_total=0.38,
            weather_data=good_df,
            clearsky_data=0,
        ),
        dict(
            location=dict(latitude=0, longitude=1.9, altitude=3818),
            fraction_of_total=0.38,
            weather_data=good_df,
            clearsky_data=clr_df.reset_index(drop=True),
        ),
        dict(
            location=dict(latitude=0, longitude=1.9, altitude=3818),
            fraction_of_total=0.38,
            weather_data=good_df,
            clearsky_data=clr_df.rename(columns={"aod700": "aod"}),
        ),
        pytest.param(
            dict(
                location=dict(latitude=0, longitude=1.9, altitude=3818),
                fraction_of_total=0.38,
                weather_data=good_df,
                clearsky_data=clr_df,
            ),
            marks=pytest.mark.xfail(strict=True),
        ),
    ],
)
def test_systemdata(inp):
    with pytest.raises(ValidationError):
        models.SystemData(**inp)
