import datetime as dt
from enum import Enum
from typing import Any, Union, Optional, List, Dict


import pandas as pd
import pvlib  # type: ignore
from pydantic import BaseModel, Field, root_validator, validator, PrivateAttr
from pydantic.fields import Undefined
from pydantic.types import UUID
import pytz
from shapely import geometry  # type: ignore


SYSTEM_ID = "6b61d9ac-2e89-11eb-be2a-4dc7a6bcd0d9"
SYSTEM_EXAMPLE = dict(
    name="Test PV System",
    boundary=dict(
        nw_corner=dict(
            latitude=32.05,
            longitude=-110.95,
        ),
        se_corner=dict(
            latitude=32.01,
            longitude=-110.85,
        ),
    ),
    ac_capacity=10.0,
    dc_ac_ratio=1.2,
    albedo=0.2,
    tracking=dict(
        tilt=20.0,
        azimuth=180.0,
    ),
)
# all compatible with luxon 1.25.0, most commen + Etc/GMT+offset
TIMEZONES = [
    tz
    for tz in pytz.common_timezones
    if not tz.startswith("US/") and tz not in ("America/Nuuk", "Antarctica/McMurdo")
] + [tz for tz in pytz.all_timezones if tz.startswith("Etc/GMT") and tz != "Etc/GMT0"]
SURFACE_ALBEDOS = pvlib.irradiance.SURFACE_ALBEDOS


# allows word chars, space, comma, apostrophe, hyphen, parentheses, underscore
# and empty string
def UserString(default: Any = Undefined, *, title: str = None, description: str = None):
    return Field(
        default,
        title=title,
        description=description,
        max_length=128,
        regex=r"^(?!\W+$)(?![_ ',\-\(\)]+$)[\w ',\-\(\)]*$",
    )


class ThisBase(BaseModel):
    class Config:
        extra = "forbid"


class FixedTracking(ThisBase):
    """Parameters for a fixed tilt array"""

    tilt: float = Field(
        ..., description="Tilt of modules in degrees from horizontal", ge=0, le=180
    )
    azimuth: float = Field(
        ...,
        description="Azimuth of modules relative to North in degrees",
        ge=0,
        lt=360.0,
    )


class SingleAxisTracking(ThisBase):
    """Parameters for a single axis tracking array"""

    axis_tilt: float = Field(
        ...,
        title="Axis Tilt",
        description="Tilt of tracker axis in degrees from horizontal",
        ge=0,
        le=90,
    )
    axis_azimuth: float = Field(
        ...,
        title="Axis Azimiuth",
        description="Azimuth of tracker axis clockwise from North in degrees",
        ge=0,
        lt=360.0,
    )
    gcr: float = Field(
        ...,
        title="GCR",
        description=(
            "Ground coverage ratio: ratio of module length to the spacing"
            " between trackers"
        ),
        ge=0,
    )
    backtracking: bool = Field(
        ..., description="True if the tracking system supports backtracking"
    )


class LatLon(ThisBase):
    latitude: float = Field(
        ..., description="Latitude of the system in degrees North", ge=31.0, le=38.0
    )
    longitude: float = Field(
        ...,
        description="Longitude of the system in degrees East",
        ge=-118.01,
        le=-103.01,
    )


class BoundingBox(ThisBase):
    """Bounding box of the PV array"""

    nw_corner: LatLon = Field(..., description="NW corner of the bounding box.")
    se_corner: LatLon = Field(..., description="SE corner of the bounding box.")
    _rect: geometry.Polygon = PrivateAttr()

    def __init__(self, **data):
        super().__init__(**data)
        self._rect = geometry.box(
            minx=self.nw_corner.longitude,
            miny=self.se_corner.latitude,
            maxx=self.se_corner.longitude,
            maxy=self.nw_corner.latitude,
        )

    @root_validator(skip_on_failure=True)
    def validate_extended_box(cls, values):
        nw_corner = values["nw_corner"]
        se_corner = values["se_corner"]
        if (
            abs(nw_corner.latitude - se_corner.latitude) < 1e-6
            or abs(nw_corner.longitude - se_corner.longitude) < 1e-6
        ):
            raise ValueError("Bounding box is too small for a meaningful result")
        return values


class PVSystem(ThisBase):
    """Parameters for an entire PV system at some location"""

    name: str = UserString(
        ...,
        description="Name of the system",
    )
    boundary: BoundingBox
    # find central lat/lons and lookup elevation from lat/lon
    ac_capacity: float = Field(
        ..., description="Total AC capcity of the plant in MW", gt=0
    )
    dc_ac_ratio: float = Field(..., description="Ratio of DC to AC capacity ", gt=0)
    # split into multiple inverters based on capacity and location
    # losses all set
    albedo: float = Field(
        ..., description="Albedo of the surface around the array", ge=0
    )
    tracking: Union[FixedTracking, SingleAxisTracking] = Field(
        ..., description="Parameters describing single-axis tracking or fixed mounting"
    )

    class Config:
        schema_extra = {"example": SYSTEM_EXAMPLE}


class StoredObjectID(ThisBase):
    object_id: UUID = Field(..., description="Unique identifier of the object")
    object_type: str = Field("system", description="Type of the object")

    class Config:
        # allow extra fields to go into Stored objects as they are
        # removed when serializing. Eases putting DB objects into models
        extra = "ignore"
        schema_extra = {
            "example": {
                "object_id": "6b61d9ac-2e89-11eb-be2a-4dc7a6bcd0d9",
                "object_type": "system",
            }
        }


class StoredObject(StoredObjectID):
    created_at: dt.datetime = Field(..., description="Datetime the object was created")
    modified_at: dt.datetime = Field(
        ..., description="Datetime the object was last modified"
    )

    class Config:
        schema_extra = {
            "example": {
                "object_id": "6b61d9ac-2e89-11eb-be2a-4dc7a6bcd0d9",
                "object_type": "system",
                "created_at": "2020-12-01T01:23:00+00:00",
                "modified_at": "2020-12-01T01:23:00+00:00",
            }
        }


class StoredPVSystem(StoredObject):

    definition: PVSystem

    class Config:
        schema_extra = {
            "example": {
                "object_id": "6b61d9ac-2e89-11eb-be2a-4dc7a6bcd0d9",
                "object_type": "system",
                "created_at": "2020-12-01T01:23:00+00:00",
                "modified_at": "2020-12-01T01:23:00+00:00",
                "definition": SYSTEM_EXAMPLE,
            }
        }


class UserInfo(StoredObject):
    """Information about the current user"""

    auth0_id: str = Field(..., description="User ID from Auth 0")


class Location(ThisBase):
    latitude: float
    longitude: float
    altitude: float


class SystemData(ThisBase):
    class Config:
        arbitrary_types_allowed = True

    location: Location = Field(
        ..., description="Values to create a pvlib.location.Location"
    )
    fraction_of_total: float = Field(
        ..., description="Fraction of total power for this data"
    )
    weather_data: pd.DataFrame = Field(
        ...,
        description=(
            "Has 'ghi', 'dni', 'dhi', 'temp_air', and 'wind_speed' columns with "
            " a DatetimeIndex"
        ),
    )
    clearsky_data: pd.DataFrame = Field(
        ...,
        description=(
            "Has 'ghi', 'dni', 'dhi', 'temp_air', and 'wind_speed' columns with "
            "a DatetimeIndex in order calculate expected clearsky power."
        ),
    )

    @validator("weather_data", "clearsky_data")
    def validate_df(cls, v):
        if not isinstance(v.index, pd.DatetimeIndex):
            raise TypeError("Must have pd.DatetimeIndex")
        if not set(v.columns) == {"ghi", "dni", "dhi", "temp_air", "wind_speed"}:
            raise ValueError(
                "Columns must be 'ghi', 'dni', 'dhi', 'temp_air' and 'wind_speed'"
            )
        return v


class DatasetEnum(str, Enum):
    nsrdb_2019 = "NSRDB_2019"


class DataStatusEnum(str, Enum):
    queued = "queued"
    running = "running"
    complete = "complete"
    statistics_missing = "statistics missing"
    timeseries_missing = "timeseries missing"
    error = "error"


class SystemDataMeta(ThisBase):
    system_id: UUID
    dataset: DatasetEnum
    version: Optional[str]
    system_modified: bool
    status: DataStatusEnum
    error: Union[List[Dict[str, Any]], Dict[str, Any]] = []
    created_at: dt.datetime
    modified_at: dt.datetime

    class Config:
        schema_extra = {
            "example": {
                "system_id": "6b61d9ac-2e89-11eb-be2a-4dc7a6bcd0d9",
                "dataset": "NSRDB_2019",
                "version": "v0.1",
                "system_modified": False,
                "status": "complete",
                "error": [],
                "created_at": "2020-12-01T01:23:00+00:00",
                "modified_at": "2020-12-01T01:23:00+00:00",
            }
        }


class ManagementSystemDataStatus(ThisBase):
    system_id: UUID
    dataset: str
    version: str
    status: str
    hash_changed: bool
    user: str
